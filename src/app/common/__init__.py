"""Shared primitives."""

from app.common.exceptions import (
    AppError,
    CommandError,
    MediaProcessingError,
    ReactionError,
    StorageError,
)

__all__ = [
    "AppError",
    "CommandError",
    "MediaProcessingError",
    "ReactionError",
    "StorageError",
]
