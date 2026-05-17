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

Run with Waitress:

```bash
uv run platform-server --host 0.0.0.0 --port 8000
```

The example in `examples/deployment/` shows this minimal product-repo shape.

## Runtime Configuration From Environment

`create_app()` remains the central entry point for production and development
deployments. Consumer repositories do not need project-specific bootstrap code
just to copy plugin settings from environment variables into `app.config`.

Use `PLATFORM_APP_CONFIG_PREFIXES` to declare which environment variable
prefixes should be copied into Flask config unchanged:

```bash
PLATFORM_APP_CONFIG_PREFIXES=PYDO,PYTODO
PYDO_DATA_DIR=/var/lib/pydo
PYDO_TODO_FILE=/var/lib/pydo/todos.json
PYTODO_PASSWORD_HASH=scrypt$...
```

With that configuration, `create_app()` will populate:

- `app.config["PYDO_DATA_DIR"]`
- `app.config["PYDO_TODO_FILE"]`
- `app.config["PYTODO_PASSWORD_HASH"]`

This is generic and not tied to a specific plugin. Any environment variable
whose name exactly matches one of the configured prefixes or starts with
`<PREFIX>_` is copied into `app.config` with the same key.

`SECRET_KEY` remains a dedicated top-level platform setting and does not need to
be listed in `PLATFORM_APP_CONFIG_PREFIXES`.

If a deployment needs a custom Flask instance directory, set:

```bash
PLATFORM_INSTANCE_PATH=/var/lib/flask-plugin-platform
```

The value is passed to Flask as `instance_path` during app creation, so a
consumer can still keep:

```python
from flask_plugin_platform import create_app

app = create_app()
```

Example production bootstrap:

```python
from flask_plugin_platform import create_app

app = create_app()
```

Default deployments are served at `/`. If a product must be mounted under a
subpath such as `/pypoc`, set:

```bash
PLATFORM_URL_PREFIX=/pypoc
```

When `PLATFORM_URL_PREFIX` is set, the platform prepends that prefix to
platform-generated URLs and menu links while keeping plugin route definitions
unchanged. The same setting works for both Gunicorn and Waitress.

Example runtime environment:

```bash
SECRET_KEY=change-me
PLATFORM_APP_CONFIG_PREFIXES=PYDO,PYTODO
PLATFORM_INSTANCE_PATH=/var/lib/example-product
PLATFORM_URL_PREFIX=/pypoc
PYDO_DATA_DIR=/var/lib/example-product/data
PYDO_TODO_FILE=/var/lib/example-product/data/todos.json
PYTODO_PASSWORD_HASH=scrypt$...
gunicorn "wsgi:app" --bind 0.0.0.0:8000 --workers 2
```

Equivalent Waitress run:

```bash
SECRET_KEY=change-me \
PLATFORM_APP_CONFIG_PREFIXES=PYDO,PYTODO \
PLATFORM_INSTANCE_PATH=/var/lib/example-product \
PLATFORM_URL_PREFIX=/pypoc \
PYDO_DATA_DIR=/var/lib/example-product/data \
PYDO_TODO_FILE=/var/lib/example-product/data/todos.json \
PYTODO_PASSWORD_HASH=scrypt$... \
uv run platform-server --host 0.0.0.0 --port 8000
```

For reverse proxies that expose the app under a subpath, keep the upstream app
serving internal routes from `/` and forward the external prefix at the proxy
layer. For example, an nginx deployment can forward `/pypoc/...` to the app
while `PLATFORM_URL_PREFIX=/pypoc` keeps generated links and static assets on
that external path.

For a public GitHub release, the platform dependency can be pinned directly to
the wheel asset:

```toml
[project]
dependencies = [
    "flask-plugin-platform @ https://github.com/<OWNER>/<REPO>/releases/download/v0.1.0/flask_plugin_platform-0.1.0-py3-none-any.whl",
    "flask-plugin-notes",
    "flask-plugin-analytics",
]
```

This repository publishes only the reusable `flask-plugin-platform` package.
Plugin packages remain separate Python distributions discovered through entry
points and can adopt the same release flow in their own repositories.

## GitHub Release Distribution

As of May 14, 2026, GitHub Packages does not provide a Python package registry.
This repository therefore ships Python distribution artifacts through GitHub
Releases instead of a package index.

Release assets published by this repository:

- `flask_plugin_platform-<version>-py3-none-any.whl`
- `flask_plugin_platform-<version>.tar.gz`

Public install examples:

```bash
uv pip install "flask-plugin-platform @ https://github.com/<OWNER>/<REPO>/releases/download/v0.1.0/flask_plugin_platform-0.1.0-py3-none-any.whl"
pip install "flask-plugin-platform @ https://github.com/<OWNER>/<REPO>/releases/download/v0.1.0/flask_plugin_platform-0.1.0-py3-none-any.whl"
```

