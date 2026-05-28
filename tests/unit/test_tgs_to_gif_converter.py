"""TGS converter scaling tests."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.media.tgs_to_gif_converter import TgsToGifConverter


def test_scaled_dimensions_downscales_large_sticker() -> None:
    converter = TgsToGifConverter(max_dimension=256, fps=20)
    animation = MagicMock()
    animation.lottie_animation_get_size.return_value = (512, 512)
    width, height = converter._scaled_dimensions(animation)
    assert width == 256
    assert height == 256


def test_scaled_dimensions_keeps_small_sticker() -> None:
    converter = TgsToGifConverter(max_dimension=512, fps=20)
    animation = MagicMock()
    animation.lottie_animation_get_size.return_value = (100, 200)
    width, height = converter._scaled_dimensions(animation)
    assert width == 100
    assert height == 200


@pytest.mark.asyncio
async def test_convert_delegates_to_thread(tmp_path: Path) -> None:
    source = tmp_path / "in.tgs"
    dest = tmp_path / "out.gif"
    source.write_bytes(b"x")
    converter = TgsToGifConverter(max_dimension=128, fps=15)
    with patch.object(converter, "_convert_sync") as mock_sync:
        mock_sync.side_effect = lambda _src, out: out.touch()
        await converter.convert(source=source, destination=dest)
        mock_sync.assert_called_once_with(source, dest)
