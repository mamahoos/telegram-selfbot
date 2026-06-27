"""Deterministic cleanup of LLM reply text before Telegram send."""

from __future__ import annotations

import re

_OPEN_THINK = "<" + "redacted_thinking" + ">"
_CLOSE_THINK = "</" + "redacted_thinking" + ">"
_REDACTED_THINKING = re.compile(
    re.escape(_OPEN_THINK) + r".*?" + re.escape(_CLOSE_THINK),
    flags=re.DOTALL | re.IGNORECASE,
)
_THINK_TAG = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", flags=re.DOTALL | re.IGNORECASE)
_REASONING_TAG = re.compile(r"<reasoning>.*?</reasoning>", flags=re.DOTALL | re.IGNORECASE)
_FENCED_BLOCK = re.compile(r"```.*?```", flags=re.DOTALL)
_MARKDOWN_BOLD = re.compile(r"\*\*(.+?)\*\*")
_MARKDOWN_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_MARKDOWN_HEADER = re.compile(r"^#{1,6}\s+", flags=re.MULTILINE)
_META_PREFIX = re.compile(
    r"^(?:"
    r"(?:پاسخ(?: نهایی)?|جواب|Reply|Final answer|Here(?:'s| is)|Sure,?|Okay,?)"
    r"[\s:：\-–—]*"
    r")+",
    flags=re.IGNORECASE | re.MULTILINE,
)
_EM_DASH = "\u2014"
_EN_DASH = "\u2013"
_HORIZ = "\u2500"
_BULLET_LINE = re.compile(r"^[\-*•]\s+", flags=re.MULTILINE)
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE = re.compile(r"\n{3,}")


def sanitize_discuss_output(text: str) -> str:
    """Remove common LLM artifacts; keep meaning, Telegram-friendly Persian."""
    cleaned = text.strip()
    if not cleaned:
        return cleaned

    cleaned = _REDACTED_THINKING.sub("", cleaned)
    cleaned = _THINK_TAG.sub("", cleaned)
    cleaned = _REASONING_TAG.sub("", cleaned)
    cleaned = _FENCED_BLOCK.sub("", cleaned)
    cleaned = _MARKDOWN_HEADER.sub("", cleaned)
    cleaned = _MARKDOWN_BOLD.sub(r"\1", cleaned)
    cleaned = _MARKDOWN_ITALIC.sub(r"\1", cleaned)
    cleaned = _replace_dashes(cleaned)
    cleaned = _META_PREFIX.sub("", cleaned)
    cleaned = _BULLET_LINE.sub("", cleaned)
    cleaned = cleaned.replace("`", "")
    cleaned = _MULTI_SPACE.sub(" ", cleaned)
    cleaned = _MULTI_NEWLINE.sub("\n\n", cleaned)
    return cleaned.strip()


def _replace_dashes(text: str) -> str:
    """Em/en dashes -> Telegram-style slash or simple hyphen."""
    result = text.replace(_EM_DASH, " / ")
    result = result.replace(_EN_DASH, " - ")
    result = result.replace(_HORIZ, "")
    result = re.sub(r"\s*/\s*/\s*", " / ", result)
    result = re.sub(r"^\s*/\s*", "", result, flags=re.MULTILINE)
    return result
