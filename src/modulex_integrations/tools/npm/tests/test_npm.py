"""Tests for the NPM integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.npm import (
    TOOLS,
    get_package_dependencies,
    get_package_download_stats,
    get_package_info,
    get_package_versions,
    get_popular_packages,
    manifest,
    search_packages,
)
from modulex_integrations.tools.npm.outputs import (
    GetPackageDependenciesOutput,
    GetPackageDownloadStatsOutput,
    GetPackageInfoOutput,
    GetPackageVersionsOutput,
    GetPopularPackagesOutput,
    SearchPackagesOutput,
)

REG = "https://registry.npmjs.org"
DL = "https://api.npmjs.org"


class TestManifest:
    def test_six_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_tools_match_actions(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_api_key_is_optional(self) -> None:
        env = manifest.auth_schemas[0].setup_environment_variables[0]
        assert env.required is False


@pytest.mark.asyncio
async def test_get_package_info(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{REG}/express",
        json={
            "name": "express",
            "description": "Fast minimalist web framework",
            "homepage": "https://expressjs.com/",
            "repository": {"url": "git+https://github.com/expressjs/express.git"},
            "license": "MIT",
            "keywords": ["web"],
            "author": {"name": "TJ Holowaychuk"},
            "dist-tags": {"latest": "4.18.0"},
            "versions": {
                "4.18.0": {
                    "dependencies": {"accepts": "1.3.8"},
                    "devDependencies": {"mocha": "1"},
                    "peerDependencies": {},
                }
            },
        },
    )

    result_dict = await get_package_info.ainvoke({"package_name": "express"})
    result = GetPackageInfoOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "express"
    assert result.version == "4.18.0"
    assert result.author == "TJ Holowaychuk"
    assert "accepts" in result.dependencies


@pytest.mark.asyncio
async def test_get_package_info_not_found(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{REG}/does-not-exist", status_code=404, text=""
    )
    result_dict = await get_package_info.ainvoke({"package_name": "does-not-exist"})
    result = GetPackageInfoOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "not found" in result.error


@pytest.mark.asyncio
async def test_search_packages(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{REG}/-/v1/search?text=react&size=10",
        json={
            "total": 1,
            "objects": [
                {
                    "package": {
                        "name": "react",
                        "version": "18.0.0",
                        "description": "React",
                        "links": {"homepage": "https://react.dev"},
                    },
                    "score": {
                        "final": 0.95,
                        "detail": {"quality": 0.9, "popularity": 0.99, "maintenance": 0.9},
                    },
                }
            ],
        },
    )
    result_dict = await search_packages.ainvoke({"query": "react"})
    result = SearchPackagesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.packages[0]["name"] == "react"
    assert result.packages[0]["score"]["popularity"] == 0.99


@pytest.mark.asyncio
async def test_get_popular_packages(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{REG}/-/v1/search?text=popularity&size=10",
        json={"objects": [{"package": {"name": "lodash", "version": "4.17.21"}}]},
    )
    result_dict = await get_popular_packages.ainvoke({})
    result = GetPopularPackagesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.packages[0]["name"] == "lodash"


@pytest.mark.asyncio
async def test_get_package_versions(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{REG}/express",
        json={
            "name": "express",
            "dist-tags": {"latest": "4.18.0"},
            "versions": {"4.17.0": {}, "4.18.0": {}},
            "time": {"4.17.0": "2021-01-01", "4.18.0": "2022-01-01"},
        },
    )
    result_dict = await get_package_versions.ainvoke({"package_name": "express"})
    result = GetPackageVersionsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_versions == 2
    # Sorted descending by publication date
    assert result.versions[0]["version"] == "4.18.0"


@pytest.mark.asyncio
async def test_get_package_dependencies_latest(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{REG}/express",
        json={
            "dist-tags": {"latest": "4.18.0"},
            "versions": {
                "4.18.0": {
                    "dependencies": {"a": "1"},
                    "devDependencies": {"b": "2"},
                }
            },
        },
    )
    result_dict = await get_package_dependencies.ainvoke({"package_name": "express"})
    result = GetPackageDependenciesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.version == "4.18.0"
    assert result.dependencies == {"a": "1"}


@pytest.mark.asyncio
async def test_get_package_download_stats(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{DL}/downloads/point/last-week/express",
        json={"start": "2026-05-09", "end": "2026-05-16", "downloads": 12345},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{DL}/downloads/range/last-week/express",
        json={"downloads": [{"day": "2026-05-09", "downloads": 1000}]},
    )

    result_dict = await get_package_download_stats.ainvoke({"package_name": "express"})
    result = GetPackageDownloadStatsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_downloads == 12345
    assert len(result.daily_downloads) == 1


@pytest.mark.asyncio
async def test_download_stats_invalid_period() -> None:
    result_dict = await get_package_download_stats.ainvoke(
        {"package_name": "express", "period": "last-decade"}
    )
    result = GetPackageDownloadStatsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "Invalid period" in result.error
