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

```bash
uv sync
uv run gunicorn "wsgi:app" --bind 0.0.0.0:8000 --workers 2
```
