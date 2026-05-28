"""Helpers for Hydrogram download paths."""

from pathlib import Path
from typing import BinaryIO

from app.common.exceptions import MediaProcessingError


def ensure_local_path(path: str | BinaryIO | None) -> Path:
    """Normalize Hydrogram download result to a local path."""
    if path is None:
        raise MediaProcessingError("Download returned empty path")
    if isinstance(path, Path):
        return path
    if isinstance(path, str):
        return Path(path)
    raise MediaProcessingError("Download returned non-path result")
