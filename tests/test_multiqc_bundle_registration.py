"""Focused MultiQC registration and existing-share behavior, with synthetic storage only."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dewey_service.multiqc_bundle import NotMultiQCReport, inspect_bundle
from dewey_service.storage import StorageObjectNotFoundError
from tests.support.sharing_v12_fakes import Harness, READER, actor

HTML = b'<title>MultiQC Report</title><script src="report_files/app.js"></script><link rel="stylesheet" href="report_files/site.css"><a href="report_data/stats.tsv">data</a>'
FILES = {"reports/report.html": HTML, "reports/report_files/app.js": b"ok",
         "reports/report_files/site.css": b"body{background:url(img.png)}",
         "reports/report_files/img.png": b"png", "reports/report_data/stats.tsv": b"x"}


def inspect(files=None, key="reports/report.html"):
    files = FILES if files is None else files
    def read(path):
        return files[path], "fixture-etag"
    def require(path):
        if path not in files:
            raise ValueError("missing asset: " + path)
    return inspect_bundle(key, read, require)


def storage(h, files=None):
    files = FILES if files is None else files
    calls = []
    def response(*, bucket, key, head=False, **kwargs):
        calls.append((key, head, kwargs.get("version_id")))
        if key not in files:
            raise StorageObjectNotFoundError("missing " + key)
        return {"ETag": "fixture-etag", **({} if head else {"Body": BytesIO(files[key])})}
    h.service.storage = SimpleNamespace(object_response=response)
    h.service._require_storage = lambda: h.service.storage
    return calls


def test_declared_dependency_closure_is_report_specific_and_includes_css_dependencies():
    bundle = inspect()
    assert bundle["include_patterns"] == ["report.html", "report_data/**", "report_files/**"]
    assert "report_files/img.png" in bundle["required_assets"]
    assert bundle["root_key"] == "reports/" and bundle["entrypoint"] == "report.html"
    assert bundle["mode"] == "bundle"


@pytest.mark.parametrize("reference", ["../secret.js", "%2e%2e/secret.js", "/other.js", "https://external.test/app.js", "other-report.html"])
def test_unsafe_or_unrelated_report_dependencies_fail_before_registration(reference):
    with pytest.raises(ValueError):
        inspect({"reports/report.html": f'<title>MultiQC</title><script src="{reference}"></script>'.encode()})


def test_missing_assets_are_explicit_and_standalone_needs_no_bundle_repair():
    missing = dict(FILES)
    del missing["reports/report_files/app.js"]
    with pytest.raises(ValueError, match="missing asset"):
        inspect(missing)
    standalone = inspect({"reports/report.html": b"<title>MultiQC</title><script>const embedded=1</script>"})
    assert standalone["mode"] == "standalone" and standalone["required_assets"] == []


def test_renamed_multiqc_is_detected_and_other_html_is_left_unchanged():
    h = Harness()
    files = {"reports/renamed.html": b"<title>MultiQC Report</title>",
             "reports/matrix.html": b'<base href="/"><title>Product matrix</title>'}
    storage(h, files)
    with actor():
        renamed = h.service._prepare_multiqc_payload(h.session, {"storage_kind":"object", "storage_backend":"s3", "bucket":"fixture-source", "key":"reports/renamed.html"})
        normal = {"storage_kind":"object", "storage_backend":"s3", "bucket":"fixture-source", "key":"reports/matrix.html"}
        assert h.service._prepare_multiqc_payload(h.session, normal) == normal
    assert renamed["report_bundle"]["entrypoint"] == "renamed.html"


def test_registration_inspection_uses_original_html_version_and_fails_missing_assets():
    h = Harness()
    calls = storage(h)
    payload = {"storage_kind":"object", "storage_backend":"s3", "bucket":"fixture-source", "key":"reports/report.html", "version_id":"html-version"}
    with actor():
        prepared = h.service._prepare_multiqc_payload(h.session, payload)
    assert prepared["report_bundle"] == inspect()
    assert calls[0] == ("reports/report.html", False, "html-version")
    assert all(version is None for key, head, version in calls[1:])
    storage(h, {"reports/report.html": HTML})
    with actor(), pytest.raises(ValueError, match="incomplete; missing asset"):
        h.service._prepare_multiqc_payload(h.session, payload)


def test_repair_preserves_identities_recipients_expiry_and_url_and_is_idempotent(monkeypatch):
    h = Harness()
    member = h.artifact(key="reports/report.html", original_filename="report.html")
    shared = h.share([member], content_mode="www", report_entrypoint="report.html", report_bundle_root="", expires_at=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat())
    storage(h)
    monkeypatch.setattr("dewey_service.services.share_revisions.require_record", lambda *args: None)
    h.service.list_shares = lambda **kwargs: [h.service.get_share(shared.euid)]
    before = deepcopy(shared.json_addl)
    with actor():
        plan = h.service.inspect_multiqc_registration(member.euid)
        result = h.service.repair_multiqc_registration(member.euid, expected_bundle_digest=plan["bundle_digest"], repair_shares=True)
        current = h.service.get_share(shared.euid)
        again = h.service.repair_multiqc_registration(member.euid, expected_bundle_digest=plan["bundle_digest"], repair_shares=True)
    assert result["shares"][0]["status"] == "repaired"
    assert again["registration_changed"] is False and again["shares"][0]["status"] == "already_repaired"
    assert current["euid"] == shared.euid and current["targets"][0]["euid"] == member.euid
    for key in ["expires_at", "audience", "denied_emails", "report_entrypoint", "report_bundle_root"]:
        assert current[key] == before[key]
    assert current["fetch_path"] == "/fetch/" + shared.euid
    assert current["grants"][0]["recipient"] == READER.email
    assert current["grants"][0]["include_subdomains"] is False
    assert current["grants"][0]["expires_at"] == before["expires_at"]
    with actor(READER):
        allowed = h.service.authorize_share_object(shared.euid, member.euid, relative_key="report_files/app.js")
        assert allowed["key"] == "reports/report_files/app.js"
        with pytest.raises(HTTPException) as denied:
            h.service.authorize_share_object(shared.euid, member.euid, relative_key="unrelated/input.tsv")
    assert denied.value.status_code == 403


def test_changed_bundle_or_custom_selection_does_not_expand_existing_share():
    h = Harness()
    member = h.artifact(key="reports/report.html", original_filename="report.html")
    shared = h.share([member], content_mode="www", report_entrypoint="report.html", exclude_patterns=["*.private"], expires_at=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat())
    storage(h)
    h.service.list_shares = lambda **kwargs: [h.service.get_share(shared.euid)]
    with actor():
        plan = h.service.inspect_multiqc_registration(member.euid)
        with pytest.raises(HTTPException) as changed:
            h.service.repair_multiqc_registration(member.euid, expected_bundle_digest="0"*64, repair_shares=True)
        assert changed.value.status_code == 409
        result = h.service.repair_multiqc_registration(member.euid, expected_bundle_digest=plan["bundle_digest"], repair_shares=True)
    assert result["shares"][0]["status"] == "blocked_custom_file_selection"
    assert shared.json_addl["policy_revision"] == 1


def test_cli_uses_supported_review_then_expected_digest_mutation(monkeypatch):
    import dewey_service.cli.registry as cli
    calls = []
    def request(method, path, **kwargs):
        calls.append((method,path,kwargs))
        return {"bundle_digest":"d"*64}
    monkeypatch.setattr(cli,"_request",request)
    monkeypatch.setattr(cli,"_emit",lambda fn:fn())
    cli._multiqc_bundle("fixture-report", apply=True, repair_shares=True)
    assert [call[0] for call in calls] == ["GET","POST"]
    assert calls[1][2]["data"] == {"expected_bundle_digest":"d"*64,"repair_shares":True}


def test_registered_section_uses_its_explicit_parent_bundle_and_custom_multiqc_title():
    files={"reports/report.html": b'<title>Project title</title><meta name="author" content="MultiQC"><script src="report_files/app.js"></script><a href="report_files/sections/one.html">section</a>',
           "reports/report_files/app.js":b"ok",
           "reports/report_files/sections/one.html":b'<meta name="author" content="MultiQC"><script src="../app.js"></script><a href="../../report.html">index</a>'}
    bundle=inspect(files,"reports/report_files/sections/one.html")
    assert bundle["root_key"]=="reports/"
    assert bundle["entrypoint"]=="report_files/sections/one.html"
    assert bundle["include_patterns"]==["report.html","report_files/**"]


def test_explicit_multiqc_declaration_supports_custom_report_titles_without_generator_metadata():
    raw=b"<html><title>Ultima FASTQ quality</title><body><table><tr><td>embedded</td></tr></table></body></html>"
    with pytest.raises(NotMultiQCReport):
        inspect_bundle("report.html",lambda path:(raw,"etag"),lambda path:None)
    bundle=inspect_bundle("report.html",lambda path:(raw,"etag"),lambda path:None,declared_multiqc=True)
    assert bundle["mode"]=="standalone" and bundle["required_assets"]==[]


def test_external_dependency_error_reports_complete_declared_asset_list():
    from dewey_service.multiqc_bundle import RequiredExternalAssets
    raw=b'<title>MultiQC</title><script src="https://cdn.example.test/plot.js"></script><link rel="stylesheet" href="https://cdn.example.test/site.css">'
    with pytest.raises(RequiredExternalAssets) as error:
        inspect_bundle("report.html",lambda path:(raw,"etag"),lambda path:None)
    assert error.value.assets==["https://cdn.example.test/plot.js","https://cdn.example.test/site.css"]


def test_vep_summary_under_multiqc_inputs_is_not_a_multiqc_registration():
    h=Harness()
    key="reports/multiqc_inputs/final/native/vep/summary.html"
    raw=b'<html><title>VEP Summary</title><script src="http://www.google.com/jsapi"></script></html>'
    storage(h,{key:raw})
    payload={"storage_kind":"object","storage_backend":"s3","bucket":"fixture-source","key":key,"artifact_type":"html"}
    with actor():
        assert h.service._prepare_multiqc_payload(h.session,payload)==payload
