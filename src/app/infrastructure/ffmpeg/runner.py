"""Async FFmpeg subprocess runner."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.common.exceptions import MediaProcessingError


class FfmpegRunner:
    """Executes ffmpeg with timeout and captures errors."""

    def __init__(self, *, binary: str, timeout_seconds: int) -> None:
        self._binary = binary
        self._timeout_seconds = timeout_seconds

    async def run(self, *args: str) -> None:
        cmd = (self._binary, *args)
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._timeout_seconds,
            )
        except TimeoutError as exc:
            raise MediaProcessingError(
                f"ffmpeg timed out after {self._timeout_seconds}s",
                cause=exc,
            ) from exc
        except FileNotFoundError as exc:
            raise MediaProcessingError(
                f"ffmpeg binary not found: {self._binary}",
                cause=exc,
            ) from exc

        if process.returncode != 0:
            detail = stderr.decode(errors="replace").strip()
            raise MediaProcessingError(f"ffmpeg failed: {detail}")

    async def video_to_gif(
        self,
        *,
        input_path: Path,
        output_path: Path,
        max_width: int,
        fps: int,
    ) -> Path:
        scale = (
            f"scale='min({max_width},iw)':-1:flags=lanczos,"
            f"fps={fps},split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        )
        await self.run(
            "-y",
            "-i",
            str(input_path),
            "-vf",
            scale,
            "-loop",
            "0",
            str(output_path),
        )
        return output_path

    async def gif_to_video_note(
        self,
        *,
        input_path: Path,
        output_path: Path,
        size: int,
        fps: int,
    ) -> Path:
        """Convert GIF/animation to square H.264 MP4 for Telegram video notes."""
        scale_crop = (
            f"scale={size}:{size}:force_original_aspect_ratio=increase,crop={size}:{size},fps={fps}"
        )
        await self.run(
            "-y",
            "-i",
            str(input_path),
            "-vf",
            scale_crop,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            "-movflags",
            "+faststart",
            str(output_path),
        )
        return output_path

    async def audio_to_voice_ogg(
        self,
        *,
        input_path: Path,
        output_path: Path,
        bitrate_kbps: int,
    ) -> Path:
        """Convert any audio file to OGG Opus for Telegram voice messages."""
        await self.run(
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-c:a",
            "libopus",
            "-b:a",
            f"{bitrate_kbps}k",
            "-application",
            "voip",
            "-vbr",
            "on",
            str(output_path),
        )
        return output_path
