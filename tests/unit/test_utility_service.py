"""Utility formatter tests."""

from app.application.services.utility_service import UtilityService


def test_format_date_single_line() -> None:
    text = UtilityService.format_date()
    assert "\n" not in text
    assert " · " in text
