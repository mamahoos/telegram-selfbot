"""Telegram reaction API adapter with flood-wait handling."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Sequence
from typing import cast

from hydrogram import Client, raw
from hydrogram.errors import FloodWait, RPCError

from app.common.exceptions import ReactionError
from app.core.logging import get_logger
from app.infrastructure.hydrogram.reaction_emoji_source import (
    emojis_from_available_reactions,
    emojis_from_chat_reactions,
)

logger = get_logger(__name__)

# Widely accepted default reactions when API discovery fails.
_SAFE_FALLBACK_EMOJIS: tuple[str, ...] = ("👍", "❤️", "😂", "😮", "😢", "🙏")


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
        self._fallback_emojis = list(fallback_emojis) or list(_SAFE_FALLBACK_EMOJIS)
        self._emoji_cache: dict[int, tuple[list[str], float]] = {}
        self._global_emojis: list[str] | None = None
        self._global_expires_at = 0.0
        self._cache_ttl_seconds = 300.0
        self._last_reaction_at: dict[int, float] = {}

    async def get_available_emojis(self, client: Client, chat_id: int) -> list[str]:
        now = time.monotonic()
        cached = self._emoji_cache.get(chat_id)
        if cached is not None:
            emojis, expires = cached
            if now < expires:
                return emojis

        emojis = await self._fetch_chat_reactions(client, chat_id)
        if not emojis:
            emojis = await self._fetch_global_reactions(client)
        if not emojis:
            emojis = list(self._fallback_emojis)
        self._emoji_cache[chat_id] = (emojis, now + self._cache_ttl_seconds)
        return emojis

    async def _fetch_global_reactions(self, client: Client) -> list[str]:
        now = time.monotonic()
        if self._global_emojis is not None and now < self._global_expires_at:
            return list(self._global_emojis)

        try:
            payload = await client.invoke(raw.functions.messages.GetAvailableReactions(hash=0))
            emojis = emojis_from_available_reactions(payload)
        except Exception as exc:
            logger.warning("Could not fetch global reactions", exc_info=exc)
            emojis = []

        if emojis:
            self._global_emojis = emojis
            self._global_expires_at = now + self._cache_ttl_seconds
        return emojis

    async def _fetch_chat_reactions(self, client: Client, chat_id: int) -> list[str]:
        try:
            peer = await client.resolve_peer(chat_id)
            available = await self._load_peer_available_reactions(client, peer)
            parsed = emojis_from_chat_reactions(available)
            if parsed is None:
                return await self._fetch_global_reactions(client)
            return parsed
        except Exception as exc:
            logger.warning(
                "Could not fetch chat reactions, using global/fallback",
                extra={"chat_id": chat_id},
                exc_info=exc,
            )
            return []

    @staticmethod
    async def _load_peer_available_reactions(
        client: Client,
        peer: object,
    ) -> object | None:
        if isinstance(peer, raw.types.InputPeerChannel):
            channel = raw.types.InputChannel(
                channel_id=peer.channel_id,
                access_hash=peer.access_hash,
            )
            full = await client.invoke(raw.functions.channels.GetFullChannel(channel=channel))
            return cast(object | None, full.full_chat.available_reactions)
        if isinstance(peer, raw.types.InputPeerChat):
            full = await client.invoke(raw.functions.messages.GetFullChat(chat_id=peer.chat_id))
            return cast(object | None, full.full_chat.available_reactions)
        return None

    async def send_random_reaction(
        self,
        client: Client,
        *,
        chat_id: int,
        message_id: int,
        big: bool = True,
    ) -> None:
        now = time.monotonic()
        last = self._last_reaction_at.get(chat_id, 0.0)
        wait = self._cooldown_seconds - (now - last)
        if wait > 0:
            await asyncio.sleep(wait)

        candidates = list(await self.get_available_emojis(client, chat_id))
        if not candidates:
            candidates = list(_SAFE_FALLBACK_EMOJIS)
        random.shuffle(candidates)

        last_exc: Exception | None = None
        for emoji in candidates:
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
                except RPCError as exc:
                    last_exc = exc
                    if _is_invalid_reaction(exc):
                        break
                    if attempt >= self._max_retries:
                        break
                    await asyncio.sleep(0.5 * attempt)
                except Exception as exc:
                    last_exc = exc
                    if attempt >= self._max_retries:
                        break
                    await asyncio.sleep(0.5 * attempt)

        raise ReactionError(
            "Failed to send reaction: no allowed emoji worked",
            cause=last_exc,
        )


def _is_invalid_reaction(exc: RPCError) -> bool:
    name = type(exc).__name__
    return name in {"ReactionInvalid", "ReactionEmpty"}
