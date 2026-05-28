"""Jalali (Shamsi) calendar formatting."""

from __future__ import annotations

from datetime import UTC, datetime

import jdatetime

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

_SEP = " · "


def format_jalali_now(*, at: datetime | None = None) -> str:
    """One-line Jalali date with Finglish weekday and month names."""
    local = (at or datetime.now(tz=UTC)).astimezone()
    jalali = jdatetime.datetime.fromgregorian(datetime=local)
    date_part = jalali.strftime("%Y-%m-%d")
    weekday = _WEEKDAYS_FINGLISH[jalali.weekday()]
    month = _MONTHS_FINGLISH[jalali.month - 1]
    time_part = local.strftime("%H:%M:%S")
    tz_label = local.strftime("%Z") or local.strftime("%z")

    return _SEP.join((date_part, weekday, month, f"{time_part} {tz_label}"))
