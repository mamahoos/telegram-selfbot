"""JSON dump delivery tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.services.json_dump_service import JsonDumpService
from app.infrastructure.hydrogram.chat_dump_gateway import ChatDumpGateway


@dataclass
class _FakeUser:
    id: int = 42
    first_name: str = "Ada"


@dataclass
class _FakeMessage:
    id: int = 7
    text: str = "hello"
    from_user: _FakeUser | None = None
    reply_to_message: object | None = None

    def __post_init__(self) -> None:
        if self.from_user is None:
            self.from_user = _FakeUser()


class _FakeChat:
    id = -100123


class _FakeTempFiles:
    @asynccontextmanager
    async def file(self, suffix: str) -> AsyncIterator[Path]:
        path = Path("/tmp/fake-dump.json")
        yield path


@pytest.mark.asyncio
async def test_inline_json_edit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = AsyncMock(spec=ChatDumpGateway)
    gateway.dump.return_value = {"chat": {"id": 1}}
    service = JsonDumpService(
        temp_files=_FakeTempFiles(),  # type: ignore[arg-type]
        chat_dump=gateway,
        inline_max_chars=500,
    )
    message = MagicMock()
    message.edit = AsyncMock()
    message.delete = AsyncMock()
    message.reply_to_message_id = None
    message.reply_to_message = None
    message.chat = _FakeChat()
    client = AsyncMock()

    await service.handle(client, message)

    gateway.dump.assert_awaited_once_with(client, _FakeChat.id)
    message.edit.assert_awaited_once()
    body = message.edit.await_args.args[0]
    assert body.startswith("```json\n")
    assert '"chat"' in body
    message.delete.assert_not_called()


@pytest.mark.asyncio
async def test_large_dump_sent_as_document(monkeypatch: pytest.MonkeyPatch) -> None:
    written: list[tuple[Path, str]] = []

    async def _fake_write(path: Path, content: str) -> None:
        written.append((path, content))

    monkeypatch.setattr(JsonDumpService, "_write_text", staticmethod(_fake_write))

    gateway = AsyncMock(spec=ChatDumpGateway)
    gateway.dump.return_value = {"chat": {"blob": "x" * 5000}}
    service = JsonDumpService(
        temp_files=_FakeTempFiles(),  # type: ignore[arg-type]
        chat_dump=gateway,
        inline_max_chars=100,
    )
    message = MagicMock()
    message.edit = AsyncMock()
    message.delete = AsyncMock()
    message.reply_to_message_id = None
    message.reply_to_message = None
    message.chat = _FakeChat()
    client = AsyncMock()

    await service.handle(client, message)

    message.delete.assert_awaited_once()
    client.send_document.assert_awaited_once()
    assert written and len(written[0][1]) > 100


@pytest.mark.asyncio
async def test_reply_dumps_message_with_from_user() -> None:
    gateway = AsyncMock(spec=ChatDumpGateway)
    service = JsonDumpService(
        temp_files=_FakeTempFiles(),  # type: ignore[arg-type]
        chat_dump=gateway,
        inline_max_chars=2000,
    )
    reply = _FakeMessage()
    message = MagicMock()
    message.edit = AsyncMock()
    message.delete = AsyncMock()
    message.reply_to_message_id = 99
    message.reply_to_message = reply
    message.chat = _FakeChat()
    client = AsyncMock()

    await service.handle(client, message)

    gateway.dump.assert_not_called()
    body = message.edit.await_args.args[0]
    assert '"from_user"' in body
    assert '"first_name": "Ada"' in body or '"first_name":"Ada"' in body.replace(" ", "")
