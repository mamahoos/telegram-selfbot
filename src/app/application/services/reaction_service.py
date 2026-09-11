"""Auto-reaction orchestration."""

from hydrogram import Client
from hydrogram.types import Message

from app.infrastructure.hydrogram.reaction_gateway import ReactionGateway
from app.infrastructure.repositories.reaction_state_repository import ReactionStateRepository


class ReactionService:
    """Manages per-chat reaction toggles and delivery."""

    def __init__(
        self,
        repository: ReactionStateRepository,
        gateway: ReactionGateway,
    ) -> None:
        self._repository = repository
        self._gateway = gateway
        self._enabled_chats: frozenset[int] | None = None

    async def _enabled_chat_ids(self) -> frozenset[int]:
        if self._enabled_chats is None:
            self._enabled_chats = await self._repository.enabled_chat_ids()
        return self._enabled_chats

    def _invalidate_enabled_cache(self) -> None:
        self._enabled_chats = None

    async def toggle(self, chat_id: int) -> bool:
        current = await self._repository.is_enabled(chat_id)
        state = await self._repository.set_enabled(chat_id, not current)
        self._invalidate_enabled_cache()
        return state.enabled

    async def is_enabled(self, chat_id: int) -> bool:
        return await self._repository.is_enabled(chat_id)

    async def react_if_enabled(
        self,
        client: Client,
        message: Message,
    ) -> None:
        if message.outgoing:
            return
        if message.chat.id not in await self._enabled_chat_ids():
            return
        await self._gateway.send_random_reaction(
            client,
            chat_id=message.chat.id,
            message_id=message.id,
        )
