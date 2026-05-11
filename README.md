# Flask Plugin Platform

A production-oriented Flask skeleton for modular, dynamically discoverable apps.
The host application does not statically import concrete apps. It discovers plugin
modules at startup, validates their metadata, registers their blueprints, and
builds the navigation menu from plugin metadata.

## Features

- Dynamic `apps.*.plugin` discovery via `pkgutil` and `importlib`
- Self-registering app contract through a module-level `PLUGIN` object
- Blueprint-based routing
- Menu generation from plugin metadata
- Optional app selection through environment variables
- Clean host/app/shared separation
- Gunicorn-ready app factory
- Pytest and Ruff configured
- Dockerfile included for optional container deployment

## Layout

```text
.
├── apps/
│   ├── analytics/
│   └── notes/
├── host/
│   ├── app.py
│   ├── config.py
│   ├── registry.py
│   └── templates/
├── shared/
├── tests/
└── scripts/
```

## Quick Start

```bash
uv sync
uv run flask --app host.app:create_app run --debug
```

Open `http://127.0.0.1:5000`.

## Production

```bash
uv sync --frozen --no-dev
uv run gunicorn "host.app:create_app()" --bind 0.0.0.0:8000 --workers 2
```

## Enable Or Disable Apps

By default, all discovered apps are enabled.

Deploy only selected apps:

```bash
PLATFORM_ENABLED_APPS=notes uv run gunicorn "host.app:create_app()" --bind 0.0.0.0:8000
```

Disable specific apps:

```bash
PLATFORM_DISABLED_APPS=analytics uv run flask --app host.app:create_app run
```

`PLATFORM_ENABLED_APPS` is an allowlist. `PLATFORM_DISABLED_APPS` is then applied
as a denylist.

## Plugin Contract

Each plugin exposes a module-level `PLUGIN` object:

```python
PLUGIN = {
    "id": "notes",
    "name": "Notes",
    "description": "Simple notes application",
    "version": "0.1.0",
    "blueprint": blueprint,
    "menu_entry": {
        "label": "Notes",
        "icon": "sticky-note",
        "path": "/notes/",
    },
}
```

The host currently discovers modules named `apps.<app_id>.plugin`. The registry is
isolated so it can later add Python package entry point discovery without changing
application code.

## Checks

```bash
uv run ruff check .
uv run pytest
```
