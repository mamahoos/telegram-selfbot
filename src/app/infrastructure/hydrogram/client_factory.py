"""Telegram user-session client factory."""

from hydrogram import Client

from app.config.settings import Settings


class TelegramClientFactory:
    """Builds configured Hydrogram user clients."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create(self) -> Client:
        self._settings.session_dir.mkdir(parents=True, exist_ok=True)
        return Client(
            name=self._settings.session_name,
            api_id=self._settings.api_id,
            api_hash=self._settings.api_hash,
            phone_number=self._settings.phone_number,
            workdir=str(self._settings.session_dir),
        )

    def session_file_exists(self) -> bool:
        """True if an authorized session already exists on disk."""
        return (self._settings.session_dir / f"{self._settings.session_name}.session").exists()
