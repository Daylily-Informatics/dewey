from __future__ import annotations

from dewey_service.artifact_ui import split_csv


def test_split_csv_accepts_commas_newlines_and_spaces() -> None:
    assert split_csv("tumor,rna") == ["tumor", "rna"]
    assert split_csv("tumor\nrna") == ["tumor", "rna"]
    assert split_csv("tumor rna urgent") == ["tumor", "rna", "urgent"]


def test_split_csv_preserves_multiword_tags_when_commas_are_used() -> None:
    assert split_csv("time of day, project-alpha") == ["time of day", "project-alpha"]
