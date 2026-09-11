"""Reaction toggle plugin."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "reactions"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._service = container.reaction_service

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="react",
                description="Toggle auto-reactions for this chat",
                plugin=self.name,
                aliases=("r",),
            ),
            self._handle_react,
        )

    async def _handle_react(self, _client: Client, message: Message) -> None:
        enabled = await self._service.toggle(message.chat.id)
        await message.edit(f"Auto-reactions: **{'on' if enabled else 'off'}**")
