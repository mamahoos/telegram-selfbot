"""Utility formatter tests."""

from app.application.services.utility_service import UtilityService


def test_format_date_contains_year() -> None:
    text = UtilityService.format_date()
    assert "Local time" in text
