from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv_env(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {item.strip() for item in raw.split(",") if item.strip()}


@dataclass(frozen=True)
class PlatformConfig:
    """Runtime configuration for plugin discovery and registration."""

    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-only-change-me"))
    plugin_package: str = field(
        default_factory=lambda: os.getenv("PLATFORM_PLUGIN_PACKAGE", "apps")
    )
    enabled_apps: set[str] = field(default_factory=lambda: _csv_env("PLATFORM_ENABLED_APPS"))
    disabled_apps: set[str] = field(default_factory=lambda: _csv_env("PLATFORM_DISABLED_APPS"))

    @classmethod
    def from_env(cls) -> PlatformConfig:
        return cls()

    def is_enabled(self, plugin_id: str) -> bool:
        if self.enabled_apps and plugin_id not in self.enabled_apps:
            return False
        return plugin_id not in self.disabled_apps
