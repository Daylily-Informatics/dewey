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
        if tag == "meta":
            name, content = attrs.get("name", "").lower(), attrs.get("content", "").lower()
            self.multiqc |= (name in {"generator", "author"} and "multiqc" in content) or (name == "description" and content.startswith("multiqc:"))
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


def inspect_bundle(key, read_document, require_asset, registered_bundle=None):
    """Read only declared HTML/CSS and inspect each referenced exact asset once.

    The callbacks retain the owning service's authorization and storage controls.
    Report-specific *_files/*_data directories may include future descendants;
    generic asset directories are represented by exact declared paths only.
    """
    original_read = read_document
    cache = {}
    def read_document(path):
        if path not in cache:
            cache[path] = original_read(path)
        return cache[path]

    source, source_etag = read_document(key)
    source_parser = _References()
    source_parser.feed(source[:MAX_DOCUMENT_BYTES].decode("utf-8-sig", errors="replace"))
    if not source_parser.multiqc:
        raise NotMultiQCReport("The selected HTML is not identified as a MultiQC report")
    if len(source) > MAX_DOCUMENT_BYTES:
        raise ValueError("MultiQC document exceeds the supported 64 MiB inspection limit")
    if source_parser.errors:
        raise ValueError(source_parser.errors[0])

    # Section exports declare their parent index explicitly. The named *_files
    # directory and reciprocal index link establish the report boundary.
    pieces = key.split("/")
    for position in range(len(pieces)-2, -1, -1):
        directory = pieces[position]
        if not directory.endswith("_files"):
            continue
        owner_stem = directory[:-6]
        owner_root = "/".join(pieces[:position])
        owner_root = owner_root + "/" if owner_root else ""
        possible = {owner_root + owner_stem + suffix for suffix in (".html", ".htm")}
        parent = next((resolved for ref, necessary in source_parser.references
                       if (resolved := relative_asset(key, ref, required=necessary)) in possible), None)
        if not parent:
            continue
        index, index_etag = read_document(parent)
        index_parser = _References()
        index_parser.feed(index[:MAX_DOCUMENT_BYTES].decode("utf-8-sig", errors="replace"))
        if not index_parser.multiqc or key not in {
                relative_asset(parent, ref, required=necessary) for ref, necessary in index_parser.references}:
            raise ValueError("MultiQC section must be declared by its linked parent report index")
        parent_bundle = registered_bundle(parent) if registered_bundle else None
        relative = key[len(owner_root):]
        if not (parent_bundle and parent_bundle["source_etag"] == index_etag
                and relative in parent_bundle["required_assets"]):
            parent_bundle = inspect_bundle(parent, read_document, require_asset)
        from dewey_service.services.share_policy import selected
        for reference, necessary in source_parser.references:
            asset = relative_asset(relative, reference, required=necessary)
            if asset is None:
                continue
            if not selected(asset, parent_bundle["include_patterns"], []):
                raise ValueError("MultiQC section dependency is outside its validated parent bundle: " + asset)
            if asset not in parent_bundle["required_assets"] and asset != parent_bundle["entrypoint"]:
                require_asset(owner_root + asset)
        required = set(parent_bundle["required_assets"]) | {parent_bundle["entrypoint"]}
        required.discard(relative)
        return {**parent_bundle, "source_key": key, "source_etag": source_etag,
                "entrypoint": relative, "required_assets": sorted(required)}

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
