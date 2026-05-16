"""Happy-path tests using ``unittest.mock.patch`` on ``langchain_tavily.TavilySearch``.

This is the canonical SDK test pattern from CONTRIBUTING.md: instead
of mocking HTTP (httpx is not used by tavily), we mock the vendor SDK
class so its ``.ainvoke()`` returns a representative payload.

Coverage:
- 3 happy-path tests (one per @tool) — mock TavilySearch, assert the
  output model parses the SDK payload correctly.
- 1 empty-api-key test (short-circuit before the SDK is constructed).
- 1 missing-SDK test (sets ``sys.modules["langchain_tavily"] = None``
  so the lazy ``from langchain_tavily import TavilySearch`` raises
  ImportError, hitting the graceful-degradation branch).
"""
from __future__ import annotations

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modulex_integrations.tools.tavily import (
    TOOLS,
    answer_search,
    manifest,
    news_search,
    web_search,
)
from modulex_integrations.tools.tavily.outputs import (
    AnswerSearchOutput,
    NewsSearchOutput,
    WebSearchOutput,
)

_API_KEY = "tvly-fake-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_and_modulex_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key", "modulex_key"}


# --- Happy-path tests via mocked SDK ---------------------------------------


def _mock_tavily_search(payload: Any) -> MagicMock:
    """Return a MagicMock that, when *called* (TavilySearch(...)) and
    then ``.ainvoke(...)``'d, returns ``payload``."""
    instance = MagicMock()
    instance.ainvoke = AsyncMock(return_value=payload)
    cls = MagicMock(return_value=instance)
    return cls


@pytest.mark.asyncio
async def test_web_search() -> None:
    fake_payload = {
        "query": "ai papers",
        "results": [
            {
                "url": "https://example.com/paper",
                "title": "AI Paper",
                "content": "AI is...",
                "score": 0.91,
                "raw_content": None,
            }
        ],
        "answer": None,
        "images": [],
        "response_time": 0.42,
        "request_id": "req-001",
    }
    mock_cls = _mock_tavily_search(fake_payload)

    with patch.dict(sys.modules, {"langchain_tavily": MagicMock(TavilySearch=mock_cls)}):
        result_dict = await web_search.ainvoke(_args(query="ai papers"))

    assert isinstance(result_dict, dict)

    result = WebSearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.query == "ai papers"
    assert result.results[0].score == 0.91
    assert result.response_time == 0.42

    # SDK was instantiated with our api_key and search_depth
    init_kwargs = mock_cls.call_args.kwargs
    assert init_kwargs["tavily_api_key"] == _API_KEY
    assert init_kwargs["search_depth"] == "basic"


@pytest.mark.asyncio
async def test_answer_search() -> None:
    fake_payload = {
        "query": "ultimate answer",
        "results": [
            {
                "url": "https://example.com/h2g2",
                "title": "Hitchhiker",
                "content": "deep thought",
                "score": 0.88,
            }
        ],
        "answer": "Forty-two.",
        "images": [],
        "response_time": 1.2,
        "request_id": "req-002",
    }
    mock_cls = _mock_tavily_search(fake_payload)

    with patch.dict(sys.modules, {"langchain_tavily": MagicMock(TavilySearch=mock_cls)}):
        result_dict = await answer_search.ainvoke(_args(query="ultimate answer"))

    assert isinstance(result_dict, dict)

    result = AnswerSearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.answer == "Forty-two."
    assert result.results[0].title == "Hitchhiker"

    # answer_search forces include_answer=True regardless of args
    init_kwargs = mock_cls.call_args.kwargs
    assert init_kwargs["include_answer"] is True


@pytest.mark.asyncio
async def test_news_search() -> None:
    fake_payload = {
        "query": "tech news recent 3 days",  # the tool augments the query
        "results": [
            {
                "url": "https://example.com/news",
                "title": "Big AI news",
                "content": "Today...",
                "score": 0.75,
            }
        ],
        "images": [],
        "response_time": 0.5,
        "request_id": "req-003",
    }
    mock_cls = _mock_tavily_search(fake_payload)

    with patch.dict(sys.modules, {"langchain_tavily": MagicMock(TavilySearch=mock_cls)}):
        result_dict = await news_search.ainvoke(_args(query="tech", days=3))

    assert isinstance(result_dict, dict)

    result = NewsSearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.results[0].url == "https://example.com/news"

    # news_search calls .ainvoke with the augmented query string
    call_arg = mock_cls.return_value.ainvoke.call_args.args[0]
    assert "tech" in call_arg["query"]
    assert "days" in call_arg["query"]


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_web_search_short_circuits_on_empty_key() -> None:
    """Empty api_key bypasses the SDK entirely — no import, no instantiation."""
    result_dict = await web_search.ainvoke({"query": "x", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = WebSearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_web_search_handles_missing_sdk() -> None:
    """If langchain-tavily isn't importable, the function degrades gracefully.

    Simulated by inserting ``None`` at ``sys.modules["langchain_tavily"]``,
    which makes the lazy ``from langchain_tavily import TavilySearch``
    raise ImportError per Python's import system semantics.
    """
    with patch.dict(sys.modules, {"langchain_tavily": None}):
        result_dict = await web_search.ainvoke(_args(query="anything"))

    assert isinstance(result_dict, dict)

    result = WebSearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "langchain-tavily" in result.error
