"""CLI entrypoint for the Telegram selfbot."""

from app.bootstrap import build_container, create_client, wire_handlers
from app.core.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    container = build_container()
    client = create_client(container)
    wire_handlers(container, client)
    logger.info("Starting selfbot session")
    client.run()


if __name__ == "__main__":
    main()
