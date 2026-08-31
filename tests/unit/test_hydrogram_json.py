"""Serializer tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import Enum

from hydrogram import enums

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


def test_enum_with_type_value_is_json_safe() -> None:
    data = hydrogram_to_jsonable(enums.ChatAction.TYPING)
    assert isinstance(data, str)
    assert data.endswith("SendMessageTypingAction")
    json.dumps({"action": enums.ChatAction.TYPING}, default=str)  # sanity
    payload = {"action": hydrogram_to_jsonable(enums.ChatAction.TYPING)}
    json.dumps(payload)


def test_type_objects_serialize_to_qualified_name() -> None:
    assert hydrogram_to_jsonable(str) == "builtins.str"
