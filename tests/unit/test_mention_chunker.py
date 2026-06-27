"""Mention chunker tests."""

from __future__ import annotations

from dataclasses import dataclass

from hydrogram import enums

from app.application.services.mention_chunker import (
    chunk_member_mentions,
    display_name,
    member_to_part,
)


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


def test_username_as_mention_link() -> None:
    user = _FakeUser(id=1, username="ada")
    chunks = chunk_member_mentions([user], max_mentions_per_message=50, max_utf16_per_message=3900)  # type: ignore[list-item]
    assert chunks[0].text == "@ada"
    assert chunks[0].entities[0].type == enums.MessageEntityType.MENTION


def test_name_as_text_mention_without_username() -> None:
    user = _FakeUser(id=42, first_name="Sara", username=None)
    chunks = chunk_member_mentions([user], max_mentions_per_message=50, max_utf16_per_message=3900)  # type: ignore[list-item]
    assert chunks[0].text == "Sara"
    assert "(" not in chunks[0].text
    assert chunks[0].entities[0].type == enums.MessageEntityType.TEXT_MENTION


def test_mixed_format_uses_middle_dot_separator() -> None:
    users = [
        _FakeUser(id=1, username="teacher"),
        _FakeUser(id=2, first_name="Oshida", username=None),
    ]
    chunks = chunk_member_mentions(users, max_mentions_per_message=50, max_utf16_per_message=3900)  # type: ignore[arg-type]
    assert chunks[0].text == "@teacher · Oshida"


def test_splits_when_mention_limit_exceeded() -> None:
    users = [_FakeUser(id=i, username=f"u{i}") for i in range(55)]  # type: ignore[misc]
    chunks = chunk_member_mentions(
        users,  # type: ignore[arg-type]
        max_mentions_per_message=50,
        max_utf16_per_message=3900,
    )
    assert len(chunks) == 2
    assert chunks[0].text.count("@") == 50


def test_member_to_part_no_id_suffix() -> None:
    user = _FakeUser(id=7, first_name="Oshida", username="Oshidapoodineh")
    part = member_to_part(user)  # type: ignore[arg-type]
    assert part.text == "@Oshidapoodineh"
    assert part.username_mention is True
