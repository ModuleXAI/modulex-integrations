"""Tavily LangChain ``@tool`` functions.

Three async tools wrapping the ``langchain-tavily`` SDK. Same
api_key-based runtime convention as exa: the modulex ``ToolExecutor``
injects ``api_key: str`` directly (resolved from `api_key` or
`modulex_key` credential), not an ``auth_type``/``auth_data`` pair.

**Lazy SDK import**: ``langchain_tavily`` is imported inside each
function so a missing SDK degrades gracefully to ``success=False`` +
a clear install message, matching the legacy modulex behavior. The
SDK is declared in ``dependencies.toml`` for the assemble script.

Tests mock ``langchain_tavily.TavilySearch`` at the module level via
``unittest.mock.patch`` — the standard SDK test pattern from
CONTRIBUTING.md.
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.tavily.outputs import (
    AnswerSearchOutput,
    NewsSearchOutput,
    TavilyResult,
    WebSearchOutput,
)

__all__ = ["answer_search", "news_search", "web_search"]


# --- Input schemas (args_schema for each @tool) ----------------------------


class WebSearchInput(BaseModel):
    query: str = Field(description="Search query")
    api_key: str = Field(description="Tavily API key (provided by credential system)")
    max_results: int = Field(default=5, description="Maximum number of results (1-10)")
    search_depth: str = Field(
        default="basic",
        description="Search depth: 'basic' for quick results or 'advanced' for thorough",
    )
    include_domains: list[str] | None = Field(default=None, description="Domains to include")
    exclude_domains: list[str] | None = Field(default=None, description="Domains to exclude")
    include_answer: bool = Field(
        default=False, description="Whether to include AI-generated answer"
    )


class AnswerSearchInput(BaseModel):
    query: str = Field(description="Question to answer")
    api_key: str = Field(description="Tavily API key (provided by credential system)")
    max_results: int = Field(default=5, description="Maximum number of supporting sources")
    search_depth: str = Field(
        default="advanced",
        description="Search depth for answer generation (use 'advanced' for better answers)",
    )
    include_domains: list[str] | None = Field(default=None, description="Domains to include")
    exclude_domains: list[str] | None = Field(default=None, description="Domains to exclude")


class NewsSearchInput(BaseModel):
    query: str = Field(description="News search query")
    api_key: str = Field(description="Tavily API key (provided by credential system)")
    max_results: int = Field(default=5, description="Maximum number of news articles")
    days: int = Field(
        default=3, description="Number of days back to search for news (1-30 recommended)"
    )
    include_domains: list[str] | None = Field(default=None, description="News domains to include")
    exclude_domains: list[str] | None = Field(default=None, description="News domains to exclude")


# --- Internal helpers ------------------------------------------------------


def _empty_key_error(action: str) -> str:
    return f"Tavily API key is empty. Please configure a valid Tavily credential ({action})."


def _missing_sdk_error() -> str:
    return (
        "langchain-tavily package not installed. "
        "Install with: pip install langchain-tavily"
    )


def _parse_results(payload: Any) -> tuple[
    list[TavilyResult], str | None, list[str], float | None, str | None, str | None
]:
    """Coerce a Tavily SDK response into our typed pieces.

    Tavily's SDK returns either a dict or a list-of-dicts depending on
    configuration. Normalize both shapes here.
    """
    if isinstance(payload, list):
        return (
            [
                TavilyResult(
                    url=item.get("url"),
                    title=item.get("title"),
                    content=item.get("content"),
                    score=item.get("score"),
                    raw_content=item.get("raw_content"),
                )
                for item in payload
                if isinstance(item, dict)
            ],
            None,
            [],
            None,
            None,
            None,
        )
    if isinstance(payload, dict):
        results = [
            TavilyResult(
                url=item.get("url"),
                title=item.get("title"),
                content=item.get("content"),
                score=item.get("score"),
                raw_content=item.get("raw_content"),
            )
            for item in (payload.get("results") or [])
            if isinstance(item, dict)
        ]
        return (
            results,
            payload.get("answer"),
            payload.get("images") or [],
            payload.get("response_time"),
            payload.get("request_id"),
            payload.get("query"),
        )
    return ([], None, [], None, None, None)


# --- @tool functions -------------------------------------------------------


@tool(args_schema=WebSearchInput)
@serialize_pydantic_return
async def web_search(
    query: str,
    api_key: str,
    max_results: int = 5,
    search_depth: str = "basic",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    include_answer: bool = False,
) -> WebSearchOutput:
    """Perform a comprehensive web search using Tavily's LangChain integration."""
    if not api_key or not api_key.strip():
        return WebSearchOutput(success=False, error=_empty_key_error("web_search"))

    try:
        try:
            from langchain_tavily import TavilySearch
        except ImportError:
            return WebSearchOutput(success=False, error=_missing_sdk_error())

        tavily_tool = TavilySearch(
            tavily_api_key=api_key,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains or [],
            exclude_domains=exclude_domains or [],
            include_answer=include_answer,
        )
        payload = await tavily_tool.ainvoke({"query": query})
    except Exception as exc:
        return WebSearchOutput(success=False, error=f"Web search failed: {exc}")

    results, answer, images, response_time, request_id, parsed_query = _parse_results(payload)
    return WebSearchOutput(
        success=True,
        query=parsed_query or query,
        answer=answer,
        results=results,
        images=images,
        response_time=response_time,
        request_id=request_id,
    )


