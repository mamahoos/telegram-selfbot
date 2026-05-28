"""Convert Hydrogram / MTProto objects to JSON-safe structures."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any


def hydrogram_to_jsonable(obj: Any, *, _seen: set[int] | None = None) -> Any:
    """Recursively serialize Hydrogram types, enums, and nested values."""
    if obj is None or isinstance(obj, str | int | float | bool):
        return obj
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, bytes):
        return obj.hex()
    if isinstance(obj, list | tuple):
        return [hydrogram_to_jsonable(item, _seen=_seen) for item in obj]
    if isinstance(obj, dict):
        return {str(key): hydrogram_to_jsonable(value, _seen=_seen) for key, value in obj.items()}

    seen = _seen if _seen is not None else set()
    object_id = id(obj)
    if object_id in seen:
        return "<recursion>"
    seen.add(object_id)
    try:
        if hasattr(obj, "__slots__"):
            return {
                name: hydrogram_to_jsonable(getattr(obj, name, None), _seen=seen)
                for name in obj.__slots__
                if not name.startswith("_")
            }
        if hasattr(obj, "__dict__"):
            return {
                key: hydrogram_to_jsonable(value, _seen=seen)
                for key, value in vars(obj).items()
                if not key.startswith("_")
            }
        return str(obj)
    finally:
        seen.discard(object_id)
