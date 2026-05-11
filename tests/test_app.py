from __future__ import annotations

from host.app import create_app
from host.config import PlatformConfig


def test_create_app_registers_discovered_blueprints() -> None:
    app = create_app(PlatformConfig(enabled_apps={"notes", "analytics"}, disabled_apps=set()))

    assert "notes" in app.blueprints
    assert "analytics" in app.blueprints


def test_index_renders_enabled_plugins() -> None:
    app = create_app(PlatformConfig(enabled_apps={"notes"}, disabled_apps=set()))

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Notes" in response.data
    assert b"Analytics" not in response.data


def test_plugin_route_is_available() -> None:
    app = create_app(PlatformConfig(enabled_apps={"notes"}, disabled_apps=set()))

    response = app.test_client().get("/notes/")

    assert response.status_code == 200
    assert b"Sample first-party app" in response.data


def test_disabled_plugin_route_is_not_registered() -> None:
    app = create_app(PlatformConfig(enabled_apps={"notes"}, disabled_apps={"notes"}))

    response = app.test_client().get("/notes/")

    assert response.status_code == 404
