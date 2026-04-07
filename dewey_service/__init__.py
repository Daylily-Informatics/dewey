"""Dewey canonical artifact registry service."""

from __future__ import annotations

from typing import Any


def create_app(*args: Any, **kwargs: Any):
    """Lazy app import so CLI entrypoints avoid unrelated service startup side effects."""
    from dewey_service.app import create_app as _create_app

    return _create_app(*args, **kwargs)


__all__ = ["create_app"]
