"""Utility formatter tests."""

from app.application.services.utility_service import UtilityService


def test_format_date_uses_jalali_labels() -> None:
    text = UtilityService.format_date()
    assert "**تاریخ:**" in text
    assert "**روز:**" in text
