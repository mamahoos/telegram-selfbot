"""System commands — help and health."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "system"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._registry = container.command_registry

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="help",
                description="List available commands",
                plugin=self.name,
            ),
            self._handle_help,
        )

    async def _handle_help(self, _client: Client, message: Message) -> None:
        lines = ["**Available commands**", ""]
        for definition in self._registry.all_definitions:
            triggers = ", ".join(f"`{t}`" for t in definition.triggers)
            lines.append(f"- {triggers} — {definition.description}")
        await message.edit("\n".join(lines))
