"""Fetch group chat members via Hydrogram."""

from __future__ import annotations

from hydrogram import Client, enums
from hydrogram.types import ChatMember, User

from app.common.exceptions import CommandError


class ChatMembersGateway:
    """Loads deduplicated human members for mention commands."""

    async def list_mentionable_members(
        self,
        client: Client,
        chat_id: int,
        *,
        exclude_user_id: int | None,
    ) -> list[User]:
        chat = await client.get_chat(chat_id)
        if chat.type not in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
            raise CommandError("`.tag` works in groups and supergroups only.")

        members_filter = (
            enums.ChatMembersFilter.SEARCH
            if chat.type == enums.ChatType.SUPERGROUP
            else enums.ChatMembersFilter.RECENT
        )
        query = ""

        seen: set[int] = set()
        users: list[User] = []

        members_iter = client.get_chat_members(
            chat_id,
            query=query,
            filter=members_filter,
        )
        if members_iter is None:
            raise CommandError("Could not list members in this chat.")

        async for member in members_iter:
            user = _member_user(member)
            if user is None:
                continue
            if user.is_bot or user.is_deleted:
                continue
            if exclude_user_id is not None and user.id == exclude_user_id:
                continue
            if user.id in seen:
                continue
            seen.add(user.id)
            users.append(user)

        if not users:
            raise CommandError("No members found to tag in this chat.")

        users.sort(key=lambda u: display_name_key(u))
        return users


def _member_user(member: ChatMember) -> User | None:
    return member.user


def display_name_key(user: User) -> str:
    parts = [user.first_name or "", user.last_name or ""]
    return " ".join(p for p in parts if p).strip().casefold() or str(user.id)
