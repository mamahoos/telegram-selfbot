"""Awk service tests."""

from __future__ import annotations

import pytest

from app.application.services.awk_service import AwkService
from app.common.exceptions import CommandError
from app.infrastructure.shell.awk_runner import AwkRunner


@pytest.mark.asyncio
async def test_awk_runner_real_binary_first_field() -> None:
    runner = AwkRunner(binary="awk", timeout_seconds=10)
    result = await runner.run(
        input_text="hello world\nfoo bar\n",
        arguments=["{print $1}"],
    )
    assert result.exit_code == 0
    assert result.stdout == "hello\nfoo\n"


def test_parse_awk_program_without_quotes() -> None:
    program = AwkService.parse_awk_program(".awk {print NR, $0}")
    assert program == "{print NR, $0}"


@pytest.mark.asyncio
async def test_awk_runner_print_nr() -> None:
    runner = AwkRunner(binary="awk", timeout_seconds=10)
    result = await runner.run(
        input_text="alpha\nbeta\n",
        arguments=["{print NR, $0}"],
    )
    assert result.exit_code == 0
    assert result.stdout == "1 alpha\n2 beta\n"


def test_format_codeblock_wraps_output() -> None:
    from app.infrastructure.shell.awk_runner import AwkResult

    service = AwkService(AwkRunner(binary="awk", timeout_seconds=1), max_output_chars=1000)
    block = service.format_codeblock(AwkResult(stdout="ok\n", stderr="", exit_code=0))
    assert block.startswith("```\n")
    assert block.endswith("\n```")
    assert "ok" in block


def test_parse_awk_program_missing_body() -> None:
    with pytest.raises(CommandError, match="Usage"):
        AwkService.parse_awk_program(".awk")


def test_parse_awk_program_rejects_awkx() -> None:
    with pytest.raises(CommandError, match="not `.awkx`"):
        AwkService.parse_awk_program(".awkx {print}")


def test_parse_awk_cli_arguments_with_flags() -> None:
    args = AwkService.parse_awk_cli_arguments(".awkx -F: '{print $2}'")
    assert args == ["-F:", "{print $2}"]


def test_parse_awk_cli_missing_args() -> None:
    with pytest.raises(CommandError, match="Usage"):
        AwkService.parse_awk_cli_arguments(".awkx")
