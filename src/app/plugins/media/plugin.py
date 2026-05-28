"""Sticker-to-photo and video-to-gif commands."""

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.media_service import MediaService
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.plugins.base import Plugin


class PluginImpl(Plugin):
    name = "media"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        self._service = MediaService(
            temp_files=container.temp_files,
            ffmpeg=container.ffmpeg,
            gif_max_width=container.settings.gif_max_width,
            gif_fps=container.settings.gif_fps,
        )

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="photo",
                description="Convert replied sticker to photo",
                plugin=self.name,
                aliases=("sticker",),
            ),
            self._handle_photo,
        )
        registry.register(
            CommandDefinition(
                name="gif",
                description="Convert replied video to optimized GIF",
                plugin=self.name,
            ),
            self._handle_gif,
        )

    async def _handle_photo(self, client: Client, message: Message) -> None:
        await self._service.send_sticker_as_photo(client, message)

    async def _handle_gif(self, client: Client, message: Message) -> None:
        await self._service.send_video_as_gif(client, message)
