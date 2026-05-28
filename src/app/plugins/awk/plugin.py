"""Run system awk on replied message text."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.awk_service import AwkService
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "awk"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._service = AwkService(
            container.awk_runner,
            max_output_chars=container.settings.awk_max_output_chars,
        )

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="awk",
                description="Run awk on replied text (.awk {program})",
                plugin=self.name,
            ),
            self._handle_awk,
        )
        registry.register(
            CommandDefinition(
                name="awkx",
                description="Run awk with full CLI flags on replied text",
                plugin=self.name,
            ),
            self._handle_awkx,
        )

    async def _handle_awk(self, _client: Client, message: Message) -> None:
        output = await self._service.run_simple_on_reply(message)
        await message.edit(output)

    async def _handle_awkx(self, _client: Client, message: Message) -> None:
        output = await self._service.run_advanced_on_reply(message)
        await message.edit(output)
