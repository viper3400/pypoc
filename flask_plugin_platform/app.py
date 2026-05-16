from __future__ import annotations

from flask import Flask, render_template, request

from flask_plugin_platform.config import PlatformConfig
from flask_plugin_platform.middleware import PrefixMiddleware
from flask_plugin_platform.registry import PluginRegistry


def _prefix_menu_path(path: str) -> str:
    script_root = request.script_root.rstrip("/")
    if not script_root:
        return path
    if path == "/":
        return script_root or "/"
    return f"{script_root}{path}"


def create_app(config: PlatformConfig | None = None) -> Flask:
    platform_config = config or PlatformConfig.from_env()

    flask_kwargs: dict[str, str] = {}
    if platform_config.instance_path:
        flask_kwargs["instance_path"] = platform_config.instance_path

    app = Flask(__name__, **flask_kwargs)
    app.config.from_mapping(platform_config.app_config)
    app.config["SECRET_KEY"] = platform_config.secret_key
    if platform_config.url_prefix:
        app.wsgi_app = PrefixMiddleware(app.wsgi_app, platform_config.url_prefix)

    registry = PluginRegistry(platform_config)
    plugins = registry.discover()

    for plugin in plugins:
        app.register_blueprint(plugin.blueprint)

    app.extensions["platform_registry"] = registry

    @app.context_processor
    def inject_platform_navigation() -> dict[str, object]:
        return {
            "platform_menu": registry.menu_entries,
            "platform_path": _prefix_menu_path,
        }

    @app.get("/")
    def index() -> str:
        return render_template("index.html", plugins=plugins)

    return app


def main() -> None:
    create_app().run(debug=True)


if __name__ == "__main__":
    main()
