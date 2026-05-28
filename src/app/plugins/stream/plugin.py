"""Stream command — progressive message edits."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.text_stream_service import TextStreamService
from app.common.exceptions import CommandError
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "stream"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._service = TextStreamService(container.message_edit_gateway)

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="stream",
                description="Type text progressively via message edits",
                plugin=self.name,
                aliases=("type",),
            ),
            self._handle_stream,
        )

    async def _handle_stream(self, _client: Client, message: Message) -> None:
        raw = message.text or message.caption or ""
        parts = raw.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            raise CommandError("Usage: `.stream <text>`")
        await self._service.stream_into_message(message, parts[1])
