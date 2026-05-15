from __future__ import annotations

from flask import Flask, render_template

from flask_plugin_platform.config import PlatformConfig
from flask_plugin_platform.registry import PluginRegistry


def create_app(config: PlatformConfig | None = None) -> Flask:
    platform_config = config or PlatformConfig.from_env()

    flask_kwargs: dict[str, str] = {}
    if platform_config.instance_path:
        flask_kwargs["instance_path"] = platform_config.instance_path

    app = Flask(__name__, **flask_kwargs)
    app.config.from_mapping(platform_config.app_config)
    app.config["SECRET_KEY"] = platform_config.secret_key

    registry = PluginRegistry(platform_config)
    plugins = registry.discover()

    for plugin in plugins:
        app.register_blueprint(plugin.blueprint)

    app.extensions["platform_registry"] = registry

    @app.context_processor
    def inject_platform_navigation() -> dict[str, object]:
        return {"platform_menu": registry.menu_entries}

    @app.get("/")
    def index() -> str:
        return render_template("index.html", plugins=plugins)

    return app


def main() -> None:
    create_app().run(debug=True)


if __name__ == "__main__":
    main()
