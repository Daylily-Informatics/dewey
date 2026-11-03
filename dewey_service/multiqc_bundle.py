"""Declared MultiQC dependency closure; no sibling discovery or implicit grants."""
from __future__ import annotations

import posixpath
import re
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

MAX_DOCUMENT_BYTES = 64 * 1024 * 1024
MAX_DEPENDENCIES = 10000


class NotMultiQCReport(ValueError):
    """An inspected HTML document belongs to another report type."""


def html_candidate(payload):
    return (payload.get("storage_kind") == "object"
            and payload.get("storage_backend") == "s3"
            and str(payload.get("key", "")).lower().endswith((".html", ".htm")))


def multiqc_candidate(payload):
    key = str(payload.get("key", ""))
    return (html_candidate(payload) and ("multiqc" in key.lower()
                 or "multiqc" in str(payload.get("artifact_type", "")).lower()
                 or payload.get("metadata", {}).get("report_kind") == "multiqc"))


class _References(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []
        self.title = False
        self.multiqc = False
        self.errors = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "base":
            self.errors.append("MultiQC bundle must use document-relative paths, without a base element")
        if tag == "title":
            self.title = True
        if tag == "meta" and attrs.get("name", "").lower() == "generator":
            self.multiqc |= "multiqc" in attrs.get("content", "").lower()
        for attribute in ("src", "href"):
            if attrs.get(attribute):
                required = tag != "a" and not (tag == "link" and "stylesheet" not in attrs.get("rel", ""))
                self.references.append((attrs[attribute], required))
        if attrs.get("srcset"):
            self.errors.append("MultiQC srcset dependencies require an explicit supported bundle format")

    def handle_endtag(self, tag):
        if tag == "title":
            self.title = False

    def handle_data(self, value):
        if self.title and "multiqc" in value.lower():
            self.multiqc = True


def relative_asset(document, reference, *, required):
    value = reference.strip()
    if not value or value.startswith(("#", "data:", "blob:", "javascript:", "mailto:")):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        if required:
            raise ValueError("MultiQC report requires an external asset; include it in the report bundle")
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    if path.startswith("/") or "\\" in path or any(ord(c) < 32 for c in path):
        raise ValueError("MultiQC asset path is not a safe report-relative path")
    result = posixpath.normpath(posixpath.join(posixpath.dirname(document), path))
    if result in {".", ".."} or result.startswith("../"):
        raise ValueError("MultiQC asset escapes its report directory")
    return result


def inspect_bundle(key, read_document, require_asset):
    """Read only declared HTML/CSS and inspect each referenced exact asset once.

    The callbacks retain the owning service's authorization and storage controls.
    Report-specific *_files/*_data directories may include future descendants;
    generic asset directories are represented by exact declared paths only.
    """
    root, _, entrypoint = key.rpartition("/")
    root = root + "/" if root else ""
    stem = entrypoint.rsplit(".", 1)[0]
    owned_directories = {stem + "_files", stem + "_data"}
    documents = [entrypoint]
    seen_documents = set()
    required = set()
    source_etag = None
    detected = False
    while documents:
        document = documents.pop(0)
        if document in seen_documents:
            continue
        seen_documents.add(document)
        raw, etag = read_document(root + document)
        if len(raw) > MAX_DOCUMENT_BYTES:
            raise ValueError("MultiQC document exceeds the supported 64 MiB inspection limit")
        text = raw.decode("utf-8-sig")
        references = []
        if document.lower().endswith((".html", ".htm")):
            parser = _References()
            parser.feed(text)
            references = parser.references
            if document == entrypoint:
                detected = parser.multiqc
                source_etag = etag
                if not detected:
                    raise NotMultiQCReport("The selected HTML is not identified as a MultiQC report")
            if parser.errors:
                raise ValueError(parser.errors[0])
        else:
            references = [(a or b or c, True) for a, b, c in re.findall(
                r"url\(\s*(?:'([^']*)'|\"([^\"]*)\"|([^)'\"]+))\s*\)", text)]
        for reference, necessary in references:
            asset = relative_asset(document, reference, required=necessary)
            if asset is None or asset == entrypoint or asset in required:
                continue
            if asset.lower().endswith((".html", ".htm")) and asset.split("/", 1)[0] not in owned_directories:
                raise ValueError("MultiQC bundle links a different report outside its report-specific assets")
            required.add(asset)
            if len(required) > MAX_DEPENDENCIES:
                raise ValueError("MultiQC bundle exceeds the supported dependency inventory")
            if asset.lower().endswith((".html", ".htm", ".css")):
                documents.append(asset)
            else:
                require_asset(root + asset)
    patterns = {entrypoint}
    for asset in required:
        directory = asset.split("/", 1)[0]
        patterns.add(directory + "/**" if "/" in asset and directory in owned_directories else asset)
    return {"schema_version": 1, "kind": "multiqc", "mode": "bundle" if required else "standalone",
            "source_key": key, "root_key": root, "entrypoint": entrypoint,
            "source_etag": source_etag, "include_patterns": sorted(patterns),
            "required_assets": sorted(required)}


def saved_bundle(payload):
    value = payload.get("report_bundle")
    if value is None:
        return None
    if (not isinstance(value, dict) or value.get("schema_version") != 1
            or value.get("kind") != "multiqc" or value.get("mode") not in {"bundle", "standalone"}
            or value.get("source_key") != payload.get("key")
            or value.get("root_key", "") + value.get("entrypoint", "") != payload.get("key")
            or not isinstance(value.get("include_patterns"), list) or not value["include_patterns"]):
        raise ValueError("Saved MultiQC bundle is invalid or its storage location changed; repair registration")
    return value
