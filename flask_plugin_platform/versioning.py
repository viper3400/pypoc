from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import metadata

from flask_plugin_platform.registry import Plugin


def _metadata_version(distribution_name: str, fallback: str = "unknown") -> str:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return fallback


@dataclass(frozen=True)
class DeploymentVersionInfo:
    name: str
    version: str
    build_sha: str
    is_configured: bool


@dataclass(frozen=True)
class PlatformVersionInfo:
    deployment: DeploymentVersionInfo
    platform_version: str
    plugins: tuple[Plugin, ...]


def resolve_platform_version() -> str:
    return _metadata_version("flask-plugin-platform", fallback="local-dev")


def resolve_deployment_version() -> DeploymentVersionInfo:
    name = os.getenv("PLATFORM_DEPLOYMENT_NAME", "").strip()
    version = os.getenv("PLATFORM_DEPLOYMENT_VERSION", "").strip()
    build_sha = os.getenv("PLATFORM_BUILD_SHA", "").strip()
    is_configured = bool(name or version or build_sha)

    if build_sha:
        build_sha = build_sha[:12]

    return DeploymentVersionInfo(
        name=name or "Local host app",
        version=version,
        build_sha=build_sha,
        is_configured=is_configured,
    )


def build_version_info(plugins: tuple[Plugin, ...]) -> PlatformVersionInfo:
    return PlatformVersionInfo(
        deployment=resolve_deployment_version(),
        platform_version=resolve_platform_version(),
        plugins=plugins,
    )
