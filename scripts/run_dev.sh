#!/usr/bin/env sh
set -eu

uv run flask --app host.app:create_app run --debug
