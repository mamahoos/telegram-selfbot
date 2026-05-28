"""Utility command formatters."""

from datetime import datetime

from hydrogram.types import Chat

from app.common.jalali_datetime import format_jalali_now


class UtilityService:
    """Pure formatting helpers for utility commands."""

    @staticmethod
    def format_chat_id(chat: Chat) -> str:
        return f"**Chat ID:** `{chat.id}`\n**Type:** `{chat.type.value}`"

    @staticmethod
    def format_date(*, at: datetime | None = None) -> str:
        return format_jalali_now(at=at)