Private repository install example:

```bash
gh release download v0.1.0 --repo <OWNER>/<REPO> --pattern "flask_plugin_platform-0.1.0-py3-none-any.whl"
uv pip install ./flask_plugin_platform-0.1.0-py3-none-any.whl
```

The same downloaded wheel can be installed with `pip install ./flask_plugin_platform-0.1.0-py3-none-any.whl`.

## GHCR Container Image

Tagged pushes also publish the production image from [Dockerfile](/Users/Jan/Documents/Development/pypoc/Dockerfile:1)
to GitHub Container Registry via [.github/workflows/container.yml](/Users/Jan/Documents/Development/pypoc/.github/workflows/container.yml:1).

Image name:

```text
ghcr.io/<OWNER>/<REPO>
```

For a tag like `v0.1.0`, the workflow publishes these tags:

- `ghcr.io/<OWNER>/<REPO>:v0.1.0`
- `ghcr.io/<OWNER>/<REPO>:0.1.0`
- `ghcr.io/<OWNER>/<REPO>:0.1`

Pull and run example:

```bash
docker pull ghcr.io/<OWNER>/<REPO>:0.1.0
docker run --rm -p 8000:8000 \
  -e SECRET_KEY=change-me \
  -e PLATFORM_APP_CONFIG_PREFIXES=PYDO,PYTODO \
  -e PYDO_DATA_DIR=/var/lib/example-product/data \
  -e PYDO_TODO_FILE=/var/lib/example-product/data/todos.json \
  -e PYTODO_PASSWORD_HASH=scrypt$... \
  ghcr.io/<OWNER>/<REPO>:0.1.0
```

## Versioning

Source of truth:
- bump `project.version` in [pyproject.toml](/Users/Jan/Documents/Development/pypoc/pyproject.toml:1)

Release tag format:
- create a matching Git tag `vX.Y.Z`
- the release workflow rejects tags that do not match `project.version`

When to bump:
- bump this repo when platform package behavior or plugin contract behavior changes
- `PATCH` for fixes, `MINOR` for backward-compatible platform capabilities, `MAJOR` for breaking platform or plugin-contract changes

Relationship to other repos:
- plugin packages version themselves independently
- deployment repositories version the shipped bundle independently
- the platform version should not be treated as the deployment version or a plugin version

## Release Process

`pyproject.toml` is the single source of truth for package metadata and version.

To publish a release:

1. Update `project.version` in `pyproject.toml`.
2. Run `uv sync --python 3.12`.
3. Run `uv run pytest`.
4. Run `uv build`.
5. Commit the version change.
6. Create a matching Git tag such as `v0.1.0`.
7. Push the commit and tag to GitHub.

The `Release Python Package` workflow runs only on version tags. It verifies
that the tag matches `pyproject.toml`, builds the wheel and sdist, validates the
artifacts with `twine check`, and uploads them to a GitHub Release.

The `Publish Container Image` workflow runs on the same tags and pushes the
container image to `ghcr.io` using the repository `GITHUB_TOKEN`.

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
uvx twine check dist/*.whl dist/*.tar.gz
```

## Standalone Executable

The platform can be bundled into a single executable with PyInstaller. This is
useful for desktop-style or appliance-style deployments where Python should not
be installed separately on the target machine.

Builds are OS-specific:

- Build on macOS to create a macOS executable.
- Build on Windows to create a `.exe`.
- Build on Linux to create a Linux executable.

Install whichever plugin packages should be included, then build:

```bash
uv sync --python 3.12
uv pip install -e examples/plugins/flask-plugin-notes
uv pip install -e examples/plugins/flask-plugin-analytics
    ./scripts/build_executable.sh
```

The output is written to:

```text
dist/platform-server
```

On Windows the output name will be `platform-server.exe`.

Run it:

```bash
./dist/platform-server --host 127.0.0.1 --port 5000
```

The executable runs the Flask application through Waitress by default. Flask is
still the web framework, but its built-in development server is only used when
you explicitly pass `--debug`:

```bash
./dist/platform-server --debug
```

The executable includes the platform plus plugin packages installed in the build
environment. To ship only selected apps, install only those plugin packages before
running the build. Runtime enable/disable filtering still works:

```bash
PLATFORM_ENABLED_APPS=notes ./dist/platform-server --port 5000
```

For normal server deployments, Gunicorn or a container image is still the
preferred Linux production model. The standalone executable uses Waitress so it
can run as a self-contained binary, including on Windows where Gunicorn is not a
good fit.

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