@tool(args_schema=AnswerSearchInput)
@serialize_pydantic_return
async def answer_search(
    query: str,
    api_key: str,
    max_results: int = 5,
    search_depth: str = "advanced",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> AnswerSearchOutput:
    """Perform a web search and get an AI-generated answer with supporting sources."""
    if not api_key or not api_key.strip():
        return AnswerSearchOutput(success=False, error=_empty_key_error("answer_search"))

    try:
        try:
            from langchain_tavily import TavilySearch
        except ImportError:
            return AnswerSearchOutput(success=False, error=_missing_sdk_error())

        tavily_tool = TavilySearch(
            tavily_api_key=api_key,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains or [],
            exclude_domains=exclude_domains or [],
            include_answer=True,
        )
        payload = await tavily_tool.ainvoke({"query": query})
    except Exception as exc:
        return AnswerSearchOutput(success=False, error=f"Answer search failed: {exc}")

    results, answer, images, response_time, request_id, parsed_query = _parse_results(payload)
    return AnswerSearchOutput(
        success=True,
        query=parsed_query or query,
        answer=answer,
        results=results,
        images=images,
        response_time=response_time,
        request_id=request_id,
    )


@tool(args_schema=NewsSearchInput)
@serialize_pydantic_return
async def news_search(
    query: str,
    api_key: str,
    max_results: int = 5,
    days: int = 3,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> NewsSearchOutput:
    """Search recent news articles using Tavily's news-focused search."""
    if not api_key or not api_key.strip():
        return NewsSearchOutput(success=False, error=_empty_key_error("news_search"))

    try:
        try:
            from langchain_tavily import TavilySearch
        except ImportError:
            return NewsSearchOutput(success=False, error=_missing_sdk_error())

        tavily_tool = TavilySearch(
            tavily_api_key=api_key,
            max_results=max_results,
            search_depth="advanced",
            include_domains=include_domains or [],
            exclude_domains=exclude_domains or [],
        )
        news_query = f"{query} news recent {days} days"
        payload = await tavily_tool.ainvoke({"query": news_query})
    except Exception as exc:
        return NewsSearchOutput(success=False, error=f"News search failed: {exc}")

    results, _, images, response_time, request_id, parsed_query = _parse_results(payload)
    return NewsSearchOutput(
        success=True,
        query=parsed_query or query,
        results=results,
        images=images,
        response_time=response_time,
        request_id=request_id,
    )
