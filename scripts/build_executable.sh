#!/usr/bin/env sh
set -eu

uv run pyinstaller --clean --noconfirm packaging/platform-server.spec
