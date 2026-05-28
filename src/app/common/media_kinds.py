"""Detect media types on Telegram messages."""

from hydrogram.types import Message


def is_gif_message(message: Message) -> bool:
    """True when the message contains a GIF or Telegram animation."""
    if getattr(message, "animation", None) is not None:
        return True
    document = getattr(message, "document", None)
    if document is None:
        return False
    mime = (getattr(document, "mime_type", None) or "").lower()
    file_name = (getattr(document, "file_name", None) or "").lower()
    return "gif" in mime or file_name.endswith(".gif")


def is_audio_message(message: Message) -> bool:
    """True when the message contains audio suitable for voice conversion."""
    if getattr(message, "audio", None) is not None or getattr(message, "voice", None) is not None:
        return True
    document = getattr(message, "document", None)
    if document is None:
        return False
    mime = (getattr(document, "mime_type", None) or "").lower()
    file_name = (getattr(document, "file_name", None) or "").lower()
    audio_extensions = (".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg", ".opus", ".wma")
    return mime.startswith("audio/") or any(file_name.endswith(ext) for ext in audio_extensions)
