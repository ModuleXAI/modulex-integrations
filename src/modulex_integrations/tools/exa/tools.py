"""Exa LangChain ``@tool`` functions.

Four async tools wrapping the Exa REST API. **The calling convention
differs from github/slack**: the modulex ``ToolExecutor`` injects an
``api_key: str`` directly (resolved from the user's `api_key` or
`modulex_key` credential), not an ``auth_type``/``auth_data`` pair.

Error model: the legacy modulex tool wraps every call in try/except,
returning the typed output with ``success=False`` + ``error`` for
non-2xx, timeouts, and unexpected exceptions. We preserve that
defensive behavior — non-2xx HTTP responses do *not* raise.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.exa.outputs import (
    AnswerOutput,
    AnswerSource,
    ContentItem,
    FindSimilarOutput,
    GetContentsOutput,
    SearchOutput,
    SearchResultItem,
    SimilarResultItem,
)

__all__ = ["answer", "find_similar", "get_contents", "search"]

_EXA_API_BASE = "https://api.exa.ai"
_SEARCH_TIMEOUT = 30.0
_CONTENTS_TIMEOUT = 60.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class SearchInput(BaseModel):
    query: str = Field(description="Search query string")
    api_key: str = Field(description="Exa API key (provided by credential system)")
    num_results: int = Field(default=10, description="Number of results to return (1-100)")
    search_type: str = Field(
        default="auto",
        description="Search type: 'auto' (default), 'neural', 'deep', or 'fast'",
    )
    category: str | None = Field(default=None, description="Filter by category")
    include_domains: list[str] | None = Field(default=None, description="Domains to include")
    exclude_domains: list[str] | None = Field(default=None, description="Domains to exclude")
    start_published_date: str | None = Field(
        default=None, description="ISO 8601 lower bound for publication date"
    )
    end_published_date: str | None = Field(
        default=None, description="ISO 8601 upper bound for publication date"
    )
    include_text: bool = Field(default=True, description="Include page text content")
    include_highlights: bool = Field(default=False, description="Include text highlights")
    include_summary: bool = Field(default=False, description="Include AI-generated summary")


class GetContentsInput(BaseModel):
    urls: list[str] = Field(description="List of URLs to extract content from")
    api_key: str = Field(description="Exa API key (provided by credential system)")
    include_text: bool = Field(default=True, description="Include full page text")
    include_highlights: bool = Field(default=False, description="Include text highlights")
    highlights_per_url: int = Field(default=3, description="Number of highlight snippets per URL")
    include_summary: bool = Field(default=False, description="Include AI-generated summary")
    livecrawl: str = Field(
        default="fallback",
        description="Live crawl option: 'never', 'fallback', 'preferred', 'always'",
    )


class FindSimilarInput(BaseModel):
    url: str = Field(description="URL to find similar pages for")
    api_key: str = Field(description="Exa API key (provided by credential system)")
    num_results: int = Field(default=10, description="Number of similar results (1-100)")
    include_domains: list[str] | None = Field(default=None, description="Domains to include")
    exclude_domains: list[str] | None = Field(default=None, description="Domains to exclude")
    exclude_source_domain: bool = Field(
        default=True, description="Exclude results from the source URL's domain"
    )
    category: str | None = Field(default=None, description="Filter by content category")
    include_text: bool = Field(default=True, description="Include page text content")


class AnswerInput(BaseModel):
    query: str = Field(description="Question to answer using web search")
    api_key: str = Field(description="Exa API key (provided by credential system)")
    num_results: int = Field(
        default=5, description="Number of search results to use for generating answer"
    )
    search_type: str = Field(
        default="auto",
        description="Search type for finding sources: 'auto', 'neural', 'deep'",
    )
    include_domains: list[str] | None = Field(default=None, description="Domains to prioritize")
    exclude_domains: list[str] | None = Field(default=None, description="Domains to exclude")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    query: str,
    api_key: str,
    num_results: int = 10,
    search_type: str = "auto",
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
    include_text: bool = True,
    include_highlights: bool = False,
    include_summary: bool = False,
) -> SearchOutput:
    """Perform semantic web search using Exa's AI-powered search engine."""
    if not api_key or not api_key.strip():
        return SearchOutput(
            success=False,
            error="Exa API key is empty. Please configure a valid Exa credential.",
        )

    payload: dict[str, Any] = {
        "query": query,
        "numResults": min(num_results, 100),
        "type": search_type,
    }
    if category:
        payload["category"] = category
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains
    if start_published_date:
        payload["startPublishedDate"] = start_published_date
    if end_published_date:
        payload["endPublishedDate"] = end_published_date
    if include_text:
        payload["text"] = True
    if include_highlights:
        payload["highlights"] = {"numSentences": 3, "highlightsPerUrl": 3}
    if include_summary:
        payload["summary"] = True

    try:
        async with httpx.AsyncClient(timeout=_SEARCH_TIMEOUT) as client:
            response = await client.post(
                f"{_EXA_API_BASE}/search", headers=_headers(api_key), json=payload
            )
        if response.status_code != 200:
            return SearchOutput(
                success=False,
                error=f"Exa API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(
            success=False,
            error="Request timed out. Try reducing num_results or using 'fast' search type.",
        )
    except Exception as exc:
        return SearchOutput(success=False, error=f"Search failed: {exc}")

    return SearchOutput(
        success=True,
        results=[
            SearchResultItem(
                title=item.get("title"),
                url=item.get("url"),
                published_date=item.get("publishedDate"),
                author=item.get("author"),
                score=item.get("score"),
                text=item.get("text") if include_text else None,
                highlights=item.get("highlights") or [] if include_highlights else [],
                summary=item.get("summary") if include_summary else None,
            )
            for item in data.get("results") or []
        ],
        total_results=len(data.get("results") or []),
        search_type=data.get("resolvedSearchType") or search_type,
        request_id=data.get("requestId"),
    )


