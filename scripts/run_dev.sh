#!/usr/bin/env sh
set -eu

uv run flask --app flask_plugin_platform.app:create_app run --debug
