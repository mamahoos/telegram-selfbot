"""DTOs for chunked mention messages."""

from __future__ import annotations

from dataclasses import dataclass

from hydrogram.types import MessageEntity


@dataclass(frozen=True, slots=True)
class MentionChunk:
    """One Telegram message worth of mention text and entities."""

    text: str
    entities: list[MessageEntity]
