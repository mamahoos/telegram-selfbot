"""Utility plugin — id, date, json."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.json_dump_service import JsonDumpService
from app.application.services.utility_service import UtilityService
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.infrastructure.hydrogram.chat_dump_gateway import ChatDumpGateway
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "utility"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._service = UtilityService()
        self._json = JsonDumpService(
            temp_files=container.temp_files,
            chat_dump=ChatDumpGateway(),
            inline_max_chars=container.settings.json_inline_max_chars,
        )

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
                name="json",
                description="Dump chat or replied message as JSON",
                plugin=self.name,
            ),
            self._handle_json,
        )

    async def _handle_id(self, _client: Client, message: Message) -> None:
        text = self._service.format_chat_id(message.chat)
        await message.edit(text)

    async def _handle_date(self, _client: Client, message: Message) -> None:
        text = self._service.format_date()
        await message.edit(text)

    async def _handle_json(self, client: Client, message: Message) -> None:
        await self._json.handle(client, message)
