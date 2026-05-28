"""Stream text into a message via progressive edits."""

from __future__ import annotations

from hydrogram.types import Message

from app.application.services.text_stream import build_stream_steps
from app.common.exceptions import CommandError
from app.infrastructure.hydrogram.message_edit_gateway import MessageEditGateway


class TextStreamService:
    """Types out text on an existing outgoing message."""

    def __init__(self, editor: MessageEditGateway) -> None:
        self._editor = editor

    async def stream_into_message(self, message: Message, text: str) -> None:
        steps = build_stream_steps(text)
        if not steps:
            raise CommandError("Provide text with at least one non-space character.")

        chat_id = message.chat.id
        for index, step in enumerate(steps):
            if index > 0:
                await self._editor.wait_between_steps(chat_id)
            await self._editor.edit_text(message, step)
