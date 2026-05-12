# Flask Plugin Platform

Reusable Flask infrastructure for building lightweight plugin-based application
platforms. The infrastructure package does not statically import concrete apps.
Plugins are discovered at runtime and register Flask blueprints through metadata.

## Architecture

This repository is the reusable infrastructure package:

```text
.
├── flask_plugin_platform/
│   ├── app.py
│   ├── config.py
│   ├── registry.py
│   ├── static/
│   └── templates/
├── examples/
│   ├── deployment/
│   └── plugins/
├── tests/
└── pyproject.toml
```

Concrete apps live outside the platform package. The examples show separately
packaged `flask-plugin-notes` and `flask-plugin-analytics` plugins.

## Quick Start

Prerequisites:

- Python 3.12
- `uv`

Set up the platform package:

```bash
uv sync --python 3.12
```

Run the infrastructure app by itself:

```bash
uv run flask --app flask_plugin_platform.app:create_app run --debug
```

The app starts at `http://127.0.0.1:5000`. With no plugin packages installed, the
home page should show zero enabled apps. That is expected: the platform package is
reusable infrastructure and does not ship concrete apps.

## Run With Example Plugins

Install the example plugins in editable mode while developing:

```bash
uv pip install -e examples/plugins/flask-plugin-notes
uv pip install -e examples/plugins/flask-plugin-analytics
```

Then start the dev server:

```bash
uv run flask --app flask_plugin_platform.app:create_app run --debug
```

Available example routes:

- `http://127.0.0.1:5000/notes/`
- `http://127.0.0.1:5000/analytics/`

You can also use the helper script:

```bash
./scripts/run_dev.sh
```

## Plugin Discovery

Production discovery uses Python entry points:

```toml
[project.entry-points."flask_plugin_platform.plugins"]
notes = "flask_plugin_notes.plugin:PLUGIN"
```

Each plugin exposes a `PLUGIN` object:

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

Local package scanning is still available for development by setting:

```bash
PLATFORM_LOCAL_PLUGIN_PACKAGE=local_plugins
```

## Create Your First App

A real app should be its own Python package. The platform discovers it through
package metadata, not through a direct import.

Minimal package layout:

```text
flask-plugin-tasks/
├── pyproject.toml
└── src/
    └── flask_plugin_tasks/
        ├── __init__.py
        ├── plugin.py
        ├── routes.py
        └── templates/
            └── tasks/
                └── index.html
```

`pyproject.toml`:

```toml
[project]
name = "flask-plugin-tasks"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
    "flask>=3.0.0",
    "flask-plugin-platform",
]

[project.entry-points."flask_plugin_platform.plugins"]
tasks = "flask_plugin_tasks.plugin:PLUGIN"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/flask_plugin_tasks"]
```

`routes.py`:

```python
from flask import Blueprint, render_template

blueprint = Blueprint(
    "tasks",
    __name__,
    url_prefix="/tasks",
    template_folder="templates",
    static_folder="static",
    static_url_path="/tasks/static",
)


@blueprint.get("/")
def index() -> str:
    tasks = ["Create first plugin", "Ship it as a package"]
    return render_template("tasks/index.html", tasks=tasks)
```

`plugin.py`:

```python
from flask_plugin_tasks.routes import blueprint

PLUGIN = {
    "id": "tasks",
    "name": "Tasks",
    "description": "Simple task tracking app",
    "version": "0.1.0",
    "blueprint": blueprint,
    "menu_entry": {
        "label": "Tasks",
        "icon": "check-square",
        "path": "/tasks/",
    },
}
```

Install it into a product or development environment:

```bash
uv pip install -e ../flask-plugin-tasks
uv run flask --app flask_plugin_platform.app:create_app run --debug
```

The app should appear in the generated menu and respond at `/tasks/`.

## Consuming Project

A product repository should be thin. It installs the reusable platform plus the
plugin packages it wants to deploy:

```toml
[project]
dependencies = [
    "flask-plugin-platform",
    "flask-plugin-notes",
    "flask-plugin-analytics",
]
```

`wsgi.py`:

```python
from flask_plugin_platform import create_app

app = create_app()
```

Run with Gunicorn:

```bash
uv run gunicorn "wsgi:app" --bind 0.0.0.0:8000 --workers 2
```

The example in `examples/deployment/` shows this minimal product-repo shape.

## Private Package Index

Publish the infrastructure package and plugin packages to your private package
index. A consuming project can then configure `uv` for that index and install
only the packages needed for that deployment.

Example package set:

- `flask-plugin-platform`
- `flask-plugin-notes`
- `flask-plugin-analytics`

## Enable Or Disable Apps

By default, all discovered plugins are enabled.

Deploy only selected apps:

```bash
PLATFORM_ENABLED_APPS=notes uv run gunicorn "wsgi:app" --bind 0.0.0.0:8000
```

Disable specific apps:

```bash
PLATFORM_DISABLED_APPS=analytics uv run gunicorn "wsgi:app" --bind 0.0.0.0:8000
```

`PLATFORM_ENABLED_APPS` is an allowlist. `PLATFORM_DISABLED_APPS` is then applied
as a denylist.

## Development

```bash
uv sync --python 3.12
uv run ruff check .
uv run pytest
uv build
```

Build the example plugin packages:

```bash
uv build examples/plugins/flask-plugin-notes
uv build examples/plugins/flask-plugin-analytics
```

Useful smoke test after building wheels:

```bash
uv venv /tmp/plugin-smoke --python 3.12
uv pip install --python /tmp/plugin-smoke/bin/python \
  dist/flask_plugin_platform-0.1.0-py3-none-any.whl \
  examples/plugins/flask-plugin-notes/dist/flask_plugin_notes-0.1.0-py3-none-any.whl
/tmp/plugin-smoke/bin/python -c "from flask_plugin_platform import create_app; app = create_app(); print(sorted(app.blueprints))"
```

The output should include `notes` and should not include `analytics` unless the
analytics plugin package was also installed.

The platform is pinned to Python `>=3.12,<3.13`.

## Troubleshooting

If `uv` is missing:

```bash
python -m pip install uv
```

If `uv` selects the wrong Python version:

```bash
uv sync --python 3.12
```

If no apps appear in the menu, check that plugin packages are installed in the
same environment used to run Flask:

```bash
uv pip list | grep flask-plugin
```

If routes from a plugin do not appear, verify the plugin package exposes an entry
point under `flask_plugin_platform.plugins` and that its `PLUGIN["id"]` is not
filtered out by `PLATFORM_ENABLED_APPS` or `PLATFORM_DISABLED_APPS`.
