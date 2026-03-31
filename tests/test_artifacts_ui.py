from __future__ import annotations

import io
import json
import zipfile
from urllib.parse import parse_qs, urlparse


def _login_user(monkeypatch, client, groups: list[str] | None = None) -> None:
    monkeypatch.setattr(
        "dewey_service.app.exchange_code",
        lambda settings, code: {"id_token": "header.payload.sig"},
    )
    monkeypatch.setattr(
        "dewey_service.app.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@example.com",
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
    assert callback.status_code == 303
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
    assert 'section=recent_artifacts#section-recent_artifacts' in page.text

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
            "artifact_meta_tags": "tumor,rna",
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
    artifact_set = next(iter(fake_service.artifact_sets.values()))
    assert artifact_set["member_count"] == 4
    assert artifact_set["metadata"]["program"] == "oncology"

    search = client.post(
        "/artifacts/search",
        data={
            "artifact_filter_study_id": "STUDY-42",
            "artifact_match_mode": "exact",
        },
    )
    assert search.status_code == 200
    assert "4 matches" in search.text
    assert "AT-000001" in search.text

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


def test_artifacts_register_infers_artifact_type_from_extension(monkeypatch, client, fake_service) -> None:
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
