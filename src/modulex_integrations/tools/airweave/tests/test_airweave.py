"""Happy-path test for the single search action + failure-path
(non-2xx -> success=False) and empty-credential tests."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.airweave import TOOLS, manifest, search
from modulex_integrations.tools.airweave.outputs import SearchOutput

API = "https://api.airweave.ai"
_API_KEY = "fake-api-key"
_COLLECTION = "my-collection"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, collection_id=_COLLECTION, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/collections/{_COLLECTION}/search",
        json={
            "results": [
                {
                    "entity_id": "ent-1",
                    "source_name": "GitHub",
                    "md_content": "# Title\n\nbody text",
                    "score": 0.87,
                    "metadata": {"repo": "acme/widgets"},
                    "breadcrumbs": ["acme", "widgets", "README"],
                    "url": "https://example.com/readme",
                }
            ],
            "completion": "The widget README explains setup.",
        },
    )

    result_dict = await search.ainvoke(
        _args(query="how do I set up widgets", generate_answer=True)
    )

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_results == 1
    assert result.results[0].entity_id == "ent-1"
    assert result.results[0].source_name == "GitHub"
    assert result.results[0].score == 0.87
    assert result.results[0].breadcrumbs == ["acme", "widgets", "README"]
    assert result.completion == "The widget README explains setup."

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_search_empty_results(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/collections/{_COLLECTION}/search",
        json={"results": []},
    )

    result_dict = await search.ainvoke(_args(query="nothing matches"))

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.results == []
    assert result.total_results == 0
    assert result.completion is None


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Errors come back as HTTP 4xx/5xx and are wrapped in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/collections/{_COLLECTION}/search",
        status_code=401,
        json={"detail": "Invalid API key"},
    )

    result_dict = await search.ainvoke(_args(query="anything"))

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error
    assert "Invalid API key" in result.error


@pytest.mark.asyncio
async def test_search_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await search.ainvoke(
        {"query": "x", "collection_id": _COLLECTION, "api_key": ""}
    )

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_search_validates_empty_collection_id() -> None:
    """Empty collection_id short-circuits before the HTTP call."""
    result_dict = await search.ainvoke(
        {"query": "x", "collection_id": "", "api_key": _API_KEY}
    )

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "collection" in result.error.lower()
