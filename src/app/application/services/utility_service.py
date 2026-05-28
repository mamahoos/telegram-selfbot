"""Utility command formatters."""

from datetime import datetime

from hydrogram.types import Chat, Message, User

from app.common.jalali_datetime import format_jalali_now


class UtilityService:
    """Pure formatting helpers for utility commands."""

    @staticmethod
    def format_chat_id(chat: Chat) -> str:
        return f"**Chat ID:** `{chat.id}`\n**Type:** `{chat.type.value}`"

    @staticmethod
    def format_date(*, at: datetime | None = None) -> str:
        return format_jalali_now(at=at)

    @staticmethod
    def format_message_info(reply: Message) -> str:
        user: User | None = reply.from_user
        if user is None:
            return "No user information available for this message."

        username = f"@{user.username}" if user.username else "—"
        text_preview = (reply.text or reply.caption or "—")[:200]
        lines = [
            "**Message Info**",
            "├ **From**",
            f"│   ├ id: `{user.id}`",
            f"│   ├ first_name: {user.first_name or '—'}",
            f"│   ├ date: `{reply.date}`",
            f"│   ├ message_id: `{reply.id}`",
            f"│   └ username: {username}",
            f"└ text: `{text_preview}`",
        ]
        return "\n".join(lines)
