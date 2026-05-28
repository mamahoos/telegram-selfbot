"""Jalali (Shamsi) calendar formatting."""

from __future__ import annotations

from datetime import UTC, datetime

import jdatetime


def format_jalali_now(*, at: datetime | None = None) -> str:
    """Format local time with Jalali date, Persian weekday, and month name."""
    local = (at or datetime.now(tz=UTC)).astimezone()
    jalali = jdatetime.datetime.fromgregorian(datetime=local)
    date_line = jalali.strftime("%Y-%m-%d")
    weekday = jdatetime.date.j_weekdays_fa[jalali.weekday()]
    month = jdatetime.date.j_months_fa[jalali.month - 1]
    time_line = local.strftime("%H:%M:%S")
    tz_label = local.strftime("%Z") or local.strftime("%z")

    return (
        f"**تاریخ:** `{date_line}`\n"
        f"**روز:** {weekday}\n"
        f"**ماه:** {month}\n"
        f"**ساعت:** `{time_line}` {tz_label}"
    )
