"""JSON file state store with asyncio lock."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, TypeVar, cast

from app.common.exceptions import StorageError

T = TypeVar("T")


class JsonStateStore:
    """Thread-safe async JSON persistence."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._cache: dict[str, Any] | None = None

    async def _load(self) -> dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if not self._path.exists():
            self._cache = {}
            return self._cache
        try:
            raw = await asyncio.to_thread(self._path.read_text, encoding="utf-8")
            self._cache = json.loads(raw) if raw.strip() else {}
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError("Failed to load state file", cause=exc) from exc
        return self._cache

    async def _persist(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=False)

        def _write() -> None:
            self._path.write_text(payload, encoding="utf-8")

        try:
            await asyncio.to_thread(_write)
            self._cache = data
        except OSError as exc:
            raise StorageError("Failed to persist state file", cause=exc) from exc

    async def get(self, key: str, default: T) -> T:
        async with self._lock:
            data = await self._load()
            return cast(T, data.get(key, default))

    async def set(self, key: str, value: T) -> None:
        async with self._lock:
            data = await self._load()
            data[key] = value
            await self._persist(data)
