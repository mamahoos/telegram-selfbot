"""Telegram reaction API adapter with flood-wait handling."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Sequence

from hydrogram import Client
from hydrogram.errors import FloodWait

from app.common.exceptions import ReactionError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReactionGateway:
    """Fetches allowed reactions and sends them safely."""

    def __init__(
        self,
        *,
        cooldown_seconds: float,
        max_retries: int,
        fallback_emojis: Sequence[str],
    ) -> None:
        self._cooldown_seconds = cooldown_seconds
        self._max_retries = max_retries
        self._fallback_emojis = list(fallback_emojis)
        self._emoji_cache: dict[int, tuple[list[str], float]] = {}
        self._cache_ttl_seconds = 300.0
        self._last_reaction_at: dict[int, float] = {}

    async def get_available_emojis(self, client: Client, chat_id: int) -> list[str]:
        import time

        now = time.monotonic()
        cached = self._emoji_cache.get(chat_id)
        if cached is not None:
            emojis, expires = cached
            if now < expires:
                return emojis

        emojis = await self._fetch_chat_reactions(client, chat_id)
        if not emojis:
            emojis = list(self._fallback_emojis)
        self._emoji_cache[chat_id] = (emojis, now + self._cache_ttl_seconds)
        return emojis

    async def _fetch_chat_reactions(self, client: Client, chat_id: int) -> list[str]:
        try:
            full = await client.get_chat(chat_id)
            reactions = getattr(full, "available_reactions", None)
            if reactions is None:
                return []
            if isinstance(reactions, str):
                return list(self._fallback_emojis)
            items = getattr(reactions, "reactions", None) or []
            result: list[str] = []
            for item in items:
                emoji = getattr(item, "emoji", None)
                if isinstance(emoji, str) and emoji:
                    result.append(emoji)
            return result
        except Exception as exc:
            logger.warning(
                "Could not fetch chat reactions, using fallback",
                extra={"chat_id": chat_id},
                exc_info=exc,
            )
            return list(self._fallback_emojis)

    async def send_random_reaction(
        self,
        client: Client,
        *,
        chat_id: int,
        message_id: int,
        big: bool = True,
    ) -> None:
        import time

        now = time.monotonic()
        last = self._last_reaction_at.get(chat_id, 0.0)
        wait = self._cooldown_seconds - (now - last)
        if wait > 0:
            await asyncio.sleep(wait)

        emojis = await self.get_available_emojis(client, chat_id)
        emoji = random.choice(emojis)

        for attempt in range(1, self._max_retries + 1):
            try:
                await client.send_reaction(chat_id, message_id, emoji, big=big)
                self._last_reaction_at[chat_id] = time.monotonic()
                return
            except FloodWait as exc:
                logger.warning(
                    "FloodWait on reaction",
                    extra={"chat_id": chat_id, "seconds": exc.value},
                )
                await asyncio.sleep(exc.value + 1)
            except Exception as exc:
                if attempt >= self._max_retries:
                    raise ReactionError(
                        f"Failed to send reaction after {attempt} attempts",
                        cause=exc,
                    ) from exc
                await asyncio.sleep(0.5 * attempt)

        raise ReactionError("Reaction delivery exhausted retries")
