"""Offline contracts for human annotation descriptions and exact SeqNAS context.

Execution remains separately gated; these tests never contact AWS or TapDB.
"""
from contextlib import nullcontext
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from itsdangerous import URLSafeTimedSerializer

from dewey_service import annotation_api as api
from dewey_service.integrations.tapdb_external_references import build_external_target
from dewey_service.registry_access import Principal
from dewey_service.services.artifacts import ArtifactServiceMixin
from dewey_service.services.base import BaseDeweyService


def context(**changes):
    target = {"scope": "attempt", "run_identity_key": "a" * 64, "run_name": "run-one",
              "attempt_id": "attempt-one", "dataset_revision": "revision-one", "xfer_name": "run-one / attempt-one"}
    return api.AnnotationContext(**{**dict(target=target,
        target_url="https://kahlo.example.invalid/seqnas/xfer/attempt-one", description="Supporting spreadsheet"), **changes})


def test_context_rejects_other_attempt_or_noncanonical_url():
    api.validate_context(context())
    for url in ("https://kahlo.example.invalid/seqnas/xfer/attempt-other",
                "https://kahlo.example.invalid/seqnas/xfer/attempt-one?token=temporary",
                "http://kahlo.example.invalid/seqnas/xfer/attempt-one"):
        with pytest.raises(HTTPException):
            api.validate_context(context(target_url=url))
    body = context()
    with pytest.raises(HTTPException):
        api.validate_context(context(target={**body.target, "xfer_name": ""}))


def test_temporary_annotation_identity_is_explicitly_opaque():
    identifier = "human-one:" + str(uuid4())
    value = build_external_target({"external_system": "kahlo", "external_object_type": "seqnas_annotation",
                                   "external_object_id": identifier})
    assert value.namespace == "kahlo"
    assert value.kind == "seqnas_annotation"
    assert value.value == identifier


def test_existing_item_replay_rechecks_human_edit_access_before_returning():
    calls = []
    record = SimpleNamespace(euid="fixture-file")
    def find(session, euid, **kwargs):
        calls.append((euid, kwargs))
        return record
    service = SimpleNamespace(
        backend=SimpleNamespace(session_scope=lambda **kw: nullcontext(SimpleNamespace(execute=lambda *args: None))),
        _fingerprint=BaseDeweyService._fingerprint,
        _registry_record=find,
        _idempotency_replay=lambda *args, **kw: SimpleNamespace(response={"euid": "fixture-file"}),
    )
    actor = Principal(subject="human-one", internal=True, roles=("READ_WRITE",))
    result = api.link_context(service, actor, "fixture-file", str(uuid4()), context())
    assert result == {"euid": "fixture-file"}
    assert calls == [("fixture-file", {"action": "edit", "lock": True})]


def test_managed_description_is_signed_and_uses_the_exact_native_location():
    stored = []
    service = SimpleNamespace(
        managed_storage_bucket="fixture-bucket", managed_storage_prefix="annotations", upload_session_ttl_seconds=300,
        _safe_filename=BaseDeweyService._safe_filename, _fingerprint=BaseDeweyService._fingerprint,
        _storage_uri=ArtifactServiceMixin._storage_uri,
        _upload_serializer=URLSafeTimedSerializer("offline-fixture-secret"),
        backend=SimpleNamespace(session_scope=lambda **kw: nullcontext(object())),
        _idempotency_replay=lambda *args, **kw: None,
        _store_idempotency=lambda *args, **kw: stored.append(kw),
        _require_storage=lambda: SimpleNamespace(generate_presigned_upload=lambda **kw: {
            "method": "PUT", "url": "https://storage.example.invalid/managed", "headers": {}}),
    )
    service._managed_key = lambda **kw: ArtifactServiceMixin._managed_key(service, **kw)
    actor = Principal(subject="human-one", internal=True)
    operation = str(uuid4())
    body = api.CreateAnnotationUpload(**context().model_dump(), filename="sheet.xlsx", size=123)
    spec = api.managed_payload(service, actor, operation, body)
    code, result = ArtifactServiceMixin.create_upload_session(service, **spec,
        idempotency_key=f"annotation:{actor.subject}:{operation}:create")
    token = service._upload_serializer.loads(result["upload_token"])
    assert code == 201
    assert token["description"] == "Supporting spreadsheet"
    assert token["metadata"]["run_name"] == "run-one"
    assert token["metadata"]["xfer_name"] == "run-one / attempt-one"
    assert token["key"] == api.managed_key(service, actor, operation, spec)
    assert api.managed_receipt(service, actor, operation, result["upload_token"])["key"] == token["key"]
    assert stored[0]["idempotency_key"] == f"annotation:{actor.subject}:{operation}:create"
