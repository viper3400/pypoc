# Migrate Any Python App To A `pypoc` Plugin

This guide is written for a coding agent. Its purpose is to convert an existing
Python application into a plugin package that can be discovered by this repo's
`flask-plugin-platform` runtime and served under the `pypoc` host UI.

## Goal

Produce a standalone Python package that:

- exposes a top-level `PLUGIN` dict
- registers through the `flask_plugin_platform.plugins` entry point group
- provides a Flask `Blueprint`
- works when the host platform is mounted at `/` or under `/pypoc`

## Hard Constraints

Do not invent a new plugin API. The platform currently accepts only this shape:

- `PLUGIN["id"]`: non-empty string
- `PLUGIN["name"]`: non-empty string
- `PLUGIN["description"]`: non-empty string
- `PLUGIN["version"]`: non-empty string
- `PLUGIN["blueprint"]`: `flask.Blueprint`
- `PLUGIN["menu_entry"]`: optional dict with `label`, `icon`, `path`

The package must register an entry point under:

```toml
[project.entry-points."flask_plugin_platform.plugins"]
myapp = "my_plugin_package.plugin:PLUGIN"
```

The menu path must start with `/`. Do not hardcode `/pypoc` anywhere. The host
applies `PLATFORM_URL_PREFIX=/pypoc` externally.

## Migration Strategy

### 1. Classify the source app

Choose one of these migration paths:

- Existing Flask app:
  Extract its routes into a `Blueprint` and keep as much code as possible.
- Other Python web framework:
  Keep domain logic, persistence, validation, and templates where reusable, but
  replace the web entry layer with Flask routes inside a `Blueprint`.
- Non-web Python app:
  Wrap the useful workflows in Flask views, forms, or JSON endpoints inside a
  `Blueprint`.

If the source app is not Flask, do not try to force the entire framework to run
inside the plugin system. Move business logic into framework-agnostic modules
and re-expose only the HTTP layer through Flask.

### 2. Separate framework-neutral code from web glue

Before editing routes, isolate:

- services
- data access
- config loading
- schemas and validators
- template-independent formatting logic

The target shape is:

- framework-neutral code in `services.py`, `repository.py`, `models.py`, etc.
- Flask-specific code only in `routes.py` and `plugin.py`

### 3. Create the plugin package layout

Use this package structure:

```text
my-plugin/
├── pyproject.toml
└── src/
    └── my_plugin/
        ├── __init__.py
        ├── plugin.py
        ├── routes.py
        ├── services.py
        ├── templates/
        │   └── my_plugin/
        │       └── index.html
        └── static/
```

### 4. Convert the HTTP layer to a Flask blueprint

Build a blueprint like this:

```python
from flask import Blueprint

blueprint = Blueprint(
    "my_plugin",
    __name__,
    url_prefix="/my-plugin",
    template_folder="templates",
    static_folder="static",
    static_url_path="/my-plugin/static",
)
```

Rules:

- The blueprint name must be unique.
- `url_prefix` should match the plugin route root.
- `static_url_path` should also stay under that route root.
- Use relative plugin-local templates such as `render_template("my_plugin/index.html")`.

### 5. Replace app-level Flask usage

If the source app already uses Flask:

- replace `app = Flask(...)` with a `Blueprint`
- replace `@app.get`, `@app.post`, `@app.route` with `@blueprint.get`, `@blueprint.post`, `@blueprint.route`
- move app bootstrap code out of the plugin package
- stop calling `app.run()`
- remove host-level concerns such as global error pages unless they are truly plugin-specific

### 6. Define the plugin contract

Create `plugin.py`:

```python
from my_plugin.routes import blueprint

PLUGIN = {
    "id": "my-plugin",
    "name": "My Plugin",
    "description": "Short description",
    "version": "0.1.0",
    "blueprint": blueprint,
    "menu_entry": {
        "label": "My Plugin",
        "icon": "plug",
        "path": "/my-plugin/",
    },
}
```

Rules:

- `id` must be stable and unique across all installed plugins.
- `menu_entry["path"]` should point to the plugin landing page.
- Keep `version` synced with `pyproject.toml`.

