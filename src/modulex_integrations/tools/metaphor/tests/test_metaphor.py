"""Happy-path tests for every metaphor @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.metaphor import (
    TOOLS,
    find_similar_links,
    get_documents_content,
    manifest,
    search,
)
from modulex_integrations.tools.metaphor.outputs import (
    FindSimilarLinksOutput,
    GetDocumentsContentOutput,
    SearchOutput,
)

API = "https://api.metaphor.systems"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={
            "results": [
                {
                    "title": "Example Result",
                    "url": "https://example.com",
                    "publishedDate": "2024-01-01",
                    "author": "Author",
                    "id": "abc123",
                    "score": 0.95,
                }
            ],
            "autopromptString": "enhanced query",
        },
    )

    result_dict = await search.ainvoke(_args(query="test query", use_autoprompt=False))

    assert isinstance(result_dict, dict)
    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.results) == 1
    assert result.results[0].title == "Example Result"
    assert result.autoprompt_string == "enhanced query"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_find_similar_links(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/findSimilar",
        json={
            "results": [
                {
                    "title": "Similar Page",
                    "url": "https://similar.com",
                    "id": "def456",
                    "score": 0.88,
                }
            ],
        },
    )

    result_dict = await find_similar_links.ainvoke(_args(url="https://example.com"))

    assert isinstance(result_dict, dict)
    result = FindSimilarLinksOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.results) == 1
    assert result.results[0].url == "https://similar.com"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_get_documents_content(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contents?ids=abc123&ids=def456",
        json={
            "contents": [
                {
                    "id": "abc123",
                    "url": "https://example.com",
                    "title": "Example",
                    "extract": "This is the extracted content...",
                }
            ],
        },
    )

    result_dict = await get_documents_content.ainvoke(
        _args(ids=["abc123", "def456"])
    )

    assert isinstance(result_dict, dict)
    result = GetDocumentsContentOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.contents) == 1
    assert result.contents[0].extract == "This is the extracted content..."

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_search_validates_empty_api_key() -> None:
    result_dict = await search.ainvoke({"query": "x", "api_key": ""})
    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")


@pytest.mark.asyncio
async def test_search_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await search.ainvoke(_args(query="anything", use_autoprompt=False))
    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error
