"""Split group member mentions into Telegram-safe message chunks."""

from __future__ import annotations

from dataclasses import dataclass

from hydrogram import enums
from hydrogram.types import MessageEntity, User

from app.application.dto.mention_chunk import MentionChunk
from app.common.telegram_text import utf16_len

_SEPARATOR = " · "
_TELEGRAM_MAX_UTF16 = 4096
_DEFAULT_MAX_MENTIONS = 50
_DEFAULT_MAX_UTF16 = 3900


@dataclass(frozen=True, slots=True)
class _Part:
    text: str
    user: User | None = None
    username_mention: bool = False


def display_name(user: User) -> str:
    """Human-readable name for a mention segment."""
    parts = (
        [user.first_name or "", user.last_name or ""] if user.last_name else [user.first_name or ""]
    )
    name = " ".join(part for part in parts if part).strip()
    return name or f"user{user.id}"


def member_to_part(user: User) -> _Part:
    """Build one mention segment for a group member."""
    if user.username:
        handle = f"@{user.username}"
        return _Part(text=handle, username_mention=True)
    name = display_name(user)
    return _Part(text=f"{name} ({user.id})", user=user)


def _entity_for_part(offset_utf16: int, part: _Part) -> MessageEntity | None:
    if part.username_mention:
        return MessageEntity(
            type=enums.MessageEntityType.MENTION,
            offset=offset_utf16,
            length=utf16_len(part.text),
        )
    if part.user is not None:
        name_len = utf16_len(display_name(part.user))
        return MessageEntity(
            type=enums.MessageEntityType.TEXT_MENTION,
            offset=offset_utf16,
            length=name_len,
            user=part.user,
        )
    return None


def _parts_to_chunk(parts: list[_Part]) -> MentionChunk:
    text_pieces: list[str] = []
    entities: list[MessageEntity] = []
    offset_utf16 = 0
    for index, part in enumerate(parts):
        if index > 0:
            text_pieces.append(_SEPARATOR)
            offset_utf16 += utf16_len(_SEPARATOR)
        text_pieces.append(part.text)
        entity = _entity_for_part(offset_utf16, part)
        if entity is not None:
            entities.append(entity)
        offset_utf16 += utf16_len(part.text)
    return MentionChunk(text="".join(text_pieces), entities=entities)


def _chunk_utf16_len(parts: list[_Part]) -> int:
    if not parts:
        return 0
    total = sum(utf16_len(part.text) for part in parts)
    total += utf16_len(_SEPARATOR) * (len(parts) - 1)
    return total


def _mention_count(parts: list[_Part]) -> int:
    return len(parts)


def chunk_member_mentions(
    users: list[User],
    *,
    max_mentions_per_message: int = _DEFAULT_MAX_MENTIONS,
    max_utf16_per_message: int = _DEFAULT_MAX_UTF16,
) -> list[MentionChunk]:
    """Pack users into multiple messages respecting Telegram limits."""
    if max_mentions_per_message < 1:
        msg = "max_mentions_per_message must be at least 1"
        raise ValueError(msg)
    if max_utf16_per_message > _TELEGRAM_MAX_UTF16:
        max_utf16_per_message = _TELEGRAM_MAX_UTF16

    chunks: list[MentionChunk] = []
    current: list[_Part] = []

    for user in users:
        part = member_to_part(user)
        next_parts = [*current, part]
        next_len = _chunk_utf16_len(next_parts)
        next_mentions = _mention_count(next_parts)

        if current and (
            next_mentions > max_mentions_per_message or next_len > max_utf16_per_message
        ):
            chunks.append(_parts_to_chunk(current))
            current = [part]
            continue

        if next_mentions > max_mentions_per_message or next_len > max_utf16_per_message:
            chunks.append(_parts_to_chunk([part]))
            current = []
            continue

        current = next_parts

    if current:
        chunks.append(_parts_to_chunk(current))

    return chunks
