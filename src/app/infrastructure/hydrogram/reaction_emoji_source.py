"""Parse allowed reaction emojis from Hydrogram raw API types."""

from __future__ import annotations

from hydrogram import raw


def emojis_from_available_reactions(
    payload: raw.types.messages.AvailableReactions
    | raw.types.messages.AvailableReactionsNotModified,
) -> list[str]:
    """Extract non-premium emoji from messages.getAvailableReactions."""
    if isinstance(payload, raw.types.messages.AvailableReactionsNotModified):
        return []
    result: list[str] = []
    for item in payload.reactions:
        if item.inactive or item.premium:
            continue
        emoticon = getattr(item.reaction, "emoticon", None)
        if isinstance(emoticon, str) and emoticon:
            result.append(emoticon)
    return result


def emojis_from_chat_reactions(available: object | None) -> list[str] | None:
    """Return emoji list, None if all reactions are allowed, [] if disabled."""
    if available is None:
        return None
    if isinstance(available, raw.types.ChatReactionsAll):
        return None
    if isinstance(available, raw.types.ChatReactionsNone):
        return []
    if isinstance(available, raw.types.ChatReactionsSome):
        result: list[str] = []
        for reaction in available.reactions:
            if isinstance(reaction, raw.types.ReactionEmoji):
                result.append(reaction.emoticon)
        return result
    return None
