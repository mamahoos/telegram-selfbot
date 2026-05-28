"""Reaction state persistence contract."""

from typing import Protocol

from app.domain.entities.reaction_state import ReactionChatState


class ReactionRepository(Protocol):
    async def get_chat_state(self, chat_id: int) -> ReactionChatState: ...

    async def set_enabled(self, chat_id: int, enabled: bool) -> ReactionChatState: ...

    async def is_enabled(self, chat_id: int) -> bool: ...
