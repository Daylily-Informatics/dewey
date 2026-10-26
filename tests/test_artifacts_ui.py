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
    response = client.get("/artifacts", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2Fartifacts"
    assert 'data-section="Add"' not in response.text

    _login_user(monkeypatch, client)

    page = client.get("/artifacts")
    assert page.status_code == 200
    assert 'data-section="Add"' in page.text
    assert 'data-writable="true"' in page.text
    assert 'href="/ui"' in page.text
    assert 'href="/sets"' in page.text
    assert 'href="/storage"' in page.text
    assert "/static/registry.js" in page.text
    assert 'id="content" aria-busy="true"' in page.text

    template = client.get("/artifacts/bulk-template.tsv")
    assert template.status_code == 200
    assert template.headers["content-type"].startswith("text/tab-separated-values")
    assert "source_mode\tartifact_type\tsource_uri" in template.text
    assert "artifact_set_label" in template.text


def test_artifacts_prefix_registration_form_creates_one_prefix_artifact(
    monkeypatch,
    client,
    fake_service,
) -> None:
    _login_user(monkeypatch, client)

    response = client.post(
        "/artifacts/register-prefix",
        data={
            "root_uri": "s3://bucket-8/prefix-only/run-a",
            "artifact_type": "folder",
            "producer_system": "atlas",
            "producer_object_euid": "RUN-A",
            "prefix_meta_title": "Prefix Run A",
            "prefix_meta_tags": "prefix only",
        },
    )

    assert response.status_code == 200
    assert "S3 Prefix Registration" in response.text
    assert "Prefix Artifact" in response.text
    assert len(fake_service.artifacts) == 1
    artifact = next(iter(fake_service.artifacts.values()))
    assert artifact["storage_kind"] == "prefix"
    assert artifact["node_kind"] == "prefix"
    assert artifact["is_terminal"] is False
    assert artifact["storage_uri"] == "s3://bucket-8/prefix-only/run-a/"
    assert artifact["producer_system"] == "atlas"
    assert artifact["metadata"]["tags"] == ["prefix", "only"]


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
    assert share.status_code == 403
    assert "current verified-email identity" in share.text
    assert fake_service.shares == {}

    recent = client.get("/artifacts?section=recent_artifacts")
    assert recent.status_code == 200
    assert 'data-section="Add"' in recent.text
    listing = client.get("/api/v1/artifacts", headers={"Authorization": "Bearer token-123"})
    assert listing.status_code == 200
    assert listing.json()["total"] == 4
    assert "local-report.txt" in {row["original_filename"] for row in listing.json()["items"]}


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
    assert 'data-section="S3 Browser"' in page.text
    assert "/static/registry.js" in page.text

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
    assert f'data-euid="{artifact_euid}"' in detail.text
    assert 'data-section="Record"' in detail.text
    record = client.get(
        f"/api/v1/artifacts/{artifact_euid}",
        headers={"Authorization": "Bearer token-123"},
    )
    assert record.status_code == 200
    assert record.json()["original_filename"] == "detail-report.txt"
    assert record.json()["storage_uri"].startswith("s3://")

    download = client.post(
        f"/artifacts/euid/{artifact_euid}/download",
        data={"share_duration_days": "1.25"},
        follow_redirects=False,
    )
    assert download.status_code == 403, download.text
    assert "current verified-email identity" in download.text
    assert "location" not in download.headers
    assert fake_service.shares == {}

    opened = client.post(
        "/shares/share-fixture/access-package",
        data={"delivery_mode": "presigned_s3", "signed_ttl_seconds": "300"},
    )
    assert opened.status_code == 403
    assert opened.json()["detail"] == "Verified sharing ingress is required"
    assert "signed_url" not in opened.text

    shares = client.get("/shares")
    assert shares.status_code == 403
    assert shares.json()["detail"] == "Verified sharing ingress is required"

    revoke = client.post(
        "/shares/share-fixture/revoke",
        data={"return_to": "artifact"},
        follow_redirects=False,
    )
    assert revoke.status_code == 403
    assert revoke.json()["detail"] == "Verified sharing ingress is required"
    assert fake_service.shares == {}


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
    assert set_share.status_code == 403
    assert "current verified-email identity" in set_share.text
    assert "Latest Set Share" not in set_share.text
    assert fake_service.shares == {}
    assert fake_service.artifact_sets[created_set["artifact_set_euid"]] == created_set
    assert len(fake_service.artifacts) == 2


def test_artifact_detail_external_reference_validate_and_create(
    monkeypatch, test_settings, fake_service
) -> None:
    test_settings.external_reference_targets = [
        {
            "service_id": "ursa",
            "base_url": "https://localhost:8913",
            "object_path": "/api/dag/v2/object/{euid}",
            "detail_url_template": "https://ursa.dev.lsmc.life/object/{euid}",
            "verify_ssl": False,
            "dag_read_token": "native-read-token",
        }
    ]

    class _Response:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {
                "service_id": "ursa",
                "euid": "Z-RGX-15T",
                "display_label": "Result Graph",
                "record_type": "instance",
                "tenant_id": None,
                "category": "analysis",
                "type": "run-linked",
                "subtype": "generic",
                "version": "1.0",
            }

    class _ManifestResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"service_id": "ursa", "contract": "dag:v2"}

    class _AsyncClient:
        def __init__(self, *, timeout: float, verify: bool) -> None:
            self.timeout = timeout
            self.verify = verify

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, *, headers: dict):
            assert headers["Authorization"] == "Bearer native-read-token"
            if url == "https://localhost:8913/api/dag/manifest":
                return _ManifestResponse()
            assert url == "https://localhost:8913/api/dag/v2/object/Z-RGX-15T"
            return _Response()

    monkeypatch.setattr("dewey_service.app.httpx.AsyncClient", _AsyncClient)

    def _validate_manifest(payload, *, expected_service_id):
        assert payload == {"service_id": expected_service_id, "contract": "dag:v2"}
        return None

    monkeypatch.setattr(
        "daylily_tapdb.web.dag_v2.validate_dag_v2_manifest",
        _validate_manifest,
    )
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
        external_object = next(iter(fake_service.external_objects.values()))
        assert external_object["external_object_type"] == "analysis"


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


