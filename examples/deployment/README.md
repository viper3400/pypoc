# Example Product Deployment

This is the shape of a product repository that consumes the reusable platform.
Install `flask-plugin-platform` plus only the plugin packages this deployment needs.

```bash
uv sync
uv run gunicorn "wsgi:app" --bind 0.0.0.0:8000 --workers 2
```
