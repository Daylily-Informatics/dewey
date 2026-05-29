from __future__ import annotations

from dewey_service.audit import authenticated_user_email_context
from dewey_service.service import DeweyService
from dewey_service.tapdb_backend import ARTIFACT_TEMPLATE
from tests.support.service_fakes import _FakeStorageClient, _InMemoryBackend


def _artifact_payload(backend: _InMemoryBackend, artifact_euid: str) -> dict[str, object]:
    with backend.session_scope(commit=False) as session:
        instance = backend.find_by_euid(
            session,
            template_code=ARTIFACT_TEMPLATE,
            euid=artifact_euid,
        )
    assert instance is not None
    return dict(instance.json_addl)


def test_authenticated_user_create_stamps_tapdb_object_email(
    service: DeweyService,
    backend: _InMemoryBackend,
) -> None:
    with authenticated_user_email_context("Operator@LSMC.BIO"):
        status_code, artifact = service.register_artifact(
            artifact_type="report",
            storage_backend="s3",
            bucket="bucket-1",
            key="reports/a.txt",
            version_id=None,
            size=12,
            checksums={},
            content_type="text/plain",
            original_filename="a.txt",
            producer_system=None,
            producer_object_euid=None,
            storage_class=None,
            availability_status="available",
            metadata={},
            idempotency_key="audit-create-1",
        )

    payload = _artifact_payload(backend, artifact["artifact_euid"])

    assert status_code == 201
    assert payload["created_by_email"] == "operator@lsmc.bio"
    assert payload["updated_by_email"] == "operator@lsmc.bio"


def test_authenticated_user_edit_stamps_updated_email_without_backfilling_creator(
    service: DeweyService,
    backend: _InMemoryBackend,
    storage: _FakeStorageClient,
) -> None:
    storage.seed_object(bucket="bucket-2", key="reports/b.txt", size=24)
    with authenticated_user_email_context(None):
        _, artifact = service.register_artifact(
            artifact_type="report",
            storage_backend="s3",
            bucket="bucket-2",
            key="reports/b.txt",
            version_id=None,
            size=24,
            checksums={},
            content_type="text/plain",
            original_filename="b.txt",
            producer_system=None,
            producer_object_euid=None,
            storage_class=None,
            availability_status="available",
            metadata={},
            idempotency_key="audit-edit-create-1",
        )

    before = _artifact_payload(backend, artifact["artifact_euid"])
    with authenticated_user_email_context("Editor@LSMC.BIO"):
        service.verify_artifact_storage(
            artifact_euid=artifact["artifact_euid"],
            idempotency_key="audit-edit-1",
        )
    after = _artifact_payload(backend, artifact["artifact_euid"])

    assert "created_by_email" not in before
    assert "updated_by_email" not in before
    assert "created_by_email" not in after
    assert after["updated_by_email"] == "editor@lsmc.bio"


def test_missing_or_service_auth_context_does_not_invent_audit_email(
    service: DeweyService,
    backend: _InMemoryBackend,
) -> None:
    with authenticated_user_email_context(None):
        _, artifact = service.register_artifact(
            artifact_type="report",
            storage_backend="s3",
            bucket="bucket-3",
            key="reports/c.txt",
            version_id=None,
            size=36,
            checksums={},
            content_type="text/plain",
            original_filename="c.txt",
            producer_system=None,
            producer_object_euid=None,
            storage_class=None,
            availability_status="available",
            metadata={},
            idempotency_key="audit-no-user-1",
        )

    payload = _artifact_payload(backend, artifact["artifact_euid"])

    assert "created_by_email" not in payload
    assert "updated_by_email" not in payload
