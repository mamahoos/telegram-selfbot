"""Telegram user-session client factory."""

from hydrogram import Client

from app.config.settings import Settings


class TelegramClientFactory:
    """Builds configured Hydrogram user clients."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create(self) -> Client:
        self._settings.data_dir.mkdir(parents=True, exist_ok=True)
        return Client(
            name=self._settings.session_name,
            api_id=self._settings.api_id,
            api_hash=self._settings.api_hash,
            phone_number=self._settings.phone_number,
            workdir=str(self._settings.data_dir),
        )
