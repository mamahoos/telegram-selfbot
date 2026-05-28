"""Command registry tests."""

from unittest.mock import AsyncMock

import pytest

from app.application.commands.registry import CommandRegistry
from app.domain.entities.command import CommandDefinition


def test_resolve_command_trigger() -> None:
    registry = CommandRegistry()
    handler = AsyncMock()
    registry.register(
        CommandDefinition(name="id", description="chat id", plugin="utility"),
        handler,
    )
    resolved = registry.resolve(".id")
    assert resolved is not None
    registered, args = resolved
    assert registered.definition.name == "id"
    assert args == ""
    assert registered.handler is handler


def test_duplicate_registration_raises() -> None:
    registry = CommandRegistry()
    definition = CommandDefinition(name="id", description="x", plugin="utility")
    registry.register(definition, AsyncMock())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(definition, AsyncMock())
