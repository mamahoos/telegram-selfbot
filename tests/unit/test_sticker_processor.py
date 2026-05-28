"""Sticker processor tests."""

from pathlib import Path

from PIL import Image

from app.infrastructure.media.sticker_processor import StickerProcessor


def test_webp_to_jpeg(tmp_path: Path) -> None:
    source = tmp_path / "sticker.webp"
    dest = tmp_path / "photo.jpg"
    Image.new("RGBA", (64, 64), (255, 0, 0, 128)).save(source, format="WEBP")

    processor = StickerProcessor(max_dimension=512)
    processor.webp_to_jpeg(source, dest)

    assert dest.exists()
    with Image.open(dest) as img:
        assert img.format == "JPEG"
