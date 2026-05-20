from __future__ import annotations

import asyncio
import io
import json
import zipfile
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from dewey_service.app import create_app


def _login_user(monkeypatch, client, groups: list[str] | None = None) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@lsmc.bio",
            "sub": "sub-1",
            "cognito:groups": groups or ["dewey-readwrite"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
    parsed = urlparse(login.headers["location"])
    state = parse_qs(parsed.query)["state"][0]
    callback = client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 302
    assert callback.headers["location"] == "/ui"


def test_artifacts_page_requires_login_and_serves_bulk_template(monkeypatch, client) -> None:
    response = client.get("/artifacts")
    assert response.status_code == 401

    _login_user(monkeypatch, client)

    page = client.get("/artifacts")
    assert page.status_code == 200
    assert "Register, Search, Download, And Share" in page.text
    assert "Artifact Sets" in page.text
    assert "Recent Artifacts" in page.text
    assert 'href="/artifacts"' in page.text
    assert 'href="/artifacts/dag"' in page.text
    assert "section=recent_artifacts#section-recent_artifacts" in page.text

    template = client.get("/artifacts/bulk-template.tsv")
    assert template.status_code == 200
    assert template.headers["content-type"].startswith("text/tab-separated-values")
    assert "source_mode\tartifact_type\tsource_uri" in template.text
    assert "artifact_set_label" in template.text


def test_artifacts_register_search_download_and_artifact_share(
    monkeypatch,
    client,
    fake_service,
) -> None:
    _login_user(monkeypatch, client)

    register = client.post(
        "/artifacts/register",
        data={
            "artifact_type": "report",
            "producer_system": "atlas",
            "producer_object_euid": "REL-42",
            "artifact_meta_study_id": "STUDY-42",
            "artifact_meta_sample_id": "SAMPLE-42",
            "artifact_meta_tags": "tumor rna",
            "artifact_meta_notes": "UI artifact intake",
            "grouping_mode": "create",
            "artifact_set_type": "batch",
            "artifact_set_label": "UI Batch 42",
            "artifact_set_description": "Register from local, URL, and S3 inputs.",
            "artifact_set_meta_program": "oncology",
            "artifact_set_meta_tags": "release,ui",
            "url_sources": "https://example.com/reports/report-a.txt",
            "s3_mode": "reference",
            "s3_sources": "s3://bucket-1/inbox/",
        },
        files=[("file_data", ("local-report.txt", b"alpha", "text/plain"))],
    )
    assert register.status_code == 200
    assert "Registration Report" in register.text
    assert "UI Batch 42" in register.text
    assert len(fake_service.artifacts) == 4
    assert len(fake_service.artifact_sets) == 1
    first_artifact = next(iter(fake_service.artifacts.values()))
    assert first_artifact["metadata"]["tags"] == ["tumor", "rna"]
    artifact_set = next(iter(fake_service.artifact_sets.values()))
    assert artifact_set["member_count"] == 4
    assert artifact_set["metadata"]["program"] == "oncology"

    search = client.post(
        "/artifacts/search",
        data={
            "artifact_filter_tags": "tumor rna",
            "artifact_match_mode": "greedy",
        },
    )
    assert search.status_code == 200
    assert "4 matches" in search.text
    assert "AT-000001" in search.text
    assert 'href="/artifacts/euid/AT-000001"' in search.text
    assert 'action="/artifacts/euid/AT-000001/download"' in search.text

    export = client.post(
        "/artifacts/search/export",
        data={
            "artifact_filter_study_id": "STUDY-42",
            "artifact_match_mode": "exact",
            "format": "json",
        },
    )
    assert export.status_code == 200
    export_payload = export.json()
    assert export_payload["row_count"] == 4
    assert export_payload["items"][0]["record_type"] == "artifact"

    selected = list(fake_service.artifacts)[:2]
    download = client.post(
        "/artifacts/download",
        data={
            "artifact_euids": selected,
            "download_naming_mode": "hybrid",
            "download_include_metadata": "yes",
        },
    )
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
        names = set(archive.namelist())
    assert "local-report.txt" in names
    assert "local-report.txt.dewey.yaml" in names

    share = client.post(
        "/artifacts/share",
        data={
            "artifact_euids": selected,
            "share_ttl_hours": "24",
            "artifact_search_form_state": json.dumps(
                {
                    "artifact_filter_study_id": "STUDY-42",
                    "artifact_match_mode": "exact",
                }
            ),
        },
    )
    assert share.status_code == 200
    assert "Issued Artifact Links" in share.text
    assert len(fake_service.share_references) == 2

    recent = client.get("/artifacts?section=recent_artifacts")
    assert recent.status_code == 200
    assert "Recent Artifacts" in recent.text
    assert "local-report.txt" in recent.text
    assert 'href="/artifacts/euid/AT-000001"' in recent.text
    assert 'action="/artifacts/euid/AT-000001/download"' in recent.text


def test_artifact_dag_page_and_storage_browser_routes(
    monkeypatch,
    client,
    fake_service,
) -> None:
    _login_user(monkeypatch, client)

    imported = client.post(
        "/artifacts/import-run-prefix",
        data={
            "root_uri": "s3://bucket-7/runs/RUN504352/2026/504352-20260404_1215/",
            "platform": "ultima",
            "owner_email": "johnm@lsmc.com",
            "finalize": "no",
        },
    )
    assert imported.status_code == 200

    run_artifact = next(
        item for item in fake_service.artifacts.values() if item["node_kind"] == "run_folder"
    )

    page = client.get(f"/artifacts/dag?artifact_euid={run_artifact['artifact_euid']}")
    assert page.status_code == 200
    assert "Directory Browser And DAG View" in page.text
    assert "S3 Directory Browser" in page.text
    assert run_artifact["artifact_euid"] in page.text

    browse_api = client.get(
        "/api/v1/storage/browse",
        params={"root_uri": run_artifact["storage_uri"]},
    )
    assert browse_api.status_code == 200
    browse_payload = browse_api.json()
    assert browse_payload["root_uri"] == run_artifact["storage_uri"]
    assert browse_payload["prefixes"]

    graph_api = client.get(f"/api/v1/artifacts/{run_artifact['artifact_euid']}/graph")
    assert graph_api.status_code == 200
    graph_payload = graph_api.json()
    assert graph_payload["root_euid"] == run_artifact["artifact_euid"]
    assert graph_payload["nodes"]
    assert graph_payload["edges"]


def test_artifact_detail_page_and_direct_download_redirect(
    monkeypatch, client, fake_service
) -> None:
    _login_user(monkeypatch, client)

    register = client.post(
        "/artifacts/register",
        data={"artifact_type": "report"},
        files=[("file_data", ("detail-report.txt", b"alpha", "text/plain"))],
    )
    assert register.status_code == 200

    artifact_euid = next(iter(fake_service.artifacts))

    detail = client.get(f"/artifacts/euid/{artifact_euid}")
    assert detail.status_code == 200
    assert artifact_euid in detail.text
    assert "detail-report.txt" in detail.text
    assert "Storage URI" in detail.text

    download = client.post(
        f"/artifacts/euid/{artifact_euid}/download",
        data={"share_duration_days": "1.25"},
        follow_redirects=False,
    )
    assert download.status_code == 303
    assert download.headers["location"] == "/share-references/SH-000001"
    assert len(fake_service.share_references) == 1

    opened = client.get(download.headers["location"], follow_redirects=False)
    assert opened.status_code == 303
    assert opened.headers["location"] == "https://downloads.example.com/SH-000001"
    assert fake_service.share_references["SH-000001"]["access_count"] == 1

    shares = client.get("/shares")
    assert shares.status_code == 200
    assert "Dewey Share References" in shares.text

    revoke = client.post(
        "/share-references/SH-000001/revoke",
        data={"return_to": "artifact"},
        follow_redirects=False,
    )
    assert revoke.status_code == 303
    assert fake_service.share_references["SH-000001"]["status"] == "revoked"


def test_artifacts_register_infers_artifact_type_from_extension(
    monkeypatch, client, fake_service
) -> None:
    _login_user(monkeypatch, client)

    register = client.post(
        "/artifacts/register",
        data={
            "artifact_type": "n/a",
            "url_sources": "https://example.com/reports/report-a.txt",
            "s3_mode": "reference",
            "s3_sources": "s3://bucket-1/data/results.json",
        },
        files=[("file_data", ("variants.vcf.gz", b"##fileformat=VCF", "application/gzip"))],
    )

    assert register.status_code == 200
    assert len(fake_service.artifacts) == 3
    artifact_types = sorted(item["artifact_type"] for item in fake_service.artifacts.values())
    assert artifact_types == ["json", "report", "vcf"]


def test_artifacts_bulk_directory_limit_and_artifact_set_routes(
    monkeypatch,
    client,
    fake_service,
) -> None:
    _login_user(monkeypatch, client)

    directory_limit = client.post(
        "/artifacts/register",
        data={"artifact_type": "report"},
        files=[
            ("directory_data", (f"nested/file-{index}.txt", b"x", "text/plain"))
            for index in range(1001)
        ],
    )
    assert directory_limit.status_code == 200
    assert "Too many directory files. Maximum is 1000." in directory_limit.text

    bulk_tsv = (
        "source_mode\tartifact_type\tsource_uri\tbucket\tkey\toriginal_filename\tproducer_system\t"
        "producer_object_euid\tartifact_set_type\tartifact_set_label\tartifact_set_description\t"
        "title\tsample_id\tstudy_id\tassay\tpipeline\trecorded_at\ttags\tnotes\n"
        "reference\tvcf\ts3://bucket-7/releases/sample-a.vcf.gz\t\t\tsample-a.vcf.gz\tatlas\t"
        "REL-1\trelease\tRelease Alpha\tRelease import\tVariant Release\tS-1\tST-1\tWGS\t"
        "caller\t\talpha,release\tBulk row 1\n"
        "register\treport\t\tbucket-7\treports/case-report.pdf\tcase-report.pdf\tbloom\tDOC-1\t"
        "release\tRelease Alpha\tRelease import\tCase Report\tS-2\tST-1\tRNA\twriter\t\t"
        "beta,release\tBulk row 2\n"
    )
    bulk = client.post(
        "/artifacts/bulk-upload",
        files={
            "bulk_tsv": ("artifacts.tsv", bulk_tsv.encode("utf-8"), "text/tab-separated-values")
        },
    )
    assert bulk.status_code == 200
    assert "Bulk Report" in bulk.text
    assert len(fake_service.artifacts) == 2
    assert len(fake_service.artifact_sets) == 1
    bulk_set = next(iter(fake_service.artifact_sets.values()))
    assert bulk_set["label"] == "Release Alpha"
    assert bulk_set["member_count"] == 2

    selected = list(fake_service.artifacts)
    create = client.post(
        "/artifacts/sets/create",
        data={
            "artifact_set_type": "collection",
            "artifact_set_label": "Selected Results",
            "artifact_set_description": "Artifacts selected from search results.",
            "artifact_set_meta_program": "oncology",
            "artifact_set_additional_metadata_json": '{"release_owner":"operator@example.com"}',
            "artifact_search_form_state": "{}",
            "artifact_set_search_form_state": "{}",
            "artifact_euids": selected,
        },
    )
    assert create.status_code == 200
    assert "Latest Artifact Set" in create.text
    created_set = fake_service.artifact_sets["AS-000002"]
    assert created_set["label"] == "Selected Results"
    assert created_set["member_count"] == 2
    assert created_set["metadata"]["program"] == "oncology"

    set_search = client.post(
        "/artifacts/sets/search",
        data={
            "artifact_set_label": "Selected Results",
            "artifact_set_match_mode": "exact",
        },
    )
    assert set_search.status_code == 200
    assert created_set["artifact_set_euid"] in set_search.text

    set_export = client.post(
        "/artifacts/sets/export",
        data={
            "artifact_set_label": "Selected Results",
            "artifact_set_match_mode": "exact",
            "format": "json",
        },
    )
    assert set_export.status_code == 200
    set_export_payload = set_export.json()
    assert set_export_payload["row_count"] == 1
    assert set_export_payload["items"][0]["record_type"] == "artifact_set"

    set_share = client.post(
        "/artifacts/sets/share",
        data={
            "selected_artifact_set_euid": created_set["artifact_set_euid"],
            "share_transport": "rclone_http",
            "share_duration_days": "1",
            "share_bucket": "managed-bucket",
            "share_host": "shares.example.com",
            "share_port": "8088",
            "share_user": "operator",
            "share_password": "secret",
            "artifact_set_search_form_state": json.dumps(
                {
                    "artifact_set_label": "Selected Results",
                    "artifact_set_match_mode": "exact",
                }
            ),
        },
    )
    assert set_share.status_code == 200
    assert "Latest Set Share" in set_share.text
    assert "http://shares.example.com:8088/" in set_share.text
    assert len(fake_service.share_references) == 1


def test_artifact_detail_external_reference_validate_and_create(
    monkeypatch, test_settings, fake_service
) -> None:
    test_settings.external_reference_targets = [
        {
            "service_id": "ursa",
            "base_url": "https://localhost:8913",
            "object_path": "/api/dag/object/{euid}",
            "detail_url_template": "https://ursa.dev.lsmc.life/object/{euid}",
            "verify_ssl": False,
            "headers": {"Authorization": "Bearer token"},
        }
    ]

    class _Response:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"euid": "Z-RGX-15T", "label": "Result Graph", "record_type": "analysis_result"}

    class _AsyncClient:
        def __init__(self, *, timeout: float, verify: bool) -> None:
            self.timeout = timeout
            self.verify = verify

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, *, headers: dict):
            assert url == "https://localhost:8913/api/dag/object/Z-RGX-15T"
            assert headers["Authorization"] == "Bearer token"
            return _Response()

    monkeypatch.setattr("dewey_service.app.httpx.AsyncClient", _AsyncClient)
    app = create_app(settings=test_settings, service=fake_service)
    with TestClient(app, base_url="https://localhost:8914") as local_client:
        _login_user(monkeypatch, local_client)
        register = local_client.post(
            "/artifacts/register",
            data={"artifact_type": "report"},
            files=[("file_data", ("linked-report.txt", b"alpha", "text/plain"))],
        )
        assert register.status_code == 200
        artifact_euid = next(iter(fake_service.artifacts))
        validate = local_client.post(
            f"/artifacts/euid/{artifact_euid}/external-reference/validate",
            data={"external_reference_euid": "Z-RGX-15T", "relation_type": "analysis_result"},
        )
        assert validate.status_code == 200
        assert "Validated ursa / Z-RGX-15T" in validate.text
        create = local_client.post(
            f"/artifacts/euid/{artifact_euid}/external-reference/create",
            data={"external_reference_euid": "Z-RGX-15T", "relation_type": "analysis_result"},
        )
        assert create.status_code == 200
        assert len(fake_service.external_relations) == 1
        assert fake_service.external_relations[0]["relation_type"] == "analysis_result"


def test_artifact_detail_external_reference_requires_explicit_targets(monkeypatch, client) -> None:
    _login_user(monkeypatch, client)
    register = client.post(
        "/artifacts/register",
        data={"artifact_type": "report"},
        files=[("file_data", ("missing-target-report.txt", b"alpha", "text/plain"))],
    )
    assert register.status_code == 200
    artifact_euid = "AT-000001"
    validate = client.post(
        f"/artifacts/euid/{artifact_euid}/external-reference/validate",
        data={"external_reference_euid": "Z-RGX-15T"},
    )
    assert validate.status_code == 400
    assert "external_reference_targets is required" in validate.text


def test_artifact_detail_rejects_invalid_share_days(monkeypatch, client) -> None:
    _login_user(monkeypatch, client)
    register = client.post(
        "/artifacts/register",
        data={"artifact_type": "report"},
        files=[("file_data", ("duration-report.txt", b"alpha", "text/plain"))],
    )
    assert register.status_code == 200
    artifact_euid = "AT-000001"
    too_long = client.post(
        f"/artifacts/euid/{artifact_euid}/download",
        data={"share_duration_days": "365.01"},
    )
    assert too_long.status_code == 400
    assert "at most 365.0" in too_long.text
