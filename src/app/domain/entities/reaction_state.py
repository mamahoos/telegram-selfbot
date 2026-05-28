"""Per-chat auto-reaction state."""

from dataclasses import dataclass


@dataclass(slots=True)
class ReactionChatState:
    """Whether auto-reactions are enabled for a chat."""

    chat_id: int
    enabled: bool = False
