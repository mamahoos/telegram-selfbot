"""Reaction emoji parsing tests."""

from hydrogram.raw import types

from app.infrastructure.hydrogram.reaction_emoji_source import (
    emojis_from_available_reactions,
    emojis_from_chat_reactions,
)


def test_emojis_from_chat_reactions_some() -> None:
    available = types.ChatReactionsSome(
        reactions=[
            types.ReactionEmoji(emoticon="👍"),
            types.ReactionEmoji(emoticon="❤️"),
        ],
    )
    assert emojis_from_chat_reactions(available) == ["👍", "❤️"]


def test_emojis_from_chat_reactions_all_returns_none() -> None:
    assert emojis_from_chat_reactions(types.ChatReactionsAll()) is None


def test_emojis_from_available_reactions_skips_premium() -> None:
    payload = types.messages.AvailableReactions(
        hash=1,
        reactions=[
            types.AvailableReaction(
                reaction=types.ReactionEmoji(emoticon="👍"),
                title="like",
                static_icon=types.DocumentEmpty(id=1),
                appear_animation=types.DocumentEmpty(id=2),
                select_animation=types.DocumentEmpty(id=3),
                activate_animation=types.DocumentEmpty(id=4),
                effect_animation=types.DocumentEmpty(id=5),
                inactive=False,
                premium=False,
            ),
            types.AvailableReaction(
                reaction=types.ReactionEmoji(emoticon="💎"),
                title="premium",
                static_icon=types.DocumentEmpty(id=6),
                appear_animation=types.DocumentEmpty(id=7),
                select_animation=types.DocumentEmpty(id=8),
                activate_animation=types.DocumentEmpty(id=9),
                effect_animation=types.DocumentEmpty(id=10),
                inactive=False,
                premium=True,
            ),
        ],
    )
    assert emojis_from_available_reactions(payload) == ["👍"]
