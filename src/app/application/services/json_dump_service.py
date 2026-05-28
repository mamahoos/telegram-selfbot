"""Build and deliver JSON dumps for chats and messages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from hydrogram import Client
from hydrogram.types import Message

from app.common.exceptions import CommandError
from app.infrastructure.hydrogram.chat_dump_gateway import ChatDumpGateway
from app.infrastructure.serialization.hydrogram_json import hydrogram_to_jsonable
from app.infrastructure.storage.temp_file_manager import TempFileManager

_CODE_FENCE = "json"
_TELEGRAM_MESSAGE_LIMIT = 4096


class JsonDumpService:
    """Formats API dumps as inline JSON or document files."""

    def __init__(
        self,
        *,
        temp_files: TempFileManager,
        chat_dump: ChatDumpGateway,
        inline_max_chars: int,
    ) -> None:
        self._temp_files = temp_files
        self._chat_dump = chat_dump
        self._inline_max_chars = min(inline_max_chars, _TELEGRAM_MESSAGE_LIMIT)

    async def handle(self, client: Client, message: Message) -> None:
        if message.reply_to_message_id is not None:
            reply = cast(Message | None, message.reply_to_message)
            if reply is None:
                raise CommandError("Replied message is not loaded; try again.")
            payload = self._dump_message(reply)
        else:
            payload = await self._chat_dump.dump(client, message.chat.id)

        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        inline_limit = self._inline_max_chars - len("```json\n\n```")

        if len(rendered) <= inline_limit:
            await message.edit(f"```{_CODE_FENCE}\n{rendered}\n```")
            return

        async with self._temp_files.file(".json") as path:
            await self._write_text(path, rendered)
            await message.delete()
            await client.send_document(
                message.chat.id,
                document=str(path),
                caption=f"JSON dump ({len(rendered)} chars)",
            )

    @staticmethod
    def _dump_message(reply: Message) -> dict[str, Any]:
        data: Any = hydrogram_to_jsonable(reply)
        if not isinstance(data, dict):
            return {"message": data}
        if reply.from_user is not None and "from_user" not in data:
            data["from_user"] = hydrogram_to_jsonable(reply.from_user)
        return {"message": data}

    @staticmethod
    async def _write_text(path: Path, content: str) -> None:
        import asyncio

        await asyncio.to_thread(path.write_text, content, encoding="utf-8")
