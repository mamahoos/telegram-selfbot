"""Utility plugin — id, date, info."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.utility_service import UtilityService
from app.common.exceptions import CommandError
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "utility"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._service = UtilityService()

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(name="id", description="Show chat id", plugin=self.name),
            self._handle_id,
        )
        registry.register(
            CommandDefinition(
                name="date",
                description="Show Jalali date, weekday, month, and local time",
                plugin=self.name,
            ),
            self._handle_date,
        )
        registry.register(
            CommandDefinition(
                name="info",
                description="Show replied message metadata",
                plugin=self.name,
            ),
            self._handle_info,
        )

    async def _handle_id(self, _client: Client, message: Message) -> None:
        text = self._service.format_chat_id(message.chat)
        await message.edit(text)

    async def _handle_date(self, _client: Client, message: Message) -> None:
        text = self._service.format_date()
        await message.edit(text)

    async def _handle_info(self, _client: Client, message: Message) -> None:
        reply = message.reply_to_message
        if reply is None:
            raise CommandError("Reply to a message to inspect it.")
        text = self._service.format_message_info(reply)
        await message.edit(text)
