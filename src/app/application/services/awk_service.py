"""Run awk on replied message text."""

from __future__ import annotations

import shlex

from hydrogram.types import Message

from app.common.exceptions import CommandError
from app.infrastructure.shell.awk_runner import AwkResult, AwkRunner

_CODE_FENCE = "```"
_TELEGRAM_MAX = 4096


class AwkService:
    """Parses `.awk` commands and formats awk output for Telegram."""

    def __init__(self, runner: AwkRunner, *, max_output_chars: int) -> None:
        self._runner = runner
        self._max_output_chars = max_output_chars

    @staticmethod
    def parse_awk_arguments(command_text: str) -> list[str]:
        stripped = command_text.strip()
        parts = stripped.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            raise CommandError(
                "Usage: reply to a message, then send `.awk <arguments>`\n"
                "Example: `.awk '{print $1}'`"
            )
        try:
            return shlex.split(parts[1])
        except ValueError as exc:
            raise CommandError(f"Could not parse awk arguments: {exc}") from exc

    @staticmethod
    def extract_reply_text(reply: Message) -> str:
        text = reply.text or reply.caption
        if text is None:
            raise CommandError("Replied message has no text or caption for awk to process.")
        return text

    async def run_on_reply(self, message: Message) -> str:
        reply = message.reply_to_message
        if reply is None:
            raise CommandError("Reply to a message, then run `.awk`.")

        command_text = message.text or message.caption or ""
        arguments = self.parse_awk_arguments(command_text)
        input_text = self.extract_reply_text(reply)
        result = await self._runner.run(input_text=input_text, arguments=arguments)
        return self.format_codeblock(result)

    def format_codeblock(self, result: AwkResult) -> str:
        body = self._build_body(result)
        body = self._truncate(body)
        return f"{_CODE_FENCE}\n{body}\n{_CODE_FENCE}"

    @staticmethod
    def _build_body(result: AwkResult) -> str:
        chunks: list[str] = []
        if result.stdout:
            chunks.append(result.stdout.rstrip("\n"))
        if result.stderr:
            stderr = result.stderr.rstrip("\n")
            chunks.append(f"[stderr]\n{stderr}" if chunks else stderr)
        if result.exit_code != 0:
            chunks.append(f"[exit {result.exit_code}]")
        if not chunks:
            return "(no output)"
        return "\n".join(chunks)

    def _truncate(self, body: str) -> str:
        fence_overhead = len(_CODE_FENCE) * 2 + 2
        limit = min(self._max_output_chars, _TELEGRAM_MAX - fence_overhead)
        if len(body) <= limit:
            return body
        return body[: limit - 20] + "\n… (truncated)"
