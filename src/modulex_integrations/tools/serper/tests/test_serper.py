"""Happy-path tests for each search type + failure-path and
empty-credential tests for the non-raising error branches."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.serper import TOOLS, manifest, search
from modulex_integrations.tools.serper.outputs import SearchOutput

API = "https://google.serper.dev"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:serper-themed"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_search_web(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={
            "organic": [
                {
                    "title": "OpenAI",
                    "link": "https://openai.com",
                    "snippet": "AI research lab.",
                    "position": 1,
                }
            ],
            "knowledgeGraph": {"title": "OpenAI", "type": "Company"},
            "relatedSearches": [{"query": "openai gpt"}],
        },
    )

    result_dict = await search.ainvoke(_args(query="openai", num=10, gl="us", hl="en"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.search_type == "search"
    assert result.search_results[0].title == "OpenAI"
    assert result.search_results[0].position == 1
    assert result.knowledge_graph == {"title": "OpenAI", "type": "Company"}
    assert result.related_searches == [{"query": "openai gpt"}]

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-API-KEY"] == _API_KEY
    import json

    body = json.loads(sent.content)
    assert body == {"q": "openai", "num": 10, "gl": "us", "hl": "en"}


@pytest.mark.asyncio
async def test_search_news(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/news",
        json={
            "news": [
                {
                    "title": "Breaking",
                    "link": "https://news.example.com/a",
                    "snippet": "Something happened.",
                    "date": "2 hours ago",
                    "source": "Example News",
                    "imageUrl": "https://img.example.com/a.jpg",
                }
            ]
        },
    )

    result_dict = await search.ainvoke(_args(query="breaking", type="news"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.search_type == "news"
    item = result.search_results[0]
    assert item.title == "Breaking"
    assert item.date == "2 hours ago"
    assert item.image_url == "https://img.example.com/a.jpg"
    assert item.source == "Example News"
    assert item.position == 1


@pytest.mark.asyncio
async def test_search_places(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/places",
        json={
            "places": [
                {
                    "title": "Blue Bottle Coffee",
                    "link": "https://maps.example.com/bluebottle",
                    "snippet": "Coffee shop",
                    "rating": 4.6,
                    "reviews": 1200,
                    "address": "123 Main St, Seattle",
                }
            ]
        },
    )

    result_dict = await search.ainvoke(_args(query="coffee in seattle", type="places"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.search_type == "places"
    item = result.search_results[0]
    assert item.title == "Blue Bottle Coffee"
    assert item.rating == 4.6
    assert item.reviews == 1200
    assert item.address == "123 Main St, Seattle"


@pytest.mark.asyncio
async def test_search_images(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/images",
        json={
            "images": [
                {
                    "title": "A cat",
                    "link": "https://example.com/cat-page",
                    "snippet": "cute cat",
                    "imageUrl": "https://example.com/cat.jpg",
                }
            ]
        },
    )

    result_dict = await search.ainvoke(_args(query="cat", type="images"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.search_type == "images"
    item = result.search_results[0]
    assert item.title == "A cat"
    assert item.image_url == "https://example.com/cat.jpg"
    assert item.position == 1


@pytest.mark.asyncio
async def test_unknown_type_falls_back_to_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={"organic": [{"title": "X", "link": "https://x.example", "position": 1}]},
    )

    result_dict = await search.ainvoke(_args(query="x", type="nonsense"))

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.search_type == "search"
    assert result.search_results[0].title == "X"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Serper errors come back as HTTP 4xx/5xx; we wrap them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        status_code=403,
        text="Forbidden",
    )

    result_dict = await search.ainvoke(_args(query="anything"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "403" in result.error


@pytest.mark.asyncio
async def test_search_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await search.ainvoke({"query": "x", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
