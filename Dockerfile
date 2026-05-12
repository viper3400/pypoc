FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY flask_plugin_platform ./flask_plugin_platform

RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "flask_plugin_platform:create_app()", "--bind", "0.0.0.0:8000", "--workers", "2"]
