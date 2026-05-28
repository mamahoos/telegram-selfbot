"""Image to WebP sticker optimization."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.common.exceptions import MediaProcessingError


class StickerProcessor:
    """Resize and convert images to Telegram-compatible WebP stickers."""

    def __init__(self, *, max_dimension: int) -> None:
        self._max_dimension = max_dimension

    def to_sticker_webp(self, source: Path, destination: Path) -> Path:
        try:
            with Image.open(source) as img:
                img = img.convert("RGBA")
                img.thumbnail(
                    (self._max_dimension, self._max_dimension),
                    Image.Resampling.LANCZOS,
                )
                canvas = Image.new("RGBA", (self._max_dimension, self._max_dimension), (0, 0, 0, 0))
                offset = (
                    (self._max_dimension - img.width) // 2,
                    (self._max_dimension - img.height) // 2,
                )
                canvas.paste(img, offset)
                destination.parent.mkdir(parents=True, exist_ok=True)
                canvas.save(
                    destination,
                    format="WEBP",
                    lossless=False,
                    quality=90,
                    method=6,
                )
        except OSError as exc:
            raise MediaProcessingError("Failed to process sticker image", cause=exc) from exc
        return destination
