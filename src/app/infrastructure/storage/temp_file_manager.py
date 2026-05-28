"""Managed temporary files with guaranteed cleanup."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path


class TempFileManager:
    """Creates namespaced temp files under a root directory."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def _unique_path(self, suffix: str) -> Path:
        return self._root / f"{uuid.uuid4().hex}{suffix}"

    @asynccontextmanager
    async def file(self, suffix: str) -> AsyncIterator[Path]:
        path = self._unique_path(suffix)
        try:
            yield path
        finally:
            await self._safe_unlink(path)

    @asynccontextmanager
    async def directory(self) -> AsyncIterator[Path]:
        path = self._root / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=True)
        try:
            yield path
        finally:
            await asyncio.to_thread(self._rmtree, path)

    async def _safe_unlink(self, path: Path) -> None:
        if not path.exists():
            return
        await asyncio.to_thread(path.unlink, missing_ok=True)

    @staticmethod
    def _rmtree(path: Path) -> None:
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
