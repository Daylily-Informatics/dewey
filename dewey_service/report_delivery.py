"""Streaming preview representations; stored report artifacts stay unchanged."""

from __future__ import annotations

import json
from pathlib import Path
import re

_VERSION = "dewey-preview-1:"
_BRIDGE = (Path(__file__).parent / "static" / "report-section-bridge.js").read_text()


def preview_etag(value):
    return 'W/"' + _VERSION + value.removeprefix('W/').strip('"') + '"'


def provider_validator(value):
    # Only a validator for this renderer revision can reuse a transformed body.
    if not value:
        return None
    tags = re.findall(r'W/"' + re.escape(_VERSION) + r'([^"\r\n]+)"', value)
    return ", ".join('"' + tag + '"' for tag in tags) or None


def accepts_gzip(value):
    for item in value.lower().split(","):
        name, *parameters = item.strip().split(";")
        if name == "gzip":
            quality = 1.0
            for parameter in parameters:
                if parameter.strip().startswith("q="):
                    try:
                        quality = float(parameter.strip()[2:])
                    except ValueError:
                        return False
            return quality > 0
    return False


def section_bridge(etag, application_origin):
    config = json.dumps({"etag": etag, "applicationOrigin": application_origin}).replace("<", "\\u003c")
    return ("\n<script>" + _BRIDGE.replace("__DEWEY_SECTION_CONFIG__", config, 1) + "</script>\n").encode()
