"""Media kind detection tests."""

from unittest.mock import MagicMock

from app.common.media_kinds import is_audio_message, is_gif_message


def test_is_gif_message_animation() -> None:
    message = MagicMock()
    message.animation = object()
    message.document = None
    assert is_gif_message(message) is True


def test_is_gif_message_document() -> None:
    message = MagicMock()
    message.animation = None
    message.document = MagicMock(mime_type="image/gif", file_name="fun.gif")
    assert is_gif_message(message) is True


def test_is_audio_message_mp3() -> None:
    message = MagicMock()
    message.audio = MagicMock()
    message.voice = None
    message.document = None
    assert is_audio_message(message) is True
