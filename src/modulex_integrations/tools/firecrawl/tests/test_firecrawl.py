"""Tests for the Firecrawl integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.firecrawl import (
    TOOLS,
    batch_scrape,
    check_crawl_status,
    crawl,
    extract,
    manifest,
    map_website,
    scrape,
    search,
)
from modulex_integrations.tools.firecrawl.outputs import (
    BatchScrapeOutput,
    CheckCrawlStatusOutput,
    CrawlOutput,
    ExtractOutput,
    MapWebsiteOutput,
    ScrapeOutput,
    SearchOutput,
)

API = "https://api.firecrawl.dev/v1"
_API_KEY = "fc-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_seven_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"api_key"}

    def test_test_endpoints_post_to_scrape(self) -> None:
        for auth in manifest.auth_schemas:
            assert auth.test_endpoint is not None
            assert auth.test_endpoint.method == "POST"
            assert auth.test_endpoint.url.endswith("/v1/scrape")


@pytest.mark.asyncio
async def test_scrape(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/scrape",
        json={
            "success": True,
            "data": {
                "markdown": "# Hello",
                "metadata": {"title": "Example", "sourceURL": "https://example.com"},
            },
        },
    )

    result_dict = await scrape.ainvoke(_args(url="https://example.com"))
    assert isinstance(result_dict, dict)
    result = ScrapeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["data"]["markdown"] == "# Hello"


@pytest.mark.asyncio
async def test_scrape_handles_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/scrape",
        status_code=402,
        text="Payment Required",
    )
    result = ScrapeOutput.model_validate(
        await scrape.ainvoke(_args(url="https://example.com"))
    )
    assert result.success is False
    assert result.error is not None and "402" in result.error


@pytest.mark.asyncio
async def test_map_website(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/map",
        json={"success": True, "links": ["https://example.com/a", "https://example.com/b"]},
    )
    result = MapWebsiteOutput.model_validate(
        await map_website.ainvoke(_args(url="https://example.com", limit=10))
    )
    assert result.success is True
    assert result.data is not None
    assert len(result.data["links"]) == 2


@pytest.mark.asyncio
async def test_search(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={
            "success": True,
            "data": [
                {"url": "https://example.com/r1", "title": "R1", "description": "..."}
            ],
        },
    )
    result = SearchOutput.model_validate(
        await search.ainvoke(_args(query="site:example.com"))
    )
    assert result.success is True
    assert result.data is not None
    assert len(result.data["data"]) == 1


@pytest.mark.asyncio
async def test_crawl(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/crawl",
        status_code=200,
        json={"success": True, "id": "job-123", "url": "https://example.com"},
    )
    result = CrawlOutput.model_validate(
        await crawl.ainvoke(_args(url="https://example.com", limit=5))
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "job-123"


@pytest.mark.asyncio
async def test_check_crawl_status(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/crawl/job-123",
        json={
            "success": True,
            "status": "completed",
            "completed": 3,
            "total": 3,
            "data": [],
        },
    )
    result = CheckCrawlStatusOutput.model_validate(
        await check_crawl_status.ainvoke(_args(crawl_id="job-123"))
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["status"] == "completed"


@pytest.mark.asyncio
async def test_extract(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/extract",
        json={"success": True, "id": "ext-1"},
    )
    result = ExtractOutput.model_validate(
        await extract.ainvoke(
            _args(
                urls=["https://example.com"],
                prompt="extract product details",
                schema_definition={"type": "object", "properties": {"price": {"type": "number"}}},
            )
        )
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "ext-1"


@pytest.mark.asyncio
async def test_batch_scrape(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/batch/scrape",
        status_code=201,
        json={"success": True, "id": "bs-1", "url": f"{API}/batch/scrape/bs-1"},
    )
    result = BatchScrapeOutput.model_validate(
        await batch_scrape.ainvoke(
            _args(urls=["https://example.com/a", "https://example.com/b"])
        )
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "bs-1"


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = ScrapeOutput.model_validate(
        await scrape.ainvoke({"api_key": "", "url": "https://example.com"})
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
