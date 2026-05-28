"""Command registry with plugin auto-discovery support."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from hydrogram import Client
from hydrogram.types import Message

from app.domain.entities.command import CommandDefinition

CommandCallable = Callable[[Client, Message], Awaitable[None]]


@dataclass
class RegisteredCommand:
    definition: CommandDefinition
    handler: CommandCallable


@dataclass
class CommandRegistry:
    """Maps dot-commands to handlers."""

    _commands: dict[str, RegisteredCommand] = field(default_factory=dict)

    def register(
        self,
        definition: CommandDefinition,
        handler: CommandCallable,
    ) -> None:
        for trigger in definition.triggers:
            key = trigger.lower()
            if key in self._commands:
                msg = f"Command trigger already registered: {trigger}"
                raise ValueError(msg)
            self._commands[key] = RegisteredCommand(definition=definition, handler=handler)

    def resolve(self, text: str) -> tuple[RegisteredCommand, str] | None:
        """Return command and remaining args from message text."""
        stripped = text.strip()
        if not stripped.startswith("."):
            return None
        parts = stripped.split(maxsplit=1)
        trigger = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        registered = self._commands.get(trigger)
        if registered is None:
            return None
        return registered, args

    @property
    def all_definitions(self) -> list[CommandDefinition]:
        seen: set[str] = set()
        result: list[CommandDefinition] = []
        for registered in self._commands.values():
            name = registered.definition.name
            if name not in seen:
                seen.add(name)
                result.append(registered.definition)
        return sorted(result, key=lambda d: d.name)
