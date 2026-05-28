"""Restrict commands to the account owner."""

from hydrogram.types import Message


class OwnerFilter:
    """Detects outgoing selfbot commands."""

    def __init__(self) -> None:
        self._owner_id: int | None = None

    async def bind_owner(self, owner_id: int) -> None:
        self._owner_id = owner_id

    def is_owner_command(self, message: Message) -> bool:
        if not message.outgoing:
            return False
        text = message.text or message.caption or ""
        return text.strip().startswith(".")

    async def is_owner(self, message: Message) -> bool:
        """Selfbot commands are only accepted from outgoing messages."""
        _ = self._owner_id
        return bool(message.outgoing)
