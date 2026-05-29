"""Restrict commands to the account owner."""

from hydrogram.types import Message

from app.common.chat_context import is_owner_command_message


class OwnerFilter:
    """Detects selfbot commands (outgoing or Saved Messages)."""

    def __init__(self) -> None:
        self._owner_id: int | None = None

    async def bind_owner(self, owner_id: int) -> None:
        self._owner_id = owner_id

    def is_owner_command(self, message: Message) -> bool:
        return is_owner_command_message(message, self._owner_id)

    async def is_owner(self, message: Message) -> bool:
        """Commands from this account only (including Saved Messages)."""
        return is_owner_command_message(message, self._owner_id)
