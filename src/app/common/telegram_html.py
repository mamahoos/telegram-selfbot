"""Telegram message formatting — Hermes-style Markdown in, HTML out."""

from __future__ import annotations

import html
import re

TELEGRAM_MESSAGE_LIMIT = 4096

_HTML_FENCE = re.compile(r"^```(?:html)?\s*(.*?)\s*```$", flags=re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_HAS_HTML_TAG = re.compile(r"</?(?:b|strong|i|em|u|ins|s|code|pre|blockquote|a|tg-spoiler)\b", re.I)

_OPEN_THINK = "<" + "redacted_thinking" + ">"
_CLOSE_THINK = "</" + "redacted_thinking" + ">"
_REDACTED_THINKING = re.compile(
    re.escape(_OPEN_THINK) + r".*?" + re.escape(_CLOSE_THINK),
    flags=re.DOTALL | re.IGNORECASE,
)
_PLANNING_LINE = re.compile(
    r"^\s*[\*\-•]\s+.*(?:User wants|Language:|Format:|Header:|Code block:|"
    r"Explanation:|No Markdown|No preamble|Use `<|Output ONLY|Telegram HTML)",
    flags=re.IGNORECASE | re.MULTILINE,
)
_PLANNING_ENGLISH = re.compile(
    r"^(User wants|Language:|Format:|Header:|Code block:|Explanation:|"
    r"No Markdown|No preamble|Telegram HTML)\b",
    flags=re.IGNORECASE | re.MULTILINE,
)
_CODE_LINE = re.compile(
    r"^(?:print\(|def |class |import |from |if __name__|#include|function |const |let |var )",
)
_PRE_BLOCK = re.compile(r"<pre>\s*<code[^>]*>.*?</code>\s*</pre>", flags=re.DOTALL | re.IGNORECASE)

# GFM table detection (from Hermes gateway/platforms/telegram.py)
_TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*){1,}\|?\s*$",
)

# Hermes-style platform hint: model writes Markdown; adapter converts for Telegram.
TELEGRAM_AI_SYSTEM = """\
You are a helpful assistant replying on Telegram. Reply in the user's language (Persian if they write Persian).

Write your answer in standard Markdown. It is automatically converted to Telegram formatting.

Supported Markdown:
- **bold**, *italic*, ~~strikethrough~~, ||spoiler||
- `inline code` and ```language code blocks```
- [links](url), ## headings
- bullet/numbered lists, blockquotes (> text)

Rules:
- Output ONLY the final answer — no planning notes, checklists, or English meta like "User wants".
- Do NOT use HTML tags; use Markdown only.
- Prefer structured formatting (headings, fenced code blocks, lists) over dense paragraphs.

Example for "write Python to print کوروش شاه جهان":

## کد پایتون

```python
print("کوروش شاه جهان")
```

*توضیح:* با `print()` این متن در خروجی نمایش داده می‌شود.
"""

# Backward-compatible alias
TELEGRAM_HTML_SYSTEM = TELEGRAM_AI_SYSTEM


def unwrap_html_fence(text: str) -> str:
    stripped = text.strip()
    match = _HTML_FENCE.match(stripped)
    if match:
        return match.group(1).strip()
    return stripped


