"""Tag all group members."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.tag_service import TagService
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.infrastructure.hydrogram.chat_members_gateway import ChatMembersGateway
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "tag"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._service = TagService(
            ChatMembersGateway(),
            max_mentions_per_message=container.settings.tag_max_mentions_per_message,
            max_utf16_per_message=container.settings.tag_max_utf16_per_message,
        )

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="tag",
                description="Mention all group members (split across messages if needed)",
                plugin=self.name,
            ),
            self._handle_tag,
        )

    async def _handle_tag(self, client: Client, message: Message) -> None:
        await self._service.tag_all_members(client, message)
