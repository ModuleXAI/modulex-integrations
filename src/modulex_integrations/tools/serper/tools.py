"""Serper LangChain ``@tool`` functions.

A single async tool wrapping the Serper Google Search API. Serper uses
the modulex *api_key* calling convention: the ``ToolExecutor`` injects
an ``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions — non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.serper.outputs import SearchOutput, SearchResultItem

__all__ = ["search"]

_SERPER_API_BASE = "https://google.serper.dev"
_SEARCH_TIMEOUT = 30.0
_VALID_TYPES = ("search", "news", "places", "images", "videos", "shopping")


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }


# --- Input schema (args_schema for the @tool) ------------------------------


class SearchInput(BaseModel):
    query: str = Field(
        description='The search query (e.g., "latest AI news", "best restaurants in NYC")'
    )
    api_key: str = Field(description="Serper API key (provided by credential system)")
    num: int | None = Field(
        default=None,
        description="Number of results to return (e.g., 10, 20, 50)",
    )
    gl: str | None = Field(
        default=None,
        description='Country code for search results (e.g., "us", "uk", "de", "fr")',
    )
    hl: str | None = Field(
        default=None,
        description='Language code for search results (e.g., "en", "es", "de", "fr")',
    )
    type: str = Field(
        default="search",
        description=(
            'Type of search to perform: "search" (default), "news", "places", '
            '"images", "videos", or "shopping"'
        ),
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    query: str,
    api_key: str,
    num: int | None = None,
    gl: str | None = None,
    hl: str | None = None,
    type: str = "search",
) -> SearchOutput:
    """A powerful web search tool that provides access to Google search results
    through the Serper API. Supports different types of searches including
    regular web search, news, places, images, videos, and shopping. Returns
    comprehensive results including organic results, knowledge graph, answer
    box, people also ask, related searches, and top stories."""
    if not api_key or not api_key.strip():
        return SearchOutput(
            success=False,
            error="Serper API key is empty. Please configure a valid Serper credential.",
        )

    search_type = type if type in _VALID_TYPES else "search"

    body: dict[str, Any] = {"q": query}
    if num is not None:
        body["num"] = int(num)
    if gl:
        body["gl"] = gl
    if hl:
        body["hl"] = hl

    try:
        async with httpx.AsyncClient(timeout=_SEARCH_TIMEOUT) as client:
            response = await client.post(
                f"{_SERPER_API_BASE}/{search_type}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return SearchOutput(
                success=False,
                error=f"Serper API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchOutput(success=False, error=f"Search failed: {exc}")

    results: list[SearchResultItem] = []
    if search_type == "news":
        for index, item in enumerate(data.get("news") or []):
            results.append(
                SearchResultItem(
                    title=item.get("title"),
                    link=item.get("link"),
                    snippet=item.get("snippet"),
                    position=index + 1,
                    date=item.get("date"),
                    image_url=item.get("imageUrl"),
                    source=item.get("source"),
                )
            )
    elif search_type == "places":
        for index, item in enumerate(data.get("places") or []):
            results.append(
                SearchResultItem(
                    title=item.get("title"),
                    link=item.get("link"),
                    snippet=item.get("snippet"),
                    position=index + 1,
                    rating=item.get("rating"),
                    reviews=item.get("reviews"),
                    address=item.get("address"),
                )
            )
    elif search_type == "images":
        for index, item in enumerate(data.get("images") or []):
            results.append(
                SearchResultItem(
                    title=item.get("title"),
                    link=item.get("link"),
                    snippet=item.get("snippet"),
                    position=index + 1,
                    image_url=item.get("imageUrl"),
                )
            )
    else:
        for index, item in enumerate(data.get("organic") or []):
            results.append(
                SearchResultItem(
                    title=item.get("title"),
                    link=item.get("link"),
                    snippet=item.get("snippet"),
                    position=index + 1,
                )
            )

    return SearchOutput(
        success=True,
        search_type=search_type,
        search_results=results,
        knowledge_graph=data.get("knowledgeGraph"),
        answer_box=data.get("answerBox"),
        people_also_ask=data.get("peopleAlsoAsk") or [],
        related_searches=data.get("relatedSearches") or [],
        top_stories=data.get("topStories") or [],
    )