def prepare_telegram_html_output(raw: str) -> str:
    """Strip model artifacts and convert Markdown → Telegram HTML."""
    text = unwrap_html_fence(raw.strip())
    text = _strip_model_artifacts(text)
    text = _drop_leading_junk(text)

    if _HAS_HTML_TAG.search(text):
        text = _cleanup_html_output(text)
    else:
        text = markdown_to_telegram_html(text)

    text = _wrap_bare_code_lines(text)
    text = _dedupe_pre_blocks(text)
    text = _dedupe_paragraphs(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if text and not _HAS_HTML_TAG.search(text):
        text = f"<b>پاسخ</b>\n\n{html.escape(text)}"
    return text


def markdown_to_telegram_html(content: str) -> str:
    """Convert standard Markdown to Telegram HTML (Hermes adapter pattern)."""
    if not content.strip():
        return content

    text = _wrap_markdown_tables(content)
    placeholders: dict[str, str] = {}
    counter = 0

    def _ph(value: str) -> str:
        nonlocal counter
        key = f"\x00PH{counter}\x00"
        counter += 1
        placeholders[key] = value
        return key

    def _fenced(match: re.Match[str]) -> str:
        raw = match.group(0)
        lang = "text"
        body = raw
        if raw.startswith("```"):
            header_end = raw.find("\n")
            if header_end != -1:
                lang_match = re.match(r"```(\w+)", raw[:header_end])
                if lang_match and lang_match.group(1):
                    lang = lang_match.group(1).lower()
                body = raw[header_end + 1 :]
                if body.endswith("```"):
                    body = body[:-3]
            elif raw.endswith("```") and len(raw) > 6:
                body = raw[3:-3]
        escaped = html.escape(body.strip("\n"))
        return _ph(f'<pre><code class="language-{lang}">{escaped}</code></pre>')

    text = re.sub(r"```(?:[^\n]*\n)?[\s\S]*?```", _fenced, text)

    text = re.sub(
        r"`([^`\n]+)`",
        lambda m: _ph(f"<code>{html.escape(m.group(1))}</code>"),
        text,
    )

    def _link(match: re.Match[str]) -> str:
        display = html.escape(match.group(1))
        url = html.escape(match.group(2), quote=True)
        return _ph(f'<a href="{url}">{display}</a>')

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, text)

    text = re.sub(
        r"^#{1,6}\s+(.+)$",
        lambda m: _ph(f"<b>{html.escape(m.group(1).strip())}</b>"),
        text,
        flags=re.MULTILINE,
    )

    text = re.sub(
        r"\*\*(.+?)\*\*",
        lambda m: _ph(f"<b>{html.escape(m.group(1))}</b>"),
        text,
    )

    text = re.sub(
        r"(?<!\*)\*([^*\n]+)\*(?!\*)",
        lambda m: _ph(f"<i>{html.escape(m.group(1))}</i>"),
        text,
    )

    text = re.sub(
        r"(?<!\w)_([^_\n]+)_(?!\w)",
        lambda m: _ph(f"<i>{html.escape(m.group(1))}</i>"),
        text,
    )

    text = re.sub(
        r"~~(.+?)~~",
        lambda m: _ph(f"<s>{html.escape(m.group(1))}</s>"),
        text,
    )

    text = re.sub(
        r"\|\|(.+?)\|\|",
        lambda m: _ph(f"<tg-spoiler>{html.escape(m.group(1))}</tg-spoiler>"),
        text,
    )

    text = re.sub(
        r"^>\s?(.+)$",
        lambda m: _ph(f"<blockquote>{html.escape(m.group(1))}</blockquote>"),
        text,
        flags=re.MULTILINE,
    )

    # Escape plain text; placeholder tokens (\x00PHn\x00) survive html.escape.
    text = html.escape(text)

    for key in reversed(list(placeholders.keys())):
        text = text.replace(key, placeholders[key])

    return text


def _strip_model_artifacts(text: str) -> str:
    text = _REDACTED_THINKING.sub("", text)
    text = _PLANNING_LINE.sub("", text)
    text = _PLANNING_ENGLISH.sub("", text)
    return text


def _cleanup_html_output(text: str) -> str:
    """Light cleanup when the model still returns HTML despite the prompt."""
    text = re.sub(r"```(\w+)?\s*\n(.*?)```", _fence_to_pre, text, flags=re.DOTALL)
    return text


def _fence_to_pre(match: re.Match[str]) -> str:
    lang = (match.group(1) or "text").strip().lower()
    code = html.escape(match.group(2).strip())
    return f'<pre><code class="language-{lang}">{code}</code></pre>'


