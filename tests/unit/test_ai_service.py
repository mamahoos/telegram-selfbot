"""Tests for AiService."""

import pytest

from app.application.services.ai_service import AiService
from app.infrastructure.llm.openai_chat_client import ChatMessage


class FakeLlm:
    def __init__(self, response: str) -> None:
        self._response = response
        self.enabled = True
        self.model = "auto"

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        _ = messages, temperature, max_tokens
        return self._response


@pytest.mark.asyncio
async def test_ask_returns_html() -> None:
    service = AiService(
        FakeLlm("## پاسخ\n\n```python\nprint(1)\n```"),  # type: ignore[arg-type]
        max_tokens=500,
    )
    result = await service.ask("سلام")
    assert "<b>پاسخ</b>" in result
    assert "<pre><code" in result


@pytest.mark.asyncio
async def test_ask_without_llm() -> None:
    service = AiService(None, max_tokens=500)
    result = await service.ask("test")
    assert "LLM" in result
