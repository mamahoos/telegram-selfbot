"""Jalali date formatting tests."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.common.jalali_datetime import format_jalali_now


def test_format_jalali_known_date_single_line_finglish() -> None:
    moment = datetime(2026, 5, 17, 12, 0, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    text = format_jalali_now(at=moment)
    assert text == "1405-02-27 · Yekshanbe · Ordibehesht · 12:00:00 +0330"
    assert "\n" not in text


def test_format_jalali_uses_middle_dot_separator() -> None:
    text = format_jalali_now()
    assert " · " in text
    assert text.count(" · ") == 3
