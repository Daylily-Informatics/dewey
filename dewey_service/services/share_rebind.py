"""Audited equivalent storage-reference changes; this module never moves S3 data."""

from __future__ import annotations

import json
from hashlib import sha256
from itertools import zip_longest

from fastapi import HTTPException

from dewey_service.registry_access import principal
from dewey_service.storage import storage_authorization_context
from dewey_service.tapdb_backend import (
    ARTIFACT_LOCATION_REVISION_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)


def equivalent_objects(source, destination):
    if source.size is None or source.size != destination.size:
        raise ValueError("Source and destination byte counts differ or are unknown")
    same_version = (source.bucket, source.key, source.version_id) == (
        destination.bucket,
        destination.key,
        destination.version_id,
    ) and bool(source.version_id)
    checksum = (
        source.checksum_type == destination.checksum_type == "FULL_OBJECT"
        and bool(source.sha256)
        and source.sha256 == destination.sha256
    )
    if not (same_version or checksum):
        raise ValueError(
            "Equivalent content requires matching S3 FULL_OBJECT SHA256; ETags and unverified supplied hashes are insufficient"
        )
    return {
        "size": source.size,
        "sha256": source.sha256 if checksum else None,
        "source_version_id": source.version_id,
        "destination_version_id": destination.version_id,
    }


def lock_storage_coordinate(session, uri, version_id):
    """Same coordinate lock used by registry registration; caller orders multiple coordinates."""
    from sqlalchemy import text

    key = int.from_bytes(
        sha256((uri + "\0" + str(version_id or "")).encode()).digest()[:8], "big", signed=True
    )
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


