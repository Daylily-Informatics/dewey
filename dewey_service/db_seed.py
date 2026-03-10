"""Seed Dewey TapDB templates/overlay."""

from __future__ import annotations

import os

from dewey_service.service import DeweyService
from dewey_service.tapdb_backend import TapDBBackend


def main() -> None:
    ttl_raw = str(os.environ.get("DEWEY_DEFAULT_SHARE_REFERENCE_TTL_SECONDS") or "3600").strip()
    try:
        ttl = int(ttl_raw)
    except ValueError:
        ttl = 3600
    backend = TapDBBackend(app_username="dewey")
    service = DeweyService(
        backend,
        default_share_ttl_seconds=ttl,
    )
    service.bootstrap()


if __name__ == "__main__":
    main()
