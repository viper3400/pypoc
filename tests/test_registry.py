from __future__ import annotations

import pytest
from flask import Blueprint

from host.config import PlatformConfig
from host.registry import PluginError, PluginRegistry, parse_plugin


def test_registry_discovers_enabled_first_party_plugins() -> None:
    registry = PluginRegistry(PlatformConfig(enabled_apps={"notes"}, disabled_apps=set()))

    plugins = registry.discover()

    assert [plugin.id for plugin in plugins] == ["notes"]
    assert [entry.path for entry in registry.menu_entries] == ["/notes/"]


def test_disabled_apps_are_filtered_after_allowlist() -> None:
    registry = PluginRegistry(
        PlatformConfig(enabled_apps={"notes", "analytics"}, disabled_apps={"analytics"})
    )

    plugins = registry.discover()

    assert [plugin.id for plugin in plugins] == ["notes"]


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