def test_gui_quick_registration_preserves_native_conflict(monkeypatch, client, fake_service):
    from fastapi import HTTPException

    _login_user(monkeypatch, client)
    calls = []

    def conflict(**kwargs):
        calls.append(kwargs)
        raise HTTPException(409, "TapDB revision conflict; explicitly reconcile")

    monkeypatch.setattr(fake_service, "import_artifact_from_uri", conflict)
    response = client.post("/ui/register", data={"source_s3_uri": "s3://fixture-bucket/input.txt"})
    assert response.status_code == 409
    assert len(calls) == 1


def test_gui_multi_upload_conflict_stops_later_writes(monkeypatch, client, fake_service):
    from fastapi import HTTPException

    _login_user(monkeypatch, client)
    calls = []

    def conflict(**kwargs):
        calls.append(kwargs)
        raise HTTPException(409, "TapDB revision conflict; explicitly reconcile")

    monkeypatch.setattr(fake_service, "upload_artifact_bytes", conflict)
    response = client.post(
        "/artifacts/register",
        data={"artifact_type": "report"},
        files=[
            ("directory_data", ("first.txt", b"one", "text/plain")),
            ("directory_data", ("second.txt", b"two", "text/plain")),
        ],
    )
    assert response.status_code == 409
    assert len(calls) == 1


def test_gui_bulk_conflict_stops_later_rows(monkeypatch, client, fake_service):
    from fastapi import HTTPException

    _login_user(monkeypatch, client)
    calls = []

    def conflict(**kwargs):
        calls.append(kwargs)
        raise HTTPException(409, "TapDB revision conflict; explicitly reconcile")

    monkeypatch.setattr(fake_service, "import_artifact_from_uri", conflict)
    body = (
        "source_mode\tartifact_type\tsource_uri\n"
        "reference\treport\ts3://fixture-bucket/first.txt\n"
        "reference\treport\ts3://fixture-bucket/second.txt\n"
    )
    response = client.post(
        "/artifacts/bulk-upload",
        files={"bulk_tsv": ("artifacts.tsv", body.encode(), "text/tab-separated-values")},
    )
    assert response.status_code == 409
    assert len(calls) == 1
