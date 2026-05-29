"""Owner filter tests."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

from hydrogram import enums

from app.common.chat_context import is_owner_command_message, is_saved_messages_chat
from app.presentation.middleware.owner_filter import OwnerFilter


@dataclass
class _FakeChat:
    id: int
    type: enums.ChatType


@dataclass
class _FakeUser:
    id: int


def test_saved_messages_chat_detected() -> None:
    chat = _FakeChat(id=12345, type=enums.ChatType.PRIVATE)
    assert is_saved_messages_chat(chat, 12345) is True  # type: ignore[arg-type]
    assert is_saved_messages_chat(_FakeChat(id=99, type=enums.ChatType.PRIVATE), 12345) is False  # type: ignore[arg-type]


def test_incoming_saved_messages_command() -> None:
    message = MagicMock()
    message.outgoing = False
    message.text = ".id"
    message.caption = None
    message.chat = _FakeChat(id=100, type=enums.ChatType.PRIVATE)
    message.from_user = _FakeUser(id=100)
    assert is_owner_command_message(message, 100) is True


def test_incoming_other_private_not_command() -> None:
    message = MagicMock()
    message.outgoing = False
    message.text = ".id"
    message.chat = _FakeChat(id=200, type=enums.ChatType.PRIVATE)
    message.from_user = _FakeUser(id=100)
    assert is_owner_command_message(message, 100) is False


def test_outgoing_command_still_works() -> None:
    message = MagicMock()
    message.outgoing = True
    message.text = ".date"
    message.caption = None
    message.chat = _FakeChat(id=200, type=enums.ChatType.SUPERGROUP)
    message.from_user = _FakeUser(id=100)
    assert is_owner_command_message(message, 100) is True


async def test_owner_filter_async_is_owner() -> None:
    filt = OwnerFilter()
    await filt.bind_owner(100)
    message = MagicMock()
    message.outgoing = False
    message.text = ".help"
    message.caption = None
    message.chat = _FakeChat(id=100, type=enums.ChatType.PRIVATE)
    message.from_user = _FakeUser(id=100)
    assert filt.is_owner_command(message) is True
    assert await filt.is_owner(message) is True
