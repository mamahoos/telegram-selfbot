"""Flood-safe Telegram message edits."""

from __future__ import annotations

import asyncio
import time

from hydrogram.errors import FloodWait
from hydrogram.types import Message

from app.common.exceptions import CommandError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MessageEditGateway:
    """Edits messages with cooldown, retries, and FloodWait handling."""

    def __init__(
        self,
        *,
        delay_seconds: float,
        max_retries: int,
    ) -> None:
        self._delay_seconds = delay_seconds
        self._max_retries = max_retries
        self._last_edit_at: dict[int, float] = {}

    async def edit_text(self, message: Message, text: str) -> None:
        chat_id = message.chat.id
        await self._respect_cooldown(chat_id)

        for attempt in range(1, self._max_retries + 1):
            try:
                await message.edit_text(text)
                self._last_edit_at[chat_id] = time.monotonic()
                return
            except FloodWait as exc:
                logger.warning(
                    "FloodWait on message edit",
                    extra={"chat_id": chat_id, "seconds": exc.value},
                )
                await asyncio.sleep(exc.value + 1)
            except Exception as exc:
                if attempt >= self._max_retries:
                    raise CommandError(
                        f"Failed to edit message after {attempt} attempts",
                        cause=exc,
                    ) from exc
                await asyncio.sleep(0.5 * attempt)

        raise CommandError("Message edit exhausted retries")

    async def wait_between_steps(self, chat_id: int) -> None:
        await self._respect_cooldown(chat_id)

    async def _respect_cooldown(self, chat_id: int) -> None:
        last = self._last_edit_at.get(chat_id, 0.0)
        elapsed = time.monotonic() - last
        wait = self._delay_seconds - elapsed
        if wait > 0:
            await asyncio.sleep(wait)
