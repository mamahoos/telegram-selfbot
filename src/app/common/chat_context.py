"""Chat-type helpers."""

from __future__ import annotations

from hydrogram import enums
from hydrogram.types import Chat, Message


def is_saved_messages_chat(chat: Chat, owner_id: int) -> bool:
    """True for Telegram Saved Messages (private chat with yourself)."""
    return chat.type == enums.ChatType.PRIVATE and chat.id == owner_id


def is_owner_command_message(message: Message, owner_id: int | None) -> bool:
    """Outgoing dot-command or a command typed in Saved Messages."""
    text = message.text or message.caption or ""
    if not text.strip().startswith("."):
        return False
    if message.outgoing:
        return True
    if owner_id is None:
        return False
    from_user = message.from_user
    if from_user is None or from_user.id != owner_id:
        return False
    return is_saved_messages_chat(message.chat, owner_id)
