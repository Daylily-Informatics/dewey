"""Rebind evidence, concurrency fences, and failure atomicity without S3 or PostgreSQL I/O."""
from copy import deepcopy
from dataclasses import replace

import pytest
from fastapi import HTTPException

from dewey_service.services.share_rebind import equivalent_objects
from dewey_service.storage import StorageObject, _STORAGE_AUTHORIZATION
from tests.support.sharing_v12_fakes import Harness, Rows, actor


class EvidenceStorage:
    def __init__(self, objects, pages=None):
        self.objects, self.pages, self.calls = objects, pages or {}, []
        self.extra_scope_request = None
    def head_object(self, *, bucket, key, **kwargs):
        _STORAGE_AUTHORIZATION.get()(bucket, key, "metadata")
        if self.extra_scope_request:
            _STORAGE_AUTHORIZATION.get()(*self.extra_scope_request)
        self.calls.append(("head", bucket, key, kwargs))
        assert kwargs["checksum_mode"] is True
        return self.objects[(bucket, key)]
    def list_share_candidates(self, *, bucket, prefix, continuation_token, **kwargs):
        _STORAGE_AUTHORIZATION.get()(bucket, prefix, "metadata")
        self.calls.append(("list", bucket, prefix, continuation_token))
        return self.pages[(bucket, continuation_token)]


def configured(monkeypatch, *, prefix=False):
    h = Harness()
    target = h.artifact(prefix=prefix)
    current = h.share([target])
    unrelated = h.share([h.artifact("fixture-unrelated")])
    h.link(h.session, parent=target, child=unrelated, relationship_type="has_share")
    checks = []
    h.service.require_storage_access = lambda bucket, key, **kwargs: checks.append((bucket, key, kwargs["action"]))
    monkeypatch.setattr("dewey_service.tapdb_backend.require_record", lambda *args: None)
    old_key, new_key = ("root/a.txt", "new/a.txt") if prefix else ("root/file.txt", "new/file.txt")
    source = StorageObject(bucket="fixture-source", key=old_key, size=5, sha256="qualified-checksum", checksum_type="FULL_OBJECT", version_id="source-version")
    destination = replace(source, bucket="fixture-destination", key=new_key, version_id="destination-version")
    objects = {(o.bucket, o.key): o for o in (source, destination)}
    pages = {(o.bucket, None): {"objects": [o], "next_continuation_token": None} for o in (source, destination)}
    storage = EvidenceStorage(objects, pages)
    h.service._require_storage = lambda: storage
    uri = "s3://fixture-destination/new/" if prefix else "s3://fixture-destination/new/file.txt"
    return h, target, current, unrelated, storage, uri, checks


@pytest.mark.parametrize("prefix", [False, True])
def test_rebind_proves_complete_equivalence_and_preserves_artifact_identity(monkeypatch, prefix):
    h, target, share, unrelated, storage, uri, checks = configured(monkeypatch, prefix=prefix)
    old_identity, old_filename = target.euid, target.json_addl["original_filename"]
    with actor():
        receipt = h.service.rebind_artifact_location(target.euid, storage_uri=uri,
            expected_location_revision=1, reason=" Reviewed equivalent destination ")
    assert receipt["artifact_euid"] == old_identity and receipt["location_revision"] == 2
    assert receipt["physical_data_changed"] is False and receipt["inventory_complete"] is True
    assert receipt["object_count"] == 1 and receipt["total_bytes"] == 5
    assert target.json_addl["original_filename"] == old_filename
    assert target.json_addl["storage_uri"] == target.json_addl["source_uri"] == uri
    evidence, = h.related(target, "artifact_location_revision", "artifact_location_revision")
    assert evidence.euid == receipt["evidence_euid"]
    assert evidence.json_addl["previous_location_revision"] == 1
    assert evidence.json_addl["previous_location"]["bucket"] == "fixture-source"
    assert evidence.json_addl["reason"] == "Reviewed equivalent destination"
    assert h.related(share, "share_location_evidence", "artifact_location_revision") == [evidence]
    assert not h.related(unrelated, "share_location_evidence", "artifact_location_revision")
    event, = h.related(share, "share_event", "share_event")
    assert event.json_addl["details"]["manifest_sha256"] == receipt["manifest_sha256"]
    assert h.related(target, "share_target_event", "share_event") == [event]
    assert len(checks) == 2 and all(check[-1] == "metadata" for check in checks)
    assert {call[0] for call in storage.calls} <= {"head", "list"}
    identities = [entry["key"] for entry in h.locks if isinstance(entry, dict)]
    assert identities == sorted(identities) and len(identities) == 2
    assert h.commits == 1


@pytest.mark.parametrize(("revision", "reason"), [(0, "reason"), (True, "reason"), (1, ""), (1, "  "), (1, None)])
def test_rebind_requires_reviewed_revision_and_reason(monkeypatch, revision, reason):
    h, target, _, _, storage, uri, _ = configured(monkeypatch)
    with actor(), pytest.raises(ValueError, match="Reviewed positive"):
        h.service.rebind_artifact_location(target.euid, storage_uri=uri, expected_location_revision=revision, reason=reason)
    assert not storage.calls and h.commits == 0


