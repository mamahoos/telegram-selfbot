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
        default="👍,❤️,😂,😮,😢,🙏",
        alias="REACTION_FALLBACK_EMOJIS",
    )

    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")
    ffmpeg_timeout_seconds: int = Field(default=120, alias="FFMPEG_TIMEOUT_SECONDS")
    sticker_max_dimension: int = Field(default=512, alias="STICKER_MAX_DIMENSION")
    gif_max_width: int = Field(default=480, alias="GIF_MAX_WIDTH")
    gif_fps: int = Field(default=15, alias="GIF_FPS")

    stream_edit_delay_seconds: float = Field(default=0.5, alias="STREAM_EDIT_DELAY_SECONDS")
    stream_edit_max_retries: int = Field(default=3, alias="STREAM_EDIT_MAX_RETRIES")

    video_note_size: int = Field(default=640, alias="VIDEO_NOTE_SIZE")
    video_note_fps: int = Field(default=30, alias="VIDEO_NOTE_FPS")

    voice_bitrate_kbps: int = Field(default=64, alias="VOICE_BITRATE_KBPS")

    awk_path: str = Field(default="awk", alias="AWK_PATH")
    awk_timeout_seconds: int = Field(default=30, alias="AWK_TIMEOUT_SECONDS")
    awk_max_output_chars: int = Field(default=3800, alias="AWK_MAX_OUTPUT_CHARS")

    json_inline_max_chars: int = Field(default=3800, alias="JSON_INLINE_MAX_CHARS")

    tag_max_mentions_per_message: int = Field(default=50, alias="TAG_MAX_MENTIONS_PER_MESSAGE")
    tag_max_utf16_per_message: int = Field(default=3900, alias="TAG_MAX_UTF16_PER_MESSAGE")

    discuss_profile_path: Path = Field(
        default=Path("data/profile.md"),
        alias="DISCUSS_PROFILE_PATH",
    )
    discuss_cognitive_profile_path: Path = Field(
        default=Path("data/cognitive-profile.md"),
        alias="DISCUSS_COGNITIVE_PROFILE_PATH",
    )
    discuss_voice_path: Path = Field(
        default=Path("data/telegram-voice/voice.compact.txt"),
        alias="DISCUSS_VOICE_PATH",
    )

    llm_api_base_url: str = Field(
        default="http://127.0.0.1:3001/v1",
        alias="LLM_API_BASE_URL",
    )
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="auto", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=120.0, alias="LLM_TIMEOUT_SECONDS")
    ai_max_tokens: int = Field(default=2000, alias="AI_MAX_TOKENS")

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
