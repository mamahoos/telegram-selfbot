"""Run awk on replied message text."""

from __future__ import annotations

import re
import shlex

from hydrogram.types import Message

from app.common.exceptions import CommandError
from app.infrastructure.shell.awk_runner import AwkResult, AwkRunner

_CODE_FENCE = "```"
_TELEGRAM_MAX = 4096
_SIMPLE_PREFIX = re.compile(r"^\.awk(?!x)", re.IGNORECASE)
_CLI_PREFIX = re.compile(r"^\.awkx(?:\s|$)", re.IGNORECASE)


class AwkService:
    """Parses `.awk` / `.awkx` commands and formats awk output for Telegram."""

    def __init__(self, runner: AwkRunner, *, max_output_chars: int) -> None:
        self._runner = runner
        self._max_output_chars = max_output_chars

    @staticmethod
    def parse_awk_program(command_text: str) -> str:
        """Everything after `.awk` is the awk program (no quoting required)."""
        stripped = command_text.strip()
        if not _SIMPLE_PREFIX.match(stripped):
            raise CommandError("Command must start with `.awk` (not `.awkx`).")
        program = stripped[4:].lstrip()
        if not program:
            raise CommandError(
                "Usage: reply to a message, then send `.awk {print NR, $0}`"
            )
        return program

    @staticmethod
    def parse_awk_cli_arguments(command_text: str) -> list[str]:
        """Parse full awk CLI after `.awkx` using shell-like rules."""
        stripped = command_text.strip()
        if not _CLI_PREFIX.match(stripped):
            raise CommandError("Command must start with `.awkx`.")
        remainder = stripped[5:].lstrip()
        if not remainder:
            raise CommandError(
                "Usage: `.awkx -F: '{print $2}'` or `.awkx -f script.awk`"
            )
        try:
            return shlex.split(remainder)
        except ValueError as exc:
            raise CommandError(f"Could not parse awk arguments: {exc}") from exc

    @staticmethod
    def extract_reply_text(reply: Message) -> str:
        text = reply.text or reply.caption
        if text is None:
            raise CommandError("Replied message has no text or caption for awk to process.")
        return text

    async def run_simple_on_reply(self, message: Message) -> str:
        return await self._run_on_reply(
            message,
            arguments=[self.parse_awk_program(message.text or message.caption or "")],
        )

    async def run_advanced_on_reply(self, message: Message) -> str:
        return await self._run_on_reply(
            message,
            arguments=self.parse_awk_cli_arguments(message.text or message.caption or ""),
        )

    async def _run_on_reply(self, message: Message, *, arguments: list[str]) -> str:
        reply = message.reply_to_message
        if reply is None:
            raise CommandError("Reply to a message, then run `.awk` or `.awkx`.")

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
