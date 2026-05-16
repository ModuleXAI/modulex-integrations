"""Pydantic response models for the NPM integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetPackageDependenciesOutput",
    "GetPackageDownloadStatsOutput",
    "GetPackageInfoOutput",
    "GetPackageVersionsOutput",
    "GetPopularPackagesOutput",
    "SearchPackagesOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetPackageInfoOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    version: str | None = None
    description: str = ""
    author: str | None = None
    homepage: str = ""
    repository: str = ""
    license: str = ""
    keywords: list[str] = Field(default_factory=list)
    dependencies: dict[str, str] = Field(default_factory=dict)
    devDependencies: dict[str, str] = Field(default_factory=dict)
    peerDependencies: dict[str, str] = Field(default_factory=dict)


class SearchPackagesOutput(_Base):
    success: bool
    error: str | None = None
    total: int = 0
    # Each package is a complex nested object — keep permissive.
    packages: list[dict[str, Any]] = Field(default_factory=list)


class GetPopularPackagesOutput(_Base):
    success: bool
    error: str | None = None
    packages: list[dict[str, Any]] = Field(default_factory=list)


class GetPackageVersionsOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    dist_tags: dict[str, str] = Field(default_factory=dict)
    versions: list[dict[str, str]] = Field(default_factory=list)
    total_versions: int = 0


class GetPackageDependenciesOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    version: str | None = None
    dependencies: dict[str, str] = Field(default_factory=dict)
    devDependencies: dict[str, str] = Field(default_factory=dict)
    peerDependencies: dict[str, str] = Field(default_factory=dict)
    optionalDependencies: dict[str, str] = Field(default_factory=dict)


class GetPackageDownloadStatsOutput(_Base):
    success: bool
    error: str | None = None
    package: str | None = None
    period: str | None = None
    start: str | None = None
    end: str | None = None
    total_downloads: int = 0
    daily_downloads: list[dict[str, Any]] = Field(default_factory=list)
