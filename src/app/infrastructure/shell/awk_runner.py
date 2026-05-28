"""Execute the system awk binary with real CLI arguments."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.common.exceptions import CommandError


@dataclass(frozen=True, slots=True)
class AwkResult:
    """Captured awk process output."""

    stdout: str
    stderr: str
    exit_code: int


class AwkRunner:
    """Runs awk without a shell; input is passed on stdin."""

    def __init__(self, *, binary: str, timeout_seconds: int) -> None:
        self._binary = binary
        self._timeout_seconds = timeout_seconds

    async def run(self, *, input_text: str, arguments: list[str]) -> AwkResult:
        if not arguments:
            raise CommandError("Awk requires at least one argument (e.g. a program or `-f script`).")

        try:
            process = await asyncio.create_subprocess_exec(
                self._binary,
                *arguments,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_b, stderr_b = await asyncio.wait_for(
                process.communicate(input_text.encode("utf-8")),
                timeout=self._timeout_seconds,
            )
        except TimeoutError as exc:
            raise CommandError(
                f"awk timed out after {self._timeout_seconds}s",
                cause=exc,
            ) from exc
        except FileNotFoundError as exc:
            raise CommandError(
                f"awk binary not found: {self._binary}",
                cause=exc,
            ) from exc

        return AwkResult(
            stdout=stdout_b.decode("utf-8", errors="replace"),
            stderr=stderr_b.decode("utf-8", errors="replace"),
            exit_code=process.returncode or 0,
        )
