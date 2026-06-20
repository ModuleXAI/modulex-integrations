"""Happy-path test per action + a failure-path test for the
non-2xx -> success=False branch and an empty-credential test (Linkup
does not raise on errors)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.linkup import TOOLS, manifest, search
from modulex_integrations.tools.linkup.outputs import SearchOutput

API = "https://api.linkup.so/v1"
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


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_search_sourced_answer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={
            "answer": "Linkup is a web search API.",
            "sources": [
                {
                    "name": "Linkup docs",
                    "url": "https://docs.linkup.so",
                    "snippet": "Linkup is a production-grade web search API.",
                }
            ],
        },
    )

    result_dict = await search.ainvoke(_args(q="what is linkup"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.answer == "Linkup is a web search API."
    assert result.sources[0].name == "Linkup docs"
    assert result.sources[0].url == "https://docs.linkup.so"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_search_results(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={
            "results": [
                {
                    "type": "text",
                    "name": "AI paper",
                    "url": "https://example.com/paper",
                    "content": "The paper discusses transformers.",
                }
            ]
        },
    )

    result_dict = await search.ainvoke(
        _args(q="ai papers", output_type="searchResults")
    )

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.results[0].name == "AI paper"
    assert result.results[0].type == "text"
    assert result.answer is None

    # Request body should carry the documented camelCase keys + split domains.
    import json as _json

    sent = httpx_mock.get_requests()[0]
    body = _json.loads(sent.content)
    assert body["outputType"] == "searchResults"
    assert body["q"] == "ai papers"


@pytest.mark.asyncio
async def test_search_splits_domains(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/search", json={"answer": "ok"})

    await search.ainvoke(
        _args(
            q="x",
            include_domains="example.com, another.com",
            exclude_domains="spam.com",
        )
    )

    import json as _json

    sent = httpx_mock.get_requests()[0]
    body = _json.loads(sent.content)
    assert body["includeDomains"] == ["example.com", "another.com"]
    assert body["excludeDomains"] == ["spam.com"]


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Linkup errors come back as HTTP 4xx/5xx; the tool wraps them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await search.ainvoke(_args(q="anything"))

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_search_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await search.ainvoke({"q": "x", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
