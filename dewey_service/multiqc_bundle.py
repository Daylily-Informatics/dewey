"""Declared MultiQC dependency closure; no sibling discovery or implicit grants."""
from __future__ import annotations

import posixpath
import re
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

MAX_DOCUMENT_BYTES = 64 * 1024 * 1024
MAX_DEPENDENCIES = 10000


class RequiredExternalAssets(ValueError):
    def __init__(self, assets):
        self.assets = sorted(set(assets))
        super().__init__("MultiQC report requires external assets in its local report bundle: " + ", ".join(self.assets))


class NotMultiQCReport(ValueError):
    """An inspected HTML document belongs to another report type."""


def html_candidate(payload):
    # Declared collateral is registered as a bundle member, not an independent
    # report. Use the same classification in transactional and detached paths.
    return (payload.get("metadata", {}).get("artifact_role") != "multiqc_report_asset"
            and payload.get("storage_kind") == "object"
            and payload.get("storage_backend") == "s3"
            and str(payload.get("key", "")).lower().endswith((".html", ".htm")))


def multiqc_candidate(payload):
    key = str(payload.get("key", ""))
    return (html_candidate(payload) and ("multiqc" in posixpath.basename(key).lower()
                 or "multiqc" in str(payload.get("artifact_type", "")).lower()
                 or payload.get("metadata", {}).get("report_kind") == "multiqc"))


class _References(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []
        self.title = False
        self.multiqc = False
        self.errors = []
        self.html_markup = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.html_markup |= tag in {"html", "head", "body", "title", "meta", "script", "style", "div", "table", "h1"}
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
            raise RequiredExternalAssets([value])
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


def inspect_bundle(key, read_document, require_asset, registered_bundle=None, *, declared_multiqc=False, prepare_batch=None):
    """Read only declared HTML/CSS and inspect each referenced exact asset once.

    The callbacks retain the owning service's authorization and storage controls.
    Report-specific *_files/*_data directories may include future descendants;
    generic asset directories are represented by exact declared paths only.
    Optional prepare_batch receives each discovered frontier as (exact key,
    head_only) pairs before the read/HEAD callbacks consume it. It may arrange
    lazy batched authorization or prefetch; the consuming callbacks must enforce
    authorization before every read and must not discover additional objects.
    """
    original_read = read_document
    cache = {}
    def read_document(path):
        if path not in cache:
            cache[path] = original_read(path)
        return cache[path]

    if prepare_batch is not None:
        prepare_batch([(key, False)])
    source, source_etag = read_document(key)
    source_parser = _References()
    source_parser.feed(source[:MAX_DOCUMENT_BYTES].decode("utf-8-sig", errors="replace"))
    if not (source_parser.multiqc or (declared_multiqc and source_parser.html_markup)):
        raise NotMultiQCReport("The selected HTML is not identified as a MultiQC report")
    if len(source) > MAX_DOCUMENT_BYTES:
        raise ValueError("MultiQC document exceeds the supported 64 MiB inspection limit")
    if source_parser.errors:
        raise ValueError(source_parser.errors[0])
    external = [reference for reference, required in source_parser.references
                if required and not reference.startswith(("data:", "blob:", "javascript:", "mailto:"))
                and (urlsplit(reference).scheme or urlsplit(reference).netloc)]
    if external:
        raise RequiredExternalAssets(external)

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
        if prepare_batch is not None:
            prepare_batch([(parent, False)])
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
            parent_bundle = inspect_bundle(parent, read_document, require_asset, prepare_batch=prepare_batch)
        from dewey_service.services.share_policy import selected
        extra_assets = []
        for reference, necessary in source_parser.references:
            asset = relative_asset(relative, reference, required=necessary)
            if asset is None:
                continue
            if not selected(asset, parent_bundle["include_patterns"], []):
                raise ValueError("MultiQC section dependency is outside its validated parent bundle: " + asset)
            if asset not in parent_bundle["required_assets"] and asset != parent_bundle["entrypoint"]:
                extra_assets.append(owner_root + asset)
        if prepare_batch is not None:
            prepare_batch([(asset, True) for asset in extra_assets])
        for asset in extra_assets:
            require_asset(asset)
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
        wave, documents = documents, []
        frontier = []
        assets = []
        for document in wave:
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
                    detected = parser.multiqc or (declared_multiqc and parser.html_markup)
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
                    frontier.append((root + asset, False))
                else:
                    assets.append(root + asset)
                    frontier.append((root + asset, True))
        if prepare_batch is not None:
            prepare_batch(frontier)
        for asset in assets:
            require_asset(asset)
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
