"""Fast single-shot AI answers with Telegram HTML formatting."""

from __future__ import annotations

import logging

from app.common.telegram_html import (
    TELEGRAM_AI_SYSTEM,
    prepare_telegram_html_output,
    truncate_telegram_html,
)
from app.infrastructure.llm.openai_chat_client import ChatMessage, OpenAiChatClient

logger = logging.getLogger(__name__)


class AiService:
    """One LLM call — no multi-layer discuss pipeline."""

    def __init__(self, llm: OpenAiChatClient | None, *, max_tokens: int) -> None:
        self._llm = llm
        self._max_tokens = max_tokens

    @property
    def enabled(self) -> bool:
        return self._llm is not None and self._llm.enabled

    @property
    def model_name(self) -> str:
        if self._llm is None:
            return "off"
        return self._llm.model

    async def ask(self, question: str, *, context: str | None = None) -> str:
        prompt = question.strip()
        if not prompt and not (context or "").strip():
            return "<b>⚠️ سوال خالی</b>\n\nبنویس: <code>.ai سوال تو</code>"

        if not self.enabled:
            return (
                "<b>⚠️ LLM تنظیم نشده</b>\n\n"
                "متغیر <code>LLM_API_KEY</code> را در <code>.env</code> بگذار."
            )

        user_parts: list[str] = []
        if context and context.strip():
            user_parts.append(f"Context message:\n{context.strip()}")
        if prompt:
            user_parts.append(f"Question:\n{prompt}")
        else:
            user_parts.append("Answer the context message above.")

        raw = await self._complete(
            [
                {"role": "system", "content": TELEGRAM_AI_SYSTEM},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
        )
        cleaned = prepare_telegram_html_output(raw)
        return truncate_telegram_html(cleaned)

    async def _complete(self, messages: list[ChatMessage]) -> str:
        if self._llm is None:
            msg = "LLM client is not configured"
            raise RuntimeError(msg)
        try:
            return await self._llm.complete(
                messages,
                temperature=0.4,
                max_tokens=self._max_tokens,
            )
        except Exception:
            logger.exception("AI request failed")
            raise
