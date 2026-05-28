"""Sticker pack and conversion orchestration."""

from __future__ import annotations

from pathlib import Path

from hydrogram import Client
from hydrogram.types import Message

from app.common.exceptions import CommandError, MediaProcessingError
from app.common.media_paths import ensure_local_path
from app.infrastructure.hydrogram.sticker_set_gateway import StickerSetGateway
from app.infrastructure.media.sticker_processor import StickerProcessor
from app.infrastructure.storage.temp_file_manager import TempFileManager


class StickerService:
    """Sticker pack operations and image conversion."""

    def __init__(
        self,
        *,
        temp_files: TempFileManager,
        processor: StickerProcessor,
        sticker_sets: StickerSetGateway,
    ) -> None:
        self._temp_files = temp_files
        self._processor = processor
        self._sticker_sets = sticker_sets

    async def send_tosticker(
        self,
        client: Client,
        message: Message,
    ) -> None:
        reply = message.reply_to_message
        if reply is None or not (reply.photo or reply.document):
            raise CommandError("Reply to a photo or image document.")

        async with self._temp_files.file(".bin") as downloaded:
            async with self._temp_files.file(".webp") as sticker_path:
                path = await client.download_media(reply, file_name=str(downloaded))
                self._processor.to_sticker_webp(ensure_local_path(path), sticker_path)
                await client.send_sticker(
                    message.chat.id,
                    sticker=str(sticker_path),
                    reply_to_message_id=reply.id,
                )

    async def create_pack_from_reply(
        self,
        client: Client,
        message: Message,
        *,
        title: str,
        short_name: str,
        emoji: str,
    ) -> str:
        reply = message.reply_to_message
        if reply is None or not (reply.photo or reply.document):
            raise CommandError("Reply to a photo when creating a pack.")

        async with self._temp_files.file(".bin") as downloaded:
            async with self._temp_files.file(".webp") as sticker_path:
                path = await client.download_media(reply, file_name=str(downloaded))
                self._processor.to_sticker_webp(ensure_local_path(path), sticker_path)
                return await self._sticker_sets.create_set(
                    client,
                    title=title,
                    short_name=short_name,
                    sticker_path=sticker_path,
                    emoji=emoji,
                )

    async def add_sticker_from_reply(
        self,
        client: Client,
        message: Message,
        *,
        pack_short_name: str,
        emoji: str,
    ) -> str:
        reply = message.reply_to_message
        if reply is None or not (reply.photo or reply.document):
            raise CommandError("Reply to a photo when adding a sticker.")

        async with self._temp_files.file(".bin") as downloaded:
            async with self._temp_files.file(".webp") as sticker_path:
                path = await client.download_media(reply, file_name=str(downloaded))
                self._processor.to_sticker_webp(ensure_local_path(path), sticker_path)
                return await self._sticker_sets.add_sticker(
                    client,
                    pack_short_name=pack_short_name,
                    sticker_path=sticker_path,
                    emoji=emoji,
                )
