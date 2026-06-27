"""Tests for discuss output sanitizer."""

from app.application.services.discuss_output_sanitizer import sanitize_discuss_output


def test_removes_em_dash() -> None:
    text = "حرفت درسته — ولی وضع موجود فرق داره"
    result = sanitize_discuss_output(text)
    assert "\u2014" not in result
    assert " / " in result


def test_strips_markdown_bold_and_meta_prefix() -> None:
    text = "پاسخ نهایی: **ببین** حرفت درسته"
    result = sanitize_discuss_output(text)
    assert "**" not in result
    assert "پاسخ" not in result.split()[0]
    assert result.startswith("ببین")


def test_strips_think_blocks() -> None:
    text = "<think>\nفکر کردم\n</think>\n\nمتن نهایی"
    result = sanitize_discuss_output(text)
    assert "فکر کردم" not in result
    assert result == "متن نهایی"
