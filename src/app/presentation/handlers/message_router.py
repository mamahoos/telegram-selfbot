"""Routes incoming messages to commands and background listeners."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from hydrogram import Client, filters
from hydrogram.types import Message

from app.application.services.reaction_service import ReactionService
from app.core.container import Container
from app.core.logging import get_logger
from app.presentation.middleware.error_handler import log_and_handle
from app.presentation.middleware.owner_filter import OwnerFilter

logger = get_logger(__name__)
Listener = Callable[[Client, Message], Awaitable[None]]


class MessageRouter:
    """Registers Hydrogram handlers for commands and reactions."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._registry = container.command_registry
        self._owner_filter = OwnerFilter()
        self._reaction_service = ReactionService(
            repository=container.reaction_repository,
            gateway=container.reaction_gateway,
        )
        self._message_listeners: list[Listener] = []
        self._owner_bind_lock = asyncio.Lock()

    def add_message_listener(self, listener: Listener) -> None:
        self._message_listeners.append(listener)

    def register(self, client: Client) -> None:
        @client.on_message(filters.outgoing)
        async def on_outgoing(_client: Client, message: Message) -> None:
            await self._ensure_owner_bound(_client)
            if not self._owner_filter.is_owner_command(message):
                return
            self._spawn_command(_client, message)

        @client.on_message(filters.incoming)
        async def on_incoming(_client: Client, message: Message) -> None:
            await self._ensure_owner_bound(_client)
            self._spawn_reaction(_client, message)
            if not self._owner_filter.is_owner_command(message):
                return
            if not await self._owner_filter.is_owner(message):
                return
            self._spawn_command(_client, message)

    async def _ensure_owner_bound(self, client: Client) -> None:
        if self._owner_filter._owner_id is not None:
            return
        async with self._owner_bind_lock:
            if self._owner_filter._owner_id is None:
                me = await client.get_me()
                if me is not None:
                    await self._owner_filter.bind_owner(me.id)

    def _spawn_reaction(self, client: Client, message: Message) -> None:
        task = asyncio.create_task(
            self._run_reaction(client, message),
            name=f"react:{message.chat.id}:{message.id}",
        )
        task.add_done_callback(self._log_background_failure)

    def _spawn_command(self, client: Client, message: Message) -> None:
        task = asyncio.create_task(
            self._dispatch_command(client, message),
            name=f"command:{message.chat.id}:{message.id}",
        )
        task.add_done_callback(self._log_background_failure)

    @staticmethod
    def _log_background_failure(task: asyncio.Task[None]) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.error(
                "Background handler task failed",
                extra={"task": task.get_name()},
                exc_info=exc,
            )

    async def _run_reaction(self, client: Client, message: Message) -> None:
        try:
            await self._reaction_service.react_if_enabled(client, message)
        except Exception:
            logger.exception(
                "Auto-reaction failed",
                extra={"chat_id": message.chat.id},
            )

    async def _dispatch_command(self, client: Client, message: Message) -> None:
        for listener in self._message_listeners:
            try:
                await listener(client, message)
            except Exception as exc:
                await log_and_handle(client, message, exc)

        text = message.text or message.caption or ""
        resolved = self._registry.resolve(text)
        if resolved is None:
            return

        registered, _args = resolved
        log_record = logging.LogRecord(
            name=logger.name,
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="Command invoked",
            args=(),
            exc_info=None,
        )
        log_record.command = registered.definition.name
        log_record.plugin = registered.definition.plugin
        log_record.chat_id = message.chat.id
        logger.handle(log_record)

        try:
            await registered.handler(client, message)
        except Exception as exc:
            await log_and_handle(client, message, exc)