@tool(args_schema=GetContentsInput)
@serialize_pydantic_return
async def get_contents(
    urls: list[str],
    api_key: str,
    include_text: bool = True,
    include_highlights: bool = False,
    highlights_per_url: int = 3,
    include_summary: bool = False,
    livecrawl: str = "fallback",
) -> GetContentsOutput:
    """Extract full page contents from a list of URLs."""
    if not api_key or not api_key.strip():
        return GetContentsOutput(
            success=False,
            error="Exa API key is empty. Please configure a valid Exa credential.",
        )
    if not urls:
        return GetContentsOutput(success=False, error="No URLs provided")

    payload: dict[str, Any] = {"urls": urls, "livecrawl": livecrawl}
    if include_text:
        payload["text"] = True
    if include_highlights:
        payload["highlights"] = {"numSentences": 3, "highlightsPerUrl": highlights_per_url}
    if include_summary:
        payload["summary"] = True

    try:
        async with httpx.AsyncClient(timeout=_CONTENTS_TIMEOUT) as client:
            response = await client.post(
                f"{_EXA_API_BASE}/contents", headers=_headers(api_key), json=payload
            )
        if response.status_code != 200:
            return GetContentsOutput(
                success=False,
                error=f"Exa API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetContentsOutput(
            success=False,
            error="Request timed out. Try fewer URLs or setting livecrawl to 'never'.",
        )
    except Exception as exc:
        return GetContentsOutput(success=False, error=f"Content extraction failed: {exc}")

    return GetContentsOutput(
        success=True,
        results=[
            ContentItem(
                url=item.get("url"),
                title=item.get("title"),
                published_date=item.get("publishedDate"),
                author=item.get("author"),
                text=item.get("text") if include_text else None,
                highlights=item.get("highlights") or [] if include_highlights else [],
                summary=item.get("summary") if include_summary else None,
            )
            for item in data.get("results") or []
        ],
        total_results=len(data.get("results") or []),
        request_id=data.get("requestId"),
    )


@tool(args_schema=FindSimilarInput)
@serialize_pydantic_return
async def find_similar(
    url: str,
    api_key: str,
    num_results: int = 10,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    exclude_source_domain: bool = True,
    category: str | None = None,
    include_text: bool = True,
) -> FindSimilarOutput:
    """Find pages similar to a given URL using semantic similarity."""
    if not api_key or not api_key.strip():
        return FindSimilarOutput(
            success=False,
            error="Exa API key is empty. Please configure a valid Exa credential.",
        )

    payload: dict[str, Any] = {
        "url": url,
        "numResults": min(num_results, 100),
        "excludeSourceDomain": exclude_source_domain,
    }
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains
    if category:
        payload["category"] = category
    if include_text:
        payload["text"] = True

    try:
        async with httpx.AsyncClient(timeout=_SEARCH_TIMEOUT) as client:
            response = await client.post(
                f"{_EXA_API_BASE}/findSimilar", headers=_headers(api_key), json=payload
            )
        if response.status_code != 200:
            return FindSimilarOutput(
                success=False,
                error=f"Exa API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return FindSimilarOutput(
            success=False, error="Request timed out. Try reducing num_results."
        )
    except Exception as exc:
        return FindSimilarOutput(success=False, error=f"Find similar failed: {exc}")

    return FindSimilarOutput(
        success=True,
        source_url=url,
        results=[
            SimilarResultItem(
                title=item.get("title"),
                url=item.get("url"),
                published_date=item.get("publishedDate"),
                author=item.get("author"),
                score=item.get("score"),
                text=item.get("text") if include_text else None,
            )
            for item in data.get("results") or []
        ],
        total_results=len(data.get("results") or []),
        request_id=data.get("requestId"),
    )


@tool(args_schema=AnswerInput)
@serialize_pydantic_return
async def answer(
    query: str,
    api_key: str,
    num_results: int = 5,
    search_type: str = "auto",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> AnswerOutput:
    """Get an AI-generated answer to a question informed by Exa search results."""
    if not api_key or not api_key.strip():
        return AnswerOutput(
            success=False,
            error="Exa API key is empty. Please configure a valid Exa credential.",
        )

    payload: dict[str, Any] = {
        "query": query,
        "numResults": num_results,
        "type": search_type,
        "text": True,
    }
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains

    try:
        async with httpx.AsyncClient(timeout=_CONTENTS_TIMEOUT) as client:
            response = await client.post(
                f"{_EXA_API_BASE}/answer", headers=_headers(api_key), json=payload
            )
        if response.status_code != 200:
            return AnswerOutput(
                success=False,
                error=f"Exa API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return AnswerOutput(
            success=False, error="Request timed out. The question may be too complex."
        )
    except Exception as exc:
        return AnswerOutput(success=False, error=f"Answer generation failed: {exc}")

    return AnswerOutput(
        success=True,
        answer=data.get("answer"),
        sources=[
            AnswerSource(
                title=item.get("title"),
                url=item.get("url"),
                published_date=item.get("publishedDate"),
            )
            for item in data.get("results") or []
        ],
        request_id=data.get("requestId"),
    )
