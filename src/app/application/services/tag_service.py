"""Tag all group members across chained messages."""

from __future__ import annotations

from hydrogram import Client
from hydrogram.types import Message

from app.application.dto.mention_chunk import MentionChunk
from app.application.services.mention_chunker import chunk_member_mentions
from app.common.exceptions import CommandError
from app.infrastructure.hydrogram.chat_members_gateway import ChatMembersGateway


class TagService:
    """Fetches members and sends mention chunks as a reply chain."""

    def __init__(
        self,
        members: ChatMembersGateway,
        *,
        max_mentions_per_message: int,
        max_utf16_per_message: int,
    ) -> None:
        self._members = members
        self._max_mentions = max_mentions_per_message
        self._max_utf16 = max_utf16_per_message

    async def tag_all_members(self, client: Client, message: Message) -> None:
        me = await client.get_me()
        exclude_id = me.id if me is not None else None

        users = await self._members.list_mentionable_members(
            client,
            message.chat.id,
            exclude_user_id=exclude_id,
        )
        chunks = chunk_member_mentions(
            users,
            max_mentions_per_message=self._max_mentions,
            max_utf16_per_message=self._max_utf16,
        )
        if not chunks:
            raise CommandError("Nothing to send.")

        await self._deliver_chain(client, message, chunks)

    @staticmethod
    async def _deliver_chain(
        client: Client,
        command_message: Message,
        chunks: list[MentionChunk],
    ) -> None:
        first, *rest = chunks
        await command_message.edit(first.text, entities=first.entities)

        reply_to_id = command_message.id
        for chunk in rest:
            sent = await client.send_message(
                command_message.chat.id,
                chunk.text,
                entities=chunk.entities,
                reply_to_message_id=reply_to_id,
            )
            reply_to_id = sent.id
