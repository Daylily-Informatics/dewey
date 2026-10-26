"""Listing cursors bind viewer, policy, selection, and current native storage location."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dewey_service.storage import StorageObject, _STORAGE_AUTHORIZATION
from tests.support.sharing_v12_fakes import Harness, READER, actor, row


def test_filtered_prefix_pages_skip_root_marker_and_denials_without_losing_progress():
    h = Harness()
    target = h.artifact(prefix=True)
    share = h.share([target], exclude_patterns=["private/**"])
    keys = [("root/", 0), ("root/one.txt", 5), ("root/private/secret.txt", 99), ("root/nested/two.txt", 7)]
    calls = []
    def listing(*, bucket, prefix, continuation_token, limit, **kwargs):
        _STORAGE_AUTHORIZATION.get()(bucket, prefix, "metadata")
        calls.append((bucket, prefix, continuation_token, limit))
        index = int(continuation_token) if continuation_token else 0
        key, size = keys[index]
        return {"objects": [StorageObject(bucket=bucket, key=key, size=size)],
                "next_continuation_token": str(index+1) if index+1 < len(keys) else None}
    h.service._require_storage = lambda: SimpleNamespace(list_share_candidates=listing)
    with actor(READER):
        first = h.service.list_share_contents(share.euid, limit=1)
        assert [v["name"] for v in first["items"]] == ["one.txt"]
        assert first["incomplete"] and first["continuation_token"]
        second = h.service.list_share_contents(share.euid, limit=1, continuation_token=first["continuation_token"])
        assert [v["name"] for v in second["items"]] == ["nested/two.txt"]
        assert second["incomplete"] is False and second["continuation_token"] is None
    assert len(calls) == 4 and {p for _,p,_,_ in calls} == {"root/"}
    assert all(item["location_revision"] == 1 for item in first["items"]+second["items"])


def test_object_listing_uses_stable_filename_after_location_basename_changes():
    h = Harness()
    target = h.artifact(key="new-location/unrelated-name.dat", original_filename="stable.txt")
    share = h.share([target], include_patterns=["stable.txt"])
    with actor(READER):
        assert h.service.list_share_contents(share.euid, prefix="unrelated")["items"] == []
        result = h.service.list_share_contents(share.euid, prefix="sta")
    assert result["items"][0]["name"] == "stable.txt"


@pytest.mark.parametrize("changed", ["policy", "location", "selection", "viewer"])
def test_continuation_cannot_cross_reviewed_authority_or_location(changed):
    h = Harness()
    first, second = h.artifact("fixture-first"), h.artifact("fixture-second")
    share = h.share([first, second])
    with actor(READER):
        page = h.service.list_share_contents(share.euid, limit=1)
        if changed == "policy": share.json_addl["policy_revision"] = 2
        if changed == "location": second.json_addl.update(location_revision=2, key="another/key")
        if changed == "viewer":
            cursor = next(r for r in h.rows if r.euid == page["continuation_token"])
            cursor.json_addl["actor"] = "different-viewer"
        # For policy drift, retain a current grant so the cursor, not authentication, is the rejecting fence.
        if changed == "policy":
            h.service._share_grants(h.session, share)[0].json_addl["policy_revision"] = 2
            h.related(share, "share_revision", "share_revision")[0].json_addl["policy_revision"] = 2
        with pytest.raises(HTTPException) as rejected:
            h.service.list_share_contents(share.euid, limit=1, prefix="s" if changed == "selection" else "",
                                          continuation_token=page["continuation_token"])
    assert rejected.value.status_code == 409


@pytest.mark.parametrize("failure", ["unknown", "expired", "unlinked"])
def test_cursor_must_exist_be_current_and_have_native_share_lineage(failure):
    h = Harness()
    share = h.share([h.artifact()])
    with actor(READER):
        if failure == "unknown": token = "fixture-unknown-cursor"
        else:
            token = h.service._save_listing_cursor(h.session, share, "fixture-context", {"member_index": 0, "s3_token": None})
            cursor = next(r for r in h.rows if r.euid == token)
            if failure == "expired": cursor.json_addl["expires_at"] = "2020-01-01T00:00:00Z"
            else: h.edges[:] = [edge for edge in h.edges if edge[2] != "share_listing_cursor"]
        with pytest.raises(HTTPException if failure == "expired" else ValueError) as caught:
            h.service._listing_cursor(h.session, share, token, "fixture-context")
    if failure == "expired": assert caught.value.status_code == 410


def test_listing_rejects_foreign_targets_and_invalid_prefixes_before_storage():
    h = Harness()
    share = h.share([h.artifact()])
    with actor(READER):
        with pytest.raises(HTTPException) as foreign:
            h.service.list_share_contents(share.euid, target_euid="fixture-outside")
        assert foreign.value.status_code == 403
        with pytest.raises(ValueError): h.service.list_share_contents(share.euid, prefix="bad\0prefix")
