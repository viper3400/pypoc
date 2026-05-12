from __future__ import annotations

from typing import Any

import pytest
from flask import Blueprint

from flask_plugin_platform.config import PlatformConfig
from flask_plugin_platform.registry import (
    PluginError,
    PluginRegistry,
    discover_entry_point_plugins,
    parse_plugin,
)


class FakeEntryPoint:
    def __init__(self, name: str, group: str, plugin: dict[str, Any]) -> None:
        self.name = name
        self.group = group
        self._plugin = plugin

    def load(self) -> dict[str, Any]:
        return self._plugin


class FakeEntryPoints:
    def __init__(self, entry_points: list[FakeEntryPoint]) -> None:
        self._entry_points = entry_points

    def select(self, group: str) -> list[FakeEntryPoint]:
        return [entry_point for entry_point in self._entry_points if entry_point.group == group]


def plugin_dict(plugin_id: str, name: str | None = None) -> dict[str, Any]:
    display_name = name or plugin_id.title()
    blueprint = Blueprint(plugin_id, __name__, url_prefix=f"/{plugin_id}")
    return {
        "id": plugin_id,
        "name": display_name,
        "description": f"{display_name} plugin",
        "version": "0.1.0",
        "blueprint": blueprint,
        "menu_entry": {
            "label": display_name,
            "icon": "plug",
            "path": f"/{plugin_id}/",
        },
    }


def test_entry_point_plugins_are_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    entry_points = FakeEntryPoints(
        [
            FakeEntryPoint("notes", "flask_plugin_platform.plugins", plugin_dict("notes")),
            FakeEntryPoint("ignored", "other.group", plugin_dict("ignored")),
        ]
    )
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entry_points)

    plugins = list(discover_entry_point_plugins())

    assert [plugin.id for plugin in plugins] == ["notes"]


def test_registry_filters_entry_point_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    entry_points = FakeEntryPoints(
        [
            FakeEntryPoint("notes", "flask_plugin_platform.plugins", plugin_dict("notes")),
            FakeEntryPoint("analytics", "flask_plugin_platform.plugins", plugin_dict("analytics")),
        ]
    )
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entry_points)
    registry = PluginRegistry(
        PlatformConfig(enabled_apps={"notes", "analytics"}, disabled_apps={"analytics"})
    )

    plugins = registry.discover()

    assert [plugin.id for plugin in plugins] == ["notes"]


def test_registry_can_discover_local_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: FakeEntryPoints([]))
    registry = PluginRegistry(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps=set(),
        )
    )

    plugins = registry.discover()

    assert [plugin.id for plugin in plugins] == ["local-sample"]
    assert [entry.path for entry in registry.menu_entries] == ["/local-sample/"]


def test_plugin_validation_rejects_missing_required_keys() -> None:
    with pytest.raises(PluginError, match="missing required keys"):
        parse_plugin({"id": "broken"}, "tests.fake")


def test_plugin_validation_requires_blueprint() -> None:
    raw_plugin = {
        "id": "broken",
        "name": "Broken",
        "description": "Invalid plugin",
        "version": "0.1.0",
        "blueprint": object(),
    }

    with pytest.raises(PluginError, match="Flask Blueprint"):
        parse_plugin(raw_plugin, "tests.fake")


def test_plugin_validation_accepts_valid_plugin() -> None:
    blueprint = Blueprint("valid", __name__)

    plugin = parse_plugin(
        {
            "id": "valid",
            "name": "Valid",
            "description": "Valid plugin",
            "version": "0.1.0",
            "blueprint": blueprint,
            "menu_entry": {"label": "Valid", "icon": "check", "path": "/valid/"},
        },
        "tests.fake",
    )

    assert plugin.id == "valid"
    assert plugin.blueprint is blueprint
    assert plugin.menu_entry is not None
    assert plugin.menu_entry.path == "/valid/"
