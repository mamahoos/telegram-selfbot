"""Routes incoming messages to commands and background listeners."""

from __future__ import annotations

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

    def add_message_listener(self, listener: Listener) -> None:
        self._message_listeners.append(listener)

    def register(self, client: Client) -> None:
        @client.on_message(filters.all)
        async def on_message(_client: Client, message: Message) -> None:
            await self._dispatch(_client, message)

    async def _dispatch(self, client: Client, message: Message) -> None:
        if self._owner_filter._owner_id is None:
            me = await client.get_me()
            if me is not None:
                await self._owner_filter.bind_owner(me.id)

        for listener in self._message_listeners:
            try:
                await listener(client, message)
            except Exception as exc:
                await log_and_handle(client, message, exc)

        try:
            await self._reaction_service.react_if_enabled(client, message)
        except Exception:
            logger.exception(
                "Auto-reaction failed",
                extra={"chat_id": message.chat.id},
            )

        text = message.text or message.caption or ""
        if not self._owner_filter.is_owner_command(message):
            return
        if not await self._owner_filter.is_owner(message):
            return

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
