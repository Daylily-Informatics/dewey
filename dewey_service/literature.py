"""Helpers for Dewey literature discovery and visibility."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _metapub_site_packages() -> list[str]:
    prefix = str(os.environ.get("CONDA_PREFIX") or "").strip()
    if not prefix:
        return []
    root = Path(prefix)
    if not root.exists():
        return []
    return [str(path) for path in sorted(root.glob("lib/python*/site-packages")) if path.is_dir()]


def _load_metapub():
    last_exc: Exception | None = None
    for _attempt in range(2):
        try:
            from metapub import PubMedFetcher as _PubMedFetcher
            from metapub.findit import FindIt as _FindIt

            return _PubMedFetcher, _FindIt, None
        except Exception as exc:  # pragma: no cover - runtime dependency guard
            last_exc = exc
            added_path = False
            for candidate in _metapub_site_packages():
                if candidate not in sys.path:
                    sys.path.insert(0, candidate)
                    added_path = True
            if not added_path:
                break
    return None, None, last_exc


METAPUB_IMPORT_ERROR: Exception | None = None
PubMedFetcher = None
FindIt = None
PubMedFetcher, FindIt, METAPUB_IMPORT_ERROR = _load_metapub()


class LiteratureUnavailableError(RuntimeError):
    """Raised when literature functionality is unavailable."""


def normalize_pmid(value: Any) -> str:
    cleaned = "".join(ch for ch in str(value or "").strip() if ch.isdigit())
    if not cleaned:
        raise ValueError("pmid is required")
    return cleaned


def normalize_doi(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    if not cleaned:
        return None
    lowered = cleaned.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            lowered = cleaned.lower()
    return cleaned.strip().strip("/").lower() or None


def normalize_pmcid(value: Any) -> str | None:
    cleaned = str(value or "").strip().upper()
    if not cleaned:
        return None
    if cleaned.isdigit():
        cleaned = f"PMC{cleaned}"
    if not cleaned.startswith("PMC"):
        return None
    digits = "".join(ch for ch in cleaned[3:] if ch.isdigit())
    if not digits:
        return None
    return f"PMC{digits}"


def normalize_email_list(values: list[str] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in values or []:
        cleaned = str(item or "").strip().lower()
        if cleaned and cleaned not in seen:
            out.append(cleaned)
            seen.add(cleaned)
    return out


def normalize_group_list(values: list[str] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in values or []:
        cleaned = str(item or "").strip()
        if cleaned and cleaned not in seen:
            out.append(cleaned)
            seen.add(cleaned)
    return out


def dedupe_strings(values: list[str | None]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        cleaned = str(item or "").strip()
        if cleaned and cleaned not in seen:
            out.append(cleaned)
            seen.add(cleaned)
    return out


def build_abstract_snippet(value: Any, max_chars: int = 320) -> str | None:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def allowed_domain_set(raw: str | list[str] | tuple[str, ...] | set[str]) -> set[str]:
    if isinstance(raw, str):
        values = raw.split(",")
    else:
        values = list(raw)
    return {str(item or "").strip().lower() for item in values if str(item or "").strip()}


def url_host(value: str | None) -> str:
    try:
        return str(urlparse(str(value or "").strip()).netloc or "").strip().lower()
    except Exception:
        return ""


def url_domain_allowed(url: str | None, allowed_domains: set[str]) -> bool:
    host = url_host(url)
    if not host:
        return False
    for domain in allowed_domains:
        if host == domain or host.endswith(f".{domain}"):
            return True
    return False


def is_paywalled_reason(reason: str | None) -> bool:
    upper = str(reason or "").upper()
    return any(token in upper for token in ("PAYWALL", "DENIED", "POSTONLY"))


def classify_fulltext(
    *,
    best_fulltext_url: str | None,
    findit_reason: str | None,
    allowed_domains: set[str],
) -> dict[str, Any]:
    downloadable = (
        bool(best_fulltext_url)
        and not is_paywalled_reason(findit_reason)
        and url_domain_allowed(
            best_fulltext_url,
            allowed_domains,
        )
    )
    external_link_only = bool(best_fulltext_url) and not downloadable
    if downloadable:
        fulltext_status = "downloadable"
    elif external_link_only:
        fulltext_status = "external_link_only"
    else:
        fulltext_status = "unavailable"
    return {
        "downloadable": downloadable,
        "external_link_only": external_link_only,
        "fulltext_status": fulltext_status,
    }


@dataclass(frozen=True)
class ViewerContext:
    subject: str
    email: str
    groups: tuple[str, ...]

    @classmethod
    def from_operator_profile(cls, profile: dict[str, Any] | None) -> "ViewerContext":
        payload = dict(profile or {})
        email = str(payload.get("email") or "").strip().lower()
        subject = str(payload.get("sub") or "").strip() or email
        if not subject:
            raise ValueError("operator_profile is missing subject/email")
        raw_groups = payload.get("groups") or []
        groups = tuple(normalize_group_list(raw_groups if isinstance(raw_groups, list) else []))
        return cls(subject=subject, email=email, groups=groups)

    @property
    def owner_label(self) -> str:
        return self.email or self.subject


class MetapubAdapter:
    """Thin wrapper around metapub PubMed search and lookup helpers."""

    def __init__(
        self,
        *,
        cache_dir: str | None = None,
        request_timeout_seconds: int = 10,
        max_redirects: int = 3,
    ) -> None:
        if PubMedFetcher is None or FindIt is None:
            raise LiteratureUnavailableError(
                "Literature endpoints require metapub to be installed in the Dewey environment."
            ) from METAPUB_IMPORT_ERROR
        cachedir = str(cache_dir or "").strip() or None
        if cachedir:
            Path(cachedir).expanduser().mkdir(parents=True, exist_ok=True)
        self.cache_dir = cachedir
        self.request_timeout_seconds = max(1, int(request_timeout_seconds))
        self.max_redirects = max(1, int(max_redirects))
        self._fetcher = PubMedFetcher(cachedir=cachedir)

    def search(self, *, query: str, page: int = 1, page_size: int = 20) -> list[dict[str, Any]]:
        clean_query = str(query or "").strip()
        if not clean_query:
            return []
        retstart = max(0, (max(1, int(page)) - 1) * max(1, int(page_size)))
        retmax = max(1, int(page_size))
        pmids = self._fetcher.pmids_for_query(
            clean_query,
            retstart=retstart,
            retmax=retmax,
        )
        return [self.fetch_record(pmid) for pmid in pmids]

    def fetch_record(self, pmid: str) -> dict[str, Any]:
        clean_pmid = normalize_pmid(pmid)
        article = self._fetcher.article_by_pmid(clean_pmid)
        findit = FindIt(
            pmid=clean_pmid,
            cachedir=self.cache_dir,
            verify=True,
            request_timeout=self.request_timeout_seconds,
            max_redirects=self.max_redirects,
        )
        return normalize_article_payload(
            article=article, best_fulltext_url=findit.url, findit_reason=findit.reason
        )


def _author_name(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    for attr in ("fullname", "name", "last_fm", "last_first"):
        candidate = str(getattr(value, attr, "") or "").strip()
        if candidate:
            return candidate
    return str(value).strip() or None


def normalize_article_payload(
    *,
    article: Any,
    best_fulltext_url: str | None,
    findit_reason: str | None,
) -> dict[str, Any]:
    pmid = normalize_pmid(getattr(article, "pmid", ""))
    doi = normalize_doi(getattr(article, "doi", None))
    pmcid = normalize_pmcid(getattr(article, "pmc", None))
    title = str(getattr(article, "title", "") or "").strip()
    journal = str(getattr(article, "journal", "") or "").strip() or None
    year = str(getattr(article, "year", "") or "").strip() or None
    authors = dedupe_strings(
        [_author_name(item) for item in list(getattr(article, "authors", []) or [])]
    )
    if not authors:
        authors_str = str(getattr(article, "authors_str", "") or "").strip()
        if authors_str:
            authors = [part.strip() for part in authors_str.split(";") if part.strip()]

    landing_url = (
        str(getattr(article, "url", "") or "").strip() or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    )
    doi_url = f"https://doi.org/{doi}" if doi else None
    pmc_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else None
    source_urls = dedupe_strings([landing_url, doi_url, pmc_url, best_fulltext_url])

    return {
        "pmid": pmid,
        "doi": doi,
        "pmcid": pmcid,
        "title": title,
        "journal": journal,
        "year": year,
        "authors": authors,
        "abstract": str(getattr(article, "abstract", "") or "").strip() or None,
        "abstract_snippet": build_abstract_snippet(getattr(article, "abstract", None)),
        "source_urls": source_urls,
        "best_fulltext_url": str(best_fulltext_url or "").strip() or None,
        "findit_reason": str(findit_reason or "").strip() or None,
    }
