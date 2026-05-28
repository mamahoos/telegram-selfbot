"""Application bootstrap and wiring."""

from hydrogram import Client

from app.application.plugins.loader import discover_and_register_plugins
from app.config.settings import Settings, get_settings
from app.core.container import Container
from app.core.logging import configure_logging, get_logger
from app.presentation.handlers.message_router import MessageRouter

logger = get_logger(__name__)


def build_container(settings: Settings | None = None) -> Container:
    resolved = settings or get_settings()
    configure_logging(level=resolved.log_level, log_dir=resolved.log_dir)
    container = Container(settings=resolved)
    plugins = discover_and_register_plugins(container, container.command_registry)
    logger.info(
        "Plugins loaded",
        extra={"plugin": ",".join(p.name for p in plugins)},
    )
    return container


def create_client(container: Container) -> Client:
    return container.client_factory.create()


def wire_handlers(container: Container, client: Client) -> MessageRouter:
    router = MessageRouter(container)
    router.register(client)
    return router
