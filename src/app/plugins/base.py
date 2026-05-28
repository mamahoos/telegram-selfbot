"""Plugin contract."""

from abc import ABC, abstractmethod

from app.application.commands.registry import CommandRegistry
from app.core.container import Container


class Plugin(ABC):
    """Base class for feature plugins."""

    name: str

    def __init__(self, container: Container) -> None:
        self._container = container

    @abstractmethod
    def register(self, registry: CommandRegistry) -> None:
        """Register commands and side effects."""
