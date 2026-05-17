"""Tests for the Scrape.do integration."""
from __future__ import annotations

import base64
from typing import Any

import pytest

from modulex_integrations.tools.scrape_do import (
    TOOLS,
    get_usage_stats,
    manifest,
    scrape,
    scrape_to_markdown,
    scrape_with_js,
    take_screenshot,
)
from modulex_integrations.tools.scrape_do.outputs import (
    GetUsageStatsOutput,
    ScrapeOutput,
    ScrapeToMarkdownOutput,
    ScrapeWithJsOutput,
    TakeScreenshotOutput,
)

API = "https://api.scrape.do"
_API_KEY = "scrapedo-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_five_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]

    def test_test_endpoint_uses_token_query_param(self) -> None:
        auth = manifest.auth_schemas[0]
        assert auth.test_endpoint is not None
        assert auth.test_endpoint.params == {"token": "{api_key}"}


@pytest.mark.asyncio
async def test_scrape_text_response(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}?token={_API_KEY}&url=https%3A%2F%2Fexample.com",
        text="<html><body>Hello</body></html>",
        headers={"content-type": "text/html; charset=utf-8"},
    )
    result_dict = await scrape.ainvoke(_args(url="https://example.com"))
    assert isinstance(result_dict, dict)
    result = ScrapeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.is_binary is False
    assert result.data is not None and "Hello" in result.data
    assert result.content_type is not None
    assert "text/html" in result.content_type


@pytest.mark.asyncio
async def test_scrape_image_response_is_base64(httpx_mock: Any) -> None:
    raw_bytes = b"\x89PNG\r\n\x1a\n" + b"fake-png-bytes"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}?token={_API_KEY}&url=https%3A%2F%2Fexample.com%2Fcat.png",
        content=raw_bytes,
        headers={"content-type": "image/png"},
    )
    result = ScrapeOutput.model_validate(
        await scrape.ainvoke(_args(url="https://example.com/cat.png"))
    )
    assert result.success is True
    assert result.is_binary is True
    assert result.data is not None
    assert base64.b64decode(result.data) == raw_bytes


@pytest.mark.asyncio
async def test_scrape_with_js_sets_render_true(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?token={_API_KEY}&url=https%3A%2F%2Fexample.com"
            "&render=true&waitUntil=networkidle0"
        ),
        text="<html>js</html>",
        headers={"content-type": "text/html"},
    )
    result = ScrapeWithJsOutput.model_validate(
        await scrape_with_js.ainvoke(
            _args(url="https://example.com", wait_until="networkidle0")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_take_screenshot_json_response(httpx_mock: Any) -> None:
    json_body = {
        "statusCode": 200,
        "screenShots": [{"type": "viewport", "image": "iVBORw0KG..."}],
        "content": "<html></html>",
    }
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?token={_API_KEY}&url=https%3A%2F%2Fexample.com"
            "&render=true&blockResources=false&returnJSON=true"
            "&screenShot=true&fullScreenShot=false"
        ),
        json=json_body,
        headers={"content-type": "application/json"},
    )
    result = TakeScreenshotOutput.model_validate(
        await take_screenshot.ainvoke(_args(url="https://example.com"))
    )
    assert result.success is True
    assert result.payload is not None
    assert result.payload["screenShots"][0]["type"] == "viewport"


@pytest.mark.asyncio
async def test_take_screenshot_rejects_conflicting_modes() -> None:
    result = TakeScreenshotOutput.model_validate(
        await take_screenshot.ainvoke(
            _args(url="https://example.com", full_page=True, selector="#hero")
        )
    )
    assert result.success is False
    assert result.error is not None and "full_page or selector" in result.error


@pytest.mark.asyncio
async def test_scrape_to_markdown(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?token={_API_KEY}&url=https%3A%2F%2Fexample.com"
            "&output=markdown"
        ),
        text="# Example\n\nHello world.",
        headers={"content-type": "text/markdown"},
    )
    result = ScrapeToMarkdownOutput.model_validate(
        await scrape_to_markdown.ainvoke(_args(url="https://example.com"))
    )
    assert result.success is True
    assert result.markdown is not None
    assert result.markdown.startswith("# Example")


@pytest.mark.asyncio
async def test_get_usage_stats(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/info?token={_API_KEY}",
        json={
            "IsActive": True,
            "ConcurrentRequest": 0,
            "MaxMonthlyRequest": 10000,
            "RemainingMonthlyRequest": 9999,
        },
    )
    result = GetUsageStatsOutput.model_validate(
        await get_usage_stats.ainvoke(_args())
    )
    assert result.success is True
    assert result.stats is not None
    assert result.stats["RemainingMonthlyRequest"] == 9999


@pytest.mark.asyncio
async def test_scrape_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}?token={_API_KEY}&url=https%3A%2F%2Fexample.com",
        status_code=429,
        text="rate limited",
    )
    result = ScrapeOutput.model_validate(
        await scrape.ainvoke(_args(url="https://example.com"))
    )
    assert result.success is False
    assert result.status_code == 429
    assert result.error is not None and "429" in result.error


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = ScrapeOutput.model_validate(
        await scrape.ainvoke({"api_key": "", "url": "https://example.com"})
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
