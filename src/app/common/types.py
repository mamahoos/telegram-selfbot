"""Shared type aliases."""

from collections.abc import Awaitable, Callable

from hydrogram import Client
from hydrogram.types import Message

type TelegramClient = Client
type CommandHandler = Callable[[Client, Message], Awaitable[None]]
