"""Reaction service tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.services.reaction_service import ReactionService
from app.core.container import Container
from app.infrastructure.repositories.reaction_state_repository import ReactionStateRepository
from app.infrastructure.storage.json_state_store import JsonStateStore
from app.presentation.handlers.message_router import MessageRouter


def _incoming_message(chat_id: int) -> MagicMock:
    message = MagicMock()
    message.outgoing = False
    message.chat.id = chat_id
    message.id = 1
    return message


@pytest.mark.asyncio
async def test_toggle_refreshes_react_if_enabled(tmp_path: Path) -> None:
    repo = ReactionStateRepository(JsonStateStore(tmp_path / "state.json"))
    gateway = AsyncMock()
    service = ReactionService(repository=repo, gateway=gateway)
    client = AsyncMock()
    message = _incoming_message(42)

    await service.react_if_enabled(client, message)
    gateway.send_random_reaction.assert_not_awaited()

    await service.toggle(42)

    await service.react_if_enabled(client, message)
    gateway.send_random_reaction.assert_awaited_once_with(
        client,
        chat_id=42,
        message_id=1,
    )


@pytest.mark.asyncio
async def test_separate_instances_do_not_share_enabled_cache(tmp_path: Path) -> None:
    """Documents stale-cache bug when router and plugin construct their own services."""
    repo = ReactionStateRepository(JsonStateStore(tmp_path / "state.json"))
    router_gateway = AsyncMock()
    plugin_gateway = AsyncMock()
    router_service = ReactionService(repository=repo, gateway=router_gateway)
    plugin_service = ReactionService(repository=repo, gateway=plugin_gateway)
    client = AsyncMock()
    message = _incoming_message(42)

    await router_service.react_if_enabled(client, message)
    await plugin_service.toggle(42)

    await plugin_service.react_if_enabled(client, message)
    plugin_gateway.send_random_reaction.assert_awaited_once()

    router_gateway.send_random_reaction.reset_mock()
    await router_service.react_if_enabled(client, message)
    router_gateway.send_random_reaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_container_shares_reaction_service_between_router_and_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_ID", "1")
    monkeypatch.setenv("API_HASH", "hash")
    monkeypatch.setenv("PHONE_NUMBER", "+10000000000")

    from app.config.settings import get_settings

    get_settings.cache_clear()
    container = Container(settings=get_settings())
    router = MessageRouter(container)
    from app.plugins.reactions.plugin import PluginImpl

    plugin = PluginImpl(container)

    assert router._reaction_service is plugin._service
    assert router._reaction_service is container.reaction_service
