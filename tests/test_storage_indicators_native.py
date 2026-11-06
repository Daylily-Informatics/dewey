"""Native permission contracts and the explicitly requested paired load comparison.

Uses the same explicit isolated PostgreSQL target as native sharing contracts.
No real S3 requests, production database writes, installs, or hidden skips.
"""
import importlib.util
import json
import os
import statistics
from contextlib import contextmanager
from pathlib import Path
from random import Random
from time import perf_counter
from types import MethodType, SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import event

from dewey_service.registry_access import Principal, principal_context
from dewey_service.share_context import share_context_context
from dewey_service.storage import StorageObject
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE, ARTIFACT_SET_TEMPLATE, POLICY_TEMPLATE,
    SHARE_TEMPLATE, SHARE_REVISION_TEMPLATE, SHARE_GRANT_TEMPLATE,
)
from tests.test_sharing_v3_postgres import native_service_factory, request_scope, OWNER

READER = Principal(subject="indicator-reader", email="reader@lsmc.com", internal=True,
                   roles=("READ_ONLY",), email_verified=True)


@pytest.fixture(scope="module")
def indicator_fixture(native_service_factory):
    service = native_service_factory()
    bucket = "indicators-" + uuid4().hex
    keys, identities = [], []
    with request_scope(), service.backend.session_scope(commit=True) as session:
        def create(template, name, data):
            return service.backend.create_instance(session, template_code=template,
                                                   name=name, json_addl=data)
        def edge(parent, child, relation):
            service.backend.create_lineage(session, parent=parent, child=child,
                                          relationship_type=relation)
        def policy(record, scope="internal"):
            row = service._registry_policy(session, record)
            service.backend.update_instance_json(session, row, {
                "owner_subject": OWNER.subject, "owner_email": OWNER.email,
                "metadata": {"scope": scope, "users": [], "domains": [], "groups": []},
                "download": {"scope": scope, "users": [], "domains": [], "groups": []},
                "explicit_restriction": scope == "private", "edit_users": [], "share_users": [],
            })
        records = []
        for index in range(250):
            key = f"page/object-{index:04}.tsv"
            row = create(ARTIFACT_TEMPLATE, key, {
                "storage_backend": "s3", "storage_kind": "object", "node_kind": "file",
                "bucket": bucket, "key": key, "storage_uri": f"s3://{bucket}/{key}",
                "original_filename": key.rpartition("/")[2], "artifact_identity_key": uuid4().hex,
            })
            policy(row)
            records.append(row); keys.append(key); identities.append(row.euid)
        # Unrelated registered population exercises filtering without any S3 IO.
        for index in range(750):
            create(ARTIFACT_TEMPLATE, "Unrelated fixture", {
                "storage_backend": "s3", "storage_kind": "object", "node_kind": "file",
                "bucket": "other-" + bucket, "key": f"background/{index}",
                "artifact_identity_key": uuid4().hex,
            })
        for private in (False, True):
            collection = create(ARTIFACT_SET_TEMPLATE, "Private" if private else "Visible", {})
            policy(collection, "private" if private else "internal")
            for index in range(1 if private else 0, 250, 2):
                edge(collection, records[index], "artifact_set_member")
        # Three current grants: exact internal, broader domain and named external.
        for group, recipient_type, recipient, subdomains in (
            (0, "domain", "lsmc.com", False),
            (1, "domain", "lsmc.com", True),
            (2, "email", "person@lsmc.bio", False),
        ):
            share = create(SHARE_TEMPLATE, "Active fixture share", {
                "schema_version": 3, "status": "active", "policy_revision": 2,
                "owner_subject": OWNER.subject, "owner_email": OWNER.email,
                "expires_at": "2050-01-01T00:00:00Z",
            })
            revision = create(SHARE_REVISION_TEMPLATE, "Current scope", {"policy_revision": 2})
            old = create(SHARE_REVISION_TEMPLATE, "Historical scope", {"policy_revision": 1})
            edge(share, revision, "share_revision"); edge(share, old, "share_revision")
            grant = create(SHARE_GRANT_TEMPLATE, "Current grant", {
                "status": "active", "policy_revision": 2, "recipient_type": recipient_type,
                "recipient": recipient, "include_subdomains": subdomains,
                "expires_at": "2050-01-01T00:00:00Z",
            })
            edge(share, grant, "share_grant")
            for index in range(group, 240, 3):
                edge(revision, records[index], "share_revision_target")
                edge(grant, records[index], "share_grant_target")
            # A historical membership and a current target without a grant must not show.
            edge(old, records[240], "share_revision_target")
            edge(grant, records[240], "share_grant_target")
            edge(revision, records[241], "share_revision_target")
            # Expired and old-revision grants also must not show.
            for index, changes in ((242, {"expires_at": "2020-01-01T00:00:00Z"}),
                                   (243, {"policy_revision": 1}),
                                   (244, {"status": "revoked"})):
                g = create(SHARE_GRANT_TEMPLATE, "Inactive fixture grant", {
                    "status": "active", "policy_revision": 2, "recipient_type": "registered",
                    "recipient": "*", "expires_at": "2050-01-01T00:00:00Z", **changes,
                })
                edge(share, g, "share_grant"); edge(g, records[index], "share_grant_target")
                edge(revision, records[index], "share_revision_target")
    service.registry_defaults = lambda: {"listing_cache_ttl_seconds": 30}
    return service, bucket, keys, identities


