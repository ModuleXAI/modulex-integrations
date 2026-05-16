"""Tests for the TinyURL integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.tinyurl import (
    TOOLS,
    create_shortened_link,
    manifest,
    retrieve_link_analytics,
    update_link_metadata,
)
from modulex_integrations.tools.tinyurl.outputs import (
    CreateShortenedLinkOutput,
    RetrieveLinkAnalyticsOutput,
    UpdateLinkMetadataOutput,
)

API = "https://api.tinyurl.com"
_API_KEY = "tinyurl-fake-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_three_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_tools_match_actions(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_auth_is_api_key(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_create_shortened_link(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/create",
        status_code=201,
        json={
            "data": {
                "tiny_url": "https://tinyurl.com/abc123",
                "url": "https://example.com/very/long/url",
                "domain": "tinyurl.com",
                "alias": "abc123",
                "created_at": "2026-05-16T12:00:00Z",
            }
        },
    )

    result_dict = await create_shortened_link.ainvoke(
        _args(url="https://example.com/very/long/url")
    )
    result = CreateShortenedLinkOutput.model_validate(result_dict)
    assert result.success is True
    assert result.tiny_url == "https://tinyurl.com/abc123"
    assert result.alias == "abc123"


@pytest.mark.asyncio
async def test_create_shortened_link_handles_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/create",
        status_code=400,
        json={"errors": ["alias already taken"]},
    )
    result_dict = await create_shortened_link.ainvoke(
        _args(url="https://example.com", alias="taken")
    )
    result = CreateShortenedLinkOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "alias already taken" in result.error


@pytest.mark.asyncio
async def test_retrieve_link_analytics(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/analytics?from=2026-01-01&alias=abc123",
        json={
            "total_clicks": 42,
            "date_range": {"from": "2026-01-01", "to": "2026-05-16"},
            "clicks_by_country": [{"country": "US", "clicks": 30}],
            "clicks_by_device": [{"device": "mobile", "clicks": 25}],
            "clicks_by_referrer": [],
        },
    )

    result_dict = await retrieve_link_analytics.ainvoke(
        _args(domain="tinyurl.com", alias="abc123", from_date="2026-01-01")
    )
    result = RetrieveLinkAnalyticsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_clicks == 42
    assert result.clicks_by_country[0]["country"] == "US"


@pytest.mark.asyncio
async def test_update_link_metadata(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/update",
        json={
            "data": {
                "tiny_url": "https://tinyurl.com/newname",
                "url": "https://example.com",
                "domain": "tinyurl.com",
                "alias": "newname",
                "updated_at": "2026-05-16T13:00:00Z",
                "analytics_enabled": True,
            }
        },
    )

    result_dict = await update_link_metadata.ainvoke(
        _args(domain="tinyurl.com", alias="abc123", new_alias="newname", new_stats=True)
    )
    result = UpdateLinkMetadataOutput.model_validate(result_dict)
    assert result.success is True
    assert result.alias == "newname"
    assert result.analytics_enabled is True


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result_dict = await create_shortened_link.ainvoke(
        {"api_key": "", "url": "https://example.com"}
    )
    result = CreateShortenedLinkOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "API token" in result.error
