from __future__ import annotations

from dataclasses import replace
from pathlib import Path

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


def test_create_app_loads_prefixed_env_values_into_app_config(monkeypatch) -> None:
    monkeypatch.setenv("PLATFORM_APP_CONFIG_PREFIXES", "PYDO, PYTODO_")
    monkeypatch.setenv("PYDO_DATA_DIR", "/var/lib/pydo")
    monkeypatch.setenv("PYDO_TODO_FILE", "/var/lib/pydo/todos.json")
    monkeypatch.setenv("PYTODO_PASSWORD_HASH", "scrypt$example")
    monkeypatch.setenv("UNRELATED_SETTING", "ignored")

    app = create_app(replace(PlatformConfig.from_env(), entry_point_group="tests.none"))

    assert app.config["PYDO_DATA_DIR"] == "/var/lib/pydo"
    assert app.config["PYDO_TODO_FILE"] == "/var/lib/pydo/todos.json"
    assert app.config["PYTODO_PASSWORD_HASH"] == "scrypt$example"
    assert "UNRELATED_SETTING" not in app.config


def test_platform_config_can_set_instance_path_from_env(monkeypatch, tmp_path: Path) -> None:
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    monkeypatch.setenv("PLATFORM_INSTANCE_PATH", str(instance_dir))

    app = create_app(replace(PlatformConfig.from_env(), entry_point_group="tests.none"))

    assert app.instance_path == str(instance_dir)


def test_explicit_platform_config_app_config_is_applied() -> None:
    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            app_config={"PYDO_DATA_DIR": "/srv/pydo", "PYTODO_PASSWORD_HASH": "hash"},
        )
    )

    assert app.config["PYDO_DATA_DIR"] == "/srv/pydo"
    assert app.config["PYTODO_PASSWORD_HASH"] == "hash"