def load(service, bucket, keys):
    calls = []
    def browse(**kwargs):
        calls.append(kwargs)
        return {"prefixes": [], "objects": [StorageObject(bucket, key, size=1234,
                etag="fixture", storage_class="STANDARD", last_modified="2026-07-11T04:36:36Z")
                for key in keys], "next_continuation_token": None, "is_truncated": False}
    service._require_storage = lambda: SimpleNamespace(browse_prefix=browse)
    result = service.registry_browse(f"s3://{bucket}/page/", limit=len(keys))
    assert len(calls) == 1
    return result


def test_native_explicit_membership_scope_and_privacy(indicator_fixture):
    service, bucket, keys, identities = indicator_fixture
    with request_scope():
        rows = load(service, bucket, keys)["items"]
        assert [r["euid"] for r in rows] == identities
        assert rows[0]["indicators"] == 7  # registration, set, exact lsmc.com share
        assert rows[1]["indicators"] == 11  # registration, private-but-admin-visible set, broader
        assert rows[2]["indicators"] == 11  # lsmc.bio is outside exact lsmc.com
        assert all(row["indicators"] == 3 for row in rows[240:])
    with request_scope(READER, maintenance=True):
        assert load(service, bucket, keys)["items"][1]["indicators"] == 3
    with request_scope(READER):
        rows = load(service, bucket, keys)["items"]
        assert rows[0]["indicators"] == 3
        assert rows[1]["indicators"] == 1  # private set and private share both absent
        assert all(not row["indicators"] & 12 for row in rows)
        assert not any(k in row for row in rows for k in ("share_euid", "recipient", "set_euid"))
    with request_scope(), share_context_context({}):
        assert all(not row["indicators"] & 12 for row in load(service, bucket, keys)["items"])
    with request_scope():
        row = load(service, bucket, ["page/unregistered-child.tsv"])["items"][0]
        assert row["euid"] is None and row["indicators"] == 0


@pytest.mark.performance
def test_requested_paired_load_comparison(indicator_fixture):
    baseline_path = Path(os.environ["DEWEY_INDICATOR_BASELINE"])
    output_path = Path(os.environ["DEWEY_INDICATOR_TIMING_OUTPUT"])
    assert baseline_path.is_absolute() and output_path.is_absolute()
    spec = importlib.util.spec_from_file_location("storage_before_indicators", baseline_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    service, bucket, all_keys, _ = indicator_fixture
    names = ("registry_browse", "_storage_access_batch", "_storage_locations_batch")
    current = {name: getattr(service, name) for name in names}
    baseline = {name: MethodType(getattr(module.RegistryStorageServiceMixin, name), service)
                for name in names}
    @contextmanager
    def variant(methods):
        for name, value in methods.items(): setattr(service, name, value)
        try: yield
        finally:
            for name, value in current.items(): setattr(service, name, value)
    results = []
    for actor in (OWNER, READER):
        with request_scope(actor):
            with service.backend.session_scope(commit=False) as session:
                engine = session.get_bind()
            count = [0]
            def queried(*args): count[0] += 1
            event.listen(engine, "after_cursor_execute", queried)
            try:
                for size in (25, 100, 250):
                    timings = {"before": [], "after": []}; counts = {"before": [], "after": []}
                    for iteration in range(55):
                        for name in (("before", "after") if iteration % 2 else ("after", "before")):
                            with variant(baseline if name == "before" else current):
                                count[0] = 0; start = perf_counter()
                                rows = load(service, bucket, all_keys[:size])["items"]
                                elapsed = (perf_counter() - start) * 1000
                            assert len(rows) == size
                            if iteration >= 5:
                                timings[name].append(elapsed); counts[name].append(count[0])
                    rng = Random(406)
                    ratios = []
                    for _ in range(2000):
                        sample = [rng.randrange(50) for __ in range(50)]
                        ratios.append(sum(timings["after"][i] for i in sample) /
                                      sum(timings["before"][i] for i in sample))
                    summary = {name: {"median_ms": statistics.median(values),
                                      "mean_ms": statistics.mean(values),
                                      "p95_ms": sorted(values)[47],
                                      "sql_request_counts": sorted(set(counts[name]))}
                               for name, values in timings.items()}
                    results.append({"actor": "admin" if actor.admin else "internal_reader",
                                    "rows": size, "samples_per_variant": 50, **summary,
                                    "paired_mean_ratio": statistics.mean(timings["after"]) /
                                                         statistics.mean(timings["before"]),
                                    "paired_bootstrap_95pct_ratio": [sorted(ratios)[49], sorted(ratios)[1949]],
                                    "raw_ms": timings})
                    print(json.dumps({k:v for k,v in results[-1].items() if k != "raw_ms"}), flush=True)
            finally: event.remove(engine, "after_cursor_execute", queried)
    output = {"dataset": {"registered_page_objects": 250, "background_objects": 750,
                          "sets": 2, "active_shares": 3}, "extra_s3_requests": 0,
              "method": "Alternating paired warmed native PostgreSQL service calls; cached listing stand-in, no artificial network delay; 5 warmups then 50 measured pairs per case.",
              "limits": "Local DB and synthetic explicit memberships; not production network, device paint or all workloads.",
              "results": results}
    output_path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({**output, "results": [{k:v for k,v in r.items() if k != "raw_ms"} for r in results]}))
