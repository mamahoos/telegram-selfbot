"""OpenAI-compatible chat completions client (FreeLLMAPI, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

import httpx

ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


@dataclass(frozen=True, slots=True)
class OpenAiChatConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float


class OpenAiChatClient:
    """Async client for /v1/chat/completions endpoints."""

    def __init__(self, config: OpenAiChatConfig) -> None:
        self._config = config
        self._endpoint = config.base_url.rstrip("/") + "/chat/completions"

    @property
    def enabled(self) -> bool:
        return bool(self._config.api_key.strip())

    @property
    def model(self) -> str:
        return self._config.model

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {
            "model": self._config.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=self._config.timeout_seconds) as client:
            response = await client.post(self._endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            msg = "LLM response missing choices"
            raise RuntimeError(msg)

        first = choices[0]
        if not isinstance(first, dict):
            msg = "LLM response choice has invalid shape"
            raise RuntimeError(msg)

        message = first.get("message")
        if not isinstance(message, dict):
            msg = "LLM response missing message"
            raise RuntimeError(msg)

        content = message.get("content")
        if not isinstance(content, str):
            msg = "LLM response missing text content"
            raise RuntimeError(msg)

        return content.strip()
