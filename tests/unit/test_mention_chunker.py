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


def test_utf16_len_ascii() -> None:
    assert common_utf16_len("abc") == 3


def test_display_name_fallback() -> None:
    user = _FakeUser(id=99, first_name=None, last_name=None)
    assert display_name(user) == "user99"  # type: ignore[arg-type]


def test_username_mention_entity() -> None:
    user = _FakeUser(id=1, username="ada")
    chunks = chunk_member_mentions([user], max_mentions_per_message=50, max_utf16_per_message=3900)  # type: ignore[list-item]
    assert len(chunks) == 1
    assert chunks[0].text == "@ada"
    assert len(chunks[0].entities) == 1
    assert chunks[0].entities[0].type == enums.MessageEntityType.MENTION


def test_text_mention_without_username() -> None:
    user = _FakeUser(id=42, first_name="Sara", username=None)
    chunks = chunk_member_mentions([user], max_mentions_per_message=50, max_utf16_per_message=3900)  # type: ignore[list-item]
    assert chunks[0].text == "Sara (42)"
    assert chunks[0].entities[0].type == enums.MessageEntityType.TEXT_MENTION
    assert chunks[0].entities[0].length == common_utf16_len("Sara")


def test_splits_when_mention_limit_exceeded() -> None:
    users = [_FakeUser(id=i, username=f"u{i}") for i in range(55)]  # type: ignore[misc]
    chunks = chunk_member_mentions(
        users,  # type: ignore[arg-type]
        max_mentions_per_message=50,
        max_utf16_per_message=3900,
    )
    assert len(chunks) == 2
    assert chunks[0].text.count("@") == 50
    assert chunks[1].text.count("@") == 5


def test_member_to_part_long_name() -> None:
    user = _FakeUser(id=7, first_name="A" * 100, username=None)
    part = member_to_part(user)  # type: ignore[arg-type]
    assert part.user is user
    assert "(7)" in part.text
