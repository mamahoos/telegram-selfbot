"""Message router dispatch tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock

import pytest
from hydrogram import enums

from app.application.commands.registry import CommandRegistry
from app.domain.entities.command import CommandDefinition
from app.presentation.handlers.message_router import MessageRouter


@dataclass
class _FakeChat:
    id: int
    type: enums.ChatType = enums.ChatType.PRIVATE


@dataclass
class _FakeUser:
    id: int


@dataclass
class _FakeContainer:
    command_registry: CommandRegistry = field(default_factory=CommandRegistry)
    reaction_repository: MagicMock = field(default_factory=MagicMock)
    reaction_gateway: MagicMock = field(default_factory=MagicMock)

    def __post_init__(self) -> None:
        self.reaction_repository.enabled_chat_ids = AsyncMock(return_value=frozenset())


def _message(
    *,
    outgoing: bool,
    text: str,
    chat_id: int = 100,
    user_id: int = 100,
    chat_type: enums.ChatType = enums.ChatType.PRIVATE,
) -> MagicMock:
    message = MagicMock()
    message.outgoing = outgoing
    message.text = text
    message.caption = None
    message.id = 1
    message.chat = _FakeChat(id=chat_id, type=chat_type)
    message.from_user = _FakeUser(id=user_id)
    return message


@pytest.fixture
def router() -> MessageRouter:
    return MessageRouter(_FakeContainer())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_dispatch_command_runs_handler(router: MessageRouter) -> None:
    await router._owner_filter.bind_owner(100)
    handler = AsyncMock()
    router._registry.register(
        CommandDefinition(name="help", description="help", plugin="system"),
        handler,
    )
    client = AsyncMock()

    await router._dispatch_command(client, _message(outgoing=True, text=".help"))

    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispatch_command_ignores_non_commands(router: MessageRouter) -> None:
    handler = AsyncMock()
    router._registry.register(
        CommandDefinition(name="help", description="help", plugin="system"),
        handler,
    )
    client = AsyncMock()

    await router._dispatch_command(client, _message(outgoing=True, text="hello"))

    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_spawn_command_returns_before_handler_finishes(router: MessageRouter) -> None:
    await router._owner_filter.bind_owner(100)
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow_handler(_client: object, _message: object) -> None:
        started.set()
        await release.wait()

    router._registry.register(
        CommandDefinition(name="help", description="help", plugin="system"),
        slow_handler,
    )
    client = AsyncMock()

    router._spawn_command(client, _message(outgoing=True, text=".help"))
    await asyncio.wait_for(started.wait(), timeout=1)
    release.set()


@pytest.mark.asyncio
async def test_run_reaction_skips_when_chat_not_enabled(router: MessageRouter) -> None:
    client = AsyncMock()
    gateway = router._reaction_service._gateway
    gateway.send_random_reaction = AsyncMock()

    await router._run_reaction(
        client,
        _message(outgoing=False, text="noise", chat_id=999, chat_type=enums.ChatType.SUPERGROUP),
    )

    gateway.send_random_reaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_owner_bound_only_calls_get_me_once(router: MessageRouter) -> None:
    client = AsyncMock()
    client.get_me = AsyncMock(return_value=MagicMock(id=100))

    await asyncio.gather(
        router._ensure_owner_bound(client),
        router._ensure_owner_bound(client),
    )

    client.get_me.assert_awaited_once()
