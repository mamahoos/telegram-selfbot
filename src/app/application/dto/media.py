"""Media-related DTOs."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProcessedSticker:
    path: Path
    emoji: str


@dataclass(frozen=True, slots=True)
class GifConversionResult:
    path: Path
    size_bytes: int
