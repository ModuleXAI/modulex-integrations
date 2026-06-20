"""Mem0 LangChain ``@tool`` functions.

Three async tools wrapping the Mem0 REST API. The calling convention is
key-based: the modulex ``ToolExecutor`` injects an ``api_key: str``
directly (resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair.

Auth header: Mem0 expects ``Authorization: Token <api_key>`` (not a
Bearer token and not ``x-api-key``).

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.mem0.outputs import (
    AddMemoriesOutput,
    GetMemoriesOutput,
    MemoryRecord,
    SearchMemoriesOutput,
    SearchResultRecord,
)

__all__ = ["add_memories", "get_memories", "search_memories"]

_MEM0_API_BASE = "https://api.mem0.ai"
_DEFAULT_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }


# --- Parsing helpers -------------------------------------------------------


def _parse_messages(messages: Any) -> list[dict[str, Any]]:
    """Accept either a JSON string or a list of message objects.

    Returns a non-empty list of ``{"role": ..., "content": ...}`` dicts.
    Raises ``ValueError`` if the input is not valid or is empty.
    """
    parsed = messages
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Messages must be valid JSON: {exc}") from exc

    if not isinstance(parsed, list) or len(parsed) == 0:
        raise ValueError("Messages must be a non-empty array")

    result: list[dict[str, Any]] = []
    for item in parsed:
        if (
            not isinstance(item, dict)
            or item.get("role") not in ("user", "assistant")
            or not isinstance(item.get("content"), str)
            or not item["content"]
        ):
            raise ValueError(
                "Each message must have role 'user' or 'assistant' and non-empty content"
            )
        result.append({"role": item["role"], "content": item["content"]})
    return result


def _memories_from_response(data: Any) -> list[dict[str, Any]]:
    """Normalize the several shapes the Mem0 read endpoints can return."""
    if isinstance(data, list):
        return [m for m in data if isinstance(m, dict)]
    if not isinstance(data, dict):
        return []
    results = data.get("results")
    if isinstance(results, list):
        return [m for m in results if isinstance(m, dict)]
    memory = data.get("memory")
    if isinstance(memory, dict):
        return [memory]
    if data.get("id"):
        return [data]
    return []


def _memory_record(item: dict[str, Any]) -> MemoryRecord:
    categories = item.get("categories")
    return MemoryRecord(
        id=item.get("id"),
        memory=item.get("memory"),
        user_id=item.get("user_id"),
        agent_id=item.get("agent_id"),
        app_id=item.get("app_id"),
        run_id=item.get("run_id"),
        hash=item.get("hash"),
        metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else None,
        categories=categories if isinstance(categories, list) else [],
        created_at=item.get("created_at"),
        updated_at=item.get("updated_at"),
    )


def _search_record(item: dict[str, Any]) -> SearchResultRecord:
    categories = item.get("categories")
    score = item.get("score")
    return SearchResultRecord(
        id=item.get("id"),
        memory=item.get("memory"),
        user_id=item.get("user_id"),
        agent_id=item.get("agent_id"),
        app_id=item.get("app_id"),
        run_id=item.get("run_id"),
        hash=item.get("hash"),
        metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else None,
        categories=categories if isinstance(categories, list) else [],
        created_at=item.get("created_at"),
        updated_at=item.get("updated_at"),
        score=float(score) if isinstance(score, (int, float)) else None,
    )


# --- Input schemas (args_schema for each @tool) ----------------------------


class AddMemoriesInput(BaseModel):
    user_id: str = Field(
        description='User ID associated with the memory (e.g., "user_123", "alice@example.com")'
    )
    messages: list[dict[str, Any]] | str = Field(
        description=(
            "Array of message objects with role and content "
            '(e.g., [{"role": "user", "content": "Hello"}]). '
            "A JSON string is also accepted."
        )
    )
    api_key: str = Field(description="Mem0 API key (provided by credential system)")


class SearchMemoriesInput(BaseModel):
    user_id: str = Field(
        description='User ID to search memories for (e.g., "user_123", "alice@example.com")'
    )
    query: str = Field(
        description='Search query to find relevant memories (e.g., "What are my favorite foods?")'
    )
    api_key: str = Field(description="Mem0 API key (provided by credential system)")
    limit: int = Field(default=10, description="Maximum number of results to return (e.g., 10, 50)")


class GetMemoriesInput(BaseModel):
    user_id: str = Field(
        description='User ID to retrieve memories for (e.g., "user_123", "alice@example.com")'
    )
    api_key: str = Field(description="Mem0 API key (provided by credential system)")
    memory_id: str | None = Field(
        default=None, description='Specific memory ID to retrieve (e.g., "mem_abc123")'
    )
    start_date: str | None = Field(
        default=None, description='Start date for filtering by created_at (e.g., "2024-01-15")'
    )
    end_date: str | None = Field(
        default=None, description='End date for filtering by created_at (e.g., "2024-12-31")'
    )
    limit: int = Field(default=10, description="Maximum number of results to return (e.g., 10, 50)")
    page: int = Field(default=1, description="Page number to retrieve for paginated list results")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=AddMemoriesInput)
@serialize_pydantic_return
async def add_memories(
    user_id: str,
    messages: list[dict[str, Any]] | str,
    api_key: str,
) -> AddMemoriesOutput:
    """Add memories to Mem0 for persistent storage and retrieval."""
    if not api_key or not api_key.strip():
        return AddMemoriesOutput(
            success=False,
            error="Mem0 API key is empty. Please configure a valid Mem0 credential.",
        )
    if not user_id or not user_id.strip():
        return AddMemoriesOutput(success=False, error="User ID is required.")

    try:
        parsed_messages = _parse_messages(messages)
    except ValueError as exc:
        return AddMemoriesOutput(success=False, error=str(exc))

    body: dict[str, Any] = {
        "messages": parsed_messages,
        "user_id": user_id.strip(),
    }

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{_MEM0_API_BASE}/v3/memories/add/",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201, 202):
            return AddMemoriesOutput(
                success=False,
                error=f"Mem0 API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddMemoriesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddMemoriesOutput(success=False, error=f"Add memories failed: {exc}")

    if not isinstance(data, dict):
        data = {}

    return AddMemoriesOutput(
        success=True,
        message=data.get("message"),
        status=data.get("status"),
        event_id=data.get("event_id"),
    )


@tool(args_schema=SearchMemoriesInput)
@serialize_pydantic_return
async def search_memories(
    user_id: str,
    query: str,
    api_key: str,
    limit: int = 10,
) -> SearchMemoriesOutput:
    """Search for memories in Mem0 using semantic search."""
    if not api_key or not api_key.strip():
        return SearchMemoriesOutput(
            success=False,
            error="Mem0 API key is empty. Please configure a valid Mem0 credential.",
        )
    if not user_id or not user_id.strip():
        return SearchMemoriesOutput(success=False, error="User ID is required.")
    if not query or not query.strip():
        return SearchMemoriesOutput(success=False, error="Search query is required.")

    body: dict[str, Any] = {
        "query": query,
        "filters": {"user_id": user_id.strip()},
        "top_k": int(limit or 10),
    }

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{_MEM0_API_BASE}/v3/memories/search/",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return SearchMemoriesOutput(
                success=False,
                error=f"Mem0 API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchMemoriesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchMemoriesOutput(success=False, error=f"Search memories failed: {exc}")

    raw_results: list[dict[str, Any]] = []
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        raw_results = [r for r in data["results"] if isinstance(r, dict)]

    records = [_search_record(item) for item in raw_results]
    ids = [r.id for r in records if r.id]

    return SearchMemoriesOutput(success=True, search_results=records, ids=ids)


@tool(args_schema=GetMemoriesInput)
@serialize_pydantic_return
async def get_memories(
    user_id: str,
    api_key: str,
    memory_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10,
    page: int = 1,
) -> GetMemoriesOutput:
    """Retrieve memories from Mem0 by ID or filter criteria."""
    if not api_key or not api_key.strip():
        return GetMemoriesOutput(
            success=False,
            error="Mem0 API key is empty. Please configure a valid Mem0 credential.",
        )

    use_single = bool(memory_id and memory_id.strip())

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            if use_single:
                assert memory_id is not None
                url = f"{_MEM0_API_BASE}/v1/memories/{quote(memory_id.strip(), safe='')}/"
                response = await client.get(url, headers=_headers(api_key))
            else:
                if not user_id or not user_id.strip():
                    return GetMemoriesOutput(
                        success=False,
                        error="User ID is required when no memory ID is provided.",
                    )
                filters: dict[str, Any] = {"user_id": user_id.strip()}
                if start_date or end_date:
                    date_filter: dict[str, Any] = {}
                    if start_date:
                        date_filter["gte"] = start_date
                    if end_date:
                        date_filter["lte"] = end_date
                    filters["created_at"] = date_filter
                body: dict[str, Any] = {
                    "filters": filters,
                    "page": int(page or 1),
                    "page_size": int(limit or 10),
                }
                response = await client.post(
                    f"{_MEM0_API_BASE}/v3/memories/",
                    headers=_headers(api_key),
                    json=body,
                )
        if response.status_code != 200:
            return GetMemoriesOutput(
                success=False,
                error=f"Mem0 API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMemoriesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMemoriesOutput(success=False, error=f"Get memories failed: {exc}")

    raw_memories = _memories_from_response(data)
    records = [_memory_record(item) for item in raw_memories]
    ids = [r.id for r in records if r.id]

    count: int | None = None
    next_url: str | None = None
    previous_url: str | None = None
    if isinstance(data, dict):
        if isinstance(data.get("count"), int):
            count = data["count"]
        if isinstance(data.get("next"), str):
            next_url = data["next"]
        if isinstance(data.get("previous"), str):
            previous_url = data["previous"]

    return GetMemoriesOutput(
        success=True,
        memories=records,
        ids=ids,
        count=count,
        next=next_url,
        previous=previous_url,
    )
