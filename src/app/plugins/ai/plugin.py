"""`.ai` — fast LLM answers with Telegram HTML formatting."""

from __future__ import annotations

import logging

from hydrogram import Client, enums
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.ai_service import AiService
from app.common.telegram_html import strip_html_tags
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.infrastructure.llm.openai_chat_client import OpenAiChatClient, OpenAiChatConfig
from app.plugins.base import Plugin
from app.presentation.middleware.error_handler import log_and_handle

logger = logging.getLogger(__name__)


class PluginImpl(Plugin):
    name = "ai"

    def __init__(self, container: Container) -> None:
        super().__init__(container)
        settings = container.settings
        llm = OpenAiChatClient(
            OpenAiChatConfig(
                base_url=settings.llm_api_base_url,
                api_key=settings.llm_api_key,
                model=settings.llm_model,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )
        self._service = AiService(llm, max_tokens=settings.ai_max_tokens)

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="ai",
                description="Fast AI answer with Telegram HTML formatting",
                plugin=self.name,
            ),
            self._handle_ai,
        )

    async def _handle_ai(self, client: Client, message: Message) -> None:
        command_text = message.text or message.caption or ""
        parts = command_text.split(maxsplit=1)
        question = parts[1] if len(parts) > 1 else ""

        context: str | None = None
        if message.reply_to_message is not None:
            replied = message.reply_to_message
            context = (replied.text or replied.caption or "").strip() or None

        if not question.strip() and context is None:
            await self._edit_html(
                message,
                "<b>⚠️ سوال خالی</b>\n\n"
                "<code>.ai سوال تو</code>\n"
                "یا روی یک پیام ریپلای بزن: <code>.ai</code>",
            )
            return

        await self._edit_html(message, "⏳ <i>در حال فکر کردن…</i>")

        try:
            answer = await self._service.ask(question, context=context)
            await self._edit_html(message, answer)
        except Exception as exc:
            logger.exception("AI .ai failed")
            await log_and_handle(client, message, exc)

    async def _edit_html(self, message: Message, text: str) -> None:
        try:
            await message.edit(text, parse_mode=enums.ParseMode.HTML)
        except Exception:
            logger.warning("HTML edit failed, falling back to plain text")
            await message.edit(strip_html_tags(text))
