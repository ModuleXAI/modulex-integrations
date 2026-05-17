"""NPM Registry LangChain ``@tool`` functions.

api_key is optional — npm's public registry needs no auth; api_key
only kicks in for private registries (added as a Bearer header when
provided). All tool signatures accept ``api_key`` as a keyword with
default ``""``.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.npm.outputs import (
    GetPackageDependenciesOutput,
    GetPackageDownloadStatsOutput,
    GetPackageInfoOutput,
    GetPackageVersionsOutput,
    GetPopularPackagesOutput,
    SearchPackagesOutput,
)

__all__ = [
    "get_package_dependencies",
    "get_package_download_stats",
    "get_package_info",
    "get_package_versions",
    "get_popular_packages",
    "search_packages",
]

_REGISTRY_URL = "https://registry.npmjs.org"
_API_URL = "https://api.npmjs.org"
_TIMEOUT = 30.0
_VALID_PERIODS = ("last-day", "last-week", "last-month", "last-year")


def _headers(api_key: str) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _author_name(raw: Any) -> str | None:
    if isinstance(raw, dict):
        return raw.get("name")
    if isinstance(raw, str):
        return raw
    return None


def _repo_url(raw: Any) -> str:
    if isinstance(raw, dict):
        return raw.get("url") or ""
    if isinstance(raw, str):
        return raw
    return ""


class GetPackageInfoInput(BaseModel):
    package_name: str = Field(description="The name of the npm package to look up")
    api_key: str = Field(default="", description="Optional API key for private registries")


class SearchPackagesInput(BaseModel):
    query: str = Field(description="Search query text")
    api_key: str = Field(default="", description="Optional API key for private registries")
    size: int = Field(default=10, description="Number of results to return (1-250)")


class GetPopularPackagesInput(BaseModel):
    api_key: str = Field(default="", description="Optional API key for private registries")
    size: int = Field(default=10, description="Number of popular packages to return (1-250)")


class GetPackageVersionsInput(BaseModel):
    package_name: str = Field(description="The name of the npm package")
    api_key: str = Field(default="", description="Optional API key for private registries")


class GetPackageDependenciesInput(BaseModel):
    package_name: str = Field(description="The name of the npm package")
    api_key: str = Field(default="", description="Optional API key for private registries")
    version: str | None = Field(default=None, description="Specific version (defaults to latest)")


class GetPackageDownloadStatsInput(BaseModel):
    package_name: str = Field(description="The name of the npm package")
    api_key: str = Field(default="", description="Optional API key for private registries")
    period: str = Field(default="last-week", description="last-day/week/month/year")


@tool(args_schema=GetPackageInfoInput)
@serialize_pydantic_return
async def get_package_info(
    package_name: str, api_key: str = ""
) -> GetPackageInfoOutput:
    """Get detailed information about an npm package."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_REGISTRY_URL}/{package_name}", headers=_headers(api_key)
            )
        if response.status_code == 404:
            return GetPackageInfoOutput(
                success=False, error=f"Package '{package_name}' not found"
            )
        if response.status_code != 200:
            return GetPackageInfoOutput(
                success=False, error=f"API error: {response.status_code} - {response.text}"
            )
        data = response.json()
    except Exception as exc:
        return GetPackageInfoOutput(success=False, error=f"Request failed: {exc}")

    latest = data.get("dist-tags", {}).get("latest") or "unknown"
    version_data = data.get("versions", {}).get(latest, {})

    return GetPackageInfoOutput(
        success=True,
        name=data.get("name"),
        version=latest,
        description=data.get("description", ""),
        author=_author_name(data.get("author")),
        homepage=data.get("homepage", ""),
        repository=_repo_url(data.get("repository")),
        license=data.get("license", "") if isinstance(data.get("license"), str) else "",
        keywords=data.get("keywords") or [],
        dependencies=version_data.get("dependencies") or {},
        devDependencies=version_data.get("devDependencies") or {},
        peerDependencies=version_data.get("peerDependencies") or {},
    )


@tool(args_schema=SearchPackagesInput)
@serialize_pydantic_return
async def search_packages(
    query: str, api_key: str = "", size: int = 10
) -> SearchPackagesOutput:
    """Search for npm packages by keyword or name."""
    clamped = max(1, min(250, size))
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_REGISTRY_URL}/-/v1/search",
                headers=_headers(api_key),
                params={"text": query, "size": clamped},
            )
        if response.status_code != 200:
            return SearchPackagesOutput(
                success=False, error=f"API error: {response.status_code} - {response.text}"
            )
        data = response.json()
    except Exception as exc:
        return SearchPackagesOutput(success=False, error=f"Request failed: {exc}")

    packages: list[dict[str, Any]] = []
    for obj in data.get("objects") or []:
        pkg = obj.get("package") or {}
        score = obj.get("score") or {}
        detail = score.get("detail") or {}
        packages.append(
            {
                "name": pkg.get("name"),
                "version": pkg.get("version"),
                "description": pkg.get("description", ""),
                "keywords": pkg.get("keywords") or [],
                "author": _author_name(pkg.get("author")),
                "links": pkg.get("links") or {},
                "score": {
                    "final": score.get("final", 0),
                    "quality": detail.get("quality", 0),
                    "popularity": detail.get("popularity", 0),
                    "maintenance": detail.get("maintenance", 0),
                },
            }
        )

    return SearchPackagesOutput(
        success=True, total=data.get("total") or len(packages), packages=packages
    )


