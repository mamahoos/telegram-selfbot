"""Tag service chat guard tests."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from hydrogram import enums

from app.application.services.tag_service import ensure_tag_allowed_chat
from app.common.exceptions import CommandError


@dataclass
class _FakeChat:
    type: enums.ChatType


def test_rejects_private_chat() -> None:
    message = MagicMock()
    message.chat = _FakeChat(type=enums.ChatType.PRIVATE)
    with pytest.raises(CommandError, match="private"):
        ensure_tag_allowed_chat(message)


def test_rejects_channel() -> None:
    message = MagicMock()
    message.chat = _FakeChat(type=enums.ChatType.CHANNEL)
    with pytest.raises(CommandError, match="channel"):
        ensure_tag_allowed_chat(message)


def test_allows_supergroup() -> None:
    message = MagicMock()
    message.chat = _FakeChat(type=enums.ChatType.SUPERGROUP)
    ensure_tag_allowed_chat(message)
