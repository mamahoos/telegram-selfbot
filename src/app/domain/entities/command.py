"""Command domain model."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    """Metadata for a registered dot-command."""

    name: str
    description: str
    plugin: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    owner_only: bool = True

    @property
    def triggers(self) -> tuple[str, ...]:
        base = (f".{self.name}",)
        return base + tuple(f".{alias}" for alias in self.aliases)
