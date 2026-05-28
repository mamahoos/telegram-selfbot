"""Fetch full chat metadata from Telegram API."""

from __future__ import annotations

from typing import Any

from hydrogram import Client, raw

from app.infrastructure.serialization.hydrogram_json import hydrogram_to_jsonable


class ChatDumpGateway:
    """Loads chat objects and related full-chat API responses."""

    async def dump(self, client: Client, chat_id: int | str) -> dict[str, Any]:
        chat = await client.get_chat(chat_id)
        payload: dict[str, Any] = {"chat": hydrogram_to_jsonable(chat)}

        peer = await client.resolve_peer(chat_id)
        if isinstance(peer, raw.types.InputPeerChannel):
            channel = raw.types.InputChannel(
                channel_id=peer.channel_id,
                access_hash=peer.access_hash,
            )
            full = await client.invoke(raw.functions.channels.GetFullChannel(channel=channel))
            payload["full_channel"] = hydrogram_to_jsonable(full)
        elif isinstance(peer, raw.types.InputPeerChat):
            full = await client.invoke(raw.functions.messages.GetFullChat(chat_id=peer.chat_id))
            payload["full_chat"] = hydrogram_to_jsonable(full)
        elif isinstance(peer, raw.types.InputPeerUser):
            user = raw.types.InputUser(user_id=peer.user_id, access_hash=peer.access_hash)
            full = await client.invoke(raw.functions.users.GetFullUser(id=user))
            payload["full_user"] = hydrogram_to_jsonable(full)
        elif isinstance(peer, raw.types.InputPeerSelf):
            full = await client.invoke(
                raw.functions.users.GetFullUser(id=raw.types.InputUserSelf())
            )
            payload["full_user"] = hydrogram_to_jsonable(full)

        return payload
