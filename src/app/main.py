"""CLI entrypoint for the Telegram selfbot."""

import sys

from app.bootstrap import build_container, create_client, wire_handlers
from app.core.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    container = build_container()

    if not container.client_factory.session_file_exists() and not sys.stdin.isatty():
        logger.error(
            "No authorized session found and stdin is not interactive. "
            "Run the one-time login first: "
            "docker compose run --rm selfbot python -m app.login"
        )
        raise SystemExit(1)

    client = create_client(container)
    wire_handlers(container, client)
    logger.info("Starting selfbot session")
    client.run()


if __name__ == "__main__":
    main()