@tool(args_schema=GetPopularPackagesInput)
@serialize_pydantic_return
async def get_popular_packages(
    api_key: str = "", size: int = 10
) -> GetPopularPackagesOutput:
    """Get a list of popular npm packages (proxied via 'popularity' search)."""
    clamped = max(1, min(250, size))
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_REGISTRY_URL}/-/v1/search",
                headers=_headers(api_key),
                params={"text": "popularity", "size": clamped},
            )
        if response.status_code != 200:
            return GetPopularPackagesOutput(
                success=False, error=f"API error: {response.status_code} - {response.text}"
            )
        data = response.json()
    except Exception as exc:
        return GetPopularPackagesOutput(success=False, error=f"Request failed: {exc}")

    packages: list[dict[str, Any]] = []
    for obj in data.get("objects") or []:
        pkg = obj.get("package") or {}
        packages.append(
            {
                "name": pkg.get("name"),
                "version": pkg.get("version"),
                "description": pkg.get("description", ""),
                "keywords": pkg.get("keywords") or [],
                "links": pkg.get("links") or {},
            }
        )
    return GetPopularPackagesOutput(success=True, packages=packages)


@tool(args_schema=GetPackageVersionsInput)
@serialize_pydantic_return
async def get_package_versions(
    package_name: str, api_key: str = ""
) -> GetPackageVersionsOutput:
    """Get all available versions of an npm package."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_REGISTRY_URL}/{package_name}", headers=_headers(api_key)
            )
        if response.status_code == 404:
            return GetPackageVersionsOutput(
                success=False, error=f"Package '{package_name}' not found"
            )
        if response.status_code != 200:
            return GetPackageVersionsOutput(
                success=False, error=f"API error: {response.status_code} - {response.text}"
            )
        data = response.json()
    except Exception as exc:
        return GetPackageVersionsOutput(success=False, error=f"Request failed: {exc}")

    versions = list((data.get("versions") or {}).keys())
    time_data = data.get("time") or {}
    version_info = [
        {"version": v, "published": time_data.get(v, "")} for v in versions
    ]
    version_info.sort(key=lambda x: x.get("published", ""), reverse=True)

    return GetPackageVersionsOutput(
        success=True,
        name=data.get("name"),
        dist_tags=data.get("dist-tags") or {},
        versions=version_info,
        total_versions=len(versions),
    )


@tool(args_schema=GetPackageDependenciesInput)
@serialize_pydantic_return
async def get_package_dependencies(
    package_name: str,
    api_key: str = "",
    version: str | None = None,
) -> GetPackageDependenciesOutput:
    """Get the dependencies of an npm package (specific or latest version)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_REGISTRY_URL}/{package_name}", headers=_headers(api_key)
            )
        if response.status_code == 404:
            return GetPackageDependenciesOutput(
                success=False, error=f"Package '{package_name}' not found"
            )
        if response.status_code != 200:
            return GetPackageDependenciesOutput(
                success=False, error=f"API error: {response.status_code} - {response.text}"
            )
        data = response.json()
    except Exception as exc:
        return GetPackageDependenciesOutput(success=False, error=f"Request failed: {exc}")

    target = version or (data.get("dist-tags") or {}).get("latest")
    if not target:
        return GetPackageDependenciesOutput(
            success=False, error="Could not determine package version"
        )
    version_data = (data.get("versions") or {}).get(target)
    if not version_data:
        return GetPackageDependenciesOutput(
            success=False,
            error=f"Version '{target}' not found for package '{package_name}'",
        )

    return GetPackageDependenciesOutput(
        success=True,
        name=package_name,
        version=target,
        dependencies=version_data.get("dependencies") or {},
        devDependencies=version_data.get("devDependencies") or {},
        peerDependencies=version_data.get("peerDependencies") or {},
        optionalDependencies=version_data.get("optionalDependencies") or {},
    )


@tool(args_schema=GetPackageDownloadStatsInput)
@serialize_pydantic_return
async def get_package_download_stats(
    package_name: str,
    api_key: str = "",
    period: str = "last-week",
) -> GetPackageDownloadStatsOutput:
    """Get download statistics for an npm package."""
    if period not in _VALID_PERIODS:
        return GetPackageDownloadStatsOutput(
            success=False,
            error=f"Invalid period '{period}'. Must be one of: {', '.join(_VALID_PERIODS)}",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            point = await client.get(
                f"{_API_URL}/downloads/point/{period}/{package_name}",
                headers=_headers(api_key),
            )
            if point.status_code == 404:
                return GetPackageDownloadStatsOutput(
                    success=False,
                    error=f"Package '{package_name}' not found or has no download data",
                )
            if point.status_code != 200:
                return GetPackageDownloadStatsOutput(
                    success=False,
                    error=f"API error: {point.status_code} - {point.text}",
                )
            point_data = point.json()

            range_resp = await client.get(
                f"{_API_URL}/downloads/range/{period}/{package_name}",
                headers=_headers(api_key),
            )
            daily: list[dict[str, Any]] = []
            if range_resp.status_code == 200:
                daily = (range_resp.json() or {}).get("downloads") or []
    except Exception as exc:
        return GetPackageDownloadStatsOutput(success=False, error=f"Request failed: {exc}")

    return GetPackageDownloadStatsOutput(
        success=True,
        package=package_name,
        period=period,
        start=point_data.get("start"),
        end=point_data.get("end"),
        total_downloads=point_data.get("downloads") or 0,
        daily_downloads=daily,
    )
