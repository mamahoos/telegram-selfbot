"""Jalali (Shamsi) calendar formatting."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import jdatetime

_TEHRAN = ZoneInfo("Asia/Tehran")

_WEEKDAYS_FINGLISH: tuple[str, ...] = (
    "Shanbe",
    "Yekshanbe",
    "Doshanbe",
    "Seshanbe",
    "Chaharshanbe",
    "Panjshanbe",
    "Jomee",
)

_MONTHS_FINGLISH: tuple[str, ...] = (
    "Farvardin",
    "Ordibehesht",
    "Khordad",
    "Tir",
    "Mordad",
    "Shahrivar",
    "Mehr",
    "Aban",
    "Azar",
    "Dey",
    "Bahman",
    "Esfand",
)


def format_jalali_now(*, at: datetime | None = None) -> str:
    """One-line Jalali date with Finglish weekday and month names (no time)."""
    local = (at or datetime.now(tz=_TEHRAN)).astimezone(_TEHRAN)
    jalali = jdatetime.datetime.fromgregorian(datetime=local)
    weekday = _WEEKDAYS_FINGLISH[jalali.weekday()]
    month = _MONTHS_FINGLISH[jalali.month - 1]
    return f"{weekday}, {jalali.day} {month} {jalali.year}"
