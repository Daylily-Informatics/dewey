"""Authenticated recursive fetching with conditional, explicit resume receipts."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests
import typer

_STATE = ".dewey-download-state"
_CHUNK = 1024 * 1024


def _fetch_path(identifier, relative_path=""):
    return (
        "/fetch/"
        + quote(identifier, safe="")
        + ("/" + quote(relative_path, safe="/") if relative_path else "")
    )


def _safe_destination(root: Path, relative: str) -> Path:
    parts = relative.rstrip("/").split("/")
    if (
        not relative
        or relative.startswith("/")
        or "\\" in relative
        or ":" in relative
        or any(ord(c) < 32 or ord(c) == 127 for c in relative)
        or any(part in {"", ".", ".."} for part in parts)
        or parts[0] == _STATE
    ):
        raise ValueError("Manifest contains an unsafe or reserved filesystem path")
    destination = root.joinpath(*parts)
    current = destination
    while current != root:
        if current.is_symlink():
            raise ValueError("A download path traverses a symbolic link")
        current = current.parent
    if destination.resolve().is_relative_to(root.resolve()) is False:
        raise ValueError("Download destination escapes its selected directory")
    return destination


def _url(base, path):
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.fragment or not parsed.path.startswith("/fetch/"):
        raise ValueError("Manifest download URL is outside the configured Dewey fetch endpoint")
    return base + path


def _pages(identifier, relative_path=""):
    from dewey_service.cli.registry import _request

    token, revision, canonical = None, None, None
    while True:
        page = _request(
            "GET",
            _fetch_path(identifier, relative_path),
            params={"format": "manifest", "limit": 200, "continuation_token": token},
        )
        if revision is None:
            revision, canonical = page["policy_revision"], page["share_euid"]
        if page["policy_revision"] != revision or page["share_euid"] != canonical:
            raise RuntimeError("Share changed during recursive enumeration; restart with --resume")
        next_token = page.get("continuation_token")
        if bool(page["incomplete"]) != bool(next_token) or next_token and next_token == token:
            raise RuntimeError("Dewey returned an inconsistent inventory cursor")
        yield page
        if not next_token:
            break
        token = next_token


def _write_state(path, value):
    # This directory belongs exclusively to this command, not artifact data.
    temporary = path.with_suffix(".new")
    if temporary.exists() or temporary.is_symlink():
        raise ValueError("A prior state update is incomplete; inspect the download state directory")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(_CHUNK), b""):
            digest.update(chunk)
    return digest


def download_file(*, base, token, item, destination: Path, state_dir: Path, resume=False):
    key = hashlib.sha256(_url(base, item["fetch_path"]).encode()).hexdigest()
    lock = state_dir / (key + ".lock")
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ValueError(
            "This download is active or has an interrupted lock; inspect its state before retrying"
        ) from exc
    os.close(fd)
    try:
        return _download_file(
            base=base,
            token=token,
            item=item,
            destination=destination,
            state_dir=state_dir,
            resume=resume,
        )
    finally:
        lock.unlink()


def _download_file(*, base, token, item, destination: Path, state_dir: Path, resume=False):
    url = _url(base, item["fetch_path"])
    expected, etag = int(item["size"]), item["etag"]
    if expected < 0 or not isinstance(etag, str) or not etag:
        raise ValueError("Manifest lacks an exact size and object validator")
    key = hashlib.sha256(url.encode()).hexdigest()
    receipt_path, partial = state_dir / (key + ".json"), state_dir / (key + ".part")
    claim = {
        "url": url,
        "destination": str(destination.resolve()),
        "size": expected,
        "etag": etag,
        "version_id": item.get("version_id"),
        "status": "partial",
    }
    if any(path.is_symlink() for path in (receipt_path, partial, destination)):
        raise ValueError("Download files must not be symbolic links")
    if receipt_path.exists():
        if not resume:
            raise ValueError(
                "A download receipt already exists; use --resume to validate and continue it"
            )
        previous = json.loads(receipt_path.read_text())
        if any(
            previous.get(k) != claim[k]
            for k in ("url", "destination", "size", "etag", "version_id")
        ):
            raise ValueError(
                "Stored resume receipt differs from the current object; choose a new output directory"
            )
        if previous.get("status") == "complete":
            if (
                not destination.is_file()
                or destination.stat().st_size != expected
                or _hash_file(destination).hexdigest() != previous.get("sha256")
            ):
                raise ValueError("Completed local file no longer matches its receipt")
            return {"status": "already_complete", "bytes_received": 0, "path": str(destination)}
    else:
        if destination.exists() or partial.exists():
            raise ValueError("Existing output has no matching Dewey receipt and cannot be adopted")
        _write_state(receipt_path, claim)
    if destination.exists():
        raise ValueError("Output already exists; a partial transfer never overwrites it")
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > expected:
        raise ValueError("Partial file exceeds its expected length")
    digest = _hash_file(partial) if offset else hashlib.sha256()
    headers = {
        "Authorization": "Bearer " + token,
        "If-Match": etag,
        "Accept": "application/octet-stream",
    }
    if offset and offset < expected:
        headers["Range"] = f"bytes={offset}-"
    method = "HEAD" if offset == expected and partial.exists() else "GET"
    received = 0
    with requests.request(
        method, url, headers=headers, stream=True, timeout=(10, 300), allow_redirects=False
    ) as response:
        wanted = 206 if "Range" in headers else 200
        if response.status_code != wanted:
            raise RuntimeError(
                f"Dewey fetch returned HTTP {response.status_code}; partial data and receipt retained"
            )
        if response.headers.get("ETag") != etag:
            raise RuntimeError("Dewey returned a different object validator; partial data retained")
        if "Range" in headers:
            value = re.fullmatch(
                r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", "")
            )
            if not value or tuple(map(int, value.groups())) != (offset, expected - 1, expected):
                raise RuntimeError("Resume response range does not match the retained partial file")
        expected_response = expected if method == "HEAD" else expected - offset
        if response.headers.get("Content-Length") != str(expected_response):
            raise RuntimeError("Dewey response length differs from the pinned manifest")
        if method != "HEAD":
            destination.parent.mkdir(parents=True, exist_ok=True)
            with partial.open("ab" if partial.exists() else "xb") as stream:
                for chunk in response.iter_content(chunk_size=_CHUNK):
                    if chunk:
                        if offset + received + len(chunk) > expected:
                            raise RuntimeError("Dewey response exceeded its pinned length")
                        stream.write(chunk)
                        digest.update(chunk)
                        received += len(chunk)
                stream.flush()
                os.fsync(stream.fileno())
            if offset + received != expected:
                raise RuntimeError(
                    "Download ended early; use --resume to continue the retained partial file"
                )
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Same-filesystem hard-link creation is atomic and refuses to replace any
    # file created at the destination during the transfer.
    os.link(partial, destination)
    partial.unlink()
    _write_state(receipt_path, {**claim, "status": "complete", "sha256": digest.hexdigest()})
    return {"status": "complete", "bytes_received": received, "path": str(destination)}


def fetch(
    identifier: str = typer.Argument(..., help="Share EUID or claimed slug."),
    output: Path = typer.Option(..., help="Destination file, or directory with --recursive."),
    relative_path: str = typer.Option(""),
    recursive: bool = typer.Option(False),
    resume: bool = typer.Option(False),
):
    """Fetch one file or every manifest page; --resume validates retained receipts and uses conditional ranges."""
    from dewey_service.cli.registry import _connection, _emit

    def run():
        base, token = _connection()
        if output.is_symlink():
            raise ValueError("Output must not be a symbolic link")
        root = output.resolve() if recursive else output.resolve().parent
        root.mkdir(parents=True, exist_ok=True)
        state_dir = root / _STATE
        if state_dir.is_symlink():
            raise ValueError("Download state directory must not be a symbolic link")
        state_dir.mkdir(mode=0o700, exist_ok=True)
        files = received = skipped = 0
        if recursive:
            for page in _pages(identifier, relative_path):
                for item in page["items"]:
                    destination = _safe_destination(root, item["path"])
                    if item["path"].endswith("/"):
                        if item["size"] != 0:
                            raise ValueError(
                                "Nonempty S3 keys ending in / require individual download"
                            )
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    result = download_file(
                        base=base,
                        token=token,
                        item=item,
                        destination=destination,
                        state_dir=state_dir,
                        resume=resume,
                    )
                    files += 1
                    received += result["bytes_received"]
                    skipped += result["status"] == "already_complete"
        else:
            path = _fetch_path(identifier, relative_path) + "?download=true"
            with requests.head(
                _url(base, path),
                headers={"Authorization": "Bearer " + token, "Accept": "application/octet-stream"},
                timeout=(10, 300),
                allow_redirects=False,
            ) as response:
                if response.status_code != 200 or not response.headers.get("ETag"):
                    raise RuntimeError(
                        f"Dewey file metadata returned HTTP {response.status_code}; select one exact file"
                    )
                item = {
                    "fetch_path": path,
                    "size": int(response.headers["Content-Length"]),
                    "etag": response.headers["ETag"],
                }
            result = download_file(
                base=base,
                token=token,
                item=item,
                destination=output.resolve(),
                state_dir=state_dir,
                resume=resume,
            )
            files, received, skipped = (
                1,
                result["bytes_received"],
                int(result["status"] == "already_complete"),
            )
        return {
            "status": "complete",
            "output": str(output.resolve()),
            "files": files,
            "already_complete": skipped,
            "bytes_received": received,
            "enumeration_complete": True,
        }

    _emit(run)


def manifest(
    identifier: str = typer.Argument(...),
    output: Path = typer.Option(..., dir_okay=False),
    relative_path: str = typer.Option(""),
):
    """Write a complete JSON manifest, following all server pages before publishing the output file."""
    from dewey_service.cli.registry import _emit

    def run():
        if output.exists() or output.is_symlink():
            raise ValueError("Manifest output already exists")
        partial = output.with_name(output.name + ".partial")
        count, first = 0, True
        with partial.open("x") as stream:
            stream.write('{"items":[')
            for page in _pages(identifier, relative_path):
                for item in page["items"]:
                    stream.write(("" if first else ",") + json.dumps(item, separators=(",", ":")))
                    first = False
                    count += 1
            stream.write(
                '],"enumeration_complete":true,"share_euid":'
                + json.dumps(page["share_euid"])
                + ',"policy_revision":'
                + str(page["policy_revision"])
                + "}"
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.link(partial, output)
        partial.unlink()
        return {"status": "complete", "output": str(output.resolve()), "objects": count}

    _emit(run)
