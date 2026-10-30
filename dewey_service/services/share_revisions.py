"""Native current-scope revisions and durable, non-reassignable share aliases."""

from __future__ import annotations

import re

from fastapi import HTTPException

from dewey_service.registry_access import principal, require_record
from dewey_service.tapdb_backend import (
    SHARE_ALIAS_TEMPLATE,
    SHARE_REVISION_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)


def normalize_slug(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", value):
        raise ValueError(
            "Slug must contain 3–63 lowercase ASCII letters/digits/hyphens and start/end with a letter or digit"
        )
    if value in {
        "fetch",
        "api",
        "auth",
        "login",
        "logout",
        "admin",
        "static",
        "recipient",
        "shares",
        "healthz",
        "readyz",
    }:
        raise ValueError("Slug is reserved")
    # Owning services allocate EUIDs; aliases cannot claim their namespace.
    if re.match(r"^[a-z]-[a-z0-9]+-", value):
        raise ValueError("Slug cannot occupy the EUID namespace")
    return value


class ShareRevisionMixin:
    def _validate_report_selection(self, policy, members):
        if policy["content_mode"] != "www":
            return
        from dewey_service.services.share_policy import selected

        path = policy["report_entrypoint"]
        if len(members) == 1:
            target = members[0]
        else:
            target_euid, separator, path = path.partition("/")
            target = next((member for member in members if member.euid == target_euid), None)
            if not separator or target is None:
                raise ValueError(
                    "A multi-target WWW entrypoint must begin with its persisted target EUID"
                )
        member = self._artifact_member_from_instance(target)
        if member["target_kind"] == "artifact_object":
            if path != member["filename"] or policy["report_bundle_root"]:
                raise ValueError(
                    "An object WWW entrypoint must match its stable filename and use an empty bundle root"
                )
        elif not path or not path.startswith(policy["report_bundle_root"]):
            raise ValueError(
                "WWW entrypoint must be inside the selected target's report bundle root"
            )
        if not selected(path, policy["include_patterns"], policy["exclude_patterns"]):
            raise ValueError("WWW entrypoint is excluded by the share selection")

    def _share_alias_query(self, session, *, lock=False):
        from daylily_tapdb import generic_instance

        template = self.backend.templates.get_template(
            session, SHARE_ALIAS_TEMPLATE, domain_code=self.backend.domain_code
        )
        if template is None:
            raise HTTPException(503, "Native share alias template is missing")
        query = session.query(generic_instance).filter(
            generic_instance.template_uid == template.uid,
            generic_instance.type == "share_alias",
            generic_instance.domain_code == self.backend.domain_code,
            generic_instance.is_deleted.is_(False),
        )
        return query.with_for_update() if lock else query

    def _find_share_alias(self, session, slug, *, lock=False):
        from daylily_tapdb import generic_instance

        return (
            self._share_alias_query(session, lock=lock)
            .filter(generic_instance.json_addl["slug"].astext == slug)
            .one_or_none()
        )

    def _share_aliases(self, session, share):
        from daylily_tapdb import generic_instance, generic_instance_lineage

        aliases = (
            self._share_alias_query(session)
            .join(
                generic_instance_lineage,
                generic_instance_lineage.parent_instance_uid == generic_instance.uid,
            )
            .filter(
                generic_instance_lineage.child_instance_uid == share.uid,
                generic_instance_lineage.relationship_type == "share_alias_target",
                generic_instance_lineage.is_deleted.is_(False),
            )
            .order_by(generic_instance.euid)
            .all()
        )
        return [
            {
                "alias_euid": alias.euid,
                "slug": normalize_instance_payload(alias)["slug"],
                "status": normalize_instance_payload(alias)["status"],
                "fetch_path": "/fetch/" + normalize_instance_payload(alias)["slug"],
            }
            for alias in aliases
        ]

    def list_share_aliases(self, share_euid):
        self._require_sharing()
        with self.backend.session_scope(commit=False) as session:
            share = self._canonical_share(session, share_euid)
            if not self._registry_share_manager(session, share):
                raise HTTPException(403, "Share management permission required")
            return self._share_aliases(session, share)

    def _share_revision(self, session, share):
        revision = normalize_instance_payload(share)["policy_revision"]
        scopes = [
            s
            for s in self._share_related(
                session, share, relationship="share_revision", kind="share_revision"
            )
            if normalize_instance_payload(s).get("policy_revision") == revision
        ]
        if len(scopes) != 1:
            raise HTTPException(503, "Share has no unique current native scope revision")
        return scopes[0]

    def _write_share_revision(self, session, share, members, revision, *, policy):
        scope = self.backend.create_instance(
            session,
            template_code=SHARE_REVISION_TEMPLATE,
            name="Share scope revision",
            json_addl={
                "schema_version": 3,
                "policy_revision": revision,
                "created_at": utc_now_iso(),
                "policy": policy,
            },
        )
        self.backend.create_lineage(
            session, parent=share, child=scope, relationship_type="share_revision"
        )
        for member in members:
            self.backend.create_lineage(
                session, parent=scope, child=member, relationship_type="share_revision_target"
            )
        return scope

    def _assert_share_delegation(self, session, members):
        """Check the creator's targets and registered protected descendants once, never the recipient's ACL."""
        from daylily_tapdb import generic_instance
        from sqlalchemy import and_, func, literal, or_

        for member in members:
            require_record(self.backend, session, member, "share")
            data = normalize_instance_payload(member)
            key = data["key"]
            if data.get("storage_kind") == "prefix" and key:
                key = key.rstrip("/") + "/"
            coordinate = generic_instance.json_addl
            registered_prefix = func.rtrim(coordinate["key"].astext, "/") + "/"
            conditions = [
                coordinate["key"].astext == key,
                and_(
                    coordinate["storage_kind"].astext == "prefix",
                    or_(
                        coordinate["key"].astext == "",
                        func.left(literal(key), func.length(registered_prefix))
                        == registered_prefix,
                    ),
                ),
            ]
            if data.get("storage_kind") == "prefix":
                conditions.append(func.left(coordinate["key"].astext, len(key)) == key)
            rows = (
                self._registry_query(session, scopes=("artifact",), authorize=False)
                .filter(
                    coordinate["storage_backend"].astext == "s3",
                    coordinate["bucket"].astext == data["bucket"],
                    or_(*conditions),
                )
                .all()
            )
            for row in rows:
                policies = self.backend.list_children(
                    session, parent=row, relationship_type="registry_policy"
                )
                if len(policies) != 1:
                    raise HTTPException(503, "Registered target lacks a unique delegation policy")
                if normalize_instance_payload(policies[0]).get("explicit_restriction"):
                    require_record(self.backend, session, row, "share")

    def claim_share_slug(self, share_euid, slug, *, policy_revision):
        self._require_sharing()
        slug = normalize_slug(slug)
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, share_euid, lock=True)
            if not self._registry_share_manager(session, share):
                raise HTTPException(403, "Share management permission required")
            data = normalize_instance_payload(share)
            if policy_revision != data["policy_revision"]:
                raise HTTPException(409, "Share policy changed; reload")
            alias, created = self.backend.claim_global_instance(
                session,
                template_code=SHARE_ALIAS_TEMPLATE,
                identity_key="dewey:share-slug:" + slug,
                name=slug,
                json_addl={"slug": slug, "status": "active", "created_at": utc_now_iso()},
                command_evidence={"operation": "share.slug.claim", "slug": slug},
            )
            if not created:
                linked = self._share_related(
                    session, alias, relationship="share_alias_target", kind="share"
                )
                if (
                    normalize_instance_payload(alias).get("status") != "active"
                    or len(linked) != 1
                    or linked[0].uid != share.uid
                ):
                    raise HTTPException(409, "Slug is already claimed or permanently retired")
            else:
                self.backend.create_lineage(
                    session, parent=alias, child=share, relationship_type="share_alias_target"
                )
                self._event(
                    session,
                    share,
                    event_type="slug_claimed",
                    decision="change",
                    details={"slug": slug},
                )
            return {
                "slug": slug,
                "alias_euid": alias.euid,
                "share_euid": share.euid,
                "fetch_path": "/fetch/" + slug,
                "canonical_fetch_path": "/fetch/" + share.euid,
            }

    def revoke_share_slug(self, share_euid, slug, *, policy_revision):
        self._require_sharing()
        slug = normalize_slug(slug)
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, share_euid, lock=True)
            if not self._registry_share_manager(session, share):
                raise HTTPException(403, "Share management permission required")
            if normalize_instance_payload(share)["policy_revision"] != policy_revision:
                raise HTTPException(409, "Share policy changed; reload")
            alias = self._find_share_alias(session, slug, lock=True)
            linked = (
                []
                if alias is None
                else self._share_related(
                    session, alias, relationship="share_alias_target", kind="share"
                )
            )
            if len(linked) != 1 or linked[0].uid != share.uid:
                raise HTTPException(404, "Share alias not found")
            self.backend.update_instance_json(
                session, alias, {"status": "retired", "retired_at": utc_now_iso()}
            )
            self._event(
                session, share, event_type="slug_retired", decision="revoke", details={"slug": slug}
            )
            return {"slug": slug, "status": "retired", "reassignable": False}

    def resolve_share_identifier(self, identifier):
        self._require_sharing()
        if (
            not isinstance(identifier, str)
            or not identifier
            or "/" in identifier
            or len(identifier) > 128
        ):
            raise ValueError("An exact share EUID or slug is required")
        denied = None
        with self.backend.session_scope(commit=True) as session:
            share = self._share_query(session).filter_by(euid=identifier).first()
            if share is None:
                alias = self._find_share_alias(session, identifier)
                if alias is None or normalize_instance_payload(alias).get("status") != "active":
                    raise HTTPException(404, "Share not found")
                linked = self._share_related(
                    session, alias, relationship="share_alias_target", kind="share"
                )
                if len(linked) != 1 or linked[0].type != "share":
                    raise HTTPException(503, "Share alias has invalid native authority")
                share = linked[0]
            share = self._canonical_share(session, share.euid)
            try:
                self._require_recipient(session, share)
            except HTTPException as exc:
                if exc.status_code != 403:
                    raise
                self._event(
                    session,
                    share,
                    event_type="authorization",
                    decision="deny",
                    details={
                        "action": "resolve",
                        "reason": str(exc.detail),
                        "status_code": exc.status_code,
                    },
                )
                denied = exc
            else:
                data = normalize_instance_payload(share)
                # Container metadata is visible to a recipient; file disclosure still
                # passes the exact-object grant/path evaluator.
                from datetime import datetime, timezone

                from dewey_service.services.share_policy import expiry, recipient_matches

                targets = set()
                for grant in self._share_grants(session, share):
                    rule = normalize_instance_payload(grant)
                    if (
                        rule.get("status") == "active"
                        and rule.get("policy_revision") == data["policy_revision"]
                        and expiry(rule["expires_at"]) > datetime.now(timezone.utc)
                        and recipient_matches(rule, principal().email)
                    ):
                        targets.update(t.euid for t in self._grant_targets(session, grant))
                scope_members = self._share_members(session, share)
                members = [
                    self._artifact_member_from_instance(t)
                    for t in scope_members
                    if t.euid in targets
                ]
                return {
                    "share_euid": share.euid,
                    "euid": share.euid,
                    "fetch_path": "/fetch/" + share.euid,
                    "name": share.name,
                    "policy_revision": data["policy_revision"],
                    "activation_generation": data.get("activation_generation", 0),
                    "content_mode": data["content_mode"],
                    "report_entrypoint": data.get("report_entrypoint"),
                    "report_bundle_root": data.get("report_bundle_root", ""),
                    "expires_at": data["expires_at"],
                    "target_count": len(members),
                    "namespaced": len(scope_members) > 1,
                    "is_collection": len(scope_members) != 1
                    or not members
                    or members[0]["target_kind"] != "artifact_object",
                    "members": members,
                }
        # Raising inside the write scope would roll back the denial receipt.
        if denied is not None:
            raise denied

    def resolve_share_fetch(self, identifier, relative_path=""):
        resolved = self.resolve_share_identifier(identifier)
        members = resolved["members"]
        if (
            not isinstance(relative_path, str)
            or "\\" in relative_path
            or "\x00" in relative_path
            or relative_path.startswith("/")
            or any(p in {".", "..", ""} for p in relative_path.rstrip("/").split("/"))
            and relative_path
        ):
            raise ValueError("Invalid root-relative fetch path")
        if len(members) == 1 and not resolved["namespaced"]:
            member, path = members[0], relative_path
        else:
            target, separator, path = relative_path.partition("/")
            member = next((m for m in members if m["artifact_euid"] == target), None)
            if member is None or not separator:
                raise HTTPException(404, "A namespaced member path is required")
        if member["target_kind"] == "artifact_object":
            if path not in {"", member["filename"]}:
                raise HTTPException(404, "Shared object path not found")
            path = ""
        elif not path:
            raise HTTPException(400, "A file path or manifest/tar representation is required")
        return self.authorize_share_object(resolved["share_euid"], member["artifact_euid"], path)
