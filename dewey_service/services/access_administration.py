"""Administrator access inventory and typed personal-token request history."""

from datetime import datetime, timezone

from daylily_tapdb import generic_instance, generic_instance_lineage
from fastapi import HTTPException

from dewey_service.registry_access import OPERATION_TEMPLATE, TOKEN_TEMPLATE, principal
from dewey_service.tapdb_backend import normalize_instance_payload, utc_now_iso


class AccessAdministrationMixin:
    def record_token_request(self, actor, *, method, route, status_code):
        with self.backend.session_scope(commit=True) as session:
            token = self.backend.find_by_euid(session, template_code=TOKEN_TEMPLATE, euid=actor.token_euid)
            if token is None:
                raise HTTPException(401, "Token record unavailable")
            event = self.backend.create_instance(
                session, template_code=OPERATION_TEMPLATE, name="Personal token request",
                json_addl={"operation": "personal_token_request", "actor": actor.subject,
                           "email": actor.email, "created_at": utc_now_iso(),
                           "method": method, "route": route, "status_code": status_code},
            )
            self.backend.create_lineage(session, parent=token, child=event, relationship_type="token_request")

    def _token_requests(self, session, token):
        return self.backend._template_query(session, template_code=OPERATION_TEMPLATE).join(
            generic_instance_lineage,
            generic_instance_lineage.child_instance_uid == generic_instance.uid,
        ).filter(generic_instance_lineage.parent_instance_uid == token.uid,
                 generic_instance_lineage.relationship_type == "token_request",
                 generic_instance_lineage.is_deleted.is_(False))

    def access_administration(self, kind, *, page=1, page_size=50, euid=None):
        if not principal().admin:
            raise HTTPException(403, "Dewey admin access required")
        if page < 1 or not 1 <= page_size <= 100:
            raise ValueError("page must be positive and page_size must be 1..100")
        with self.backend.session_scope(commit=False) as session:
            data = generic_instance.json_addl
            if kind == "tokens":
                query = self.backend._template_query(session, template_code=TOKEN_TEMPLATE)
            elif kind == "shares":
                query = self._share_query(session)
            elif kind == "users":
                tokens = self.backend._template_query(session, template_code=TOKEN_TEMPLATE).with_entities(
                    data["subject"].astext.label("subject"), data["email"].astext.label("email"))
                browsers = self.backend._template_query(session, template_code=OPERATION_TEMPLATE).filter(
                    data["operation"].astext == "browser_session_binding").with_entities(
                    data["actor"].astext.label("subject"), data["principal"]["email"].astext.label("email"))
                users = tokens.union(browsers).subquery()
                query = session.query(users.c.subject, users.c.email).order_by(users.c.email, users.c.subject)
                rows = query.offset((page - 1) * page_size).limit(page_size + 1).all()
                items = []
                from dewey_service.services.share_policy import EVENT_TEMPLATE
                for user in rows[:page_size]:
                    token_count = self.backend._template_query(session, template_code=TOKEN_TEMPLATE).filter(
                        data["subject"].astext == user.subject).count()
                    requests = self.backend._template_query(session, template_code=OPERATION_TEMPLATE).filter(
                        data["operation"].astext == "personal_token_request", data["actor"].astext == user.subject)
                    events = self.backend._template_query(session, template_code=EVENT_TEMPLATE).filter(
                        data["actor"].astext == user.subject)
                    items.append({"subject": user.subject, "email": user.email, "tokens_issued": token_count,
                                  "recorded_token_requests": requests.count(), "share_events": events.count(),
                                  "shares_owned": self._share_query(session).filter(data["owner_subject"].astext == user.subject).count()})
                return {"items": items,
                        "page": page, "has_more": len(rows) > page_size,
                        "scope": "All users recorded in Dewey browser bindings or issued personal tokens; Login owns the identity directory."}
            elif kind == "usage":
                token = self.backend.find_by_euid(session, template_code=TOKEN_TEMPLATE, euid=euid)
                if token is None:
                    raise HTTPException(404, "Token not found")
                query = self._token_requests(session, token)
            else:
                raise ValueError("Unknown access inventory")
            rows = query.order_by(generic_instance.created_dt.desc(), generic_instance.euid).offset(
                (page - 1) * page_size).limit(page_size + 1).all()
            items = []
            for row in rows[:page_size]:
                value = normalize_instance_payload(row)
                if kind == "usage":
                    item = {k: value.get(k) for k in ("created_at", "method", "route", "status_code")}
                elif kind == "tokens":
                    item = {k: value.get(k) for k in ("subject", "email", "roles", "status", "expires_at", "revoked_at")}
                    if item["status"] == "active" and datetime.fromisoformat(item["expires_at"]) <= datetime.now(timezone.utc):
                        item["status"] = "expired"
                    usage = self._token_requests(session, row)
                    item["request_count"] = usage.count()
                    latest = usage.order_by(generic_instance.created_dt.desc()).first()
                    item["last_used_at"] = normalize_instance_payload(latest)["created_at"] if latest else None
                    item["usage_coverage"] = "Recorded after personal-token request auditing was deployed"
                else:
                    item = {k: value.get(k) for k in ("owner_subject", "owner_email", "status", "expires_at", "policy_revision", "purpose")}
                    if item["status"] == "active" and item["expires_at"] and datetime.fromisoformat(item["expires_at"]) <= datetime.now(timezone.utc):
                        item["status"] = "expired"
                    from dewey_service.services.share_policy import EVENT_TEMPLATE
                    events = self.backend._template_query(session, template_code=EVENT_TEMPLATE).join(
                        generic_instance_lineage, generic_instance_lineage.child_instance_uid == generic_instance.uid,
                    ).filter(generic_instance_lineage.parent_instance_uid == row.uid,
                             generic_instance_lineage.relationship_type == "share_event",
                             generic_instance_lineage.is_deleted.is_(False))
                    item["audit_event_count"] = events.count()
                    latest = events.order_by(generic_instance.created_dt.desc()).first()
                    item["last_event_at"] = normalize_instance_payload(latest)["created_at"] if latest else None
                item.update(euid=row.euid, name=row.name, issued_at=row.created_dt.isoformat())
                items.append(item)
            return {"items": items, "page": page, "has_more": len(rows) > page_size}
