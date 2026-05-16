# Example Product Deployment

This is the shape of a product repository that consumes the reusable platform.
Install `flask-plugin-platform` plus only the plugin packages this deployment needs.

For a public GitHub release, pin the platform dependency to the published wheel:

```toml
[project]
dependencies = [
    "flask-plugin-platform @ https://github.com/<OWNER>/<REPO>/releases/download/v0.1.0/flask_plugin_platform-0.1.0-py3-none-any.whl",
    "flask-plugin-notes",
]
```

For a private repository, download the wheel from the release before installing:

```bash
gh release download v0.1.0 --repo <OWNER>/<REPO> --pattern "flask_plugin_platform-0.1.0-py3-none-any.whl"
uv pip install ./flask_plugin_platform-0.1.0-py3-none-any.whl
```

Consumer bootstrap stays minimal:

```python
from flask_plugin_platform import create_app

app = create_app()
```

Plugin runtime configuration can be provided directly via environment variables:

```bash
SECRET_KEY=change-me
PLATFORM_APP_CONFIG_PREFIXES=PYDO,PYTODO
PLATFORM_INSTANCE_PATH=/var/lib/example-product
PYDO_DATA_DIR=/var/lib/example-product/data
PYDO_TODO_FILE=/var/lib/example-product/data/todos.json
PYTODO_PASSWORD_HASH=scrypt$...
```

Default mode serves the product at `/`. To mount it under a subpath, set:

```bash
PLATFORM_URL_PREFIX=/pypoc
```

```bash
uv sync
uv run gunicorn "wsgi:app" --bind 0.0.0.0:8000 --workers 2
```

The same product config also works with Waitress:

```bash
uv sync
uv run platform-server --host 0.0.0.0 --port 8000
```

Behind nginx or another reverse proxy, forward `/pypoc/...` to the app and keep
`PLATFORM_URL_PREFIX=/pypoc` in the runtime environment when the deployment is
served from that subpath.
