"""One-time interactive login. Creates the Telegram session file and exits.

Run this once, interactively, before starting the bot in detached mode:

    docker compose run --rm selfbot python -m app.login

`docker compose run` allocates a TTY and attaches your terminal automatically,
so the phone-code / 2FA prompts reach you even though `docker compose up -d`
never will. The resulting *.session file lands in the mounted session volume,
so `docker compose up -d` afterwards starts non-interactively and reuses it.
"""

import sys

from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.infrastructure.hydrogram.client_factory import TelegramClientFactory

logger = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(level=settings.log_level, log_dir=settings.log_dir)

    factory = TelegramClientFactory(settings)

    if factory.session_file_exists():
        logger.info(
            "Session already exists at %s — nothing to do. Delete it first "
            "if you need to re-authenticate.",
            settings.session_dir / f"{settings.session_name}.session",
        )
        return

    if not sys.stdin.isatty():
        logger.error(
            "Login needs an interactive terminal. Run with "
            "'docker compose run --rm selfbot python -m app.login' "
            "(not 'up')."
        )
        raise SystemExit(1)

    client = factory.create()
    client.start()
    me = client.get_me()
    client.stop()
    logger.info("Logged in as %s (id=%s). Session saved to %s.", me.first_name, me.id, settings.session_dir)


if __name__ == "__main__":
    main()
