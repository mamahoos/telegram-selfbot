"""Tests for Telegram HTML helpers."""

from app.common.telegram_html import (
    markdown_to_telegram_html,
    prepare_telegram_html_output,
    strip_html_tags,
    truncate_telegram_html,
    unwrap_html_fence,
)

SAMPLE_JUNK = """\
*   User wants a Python code that prints "کوروش شاه جهان".
*   Language: Persian.
*   Format: Telegram HTML.

کد پایتون برای چاپ عبارت:

print("کوروش شاه جهان")

توضیح:
در پایتون، تابع print() برای نمایش متن در خروجی استفاده می‌شود.

کد پایتون برای چاپ عبارت:

print("کوروش شاه جهان")

توضیح کوتاه:
در زبان پایتون، برای نمایش یک متن در خروجی از تابع print() استفاده می‌شود.
"""

SAMPLE_MARKDOWN = """\
## کد پایتون

```python
print("کوروش شاه جهان")
```

*توضیح:* با `print()` این متن در خروجی نمایش داده می‌شود.
"""


def test_unwrap_html_fence() -> None:
    raw = "```html\n<b>hi</b>\n```"
    assert unwrap_html_fence(raw) == "<b>hi</b>"


def test_markdown_to_telegram_html() -> None:
    result = markdown_to_telegram_html(SAMPLE_MARKDOWN)
    assert "<b>کد پایتون</b>" in result
    assert '<pre><code class="language-python">' in result
    assert 'print(&quot;کوروش شاه جهان&quot;)' in result
    assert "<i>توضیح:</i>" in result
    assert "<code>print()</code>" in result


def test_prepare_strips_planning_and_wraps_code() -> None:
    result = prepare_telegram_html_output(SAMPLE_JUNK)
    assert "User wants" not in result
    assert "<pre><code" in result
    assert result.lower().count("<pre>") == 1


def test_prepare_converts_markdown() -> None:
    result = prepare_telegram_html_output(SAMPLE_MARKDOWN)
    assert "<b>کد پایتون</b>" in result
    assert result.lower().count("<pre>") == 1
    assert "User wants" not in result


def test_prepare_keeps_valid_html() -> None:
    raw = (
        "<b>کد پایتون</b>\n\n"
        '<pre><code class="language-python">print("x")</code></pre>\n\n'
        "<i>توضیح:</i> تست"
    )
    assert prepare_telegram_html_output(raw) == raw


def test_strip_html_tags() -> None:
    assert strip_html_tags("<b>سلام</b> &amp; <code>x</code>") == "سلام & x"


def test_truncate() -> None:
    assert len(truncate_telegram_html("a" * 5000)) == 4096
