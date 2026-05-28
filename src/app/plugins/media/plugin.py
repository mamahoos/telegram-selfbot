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
            sticker_processor=container.sticker_processor,
            tgs_to_gif=container.tgs_to_gif,
            gif_max_width=container.settings.gif_max_width,
            gif_fps=container.settings.gif_fps,
            video_note_size=container.settings.video_note_size,
            video_note_fps=container.settings.video_note_fps,
            voice_bitrate_kbps=container.settings.voice_bitrate_kbps,
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
                description="Convert replied video or animated sticker to GIF",
                plugin=self.name,
            ),
            self._handle_gif,
        )
        registry.register(
            CommandDefinition(
                name="vmsg",
                description="Send replied GIF as a round video message",
                plugin=self.name,
                aliases=("gif2vm",),
            ),
            self._handle_vmsg,
        )
        registry.register(
            CommandDefinition(
                name="tovoice",
                description="Send replied audio as a voice message (OGG)",
                plugin=self.name,
                aliases=("voice", "vce"),
            ),
            self._handle_tovoice,
        )

    async def _handle_photo(self, client: Client, message: Message) -> None:
        await self._service.send_sticker_as_photo(client, message)

    async def _handle_gif(self, client: Client, message: Message) -> None:
        await self._service.send_reply_as_gif(client, message)

    async def _handle_vmsg(self, client: Client, message: Message) -> None:
        await self._service.send_gif_as_video_note(client, message)

    async def _handle_tovoice(self, client: Client, message: Message) -> None:
        await self._service.send_audio_as_voice(client, message)
