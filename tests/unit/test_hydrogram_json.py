"""Serializer tests."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from app.infrastructure.serialization.hydrogram_json import hydrogram_to_jsonable


class _Color(Enum):
    RED = "red"


class _Node:
    __slots__ = ("child", "name")

    def __init__(self, name: str, child: _Node | None = None) -> None:
        self.name = name
        self.child = child


def test_primitives_and_enums() -> None:
    assert hydrogram_to_jsonable(None) is None
    assert hydrogram_to_jsonable(_Color.RED) == "red"
    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert hydrogram_to_jsonable(moment) == "2026-01-02T03:04:05+00:00"
    assert hydrogram_to_jsonable(b"\xab\xcd") == "abcd"


def test_slots_and_recursion() -> None:
    root = _Node("root")
    root.child = root
    data = hydrogram_to_jsonable(root)
    assert data == {"name": "root", "child": "<recursion>"}
