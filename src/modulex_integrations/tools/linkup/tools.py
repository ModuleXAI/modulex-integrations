"""Linkup LangChain ``@tool`` functions.

A single async tool wrapping the Linkup web-search REST API. The calling
convention is the modulex *api_key* one: the ``ToolExecutor`` injects an
``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.linkup.outputs import (
    SearchOutput,
    SearchResultItem,
    SearchSource,
)

__all__ = ["search"]

_LINKUP_API_BASE = "https://api.linkup.so/v1"
_SEARCH_TIMEOUT = 60.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _split_domains(value: str) -> list[str]:
    """Split a comma-separated domain string into a trimmed, non-empty list."""
    return [d.strip() for d in value.split(",") if d.strip()]


# --- Input schemas (args_schema for each @tool) ----------------------------


class SearchInput(BaseModel):
    q: str = Field(description='The search query (e.g., "latest AI research papers 2024")')
    api_key: str = Field(description="Linkup API key (provided by credential system)")
    depth: str = Field(
        default="standard",
        description=(
            'Search depth: "standard" for quick results, "deep" for comprehensive '
            'search (also supports "fast")'
        ),
    )
    output_type: str = Field(
        default="sourcedAnswer",
        description=(
            'Output format: "sourcedAnswer" for an AI-generated answer with '
            'citations, "searchResults" for raw results, or "structured"'
        ),
    )
    include_images: bool | None = Field(
        default=None, description="Whether to include images in search results"
    )
    include_inline_citations: bool | None = Field(
        default=None,
        description=(
            "Add inline citations to answers (only applies when output_type is "
            '"sourcedAnswer")'
        ),
    )
    include_sources: bool | None = Field(
        default=None, description="Include sources in the response"
    )
    from_date: str | None = Field(
        default=None, description="Start date for filtering results (YYYY-MM-DD format)"
    )
    to_date: str | None = Field(
        default=None, description="End date for filtering results (YYYY-MM-DD format)"
    )
    include_domains: str | None = Field(
        default=None,
        description="Comma-separated list of domain names to restrict search results to",
    )
    exclude_domains: str | None = Field(
        default=None,
        description="Comma-separated list of domain names to exclude from search results",
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    q: str,
    api_key: str,
    depth: str = "standard",
    output_type: str = "sourcedAnswer",
    include_images: bool | None = None,
    include_inline_citations: bool | None = None,
    include_sources: bool | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    include_domains: str | None = None,
    exclude_domains: str | None = None,
) -> SearchOutput:
    """Search the web for information using Linkup."""
    if not api_key or not api_key.strip():
        return SearchOutput(
            success=False,
            error="Linkup API key is empty. Please configure a valid Linkup credential.",
        )

    payload: dict[str, Any] = {
        "q": q,
        "depth": depth,
        "outputType": output_type,
    }
    if include_images is not None:
        payload["includeImages"] = include_images
    if from_date:
        payload["fromDate"] = from_date
    if to_date:
        payload["toDate"] = to_date
    if exclude_domains:
        payload["excludeDomains"] = _split_domains(exclude_domains)
    if include_domains:
        payload["includeDomains"] = _split_domains(include_domains)
    if include_inline_citations is not None:
        payload["includeInlineCitations"] = include_inline_citations
    if include_sources is not None:
        payload["includeSources"] = include_sources

    try:
        async with httpx.AsyncClient(timeout=_SEARCH_TIMEOUT) as client:
            response = await client.post(
                f"{_LINKUP_API_BASE}/search", headers=_headers(api_key), json=payload
            )
        if response.status_code != 200:
            return SearchOutput(
                success=False,
                error=f"Linkup API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(
            success=False,
            error='Request timed out. Try a shallower depth (e.g. "standard").',
        )
    except Exception as exc:
        return SearchOutput(success=False, error=f"Search failed: {exc}")

    if not isinstance(data, dict):
        # ``structured`` may return a top-level JSON value other than an object
        # depending on the supplied schema; wrap it so the model stays valid.
        return SearchOutput(success=True, structured_data={"data": data})

    structured_data: dict[str, Any] | None = None
    known_keys = {"answer", "sources", "results"}
    if output_type == "structured" or not (known_keys & set(data.keys())):
        structured_data = data

    return SearchOutput(
        success=True,
        answer=data.get("answer"),
        sources=[
            SearchSource(
                name=item.get("name"),
                url=item.get("url"),
                snippet=item.get("snippet"),
            )
            for item in data.get("sources") or []
        ],
        results=[
            SearchResultItem(
                type=item.get("type"),
                name=item.get("name"),
                url=item.get("url"),
                content=item.get("content"),
            )
            for item in data.get("results") or []
        ],
        structured_data=structured_data,
    )
