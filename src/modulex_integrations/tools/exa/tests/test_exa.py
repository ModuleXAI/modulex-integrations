"""Happy-path tests per action + one failure-path test for the
non-2xx → success=False branch (since Exa doesn't raise on errors)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.exa import (
    TOOLS,
    answer,
    find_similar,
    get_contents,
    manifest,
    search,
)
from modulex_integrations.tools.exa.outputs import (
    AnswerOutput,
    FindSimilarOutput,
    GetContentsOutput,
    SearchOutput,
)

API = "https://api.exa.ai"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_and_modulex_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key", "modulex_key"}

    def test_test_endpoints_carry_post_body(self) -> None:
        # Both auth_schemas use POST /search with a body to validate the
        # credential. Tests the new TestEndpoint.body schema field.
        for auth in manifest.auth_schemas:
            assert auth.test_endpoint is not None
            assert auth.test_endpoint.method == "POST"
            assert auth.test_endpoint.body == {"query": "test", "numResults": 1}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={
            "results": [
                {
                    "title": "AI paper",
                    "url": "https://example.com/paper",
                    "publishedDate": "2025-01-01",
                    "author": "alice",
                    "score": 0.91,
                    "text": "The paper discusses...",
                }
            ],
            "resolvedSearchType": "neural",
            "requestId": "req-001",
        },
    )

    result_dict = await search.ainvoke(_args(query="ai papers"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.results[0].title == "AI paper"
    assert result.results[0].score == 0.91
    assert result.search_type == "neural"
    assert result.request_id == "req-001"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_get_contents(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contents",
        json={
            "results": [
                {
                    "url": "https://example.com/a",
                    "title": "Article A",
                    "publishedDate": "2025-02-01",
                    "author": None,
                    "text": "Full article text here.",
                }
            ],
            "requestId": "req-002",
        },
    )

    result_dict = await get_contents.ainvoke(_args(urls=["https://example.com/a"]))

    assert isinstance(result_dict, dict)

    result = GetContentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.results[0].text == "Full article text here."
    assert result.total_results == 1


@pytest.mark.asyncio
async def test_find_similar(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/findSimilar",
        json={
            "results": [
                {
                    "title": "Similar paper",
                    "url": "https://example.com/sim",
                    "publishedDate": "2025-03-01",
                    "score": 0.85,
                }
            ],
            "requestId": "req-003",
        },
    )

    result_dict = await find_similar.ainvoke(_args(url="https://example.com/source"))

    assert isinstance(result_dict, dict)

    result = FindSimilarOutput.model_validate(result_dict)
    assert result.success is True
    assert result.source_url == "https://example.com/source"
    assert result.results[0].score == 0.85


@pytest.mark.asyncio
async def test_answer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/answer",
        json={
            "answer": "Forty-two.",
            "results": [
                {
                    "title": "Hitchhiker",
                    "url": "https://example.com/h2g2",
                    "publishedDate": "1979-10-12",
                }
            ],
            "requestId": "req-004",
        },
    )

    result_dict = await answer.ainvoke(_args(query="ultimate answer"))

    assert isinstance(result_dict, dict)

    result = AnswerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.answer == "Forty-two."
    assert result.sources[0].title == "Hitchhiker"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Exa errors come back as HTTP 4xx/5xx; legacy wraps them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await search.ainvoke(_args(query="anything"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_search_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await search.ainvoke({"query": "x", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
