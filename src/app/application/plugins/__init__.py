"""Plugin loading."""

from app.application.plugins.loader import discover_and_register_plugins

__all__ = ["discover_and_register_plugins"]
