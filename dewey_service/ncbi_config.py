"""Load the explicitly configured NCBI key before importing Metapub."""
import os
from pathlib import Path


def load_ncbi_key() -> None:
    configured = os.environ.get("DEWEY_NCBI_API_KEY_FILE", "")
    if not configured:
        return
    path = Path(configured)
    if not path.is_absolute():
        raise RuntimeError("DEWEY_NCBI_API_KEY_FILE must be an absolute path")
    try:
        key = path.read_text(encoding="utf-8").strip()
    except OSError:
        raise RuntimeError("Dewey cannot read its configured NCBI key file") from None
    if not key or any(character.isspace() for character in key):
        raise RuntimeError("The configured NCBI key file must contain one nonempty key")
    os.environ["NCBI_API_KEY"] = key
