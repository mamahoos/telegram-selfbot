"""Graceful command error handling."""

from hydrogram import Client
from hydrogram.types import Message

from app.common.exceptions import AppError, CommandError
from app.core.logging import get_logger

logger = get_logger(__name__)


async def reply_error(message: Message, exc: Exception) -> None:
    if isinstance(exc, CommandError | AppError):
        text = f"**Error:** {exc}"
    else:
        text = "**Error:** An unexpected error occurred."
    try:
        if message.outgoing:
            await message.edit(text)
        else:
            await message.reply(text)
    except Exception:
        logger.exception("Failed to deliver error message to chat")


async def log_and_handle(client: Client, message: Message, exc: Exception) -> None:
    logger.exception(
        "Handler failure",
        extra={
            "chat_id": message.chat.id,
            "user_id": message.from_user.id if message.from_user else None,
        },
    )
    await reply_error(message, exc)
