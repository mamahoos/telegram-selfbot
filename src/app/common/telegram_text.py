"""Telegram UTF-16 text length helpers for message entities."""

from __future__ import annotations


def utf16_len(text: str) -> int:
    """Length of text in UTF-16 code units (Telegram entity offsets)."""
    return len(text.encode("utf-16-le")) // 2
