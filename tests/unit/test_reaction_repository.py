"""Reaction state persistence tests."""

from pathlib import Path

import pytest

from app.infrastructure.repositories.reaction_state_repository import ReactionStateRepository
from app.infrastructure.storage.json_state_store import JsonStateStore


@pytest.mark.asyncio
async def test_toggle_reaction_state(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    store = JsonStateStore(path)
    repo = ReactionStateRepository(store)
    assert await repo.is_enabled(42) is False
    await repo.set_enabled(42, True)
    assert await repo.is_enabled(42) is True
    state = await repo.get_chat_state(42)
    assert state.enabled is True
