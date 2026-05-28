"""Raw MTProto sticker set operations."""

from __future__ import annotations

from pathlib import Path

from hydrogram import Client, raw
from hydrogram.errors import RPCError

from app.common.exceptions import CommandError
from app.core.logging import get_logger

logger = get_logger(__name__)


class StickerSetGateway:
    """Creates and updates user sticker sets via raw API."""

    async def _upload_sticker_document(self, client: Client, path: Path) -> raw.base.InputDocument:
        uploaded = await client.save_file(str(path))
        media = raw.types.InputMediaUploadedDocument(
            mime_type="image/webp",
            file=uploaded,
            attributes=[
                raw.types.DocumentAttributeSticker(alt="", stickerset=raw.types.InputStickerSetEmpty()),
            ],
        )
        peer = await client.resolve_peer("me")
        if not isinstance(
            peer,
            (
                raw.types.InputPeerSelf,
                raw.types.InputPeerUser,
                raw.types.InputPeerChat,
                raw.types.InputPeerChannel,
            ),
        ):
            raise CommandError("Unsupported peer type for sticker upload.")
        result = await client.invoke(
            raw.functions.messages.UploadMedia(
                peer=peer,
                media=media,
            ),
        )
        document = getattr(result, "document", None)
        if document is None:
            raise CommandError("Telegram did not return an uploaded sticker document.")
        return raw.types.InputDocument(
            id=document.id,
            access_hash=document.access_hash,
            file_reference=document.file_reference,
        )

    async def create_set(
        self,
        client: Client,
        *,
        title: str,
        short_name: str,
        sticker_path: Path,
        emoji: str,
    ) -> str:
        me = await client.get_me()
        if me is None or me.username is None:
            raise CommandError("Unable to resolve username for sticker pack suffix.")
        pack_name = f"{short_name}_by_{me.username}"
        document = await self._upload_sticker_document(client, sticker_path)
        sticker_item = raw.types.InputStickerSetItem(document=document, emoji=emoji)
        try:
            await client.invoke(
                raw.functions.stickers.CreateStickerSet(
                    user_id=raw.types.InputUserSelf(),
                    title=title,
                    short_name=pack_name,
                    stickers=[sticker_item],
                ),
            )
        except RPCError as exc:
            logger.exception("CreateStickerSet failed")
            raise CommandError(
                "Could not create sticker set. Telegram may require @Stickers for this account.",
                cause=exc,
            ) from exc
        return pack_name

    async def add_sticker(
        self,
        client: Client,
        *,
        pack_short_name: str,
        sticker_path: Path,
        emoji: str,
    ) -> str:
        me = await client.get_me()
        if me is None or me.username is None:
            raise CommandError("Unable to resolve username for sticker pack suffix.")
        pack_name = f"{pack_short_name}_by_{me.username}"
        document = await self._upload_sticker_document(client, sticker_path)
        sticker_item = raw.types.InputStickerSetItem(document=document, emoji=emoji)
        stickerset = raw.types.InputStickerSetShortName(short_name=pack_name)
        try:
            await client.invoke(
                raw.functions.stickers.AddStickerToSet(
                    stickerset=stickerset,
                    sticker=sticker_item,
                ),
            )
        except RPCError as exc:
            logger.exception("AddStickerToSet failed")
            raise CommandError(
                f"Could not add sticker to `{pack_name}`. Verify the pack exists.",
                cause=exc,
            ) from exc
        return pack_name
