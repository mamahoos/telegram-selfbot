"""Sticker processor tests."""

from pathlib import Path

from PIL import Image

from app.infrastructure.media.sticker_processor import StickerProcessor


def test_to_sticker_webp_resizes(tmp_path: Path) -> None:
    source = tmp_path / "in.png"
    dest = tmp_path / "out.webp"
    Image.new("RGB", (1024, 768), color=(255, 0, 0)).save(source)
    processor = StickerProcessor(max_dimension=512)
    processor.to_sticker_webp(source, dest)
    assert dest.exists()
    with Image.open(dest) as img:
        assert img.size == (512, 512)