### 7. Add package metadata

Use a `pyproject.toml` similar to:

```toml
[project]
name = "my-plugin"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
    "flask>=3.0.0",
    "flask-plugin-platform",
]

[project.entry-points."flask_plugin_platform.plugins"]
my_plugin = "my_plugin.plugin:PLUGIN"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_plugin"]
```

## Config Migration Rules

The host platform copies selected environment variables into `app.config`.

Use this when the source app has custom environment settings:

```bash
PLATFORM_APP_CONFIG_PREFIXES=MYPLUGIN
MYPLUGIN_DATA_DIR=/var/lib/my-plugin
MYPLUGIN_API_TOKEN=secret
```

Inside plugin code, read configuration from `current_app.config`.

Rules:

- prefer one stable env prefix per plugin
- do not read unrelated host env vars directly when `app.config` is enough
- do not store mutable runtime data in the package directory
- use `PLATFORM_INSTANCE_PATH` when the deployment needs a writable instance path

## URL And Template Rules

- Do not hardcode `/pypoc`.
- Do not assume the host app lives at `/`.
- Use blueprint routes such as `/my-plugin/`.
- Use `url_for(...)` for endpoint links and static asset links.
- Keep plugin templates namespaced under `templates/my_plugin/` to avoid collisions.

When the platform runs with `PLATFORM_URL_PREFIX=/pypoc`, the host rewrites
generated navigation URLs. Plugin route definitions should remain unchanged.

## Migration Patterns By App Type

### Flask app

Preferred approach:

1. Move route handlers into `routes.py`.
2. Change the global app object to a `Blueprint`.
3. Move reusable logic into service modules.
4. Remove standalone server startup code.
5. Add `plugin.py` and entry point metadata.

### FastAPI, Starlette, Django, Bottle, Tornado, other web frameworks

Preferred approach:

1. Keep domain logic and storage code.
2. Recreate only the needed HTTP endpoints in Flask.
3. Reuse Jinja templates where practical; otherwise port the views incrementally.
4. Drop framework-specific middleware unless it is essential and can be replaced in Flask.
5. Treat the original framework as the source implementation, not as something to embed unchanged.

### CLI or worker app

Preferred approach:

1. Extract the core operations into callable services.
2. Add Flask forms or action endpoints that trigger those services.
3. Return HTML for human workflows or JSON for tool-oriented flows.

## Definition Of Done

The migration is complete only when all of the following are true:

- the plugin installs as its own package
- the package exposes a valid `PLUGIN` dict
- the package registers an entry point in `flask_plugin_platform.plugins`
- the host platform discovers the plugin without manual imports
- the plugin renders at its route root
- its menu item appears in the platform UI
- no plugin code hardcodes `/pypoc`

## Verification Checklist

Use this exact verification flow:

1. Install the plugin package into the environment.
2. Start the host:

```bash
uv run flask --app flask_plugin_platform.app:create_app run --debug
```

3. Open `/` and confirm the plugin appears in the menu.
4. Open the plugin route, for example `/my-plugin/`.
5. Repeat with:

```bash
PLATFORM_URL_PREFIX=/pypoc uv run flask --app flask_plugin_platform.app:create_app run --debug
```

6. Confirm the plugin is reachable through `/pypoc/...` without changing plugin route code.

## Common Mistakes

- exporting a Flask app instead of a Flask `Blueprint`
- forgetting the entry point declaration
- using a `menu_entry.path` that does not start with `/`
- hardcoding `/pypoc` into routes, templates, or redirects
- leaving business logic trapped inside framework-specific handlers
- using non-namespaced template paths that collide with other plugins
- keeping `app.run()` or direct bootstrap code inside the plugin package

## Minimal Output Expected From The Coding Agent

For each migration, produce:

- a standalone plugin package
- `pyproject.toml`
- `src/<package>/plugin.py`
- `src/<package>/routes.py`
- any extracted service modules needed to keep the web layer thin
- a short note describing what was ported, what was rewritten, and what still depends on the original app
