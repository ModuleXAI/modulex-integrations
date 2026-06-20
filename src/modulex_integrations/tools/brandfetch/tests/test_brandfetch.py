"""Happy-path tests per action + failure-path and empty-credential tests
for the non-2xx -> success=False branch (Brandfetch tools don't raise)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.brandfetch import (
    TOOLS,
    get_brand,
    manifest,
    search,
)
from modulex_integrations.tools.brandfetch.outputs import GetBrandOutput, SearchOutput

API = "https://api.brandfetch.io/v2"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:brandfetch-themed"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_get_brand(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/brands/nike.com",
        json={
            "id": "id_abc",
            "name": "Nike",
            "domain": "nike.com",
            "claimed": True,
            "description": "Just do it.",
            "longDescription": "Nike, Inc. is an American athletic footwear company.",
            "links": [{"name": "twitter", "url": "https://twitter.com/nike"}],
            "logos": [
                {
                    "type": "logo",
                    "theme": "dark",
                    "formats": [
                        {
                            "src": "https://asset.brandfetch.io/nike.svg",
                            "format": "svg",
                            "width": 400,
                            "height": 200,
                            "background": None,
                            "size": 1234,
                        }
                    ],
                }
            ],
            "colors": [{"hex": "#111111", "type": "dark", "brightness": 17}],
            "fonts": [
                {
                    "name": "Helvetica",
                    "type": "title",
                    "origin": "system",
                    "originId": None,
                    "weights": [400, 700],
                }
            ],
            "company": {"employees": "10000+", "foundedYear": 1964},
            "qualityScore": 0.95,
            "isNsfw": False,
        },
    )

    result_dict = await get_brand.ainvoke(_args(identifier="nike.com"))

    assert isinstance(result_dict, dict)

    result = GetBrandOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Nike"
    assert result.domain == "nike.com"
    assert result.claimed is True
    assert result.links[0].name == "twitter"
    assert result.logos[0].formats[0].format == "svg"
    assert result.colors[0].hex == "#111111"
    assert result.fonts[0].name == "Helvetica"
    assert result.company == {"employees": "10000+", "foundedYear": 1964}
    assert result.quality_score == 0.95
    assert result.is_nsfw is False

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/search/Nike",
        json=[
            {
                "brandId": "id_abc",
                "name": "Nike",
                "domain": "nike.com",
                "claimed": True,
                "icon": "https://asset.brandfetch.io/nike-icon.png",
            },
            {
                "brandId": "id_def",
                "name": "Nike Store",
                "domain": "store.nike.com",
                "claimed": False,
                "icon": None,
            },
        ],
    )

    result_dict = await search.ainvoke(_args(name="Nike"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_results == 2
    assert result.results[0].brand_id == "id_abc"
    assert result.results[0].domain == "nike.com"
    assert result.results[1].name == "Nike Store"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_get_brand_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Brandfetch errors come back as HTTP 4xx/5xx; the tool wraps them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/brands/unknown.example",
        status_code=404,
        text="Brand not found",
    )

    result_dict = await get_brand.ainvoke(_args(identifier="unknown.example"))

    assert isinstance(result_dict, dict)

    result = GetBrandOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error


@pytest.mark.asyncio
async def test_search_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await search.ainvoke({"name": "Nike", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_get_brand_validates_empty_api_key() -> None:
    result_dict = await get_brand.ainvoke({"identifier": "nike.com", "api_key": "  "})

    assert isinstance(result_dict, dict)

    result = GetBrandOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
