"""Application exception hierarchy."""


class AppError(Exception):
    """Base exception for recoverable application errors."""

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class CommandError(AppError):
    """Raised when a user-facing command cannot complete."""


class MediaProcessingError(AppError):
    """Raised when ffmpeg or image pipeline fails."""


class ReactionError(AppError):
    """Raised when reaction delivery fails after retries."""


class StorageError(AppError):
    """Raised when persistence layer fails."""
