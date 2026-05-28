"""Reaction enablement persistence."""

from app.domain.entities.reaction_state import ReactionChatState
from app.infrastructure.storage.json_state_store import JsonStateStore

_REACTIONS_KEY = "reactions"


class ReactionStateRepository:
    """JSON-backed per-chat reaction toggles."""

    def __init__(self, store: JsonStateStore) -> None:
        self._store = store

    async def _read_map(self) -> dict[str, bool]:
        raw: dict[str, bool] = await self._store.get(_REACTIONS_KEY, {})
        return {str(k): bool(v) for k, v in raw.items()}

    async def _write_map(self, data: dict[str, bool]) -> None:
        await self._store.set(_REACTIONS_KEY, data)

    async def get_chat_state(self, chat_id: int) -> ReactionChatState:
        data = await self._read_map()
        enabled = data.get(str(chat_id), False)
        return ReactionChatState(chat_id=chat_id, enabled=enabled)

    async def set_enabled(self, chat_id: int, enabled: bool) -> ReactionChatState:
        data = await self._read_map()
        data[str(chat_id)] = enabled
        await self._write_map(data)
        return ReactionChatState(chat_id=chat_id, enabled=enabled)

    async def is_enabled(self, chat_id: int) -> bool:
        state = await self.get_chat_state(chat_id)
        return state.enabled
