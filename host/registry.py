from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Iterable
from dataclasses import dataclass
from types import ModuleType
from typing import Any

from flask import Blueprint

from host.config import PlatformConfig


class PluginError(RuntimeError):
    """Raised when plugin discovery or validation fails."""


@dataclass(frozen=True)
class MenuEntry:
    label: str
    icon: str
    path: str


@dataclass(frozen=True)
class Plugin:
    id: str
    name: str
    description: str
    version: str
    blueprint: Blueprint
    menu_entry: MenuEntry | None = None


class PluginRegistry:
    def __init__(self, config: PlatformConfig) -> None:
        self._config = config
        self._plugins: dict[str, Plugin] = {}

    @property
    def plugins(self) -> tuple[Plugin, ...]:
        return tuple(sorted(self._plugins.values(), key=lambda plugin: plugin.name.lower()))

    @property
    def menu_entries(self) -> tuple[MenuEntry, ...]:
        return tuple(plugin.menu_entry for plugin in self.plugins if plugin.menu_entry is not None)

    def discover(self) -> tuple[Plugin, ...]:
        for module in discover_plugin_modules(self._config.plugin_package):
            plugin = load_plugin(module)
            if self._config.is_enabled(plugin.id):
                self.register(plugin)
        return self.plugins

    def register(self, plugin: Plugin) -> None:
        if plugin.id in self._plugins:
            raise PluginError(f"Duplicate plugin id: {plugin.id}")
        self._plugins[plugin.id] = plugin


def discover_plugin_modules(package_name: str) -> Iterable[ModuleType]:
    try:
        package = importlib.import_module(package_name)
    except ImportError as exc:
        raise PluginError(f"Could not import plugin package {package_name!r}") from exc

    package_paths = getattr(package, "__path__", None)
    if package_paths is None:
        raise PluginError(f"Plugin package {package_name!r} is not a package")

    for module_info in pkgutil.iter_modules(package_paths, prefix=f"{package_name}."):
        if not module_info.ispkg:
            continue
        module_name = f"{module_info.name}.plugin"
        try:
            yield importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                continue
            raise


def load_plugin(module: ModuleType) -> Plugin:
    raw_plugin = getattr(module, "PLUGIN", None)
    if raw_plugin is None:
        raise PluginError(f"{module.__name__} does not expose PLUGIN")
    if not isinstance(raw_plugin, dict):
        raise PluginError(f"{module.__name__}.PLUGIN must be a dict")
    return parse_plugin(raw_plugin, module.__name__)


def parse_plugin(raw_plugin: dict[str, Any], source: str) -> Plugin:
    required = ("id", "name", "description", "version", "blueprint")
    missing = [key for key in required if key not in raw_plugin]
    if missing:
        raise PluginError(f"{source}.PLUGIN missing required keys: {', '.join(missing)}")

    blueprint = raw_plugin["blueprint"]
    if not isinstance(blueprint, Blueprint):
        raise PluginError(f"{source}.PLUGIN['blueprint'] must be a Flask Blueprint")

    menu_entry = raw_plugin.get("menu_entry")
    parsed_menu = parse_menu_entry(menu_entry, source) if menu_entry is not None else None

    return Plugin(
        id=parse_non_empty_string(raw_plugin["id"], "id", source),
        name=parse_non_empty_string(raw_plugin["name"], "name", source),
        description=parse_non_empty_string(raw_plugin["description"], "description", source),
        version=parse_non_empty_string(raw_plugin["version"], "version", source),
        blueprint=blueprint,
        menu_entry=parsed_menu,
    )


def parse_menu_entry(menu_entry: Any, source: str) -> MenuEntry:
    if not isinstance(menu_entry, dict):
        raise PluginError(f"{source}.PLUGIN['menu_entry'] must be a dict")

    required = ("label", "icon", "path")
    missing = [key for key in required if key not in menu_entry]
    if missing:
        raise PluginError(f"{source}.PLUGIN['menu_entry'] missing keys: {', '.join(missing)}")

    path = parse_non_empty_string(menu_entry["path"], "menu_entry.path", source)
    if not path.startswith("/"):
        raise PluginError(f"{source}.PLUGIN['menu_entry']['path'] must start with '/'")

    return MenuEntry(
        label=parse_non_empty_string(menu_entry["label"], "menu_entry.label", source),
        icon=parse_non_empty_string(menu_entry["icon"], "menu_entry.icon", source),
        path=path,
    )


def parse_non_empty_string(value: Any, field_name: str, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PluginError(f"{source}.PLUGIN['{field_name}'] must be a non-empty string")
    return value
