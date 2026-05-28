"""Sticker-to-image and video/TGS-to-gif pipelines."""

from __future__ import annotations

from pathlib import Path

from hydrogram import Client
from hydrogram.types import Message

from app.application.dto.media import GifConversionResult
from app.common.exceptions import CommandError
from app.common.media_paths import ensure_local_path
from app.infrastructure.ffmpeg.runner import FfmpegRunner
from app.infrastructure.media.tgs_to_gif_converter import TgsToGifConverter
from app.infrastructure.storage.temp_file_manager import TempFileManager


def _has_convertible_video(message: Message) -> bool:
    """Whether the message contains video-like media (avoids stub narrowing)."""
    return any(
        getattr(message, field, None) is not None
        for field in ("video", "animation", "document")
    )


class MediaService:
    """Media download, conversion, and delivery."""

    def __init__(
        self,
        *,
        temp_files: TempFileManager,
        ffmpeg: FfmpegRunner,
        tgs_to_gif: TgsToGifConverter,
        gif_max_width: int,
        gif_fps: int,
    ) -> None:
        self._temp_files = temp_files
        self._ffmpeg = ffmpeg
        self._tgs_to_gif = tgs_to_gif
        self._gif_max_width = gif_max_width
        self._gif_fps = gif_fps

    async def send_sticker_as_photo(self, client: Client, message: Message) -> None:
        reply = message.reply_to_message
        if reply is None or reply.sticker is None:
            raise CommandError("Reply to a sticker message.")

        sticker = reply.sticker
        if sticker.is_animated and not sticker.is_video:
            raise CommandError("Animated TGS stickers are not supported for `.photo`.")

        suffix = ".webm" if sticker.is_video else ".webp"
        async with self._temp_files.file(suffix) as downloaded:
            path = await client.download_media(reply, file_name=str(downloaded))
            local_path = ensure_local_path(path)
            await message.delete()
            await client.send_photo(
                message.chat.id,
                photo=str(local_path),
                reply_to_message_id=reply.id,
            )

    async def send_reply_as_gif(self, client: Client, message: Message) -> None:
        """Convert replied video, video sticker, or TGS sticker to GIF."""
        reply = message.reply_to_message
        if reply is None:
            raise CommandError("Reply to a video or animated sticker.")

        if reply.sticker is not None:
            await self._send_sticker_as_gif(client, message, reply)
        elif _has_convertible_video(reply):  # type: ignore[unreachable]
            async with self._temp_files.file(".mp4") as video_path:
                async with self._temp_files.file(".gif") as gif_path:
                    await self._convert_video_file(client, message, video_path, gif_path)
                    await message.delete()
                    await client.send_animation(
                        message.chat.id,
                        animation=str(gif_path),
                        reply_to_message_id=reply.id,
                    )
        else:
            raise CommandError("Reply to a video, video sticker, or animated (TGS) sticker.")

    async def _send_sticker_as_gif(self, client: Client, message: Message, reply: Message) -> None:
        sticker = reply.sticker
        if sticker is None:
            raise CommandError("Reply to a sticker message.")
        if sticker.is_animated and not sticker.is_video:
            suffix = ".tgs"
        elif sticker.is_video:
            suffix = ".webm"
        else:
            raise CommandError("Reply to an animated or video sticker for `.gif`.")

        async with self._temp_files.file(suffix) as source_path:
            async with self._temp_files.file(".gif") as gif_path:
                downloaded = await client.download_media(reply, file_name=str(source_path))
                local_source = ensure_local_path(downloaded)
                if suffix == ".tgs":
                    await self._tgs_to_gif.convert(source=local_source, destination=gif_path)
                else:
                    await self._ffmpeg.video_to_gif(
                        input_path=local_source,
                        output_path=gif_path,
                        max_width=self._gif_max_width,
                        fps=self._gif_fps,
                    )
                await message.delete()
                await client.send_animation(
                    message.chat.id,
                    animation=str(gif_path),
                    reply_to_message_id=reply.id,
                )

    async def send_video_as_gif(self, client: Client, message: Message) -> None:
        """Backward-compatible alias for video-only conversion."""
        await self.send_reply_as_gif(client, message)

    async def video_reply_to_gif(
        self,
        client: Client,
        message: Message,
    ) -> GifConversionResult:
        reply = message.reply_to_message
        if reply is None or not (reply.video or reply.animation or reply.document):
            raise CommandError("Reply to a video, animation, or video document.")

        async with self._temp_files.file(".mp4") as video_path:
            async with self._temp_files.file(".gif") as gif_path:
                return await self._convert_video_file(client, message, video_path, gif_path)

    async def _convert_video_file(
        self,
        client: Client,
        message: Message,
        video_path: Path,
        gif_path: Path,
    ) -> GifConversionResult:
        reply = message.reply_to_message
        if reply is None:
            raise CommandError("Reply to a video message.")
        downloaded = await client.download_media(reply, file_name=str(video_path))
        await self._ffmpeg.video_to_gif(
            input_path=ensure_local_path(downloaded),
            output_path=gif_path,
            max_width=self._gif_max_width,
            fps=self._gif_fps,
        )
        size = gif_path.stat().st_size
        return GifConversionResult(path=gif_path, size_bytes=size)
