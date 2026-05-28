"""Generic key-value state persistence contract."""

from typing import Protocol, TypeVar

T = TypeVar("T")


class StateRepository(Protocol):
    """Async JSON-backed state access."""

    async def get(self, key: str, default: T) -> T: ...

    async def set(self, key: str, value: T) -> None: ...