def _drop_leading_junk(text: str) -> str:
    for marker in ("<b>", "<pre>", "<blockquote>", "<i>", "##", "**", "```"):
        idx = text.find(marker)
        if idx > 0 and _looks_like_planning(text[:idx]):
            return text[idx:].lstrip()
    if not _looks_like_planning(text):
        return text
    lines = [line for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        stripped = line.strip()
        if (
            _HAS_HTML_TAG.search(line)
            or stripped.startswith("#")
            or stripped.startswith("```")
            or _CODE_LINE.match(stripped)
        ):
            return "\n".join(lines[i:])
    return text


def _looks_like_planning(text: str) -> bool:
    lower = text.lower()
    markers = ("user wants", "format:", "language:", "no markdown", "no preamble", "code block:")
    return any(m in lower for m in markers) or lower.count("*") >= 2


def _wrap_bare_code_lines(text: str) -> str:
    if "<pre>" in text.lower():
        return text
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and _CODE_LINE.match(stripped) and "<" not in stripped:
            out.append(f'<pre><code class="language-python">{html.escape(stripped)}</code></pre>')
        else:
            out.append(line)
    return "\n".join(out)


def _dedupe_pre_blocks(text: str) -> str:
    seen: set[str] = set()

    def repl(match: re.Match[str]) -> str:
        block = match.group(0)
        key = re.sub(r"\s+", "", block)
        if key in seen:
            return ""
        seen.add(key)
        return block

    cleaned = _PRE_BLOCK.sub(repl, text)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _dedupe_paragraphs(text: str) -> str:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for part in parts:
        key = re.sub(r"\s+", " ", part)
        if key in seen:
            continue
        seen.add(key)
        unique.append(part)
    return "\n\n".join(unique)


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and "|" in stripped


def _split_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _render_table_block_for_telegram(table_block: list[str]) -> str:
    if len(table_block) < 3:
        return "\n".join(table_block)

    headers = _split_markdown_table_row(table_block[0])
    if len(headers) < 2:
        return "\n".join(table_block)

    first_data_row = _split_markdown_table_row(table_block[2]) if len(table_block) > 2 else []
    has_row_label_col = len(first_data_row) == len(headers) + 1

    rendered_rows: list[str] = []
    for index, row in enumerate(table_block[2:], start=1):
        cells = _split_markdown_table_row(row)
        if has_row_label_col:
            heading = cells[0] if cells and cells[0] else f"Row {index}"
            data_cells = cells[1:]
        else:
            heading = next((cell for cell in cells if cell), f"Row {index}")
            data_cells = cells

        if len(data_cells) < len(headers):
            data_cells.extend([""] * (len(headers) - len(data_cells)))
        elif len(data_cells) > len(headers):
            data_cells = data_cells[: len(headers)]

        rendered_rows.append(f"**{heading}**")
        rendered_rows.extend(
            f"• {header}: {value}" for header, value in zip(headers, data_cells, strict=False)
        )

    return "\n\n".join(rendered_rows)


def _wrap_markdown_tables(text: str) -> str:
    if "|" not in text or "-" not in text:
        return text

    lines = text.split("\n")
    out: list[str] = []
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue
        if in_fence:
            out.append(line)
            i += 1
            continue

        if "|" in line and i + 1 < len(lines) and _TABLE_SEPARATOR_RE.match(lines[i + 1]):
            table_block = [line, lines[i + 1]]
            j = i + 2
            while j < len(lines) and _is_table_row(lines[j]):
                table_block.append(lines[j])
                j += 1
            out.append(_render_table_block_for_telegram(table_block))
            i = j
            continue

        out.append(line)
        i += 1

    return "\n".join(out)


def strip_html_tags(text: str) -> str:
    return _TAG_RE.sub("", text).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def truncate_telegram_html(text: str, *, limit: int = TELEGRAM_MESSAGE_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"
