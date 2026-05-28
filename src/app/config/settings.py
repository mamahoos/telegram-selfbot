"""Environment-backed application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_id: int = Field(..., alias="API_ID")
    api_hash: str = Field(..., alias="API_HASH")
    phone_number: str = Field(..., alias="PHONE_NUMBER")
    session_name: str = Field(default="selfbot", alias="SESSION_NAME")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: Path = Field(default=Path("logs"), alias="LOG_DIR")
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    temp_dir: Path = Field(default=Path("tmp"), alias="TEMP_DIR")

    reaction_cooldown_seconds: float = Field(default=2.0, alias="REACTION_COOLDOWN_SECONDS")
    reaction_max_retries: int = Field(default=3, alias="REACTION_MAX_RETRIES")
    reaction_fallback_emojis: str = Field(
        default="👍,🔥,❤️,😂,🎉",
        alias="REACTION_FALLBACK_EMOJIS",
    )

    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")
    ffmpeg_timeout_seconds: int = Field(default=120, alias="FFMPEG_TIMEOUT_SECONDS")
    sticker_max_dimension: int = Field(default=512, alias="STICKER_MAX_DIMENSION")
    gif_max_width: int = Field(default=480, alias="GIF_MAX_WIDTH")
    gif_fps: int = Field(default=15, alias="GIF_FPS")

    @field_validator("log_dir", "data_dir", "temp_dir", mode="before")
    @classmethod
    def _coerce_path(cls, value: str | Path) -> Path:
        return Path(value)

    @property
    def fallback_emoji_list(self) -> list[str]:
        return [e.strip() for e in self.reaction_fallback_emojis.split(",") if e.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
