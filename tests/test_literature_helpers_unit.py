from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import dewey_service.literature as literature


def test_metapub_site_packages_discovers_conda_site_packages(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    site_packages = tmp_path / "lib" / "python3.13" / "site-packages"
    site_packages.mkdir(parents=True)
    (tmp_path / "lib" / "python3.13" / "not-a-dir.txt").write_text("", encoding="utf-8")

    monkeypatch.setenv("CONDA_PREFIX", str(tmp_path))
    assert literature._metapub_site_packages() == [str(site_packages)]

    monkeypatch.setenv("CONDA_PREFIX", str(tmp_path / "missing"))
    assert literature._metapub_site_packages() == []


def test_identifier_normalizers_cover_common_inputs() -> None:
    assert literature.normalize_pmid(" PMID: 123-45 ") == "12345"
    with pytest.raises(ValueError, match="pmid is required"):
        literature.normalize_pmid("pmid:none")

    assert literature.normalize_doi(" DOI:10.1000/ABC/ ") == "10.1000/abc"
    assert literature.normalize_doi("https://doi.org/10.1000/XYZ") == "10.1000/xyz"
    assert literature.normalize_doi("") is None

    assert literature.normalize_pmcid("12345") == "PMC12345"
    assert literature.normalize_pmcid(" pmc-12345 ") == "PMC12345"
    assert literature.normalize_pmcid("pmc") is None
    assert literature.normalize_pmcid("not-a-pmcid") is None


def test_list_and_snippet_normalizers_cover_edge_cases() -> None:
    assert literature.normalize_email_list([" A@EXAMPLE.COM ", "", "a@example.com"]) == [
        "a@example.com"
    ]
    assert literature.normalize_group_list([" ops ", "", "ops", "reviewers"]) == [
        "ops",
        "reviewers",
    ]
    assert literature.dedupe_strings([" Alpha ", "", None, "Alpha", "Beta"]) == ["Alpha", "Beta"]
    assert literature.build_abstract_snippet("   ") is None
    assert literature.build_abstract_snippet("short abstract", max_chars=20) == "short abstract"
    assert literature.build_abstract_snippet("word " * 20, max_chars=25) == "word word word word word…"


def test_domain_and_fulltext_helpers_cover_all_statuses(monkeypatch: pytest.MonkeyPatch) -> None:
    assert literature.allowed_domain_set("EuropePMC.org, ncbi.nlm.nih.gov ,") == {
        "europepmc.org",
        "ncbi.nlm.nih.gov",
    }
    assert literature.url_host("https://Sub.Example.com/path") == "sub.example.com"

    monkeypatch.setattr(literature, "urlparse", lambda _value: (_ for _ in ()).throw(ValueError("bad")))
    assert literature.url_host("https://broken.example.com") == ""

    monkeypatch.undo()
    allowed = {"europepmc.org", "ncbi.nlm.nih.gov"}
    assert literature.url_domain_allowed("https://europepmc.org/article", allowed) is True
    assert literature.url_domain_allowed("https://sub.ncbi.nlm.nih.gov/article", allowed) is True
    assert literature.url_domain_allowed("https://elsevier.com/article", allowed) is False
    assert literature.is_paywalled_reason("postonly redirect") is True
    assert literature.is_paywalled_reason("open access") is False
    assert literature.classify_fulltext(
        best_fulltext_url="https://europepmc.org/article",
        findit_reason=None,
        allowed_domains=allowed,
    ) == {
        "downloadable": True,
        "external_link_only": False,
        "fulltext_status": "downloadable",
    }
    assert literature.classify_fulltext(
        best_fulltext_url="https://elsevier.com/article",
        findit_reason=None,
        allowed_domains=allowed,
    ) == {
        "downloadable": False,
        "external_link_only": True,
        "fulltext_status": "external_link_only",
    }
    assert literature.classify_fulltext(
        best_fulltext_url=None,
        findit_reason="PAYWALL",
        allowed_domains=allowed,
    ) == {
        "downloadable": False,
        "external_link_only": False,
        "fulltext_status": "unavailable",
    }


def test_viewer_context_author_name_and_article_normalization() -> None:
    viewer = literature.ViewerContext.from_operator_profile(
        {
            "email": " Reader@Example.com ",
            "groups": ["ops", "ops", "reviewers"],
        }
    )
    assert viewer == literature.ViewerContext(
        subject="reader@example.com",
        email="reader@example.com",
        groups=("ops", "reviewers"),
    )
    assert viewer.owner_label == "reader@example.com"
    assert literature.ViewerContext.from_operator_profile(
        {"sub": "sub-123", "groups": "ignored"}
    ).owner_label == "sub-123"
    with pytest.raises(ValueError, match="missing subject/email"):
        literature.ViewerContext.from_operator_profile({})

    author = SimpleNamespace(fullname="Ada Lovelace")
    named = SimpleNamespace(name="Grace Hopper")
    fallback = SimpleNamespace(last_first="Doe, Jane")
    assert literature._author_name(None) is None
    assert literature._author_name(" Turing ") == "Turing"
    assert literature._author_name(author) == "Ada Lovelace"
    assert literature._author_name(named) == "Grace Hopper"
    assert literature._author_name(fallback) == "Doe, Jane"

    article = SimpleNamespace(
        pmid="PMID: 123456",
        doi="DOI:10.1000/XYZ",
        pmc="pmc123456",
        title="  Gene Therapy in Practice  ",
        journal="  Nature Medicine ",
        year=" 2026 ",
        authors=[author, named, None, "Alan Turing"],
        authors_str="ignored; because authors are present",
        abstract="  Long   abstract text. ",
        url="",
    )
    payload = literature.normalize_article_payload(
        article=article,
        best_fulltext_url=" https://europepmc.org/articles/PMC123456?pdf=render ",
        findit_reason="",
    )
    assert payload == {
        "pmid": "123456",
        "doi": "10.1000/xyz",
        "pmcid": "PMC123456",
        "title": "Gene Therapy in Practice",
        "journal": "Nature Medicine",
        "year": "2026",
        "authors": ["Ada Lovelace", "Grace Hopper", "Alan Turing"],
        "abstract": "Long   abstract text.",
        "abstract_snippet": "Long abstract text.",
        "source_urls": [
            "https://pubmed.ncbi.nlm.nih.gov/123456/",
            "https://doi.org/10.1000/xyz",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC123456/",
            "https://europepmc.org/articles/PMC123456?pdf=render",
        ],
        "best_fulltext_url": "https://europepmc.org/articles/PMC123456?pdf=render",
        "findit_reason": None,
    }

    fallback_payload = literature.normalize_article_payload(
        article=SimpleNamespace(
            pmid="789012",
            doi=None,
            pmc=None,
            title="Fallback Authors",
            journal="",
            year="",
            authors=[],
            authors_str="One Author; Two Author",
            abstract=None,
            url="https://pubmed.example.com/789012",
        ),
        best_fulltext_url=None,
        findit_reason="POSTONLY",
    )
    assert fallback_payload["authors"] == ["One Author", "Two Author"]
    assert fallback_payload["source_urls"] == ["https://pubmed.example.com/789012"]
    assert fallback_payload["findit_reason"] == "POSTONLY"


def test_metapub_adapter_requires_dependencies_and_supports_search(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(literature, "PubMedFetcher", None)
    monkeypatch.setattr(literature, "FindIt", None)
    monkeypatch.setattr(literature, "METAPUB_IMPORT_ERROR", RuntimeError("missing"))
    with pytest.raises(literature.LiteratureUnavailableError, match="metapub"):
        literature.MetapubAdapter()

    fetcher_calls: dict[str, object] = {}
    findit_calls: list[dict[str, object]] = []

    class FakeFetcher:
        def __init__(self, *, cachedir: str | None) -> None:
            fetcher_calls["cachedir"] = cachedir

        def pmids_for_query(self, query: str, *, retstart: int, retmax: int) -> list[str]:
            fetcher_calls["query"] = query
            fetcher_calls["retstart"] = retstart
            fetcher_calls["retmax"] = retmax
            return ["123456"]

        def article_by_pmid(self, pmid: str) -> SimpleNamespace:
            fetcher_calls["pmid"] = pmid
            return SimpleNamespace(
                pmid=pmid,
                doi="10.1000/example",
                pmc="PMC123456",
                title="Example",
                journal="Journal",
                year="2024",
                authors=["A. Author"],
                abstract="Abstract text",
                url="https://pubmed.ncbi.nlm.nih.gov/123456/",
            )

    class FakeFindIt:
        def __init__(
            self,
            *,
            pmid: str,
            cachedir: str | None,
            verify: bool,
            request_timeout: int,
            max_redirects: int,
        ) -> None:
            findit_calls.append(
                {
                    "pmid": pmid,
                    "cachedir": cachedir,
                    "verify": verify,
                    "request_timeout": request_timeout,
                    "max_redirects": max_redirects,
                }
            )
            self.url = "https://europepmc.org/articles/PMC123456?pdf=render"
            self.reason = None

    monkeypatch.setattr(literature, "PubMedFetcher", FakeFetcher)
    monkeypatch.setattr(literature, "FindIt", FakeFindIt)
    monkeypatch.setattr(literature, "METAPUB_IMPORT_ERROR", None)

    adapter = literature.MetapubAdapter(
        cache_dir=str(tmp_path / "cache"),
        request_timeout_seconds=0,
        max_redirects=0,
    )

    assert adapter.search(query="   ", page=1, page_size=20) == []
    results = adapter.search(query=" gene therapy ", page=2, page_size=3)

    assert (tmp_path / "cache").is_dir()
    assert fetcher_calls == {
        "cachedir": str(tmp_path / "cache"),
        "query": "gene therapy",
        "retstart": 3,
        "retmax": 3,
        "pmid": "123456",
    }
    assert findit_calls == [
        {
            "pmid": "123456",
            "cachedir": str(tmp_path / "cache"),
            "verify": True,
            "request_timeout": 1,
            "max_redirects": 1,
        }
    ]
    assert results[0]["pmid"] == "123456"
    assert results[0]["best_fulltext_url"] == "https://europepmc.org/articles/PMC123456?pdf=render"
