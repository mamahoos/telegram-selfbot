"""Discuss plugin — draft replies based on owner worldview and tone."""

from __future__ import annotations

import logging
from typing import cast

from hydrogram import Client
from hydrogram.types import Message

from app.application.commands.registry import CommandRegistry
from app.application.services.discuss_service import DiscussService
from app.core.container import Container
from app.domain.entities.command import CommandDefinition
from app.infrastructure.llm.openai_chat_client import OpenAiChatClient, OpenAiChatConfig
from app.plugins.base import Plugin
from app.presentation.middleware.error_handler import log_and_handle

logger = logging.getLogger(__name__)


class PluginImpl(Plugin):
    name = "discuss"

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
        self._service = DiscussService(
            settings.discuss_profile_path,
            cognitive_path=settings.discuss_cognitive_profile_path,
            voice_path=settings.discuss_voice_path,
            llm=llm,
        )

    def register(self, registry: CommandRegistry) -> None:
        registry.register(
            CommandDefinition(
                name="answer",
                description="Analyze opponent message and reply in your voice (reply required)",
                plugin=self.name,
            ),
            self._handle_answer,
        )
        registry.register(
            CommandDefinition(
                name="assist",
                description="Draft a discussion reply using your political/economic profile",
                plugin=self.name,
                aliases=("reply", "draft"),
            ),
            self._handle_assist,
        )
        registry.register(
            CommandDefinition(
                name="profile",
                description="Show loaded worldview/tone profile summary",
                plugin=self.name,
            ),
            self._handle_profile,
        )

    async def _handle_answer(self, client: Client, message: Message) -> None:
        replied = cast(Message | None, message.reply_to_message)
        if replied is None:
            await message.edit("⚠️ روی پیام طرف **ریپلای** کن و `.answer` بزن.")
            return

        opponent = (replied.text or replied.caption or "").strip()
        if not opponent:
            await message.edit("⚠️ پیام ریپلای متن ندارد.")
            return

        command_text = message.text or message.caption or ""
        parts = command_text.split(maxsplit=1)
        extra = parts[1] if len(parts) > 1 else ""

        async def on_progress(status: str) -> None:
            await message.edit(status)

        try:
            final = await self._service.answer(
                opponent,
                extra_prompt=extra,
                progress=on_progress,
            )
            await message.edit(final)
        except Exception as exc:
            logger.exception("Discuss .answer failed")
            await log_and_handle(client, message, exc)

    async def _handle_assist(self, client: Client, message: Message) -> None:
        text = message.text or message.caption or ""
        parts = text.split(maxsplit=1)
        prompt = parts[1] if len(parts) > 1 else ""
        reply_context: str | None = None
        if message.reply_to_message is not None:
            replied = message.reply_to_message
            reply_context = replied.text or replied.caption

        async def on_progress(status: str) -> None:
            await message.edit(status)

        try:
            if reply_context:
                draft = await self._service.answer(
                    reply_context.strip(),
                    extra_prompt=prompt,
                    progress=on_progress,
                )
            else:
                draft = await self._service.answer(prompt, progress=on_progress)
            await message.edit(draft)
        except Exception as exc:
            logger.exception("Discuss .assist failed")
            await log_and_handle(client, message, exc)

    async def _handle_profile(self, _client: Client, message: Message) -> None:
        profile = await self._service.load_profile()
        llm_ok = "✅" if self._service.llm_enabled else "⚠️"
        status = "✅ بارگذاری شد" if profile.loaded else "⚠️ تنظیم نشده"
        await message.edit(
            f"**Discuss profile** — {status}\n"
            f"**LLM** — {llm_ok} `{self._service.llm_model_name}`\n\n"
            f"{profile.summary}",
        )
