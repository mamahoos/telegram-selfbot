"""Jalali date formatting tests."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.common.jalali_datetime import format_jalali_now


def test_format_jalali_known_date_single_line_finglish() -> None:
    moment = datetime(2026, 5, 17, 12, 0, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    text = format_jalali_now(at=moment)
    assert text == "Yekshanbe, 27 Ordibehesht 1405"
    assert "\n" not in text
    assert ":" not in text


def test_format_jalali_no_time_components() -> None:
    text = format_jalali_now()
    assert "\n" not in text
    assert "+" not in text
    parts = text.split(", ", 1)
    assert len(parts) == 2
    assert parts[1].count(" ") == 2  # day month year