class ShareRebindMixin:
    def rebind_artifact_location(
        self, euid, *, storage_uri, expected_location_revision, reason, version_id=None
    ):
        self._require_sharing()
        if (
            type(expected_location_revision) is not int
            or expected_location_revision < 1
            or not isinstance(reason, str)
            or not reason.strip()
        ):
            raise ValueError("Reviewed positive location revision and a reason are required")
        from daylily_tapdb import generic_instance
        from sqlalchemy import and_, func, or_

        with self.backend.session_scope(commit=True) as session:
            artifact = self._registry_record(session, euid, action="edit")
            old = normalize_instance_payload(artifact)
            if old.get("storage_backend") != "s3":
                raise ValueError("Only explicit S3-backed artifact locations can be rebound")
            revision = int(old.get("location_revision", 1))
            if revision != expected_location_revision:
                raise HTTPException(409, "Artifact location changed; review the current revision")
            prefix = old["storage_kind"] == "prefix"
            bucket, key, uri = self._parse_share_s3_uri(storage_uri, require_prefix=prefix)
            if prefix and version_id is not None:
                raise ValueError("A prefix cannot have a single object version ID")
            if not prefix and not key:
                raise ValueError("An object rebind requires an exact destination key")
            if (bucket, key, version_id) == (old["bucket"], old["key"], old.get("version_id")):
                raise ValueError("Destination is already the current artifact location")
            self.require_storage_access(bucket, key, action="metadata", session=session)
            self.require_storage_access(
                old["bucket"], old["key"], action="metadata", session=session
            )
            new = {
                **old,
                "bucket": bucket,
                "key": key,
                "storage_uri": uri,
                "source_uri": uri,
                "version_id": version_id,
                "location_revision": revision + 1,
            }
            new["artifact_identity_key"] = self._artifact_identity_key(new)
            for coordinate in sorted(
                {
                    (old["storage_uri"], str(old.get("version_id") or "")),
                    (uri, str(version_id or "")),
                }
            ):
                lock_storage_coordinate(session, *coordinate)
            for identity in sorted({old["artifact_identity_key"], new["artifact_identity_key"]}):
                self.backend.lock_external_key(session, operation="artifact.identity", key=identity)
            # Registration takes coordinate/identity locks before the native row.
            # Keep the same order, then reread the reviewed revision under lock.
            session.expire(artifact)
            artifact = self._registry_record(session, euid, action="edit", lock=True)
            current = normalize_instance_payload(artifact)
            if int(current.get("location_revision", 1)) != revision or any(
                current.get(field) != old.get(field)
                for field in ("bucket", "key", "version_id", "storage_uri", "artifact_identity_key")
            ):
                raise HTTPException(409, "Artifact location changed; review the current revision")
            payload = generic_instance.json_addl
            collision = (
                self._registry_query(session, scopes=("artifact",), authorize=False)
                .filter(
                    generic_instance.uid != artifact.uid,
                    or_(
                        payload["artifact_identity_key"].astext == new["artifact_identity_key"],
                        and_(
                            payload["storage_uri"].astext == uri,
                            payload["storage_kind"].astext == old["storage_kind"],
                            func.coalesce(payload["version_id"].astext, "")
                            == str(version_id or ""),
                        ),
                    ),
                )
                .first()
            )
            if collision is not None:
                raise HTTPException(409, "Destination is already registered to another artifact")
            storage = self._require_storage()

            def scope(b, k, action):
                if action != "metadata" or not any(
                    b == v["bucket"] and (k.startswith(v["key"]) if prefix else k == v["key"])
                    for v in (old, new)
                ):
                    raise HTTPException(
                        403, "Rebind evidence request exceeds the reviewed coordinates"
                    )

            def objects(location):
                if not prefix:
                    yield (
                        "",
                        storage.head_object(
                            bucket=location["bucket"],
                            key=location["key"],
                            version_id=location.get("version_id"),
                            request_payer=self._request_payer_for_bucket(location["bucket"]),
                            checksum_mode=True,
                        ),
                    )
                    return
                token, seen = None, set()
                while True:
                    page = storage.list_share_candidates(
                        bucket=location["bucket"],
                        prefix=location["key"],
                        limit=1000,
                        continuation_token=token,
                        request_payer=self._request_payer_for_bucket(location["bucket"]),
                    )
                    for obj in page["objects"]:
                        head = storage.head_object(
                            bucket=obj.bucket,
                            key=obj.key,
                            request_payer=self._request_payer_for_bucket(obj.bucket),
                            checksum_mode=True,
                        )
                        yield obj.key[len(location["key"]) :], head
                    token = page["next_continuation_token"]
                    if not token:
                        return
                    if token in seen:
                        raise ValueError("Storage inventory repeated a continuation token")
                    seen.add(token)

            manifest, count, byte_count = sha256(), 0, 0
            with storage_authorization_context(scope):
                for left, right in zip_longest(objects(old), objects(new)):
                    if left is None or right is None or left[0] != right[0]:
                        raise ValueError(
                            "Prefix inventories do not contain exactly the same relative keys"
                        )
                    evidence = equivalent_objects(left[1], right[1])
                    manifest.update(
                        json.dumps(
                            {"relative_key": left[0], **evidence},
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()
                        + b"\n"
                    )
                    count += 1
                    byte_count += evidence["size"]
            if count == 0:
                raise ValueError("An empty prefix cannot establish artifact content equivalence")
            fields = (
                "storage_backend",
                "storage_kind",
                "bucket",
                "key",
                "version_id",
                "storage_uri",
                "source_uri",
                "artifact_identity_key",
                "checksums",
                "size",
            )
            history = self.backend.create_instance(
                session,
                template_code=ARTIFACT_LOCATION_REVISION_TEMPLATE,
                name="Verified artifact location revision",
                json_addl={
                    "location_revision": revision + 1,
                    "previous_location_revision": revision,
                    "previous_location": {k: old.get(k) for k in fields},
                    "location": {k: new.get(k) for k in fields},
                    "manifest_sha256": manifest.hexdigest(),
                    "inventory_complete": True,
                    "object_count": count,
                    "total_bytes": byte_count,
                    "reason": reason.strip(),
                    "actor_subject": principal().subject,
                    "created_at": utc_now_iso(),
                },
            )
            self.backend.create_lineage(
                session,
                parent=artifact,
                child=history,
                relationship_type="artifact_location_revision",
            )
            self.backend.update_instance_json(
                session,
                artifact,
                {
                    k: new[k]
                    for k in (
                        "bucket",
                        "key",
                        "version_id",
                        "storage_uri",
                        "source_uri",
                        "artifact_identity_key",
                        "location_revision",
                    )
                },
            )
            # Link each affected share to the native location evidence, retaining prior evidence.
            for share in self._share_related(
                session, artifact, relationship="has_share", kind="share"
            ):
                if (
                    share.type == "share"
                    and normalize_instance_payload(share).get("schema_version") == 3
                    and any(m.uid == artifact.uid for m in self._share_members(session, share))
                ):
                    self._event(
                        session,
                        share,
                        event_type="location_rebound",
                        decision="change",
                        target=artifact,
                        details={
                            "location_revision": revision + 1,
                            "manifest_sha256": manifest.hexdigest(),
                            "object_count": count,
                            "total_bytes": byte_count,
                            "inventory_complete": True,
                            "reason": reason,
                        },
                    )
                    self.backend.create_lineage(
                        session,
                        parent=share,
                        child=history,
                        relationship_type="share_location_evidence",
                    )
            return {
                "artifact_euid": artifact.euid,
                "location_revision": revision + 1,
                "evidence_euid": history.euid,
                "manifest_sha256": manifest.hexdigest(),
                "object_count": count,
                "total_bytes": byte_count,
                "inventory_complete": True,
                "storage_uri": uri,
                "physical_data_changed": False,
            }
