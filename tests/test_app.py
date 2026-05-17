from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
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
    assert b'href="/static/platform.css"' in response.data
    assert b'href="/local-sample/"' in response.data
    assert b'href="/about"' in response.data


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


def test_platform_url_prefix_prefixes_generated_links(monkeypatch) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")
    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps=set(),
            url_prefix="/pypoc",
        )
    )

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b'href="/pypoc/static/platform.css"' in response.data
    assert b'href="/pypoc/local-sample/"' in response.data


@pytest.mark.parametrize(
    ("request_path", "expected_status", "expected_body"),
    [
        ("/pypoc/", 200, b"Installed Apps"),
        ("/pypoc/local-sample/", 200, b"local sample"),
        ("/", 200, b"Installed Apps"),
    ],
)
def test_platform_url_prefix_accepts_prefixed_and_upstream_paths(
    monkeypatch,
    request_path: str,
    expected_status: int,
    expected_body: bytes,
) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")
    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps=set(),
            url_prefix="/pypoc",
        )
    )

    response = app.test_client().get(request_path)

    assert response.status_code == expected_status
    assert expected_body in response.data


@pytest.mark.parametrize(
    ("raw_prefix", "expected_prefix"),
    [
        (None, None),
        ("", None),
        ("/pypoc/", "/pypoc"),
        ("/", "/"),
    ],
)
def test_platform_config_normalizes_url_prefix(raw_prefix: str | None, expected_prefix: str | None) -> None:
    assert PlatformConfig(url_prefix=raw_prefix).url_prefix == expected_prefix


def test_platform_config_rejects_invalid_url_prefix() -> None:
    with pytest.raises(ValueError, match="PLATFORM_URL_PREFIX"):
        PlatformConfig(url_prefix="pypoc")


def test_about_page_renders_version_information(monkeypatch) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")
    monkeypatch.setenv("PLATFORM_DEPLOYMENT_NAME", "pypoc-deploy")
    monkeypatch.setenv("PLATFORM_DEPLOYMENT_VERSION", "0.2.3")
    monkeypatch.setenv("PLATFORM_BUILD_SHA", "abcdef1234567890")

    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps=set(),
        )
    )

    response = app.test_client().get("/about")

    assert response.status_code == 200
    assert b"About This Deployment" in response.data
    assert b"pypoc-deploy" in response.data
    assert b"v0.2.3" in response.data
    assert b"abcdef123456" in response.data
    assert b"Local Sample" in response.data


def test_about_page_handles_missing_deployment_metadata(monkeypatch) -> None:
    monkeypatch.syspath_prepend("tests/fixtures")
    monkeypatch.delenv("PLATFORM_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("PLATFORM_DEPLOYMENT_VERSION", raising=False)
    monkeypatch.delenv("PLATFORM_BUILD_SHA", raising=False)

    app = create_app(
        PlatformConfig(
            entry_point_group="tests.none",
            local_plugin_package="local_plugins",
            enabled_apps={"local-sample"},
            disabled_apps=set(),
        )
    )

    response = app.test_client().get("/about")

    assert response.status_code == 200
    assert b"Local host app" in response.data
    assert b"Version not provided by host deployment" in response.data
    assert b"local-dev" not in response.data
    assert b"unknown" not in response.data
