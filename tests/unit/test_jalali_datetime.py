"""Jalali date formatting tests."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.common.jalali_datetime import format_jalali_now


def test_format_jalali_known_date() -> None:
    # 2026-05-17 12:00 Tehran ≈ 1405-02-27
    moment = datetime(2026, 5, 17, 12, 0, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    text = format_jalali_now(at=moment)
    assert "1405-02-27" in text
    assert "یک‌شنبه" in text
    assert "اردیبهشت" in text
    assert "12:00:00" in text


def test_format_jalali_contains_persian_labels() -> None:
    text = format_jalali_now()
    assert "**تاریخ:**" in text
    assert "**روز:**" in text
    assert "**ماه:**" in text
