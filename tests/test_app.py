from __future__ import annotations

from flask import Blueprint

from flask_plugin_platform.app import create_app
from flask_plugin_platform.config import PlatformConfig


def test_create_app_registers_local_plugin_blueprints(monkeypatch) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")

    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps=set(),
        )
    )

    assert "local_sample" in app.blueprints


def test_index_renders_enabled_local_plugins(monkeypatch) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")
    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps=set(),
        )
    )

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Local Sample" in response.data


def test_plugin_route_is_available(monkeypatch) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")
    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps=set(),
        )
    )

    response = app.test_client().get("/local-sample/")

    assert response.status_code == 200
    assert b"local sample" in response.data


def test_disabled_plugin_route_is_not_registered(monkeypatch) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")
    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps={"local-sample"},
        )
    )

    response = app.test_client().get("/local-sample/")

    assert response.status_code == 404


def test_entry_point_plugin_blueprint_is_registered(monkeypatch) -> None:
    blueprint = Blueprint("entry_sample", __name__, url_prefix="/entry-sample")

    @blueprint.get("/")
    def index() -> str:
        return "entry sample"

    plugin = {
        "id": "entry-sample",
        "name": "Entry Sample",
        "description": "Entry point sample plugin",
        "version": "0.1.0",
        "blueprint": blueprint,
        "menu_entry": {
            "label": "Entry Sample",
            "icon": "plug",
            "path": "/entry-sample/",
        },
    }

    class FakeEntryPoint:
        name = "entry-sample"
        group = "flask_plugin_platform.plugins"

        def load(self):
            return plugin

    class FakeEntryPoints:
        def select(self, group: str):
            return [FakeEntryPoint()] if group == "flask_plugin_platform.plugins" else []

    monkeypatch.setattr("importlib.metadata.entry_points", lambda: FakeEntryPoints())

    app = create_app(PlatformConfig(enabled_apps={"entry-sample"}, disabled_apps=set()))

    assert app.test_client().get("/entry-sample/").data == b"entry sample"
