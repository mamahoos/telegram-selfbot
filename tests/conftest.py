"""Pytest fixtures."""

from pathlib import Path

import pytest

from app.config.settings import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings.model_validate(
        {
            "API_ID": 1,
            "API_HASH": "test_hash",
            "PHONE_NUMBER": "+10000000000",
            "SESSION_NAME": "test",
            "LOG_DIR": str(tmp_path / "logs"),
            "DATA_DIR": str(tmp_path / "data"),
            "TEMP_DIR": str(tmp_path / "tmp"),
        },
    )
