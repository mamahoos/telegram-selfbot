"""Mention chunker tests."""

from __future__ import annotations

from dataclasses import dataclass

from hydrogram import enums

from app.application.services.mention_chunker import (
    chunk_member_mentions,
    display_name,
    member_to_part,
)
from app.common.telegram_text import utf16_len as common_utf16_len


@dataclass
class _FakeUser:
    id: int
    first_name: str | None = "Ali"
    last_name: str | None = None
    username: str | None = None
    is_bot: bool = False
    is_deleted: bool = False


def test_display_name_fallback() -> None:
    user = _FakeUser(id=99, first_name=None, last_name=None)
    assert display_name(user) == "User 99"  # type: ignore[arg-type]


def test_name_only_text_mention_with_username() -> None:
    user = _FakeUser(id=1, first_name="Ada", username="ada")
    chunks = chunk_member_mentions([user], max_mentions_per_message=50, max_utf16_per_message=3900)  # type: ignore[list-item]
    assert chunks[0].text == "Ada"
    assert "@" not in chunks[0].text
    assert chunks[0].entities[0].type == enums.MessageEntityType.TEXT_MENTION
    assert chunks[0].entities[0].length == common_utf16_len("Ada")


def test_name_only_without_username() -> None:
    user = _FakeUser(id=42, first_name="Sara", username=None)
    chunks = chunk_member_mentions([user], max_mentions_per_message=50, max_utf16_per_message=3900)  # type: ignore[list-item]
    assert chunks[0].text == "Sara"
    assert "(" not in chunks[0].text
    assert chunks[0].entities[0].type == enums.MessageEntityType.TEXT_MENTION


def test_splits_when_mention_limit_exceeded() -> None:
    users = [_FakeUser(id=i, first_name=f"U{i}") for i in range(55)]  # type: ignore[misc]
    chunks = chunk_member_mentions(
        users,  # type: ignore[arg-type]
        max_mentions_per_message=50,
        max_utf16_per_message=3900,
    )
    assert len(chunks) == 2
    assert len(chunks[0].entities) == 50
    assert len(chunks[1].entities) == 5


def test_member_to_part_uses_display_name_only() -> None:
    user = _FakeUser(id=7, first_name="Oshida", last_name="Poodineh", username="Oshidapoodineh")
    part = member_to_part(user)  # type: ignore[arg-type]
    assert part.text == "Oshida Poodineh"
    assert part.user is user
