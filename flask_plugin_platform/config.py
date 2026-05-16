from __future__ import annotations

import os
from dataclasses import dataclass, field


def _normalize_prefixes(prefixes: set[str]) -> set[str]:
    return {prefix.strip().rstrip("_").upper() for prefix in prefixes if prefix.strip()}


def _csv_env(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def _env_app_config(prefixes: set[str]) -> dict[str, str]:
    normalized_prefixes = _normalize_prefixes(prefixes)
    config: dict[str, str] = {}

    for key, value in os.environ.items():
        upper_key = key.upper()
        if any(upper_key == prefix or upper_key.startswith(f"{prefix}_") for prefix in normalized_prefixes):
            config[key] = value

    return config


def _instance_path_env() -> str | None:
    raw = os.getenv("PLATFORM_INSTANCE_PATH", "").strip()
    if not raw:
        return None
    return os.path.abspath(raw)


def _normalize_url_prefix(raw: str | None) -> str | None:
    if raw is None:
        return None

    prefix = raw.strip()
    if not prefix:
        return None
    if not prefix.startswith("/"):
        raise ValueError("PLATFORM_URL_PREFIX must start with '/'")
    if prefix != "/" and prefix.endswith("/"):
        prefix = prefix.rstrip("/")
    return prefix


@dataclass(frozen=True)
class PlatformConfig:
    """Runtime configuration for plugin discovery and registration."""

    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-only-change-me"))
    entry_point_group: str = field(
        default_factory=lambda: os.getenv(
            "PLATFORM_ENTRY_POINT_GROUP",
            "flask_plugin_platform.plugins",
        )
    )
    local_plugin_package: str = field(
        default_factory=lambda: os.getenv("PLATFORM_LOCAL_PLUGIN_PACKAGE", "")
    )
    enabled_apps: set[str] = field(default_factory=lambda: _csv_env("PLATFORM_ENABLED_APPS"))
    disabled_apps: set[str] = field(default_factory=lambda: _csv_env("PLATFORM_DISABLED_APPS"))
    app_config_prefixes: set[str] = field(
        default_factory=lambda: _normalize_prefixes(_csv_env("PLATFORM_APP_CONFIG_PREFIXES"))
    )
    app_config: dict[str, str] = field(default_factory=dict)
    instance_path: str | None = field(default_factory=_instance_path_env)
    url_prefix: str | None = field(
        default_factory=lambda: _normalize_url_prefix(os.getenv("PLATFORM_URL_PREFIX"))
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "url_prefix", _normalize_url_prefix(self.url_prefix))

    @classmethod
    def from_env(cls) -> PlatformConfig:
        app_config_prefixes = _normalize_prefixes(_csv_env("PLATFORM_APP_CONFIG_PREFIXES"))
        return cls(
            app_config_prefixes=app_config_prefixes,
            app_config=_env_app_config(app_config_prefixes),
            instance_path=_instance_path_env(),
            url_prefix=_normalize_url_prefix(os.getenv("PLATFORM_URL_PREFIX")),
        )

    def is_enabled(self, plugin_id: str) -> bool:
        if self.enabled_apps and plugin_id not in self.enabled_apps:
            return False
        return plugin_id not in self.disabled_apps
