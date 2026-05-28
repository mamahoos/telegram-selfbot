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

    async def toggle(self, chat_id: int) -> bool:
        current = await self._repository.is_enabled(chat_id)
        state = await self._repository.set_enabled(chat_id, not current)
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
        if not await self._repository.is_enabled(message.chat.id):
            return
        await self._gateway.send_random_reaction(
            client,
            chat_id=message.chat.id,
            message_id=message.id,
        )
