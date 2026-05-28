"""Sticker conversion and pack commands."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.sticker_service import StickerService
from app.common.exceptions import CommandError
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "stickers"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._service = StickerService(
            temp_files=container.temp_files,
            processor=container.sticker_processor,
            sticker_sets=container.sticker_set_gateway,
        )

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="tosticker",
                description="Convert replied image to sticker",
                plugin=self.name,
            ),
            self._handle_tosticker,
        )
        registry.register(
            CommandDefinition(
                name="newpack",
                description="Create sticker pack from replied image",
                plugin=self.name,
            ),
            self._handle_newpack,
        )
        registry.register(
            CommandDefinition(
                name="addsticker",
                description="Add replied image to sticker pack",
                plugin=self.name,
            ),
            self._handle_addsticker,
        )

    async def _handle_tosticker(self, client: Client, message: Message) -> None:
        await self._service.send_tosticker(client, message)
        await message.delete()

    async def _handle_newpack(self, client: Client, message: Message) -> None:
        parts = (message.text or "").split()
        if len(parts) < 2:
            raise CommandError("Usage: `.newpack <title> [short_name] [emoji]`")
        title = parts[1]
        short_name = parts[2] if len(parts) > 2 else title.lower().replace(" ", "_")[:32]
        emoji = parts[3] if len(parts) > 3 else "😎"
        pack = await self._service.create_pack_from_reply(
            client,
            message,
            title=title,
            short_name=short_name,
            emoji=emoji,
        )
        await message.edit(f"Sticker pack created: `{pack}`")

    async def _handle_addsticker(self, client: Client, message: Message) -> None:
        parts = (message.text or "").split()
        if len(parts) < 3:
            raise CommandError("Usage: `.addsticker <pack_short_name> <emoji>`")
        pack_short = parts[1]
        emoji = parts[2]
        pack = await self._service.add_sticker_from_reply(
            client,
            message,
            pack_short_name=pack_short,
            emoji=emoji,
        )
        await message.edit(f"Sticker added to `{pack}`")
