"""TGS (Telegram animated sticker) to GIF conversion via rlottie."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rlottie_python.rlottie_wrapper import LottieAnimation

from app.common.exceptions import MediaProcessingError


class TgsToGifConverter:
    """Renders .tgs Lottie stickers to GIF using rlottie (stable frame output)."""

    def __init__(self, *, max_dimension: int, fps: int) -> None:
        self._max_dimension = max_dimension
        self._fps = fps

    async def convert(self, *, source: Path, destination: Path) -> Path:
        try:
            await asyncio.to_thread(self._convert_sync, source, destination)
        except OSError as exc:
            raise MediaProcessingError("Failed to write GIF output", cause=exc) from exc
        except Exception as exc:
            raise MediaProcessingError("TGS to GIF conversion failed", cause=exc) from exc
        if not destination.exists():
            raise MediaProcessingError("GIF output file was not created")
        return destination

    def _convert_sync(self, source: Path, destination: Path) -> None:
        animation = LottieAnimation.from_tgs(str(source))
        width, height = self._scaled_dimensions(animation)
        animation.save_animation(
            str(destination),
            fps=self._fps,
            width=width,
            height=height,
            optimize=True,
        )

    def _scaled_dimensions(self, animation: LottieAnimation) -> tuple[int, int]:
        size = animation.lottie_animation_get_size()
        src_width = int(size[0])
        src_height = int(size[1])
        if src_width <= 0 or src_height <= 0:
            return self._max_dimension, self._max_dimension
        if src_width <= self._max_dimension and src_height <= self._max_dimension:
            return src_width, src_height
        scale = self._max_dimension / max(src_width, src_height)
        return max(1, int(src_width * scale)), max(1, int(src_height * scale))