@pytest.mark.parametrize("failure", ["backend", "stale", "empty-object-key", "unchanged", "prefix-version", "collision", "concurrent"])
def test_rebind_fences_invalid_or_changed_coordinates_before_evidence(monkeypatch, failure):
    h, target, _, _, storage, uri, _ = configured(monkeypatch, prefix=failure == "prefix-version")
    revision, version = 1, None
    if failure == "backend": target.json_addl["storage_backend"] = "http"
    elif failure == "stale": revision = 2
    elif failure == "empty-object-key": uri = "s3://fixture-destination/"
    elif failure == "unchanged": uri = target.json_addl["storage_uri"]
    elif failure == "prefix-version": version = "one-version-cannot-cover-prefix"
    elif failure == "collision": h.service._registry_query = lambda *args, **kwargs: Rows([target])
    elif failure == "concurrent": h.on_expire = lambda instance: instance.json_addl.update(location_revision=2)
    error = HTTPException if failure in {"stale", "collision", "concurrent"} else ValueError
    with actor(), pytest.raises(error) as caught:
        h.service.rebind_artifact_location(target.euid, storage_uri=uri, expected_location_revision=revision,
            reason="reviewed", version_id=version)
    if error is HTTPException: assert caught.value.status_code == 409
    assert not storage.calls
    assert not h.related(target, "artifact_location_revision", "artifact_location_revision")


@pytest.mark.parametrize("failure", ["checksum", "unknown-size", "size", "key", "cardinality", "empty", "repeated-token", "outside-scope", "wrong-action"])
def test_rebind_evidence_failure_never_changes_the_reference(monkeypatch, failure):
    prefix = failure in {"key", "cardinality", "empty", "repeated-token"}
    h, target, _, _, storage, uri, _ = configured(monkeypatch, prefix=prefix)
    before = deepcopy(target.json_addl)
    destination_key = next(key for key in storage.objects if key[0] == "fixture-destination")
    destination = storage.objects[destination_key]
    if failure == "checksum": storage.objects[destination_key] = replace(destination, sha256="different")
    elif failure == "unknown-size": storage.objects[destination_key] = replace(destination, size=None)
    elif failure == "size": storage.objects[destination_key] = replace(destination, size=6)
    elif failure == "key":
        changed = replace(destination, key="new/different.txt")
        storage.objects[(changed.bucket, changed.key)] = changed
        storage.pages[(changed.bucket, None)]["objects"] = [changed]
    elif failure == "cardinality": storage.pages[(destination.bucket, None)]["objects"] = []
    elif failure == "empty":
        for page in storage.pages.values(): page["objects"] = []
    elif failure == "repeated-token":
        for bucket in ("fixture-source", "fixture-destination"):
            storage.pages[(bucket, None)]["next_continuation_token"] = "repeat"
            storage.pages[(bucket, "repeat")] = {"objects": [], "next_continuation_token": "repeat"}
    elif failure == "outside-scope": storage.extra_scope_request = ("unreviewed-bucket", "private/key", "metadata")
    elif failure == "wrong-action": storage.extra_scope_request = ("fixture-source", "root/file.txt", "download")
    error = HTTPException if failure in {"outside-scope", "wrong-action"} else ValueError
    with actor(), pytest.raises(error):
        h.service.rebind_artifact_location(target.euid, storage_uri=uri, expected_location_revision=1, reason="reviewed")
    assert target.json_addl == before and h.rollbacks == 1
    assert not h.related(target, "artifact_location_revision", "artifact_location_revision")


def test_rebind_rolls_back_reference_and_evidence_if_audit_persistence_fails(monkeypatch):
    h, target, _, _, _, uri, _ = configured(monkeypatch)
    before = [(r.euid, deepcopy(vars(r))) for r in h.rows]
    edges = list(h.edges)
    def fail(*args, **kwargs): raise RuntimeError("native audit persistence unavailable")
    h.service._event = fail
    with actor(), pytest.raises(RuntimeError, match="audit persistence"):
        h.service.rebind_artifact_location(target.euid, storage_uri=uri, expected_location_revision=1, reason="reviewed")
    assert [(r.euid, vars(r)) for r in h.rows] == before and h.edges == edges


def test_equivalence_can_use_exact_immutable_version_but_never_etag_alone():
    source = StorageObject(bucket="fixture", key="file", version_id="immutable-version", size=0, etag="opaque")
    assert equivalent_objects(source, source)["sha256"] is None
    with pytest.raises(ValueError, match="FULL_OBJECT"):
        equivalent_objects(replace(source, version_id=None), replace(source, version_id=None))
    with pytest.raises(ValueError, match="byte counts"):
        equivalent_objects(replace(source, size=None), replace(source, size=None))
