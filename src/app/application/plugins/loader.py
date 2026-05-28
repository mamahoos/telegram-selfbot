"""Discover and register built-in plugins."""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

from app.application.commands.registry import CommandRegistry
from app.core.container import Container
from app.plugins.base import Plugin


def _iter_plugin_modules(package: ModuleType) -> list[ModuleType]:
    modules: list[ModuleType] = []
    for info in pkgutil.iter_modules(package.__path__):
        if info.name in {"base", "__pycache__"}:
            continue
        modules.append(importlib.import_module(f"{package.__name__}.{info.name}"))
    return modules


def discover_and_register_plugins(
    container: Container,
    registry: CommandRegistry,
) -> list[Plugin]:
    """Import plugin packages and invoke register()."""
    import app.plugins as plugins_package

    loaded: list[Plugin] = []
    for module in _iter_plugin_modules(plugins_package):
        plugin_cls = getattr(module, "PluginImpl", None)
        if plugin_cls is None:
            continue
        plugin: Plugin = plugin_cls(container)
        plugin.register(registry)
        loaded.append(plugin)
    return loaded
