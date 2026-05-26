"""Dewey domain service built on TapDB persistence."""

from __future__ import annotations

from dewey_service.services.artifact_sets import ArtifactSetServiceMixin
from dewey_service.services.artifacts import ArtifactServiceMixin
from dewey_service.services.base import BaseDeweyService, DeweyConflictError, DeweyNotFoundError
from dewey_service.services.external_objects import ExternalObjectServiceMixin
from dewey_service.services.literature import LiteratureServiceMixin
from dewey_service.services.search import SearchServiceMixin
from dewey_service.services.sequencer_runs import SequencerRunRegistrationServiceMixin
from dewey_service.services.sharing import SharingServiceMixin


class DeweyService(
    SequencerRunRegistrationServiceMixin,
    ArtifactServiceMixin,
    LiteratureServiceMixin,
    SearchServiceMixin,
    ArtifactSetServiceMixin,
    SharingServiceMixin,
    ExternalObjectServiceMixin,
    BaseDeweyService,
):
    """Persistent Dewey artifact service."""


__all__ = ["DeweyService", "DeweyConflictError", "DeweyNotFoundError"]
