from __future__ import annotations

import pytest

from dewey_service.literature import ViewerContext
from dewey_service.service import DeweyService


def test_literature_save_reuses_artifact_and_hides_private_saves(
    service: DeweyService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _PdfResponse:
        status_code = 200
        headers = {"content-type": "application/pdf"}
        content = b"%PDF-1.7 test pdf"

        def raise_for_status(self) -> None:
            return

    monkeypatch.setattr(
        "dewey_service.services.literature.requests.get",
        lambda *args, **kwargs: _PdfResponse(),
    )

    owner = ViewerContext(
        subject="sub-1",
        email="owner@example.com",
        groups=("dewey-readwrite",),
    )
    collaborator = ViewerContext(subject="sub-2", email="collab@example.com", groups=("reviewers",))
    auditor = ViewerContext(subject="sub-3", email="auditor@example.com", groups=("reviewers",))

    code1, first = service.save_literature(
        viewer=owner,
        pmid="123456",
        save_mode="auto",
        visibility_scope="private",
        allowed_users=[],
        allowed_groups=[],
        idempotency_key="lit-save-1",
    )
    code2, second = service.save_literature(
        viewer=collaborator,
        pmid="123456",
        save_mode="external_reference",
        visibility_scope="restricted",
        allowed_users=[auditor.email],
        allowed_groups=[],
        idempotency_key="lit-save-2",
    )

    assert code1 == 201
    assert code2 == 201
    assert first["artifact"]["artifact_euid"] == second["artifact"]["artifact_euid"]
    assert service.list_my_literature_saves(viewer=owner)[0]["artifact"]["pmid"] == "123456"

    owner_search = service.search_literature(viewer=owner, query="Gene Therapy")
    assert owner_search["items"][0]["saved_by_me"] is True
    assert owner_search["items"][0]["saved_by_others_count"] == 0

    auditor_search = service.search_literature(viewer=auditor, query="Gene Therapy")
    assert auditor_search["items"][0]["saved_by_me"] is False
    assert auditor_search["items"][0]["saved_by_others_count"] == 1
    assert auditor_search["items"][0]["visible_owner_labels"] == ["collab@example.com"]


def test_literature_external_artifact_promotes_in_place(
    service: DeweyService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    viewer = ViewerContext(
        subject="sub-1",
        email="owner@example.com",
        groups=("dewey-readwrite",),
    )

    first_code, first = service.save_literature(
        viewer=viewer,
        pmid="789012",
        save_mode="external_reference",
        visibility_scope="private",
        allowed_users=[],
        allowed_groups=[],
        idempotency_key="lit-promote-1",
    )
    assert first_code == 201
    assert first["artifact"]["metadata"]["storage_mode"] == "external_reference"

    service.literature.records["789012"]["best_fulltext_url"] = (
        "https://europepmc.org/articles/PMC789012?pdf=render"
    )
    service.literature.records["789012"]["findit_reason"] = None

    class _PdfResponse:
        status_code = 200
        headers = {"content-type": "application/pdf"}
        content = b"%PDF-1.7 promoted"

        def raise_for_status(self) -> None:
            return

    monkeypatch.setattr(
        "dewey_service.services.literature.requests.get",
        lambda *args, **kwargs: _PdfResponse(),
    )

    second_code, second = service.save_literature(
        viewer=viewer,
        pmid="789012",
        save_mode="managed_artifact",
        visibility_scope="private",
        allowed_users=[],
        allowed_groups=[],
        idempotency_key="lit-promote-2",
    )

    assert second_code == 200
    assert second["artifact"]["artifact_euid"] == first["artifact"]["artifact_euid"]
    assert second["artifact"]["metadata"]["storage_mode"] == "managed"
    assert second["artifact"]["storage_backend"] == "s3"
