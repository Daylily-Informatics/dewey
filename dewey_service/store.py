"""In-memory canonical artifact store for Dewey v1 scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_euid: str
    artifact_type: str
    storage_uri: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactSetRecord:
    artifact_set_euid: str
    artifact_set_type: str
    artifact_euids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ShareReferenceRecord:
    share_reference_euid: str
    target_euid: str
    target_type: str


class InMemoryArtifactStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._artifact_seq = count(1)
        self._set_seq = count(1)
        self._share_seq = count(1)
        self._artifacts: dict[str, ArtifactRecord] = {}
        self._artifact_sets: dict[str, ArtifactSetRecord] = {}
        self._share_refs: dict[str, ShareReferenceRecord] = {}

    def create_artifact(
        self,
        *,
        artifact_type: str,
        storage_uri: str,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactRecord:
        with self._lock:
            artifact_euid = f"AT-{next(self._artifact_seq):08d}"
            rec = ArtifactRecord(
                artifact_euid=artifact_euid,
                artifact_type=artifact_type,
                storage_uri=storage_uri,
                metadata=dict(metadata or {}),
            )
            self._artifacts[artifact_euid] = rec
            return rec

    def get_artifact(self, artifact_euid: str) -> ArtifactRecord | None:
        return self._artifacts.get(str(artifact_euid))

    def create_artifact_set(self, *, artifact_set_type: str) -> ArtifactSetRecord:
        with self._lock:
            artifact_set_euid = f"AS-{next(self._set_seq):08d}"
            rec = ArtifactSetRecord(
                artifact_set_euid=artifact_set_euid,
                artifact_set_type=artifact_set_type,
                artifact_euids=[],
            )
            self._artifact_sets[artifact_set_euid] = rec
            return rec

    def get_artifact_set(self, artifact_set_euid: str) -> ArtifactSetRecord | None:
        return self._artifact_sets.get(str(artifact_set_euid))

    def add_artifact_to_set(self, *, artifact_set_euid: str, artifact_euid: str) -> ArtifactSetRecord:
        with self._lock:
            set_rec = self._artifact_sets.get(str(artifact_set_euid))
            if set_rec is None:
                raise KeyError(f"Artifact set not found: {artifact_set_euid}")
            if artifact_euid not in self._artifacts:
                raise KeyError(f"Artifact not found: {artifact_euid}")
            if artifact_euid in set_rec.artifact_euids:
                return set_rec
            updated = ArtifactSetRecord(
                artifact_set_euid=set_rec.artifact_set_euid,
                artifact_set_type=set_rec.artifact_set_type,
                artifact_euids=[*set_rec.artifact_euids, artifact_euid],
            )
            self._artifact_sets[set_rec.artifact_set_euid] = updated
            return updated

    def create_share_reference(self, *, target_type: str, target_euid: str) -> ShareReferenceRecord:
        with self._lock:
            if target_type == "artifact" and target_euid not in self._artifacts:
                raise KeyError(f"Artifact not found: {target_euid}")
            if target_type == "artifact_set" and target_euid not in self._artifact_sets:
                raise KeyError(f"Artifact set not found: {target_euid}")
            share_reference_euid = f"SH-{next(self._share_seq):08d}"
            rec = ShareReferenceRecord(
                share_reference_euid=share_reference_euid,
                target_type=target_type,
                target_euid=target_euid,
            )
            self._share_refs[share_reference_euid] = rec
            return rec
