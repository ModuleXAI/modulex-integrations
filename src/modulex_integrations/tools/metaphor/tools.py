"""Metaphor LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.metaphor.outputs import (
    DocumentContent,
    FindSimilarLinksOutput,
    GetDocumentsContentOutput,
    SearchOutput,
    SearchResult,
)

__all__ = [
    "find_similar_links",
    "get_documents_content",
    "search",
]

_BASE_URL = "https://api.metaphor.systems"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _parse_result(item: dict[str, Any]) -> SearchResult:
    return SearchResult(
        title=item.get("title"),
        url=item.get("url"),
        published_date=item.get("publishedDate"),
        author=item.get("author"),
        id=item.get("id"),
        score=item.get("score"),
    )


# --- Input schemas --------------------------------------------------------


class SearchInput(BaseModel):
    query: str = Field(description="The query string in the form of a declarative suggestion")
    api_key: str = Field(description="Metaphor API key (provided by credential system)")
    num_results: int | None = Field(default=None, description="Number of search results to return. Default 10.")
    include_domains: list[str] | None = Field(default=None, description="List of domains to include in the search")
    exclude_domains: list[str] | None = Field(default=None, description="List of domains to exclude in the search")
    start_crawl_date: str | None = Field(default=None, description="Only include links crawled after this date (ISO 8601)")
    end_crawl_date: str | None = Field(default=None, description="Only include links crawled before this date (ISO 8601)")
    start_published_date: str | None = Field(default=None, description="Only include links published after this date (ISO 8601)")
    end_published_date: str | None = Field(default=None, description="Only include links published before this date (ISO 8601)")
    use_autoprompt: bool = Field(default=False, description="Whether to use autoprompt to enhance the query")
    type: str | None = Field(default=None, description="The type of search: 'keyword' or 'neural'. Default: neural.")


class FindSimilarLinksInput(BaseModel):
    url: str = Field(description="The URL for which you would like to find similar links")
    api_key: str = Field(description="Metaphor API key (provided by credential system)")
    num_results: int | None = Field(default=None, description="Number of search results to return. Default 10.")
    include_domains: list[str] | None = Field(default=None, description="List of domains to include in the search")
    exclude_domains: list[str] | None = Field(default=None, description="List of domains to exclude in the search")
    start_crawl_date: str | None = Field(default=None, description="Only include links crawled after this date (ISO 8601)")
    end_crawl_date: str | None = Field(default=None, description="Only include links crawled before this date (ISO 8601)")
    start_published_date: str | None = Field(default=None, description="Only include links published after this date (ISO 8601)")
    end_published_date: str | None = Field(default=None, description="Only include links published before this date (ISO 8601)")


class GetDocumentsContentInput(BaseModel):
    ids: list[str] = Field(description="An array of document IDs obtained from search or find_similar_links")
    api_key: str = Field(description="Metaphor API key (provided by credential system)")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    query: str,
    api_key: str,
    num_results: int | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_crawl_date: str | None = None,
    end_crawl_date: str | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
    use_autoprompt: bool = False,
    type: str | None = None,
) -> SearchOutput:
    """Perform a search with a Metaphor prompt-engineered query and retrieve a list of relevant results."""
    if not api_key or not api_key.strip():
        return SearchOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    payload: dict[str, Any] = {
        "query": query,
        "useAutoprompt": use_autoprompt,
    }
    if num_results is not None:
        payload["numResults"] = num_results
    if include_domains is not None:
        payload["includeDomains"] = include_domains
    if exclude_domains is not None:
        payload["excludeDomains"] = exclude_domains
    if start_crawl_date is not None:
        payload["startCrawlDate"] = start_crawl_date
    if end_crawl_date is not None:
        payload["endCrawlDate"] = end_crawl_date
    if start_published_date is not None:
        payload["startPublishedDate"] = start_published_date
    if end_published_date is not None:
        payload["endPublishedDate"] = end_published_date
    if type is not None:
        payload["type"] = type
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return SearchOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchOutput(success=False, error=f"Call failed: {exc}")

    return SearchOutput(
        success=True,
        results=[_parse_result(r) for r in data.get("results", [])],
        autoprompt_string=data.get("autopromptString"),
    )


@tool(args_schema=FindSimilarLinksInput)
@serialize_pydantic_return
async def find_similar_links(
    url: str,
    api_key: str,
    num_results: int | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_crawl_date: str | None = None,
    end_crawl_date: str | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
) -> FindSimilarLinksOutput:
    """Find similar links to the link provided."""
    if not api_key or not api_key.strip():
        return FindSimilarLinksOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    payload: dict[str, Any] = {"url": url}
    if num_results is not None:
        payload["numResults"] = num_results
    if include_domains is not None:
        payload["includeDomains"] = include_domains
    if exclude_domains is not None:
        payload["excludeDomains"] = exclude_domains
    if start_crawl_date is not None:
        payload["startCrawlDate"] = start_crawl_date
    if end_crawl_date is not None:
        payload["endCrawlDate"] = end_crawl_date
    if start_published_date is not None:
        payload["startPublishedDate"] = start_published_date
    if end_published_date is not None:
        payload["endPublishedDate"] = end_published_date
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/findSimilar",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return FindSimilarLinksOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return FindSimilarLinksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindSimilarLinksOutput(success=False, error=f"Call failed: {exc}")

    return FindSimilarLinksOutput(
        success=True,
        results=[_parse_result(r) for r in data.get("results", [])],
    )


@tool(args_schema=GetDocumentsContentInput)
@serialize_pydantic_return
async def get_documents_content(
    ids: list[str],
    api_key: str,
) -> GetDocumentsContentOutput:
    """Retrieve contents of documents based on a list of document IDs obtained from search or find_similar_links."""
    if not api_key or not api_key.strip():
        return GetDocumentsContentOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/contents",
                headers=_headers(api_key),
                params={"ids": ids},
            )
        if response.status_code != 200:
            return GetDocumentsContentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetDocumentsContentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDocumentsContentOutput(success=False, error=f"Call failed: {exc}")

    return GetDocumentsContentOutput(
        success=True,
        contents=[
            DocumentContent(
                id=c.get("id"),
                url=c.get("url"),
                title=c.get("title"),
                extract=c.get("extract"),
            )
            for c in data.get("contents", [])
        ],
    )
