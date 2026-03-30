from __future__ import annotations


def test_metapub_dependency_is_available() -> None:
    from dewey_service import literature

    assert literature.PubMedFetcher is not None
    assert literature.FindIt is not None
