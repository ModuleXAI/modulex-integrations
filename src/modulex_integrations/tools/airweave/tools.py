"""Airweave LangChain ``@tool`` functions.

A single async tool wrapping the Airweave Search REST API. The calling
convention is key-based: the modulex ``ToolExecutor`` injects an
``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair. The key is sent in
the ``x-api-key`` request header.

Error model: every call is wrapped in try/except. Non-2xx responses,
timeouts, and unexpected exceptions surface as the typed output with
``success=False`` + ``error`` — they do *not* raise.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.airweave.outputs import (
    SearchOutput,
    SearchResultItem,
)

__all__ = ["search"]

_AIRWEAVE_API_BASE = "https://api.airweave.ai"
_SEARCH_TIMEOUT = 60.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class SearchInput(BaseModel):
    collection_id: str = Field(description="The readable ID of the collection to search")
    query: str = Field(description="The search query text")
    api_key: str = Field(description="Airweave API key (provided by credential system)")
    limit: int | None = Field(
        default=None, description="Maximum number of results to return"
    )
    retrieval_strategy: str | None = Field(
        default=None,
        description="Retrieval strategy: 'hybrid' (default), 'neural', or 'keyword'",
    )
    expand_query: bool | None = Field(
        default=None, description="Generate query variations to improve recall"
    )
    rerank: bool | None = Field(
        default=None, description="Reorder results for improved relevance using an LLM"
    )
    generate_answer: bool | None = Field(
        default=None, description="Generate a natural-language answer to the query"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    collection_id: str,
    query: str,
    api_key: str,
    limit: int | None = None,
    retrieval_strategy: str | None = None,
    expand_query: bool | None = None,
    rerank: bool | None = None,
    generate_answer: bool | None = None,
) -> SearchOutput:
    """Search your synced data collections using Airweave.

    Supports semantic search with hybrid, neural, or keyword retrieval
    strategies. Optionally generate AI-powered answers from search results.
    """
    if not api_key or not api_key.strip():
        return SearchOutput(
            success=False,
            error="Airweave API key is empty. Please configure a valid Airweave credential.",
        )
    if not collection_id or not collection_id.strip():
        return SearchOutput(success=False, error="A collection ID is required.")

    payload: dict[str, Any] = {"query": query}
    if limit is not None:
        payload["limit"] = int(limit)
    if retrieval_strategy:
        payload["retrieval_strategy"] = retrieval_strategy
    if expand_query is not None:
        payload["expand_query"] = expand_query
    if rerank is not None:
        payload["rerank"] = rerank
    if generate_answer is not None:
        payload["generate_answer"] = generate_answer

    url = f"{_AIRWEAVE_API_BASE}/collections/{collection_id}/search"
    try:
        async with httpx.AsyncClient(timeout=_SEARCH_TIMEOUT) as client:
            response = await client.post(url, headers=_headers(api_key), json=payload)
        if response.status_code != 200:
            detail: str = response.text
            try:
                body = response.json()
                detail = body.get("detail") or body.get("message") or response.text
            except Exception:
                pass
            return SearchOutput(
                success=False,
                error=f"Airweave API error ({response.status_code}): {detail}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(
            success=False,
            error="Request timed out. Try reducing limit or disabling answer generation.",
        )
    except Exception as exc:
        return SearchOutput(success=False, error=f"Search failed: {exc}")

    results = data.get("results") or []
    return SearchOutput(
        success=True,
        results=[
            SearchResultItem(
                entity_id=item.get("entity_id") or item.get("id"),
                source_name=item.get("source_name"),
                md_content=item.get("md_content"),
                score=item.get("score"),
                metadata=item.get("metadata"),
                breadcrumbs=item.get("breadcrumbs") or [],
                url=item.get("url"),
            )
            for item in results
        ],
        completion=data.get("completion"),
        total_results=len(results),
    )
