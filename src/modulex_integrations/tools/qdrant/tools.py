"""Qdrant LangChain ``@tool`` functions.

Pure HTTP pass-through over the Qdrant REST API. Token-based runtime
convention (``auth_type, auth_data`` first args) — ``auth_type`` is
informational (modulex schema label ``custom``); the tool body pulls
``base_url`` and the optional ``api_key`` out of ``auth_data``.

Requests hit the user's own Qdrant instance (Cloud or self-hosted) with
the user's own credential. No ModuleX-side embedding or result
normalization: search takes a query vector (or, on Qdrant Cloud with
inference, a text + model document) and responses are returned in
Qdrant's native shape.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.qdrant.outputs import (
    CreateCollectionOutput,
    DeleteCollectionOutput,
    DeletePointsOutput,
    GetCollectionInfoOutput,
    ListCollectionsOutput,
    QueryOutput,
    UpsertPointsOutput,
)

__all__ = [
    "create_collection",
    "delete_collection",
    "delete_points",
    "get_collection_info",
    "list_collections",
    "query",
    "upsert_points",
]

_TIMEOUT = 30.0


def _base_url(auth_data: dict[str, Any]) -> str:
    return str(auth_data.get("base_url", "") or "").rstrip("/")


def _headers(auth_data: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = auth_data.get("api_key")
    if api_key:
        headers["api-key"] = str(api_key)
    return headers


def _missing_credentials(auth_data: dict[str, Any]) -> str | None:
    if not auth_data.get("base_url"):
        return "Missing Qdrant base URL in credentials."
    return None


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (custom)")
    auth_data: dict[str, Any] = Field(description="base_url + optional api_key")


class QueryInput(_AuthFields):
    collection_name: str = Field(description="Collection to search")
    query_vector: list[float] | None = Field(
        default=None, description="Query embedding vector"
    )
    query_text: str | None = Field(
        default=None,
        description=(
            "Raw text to embed server-side (Qdrant Cloud inference only; "
            "requires `model`)"
        ),
    )
    model: str | None = Field(
        default=None,
        description="Inference model name used to embed query_text (Cloud only)",
    )
    using: str | None = Field(
        default=None, description="Named vector to search against (optional)"
    )
    limit: int = Field(default=5, description="Maximum number of results")
    score_threshold: float | None = Field(
        default=None, description="Minimum similarity score"
    )
    filter: dict[str, Any] | None = Field(
        default=None, description="Qdrant filter object (must/should/must_not)"
    )
    with_payload: bool = Field(default=True, description="Include payload in results")
    with_vector: bool = Field(default=False, description="Include vectors in results")


class ListCollectionsInput(_AuthFields):
    pass


class GetCollectionInfoInput(_AuthFields):
    collection_name: str = Field(description="Collection name")


class UpsertPointsInput(_AuthFields):
    collection_name: str = Field(description="Collection name")
    points: list[dict[str, Any]] = Field(
        description="Points to upsert — Qdrant-native {id, vector, payload?} objects"
    )


class DeletePointsInput(_AuthFields):
    collection_name: str = Field(description="Collection name")
    point_ids: list[Any] | None = Field(
        default=None, description="Point IDs to delete (numbers or UUID strings)"
    )
    filter: dict[str, Any] | None = Field(
        default=None, description="Qdrant filter selecting the points to delete"
    )


class CreateCollectionInput(_AuthFields):
    collection_name: str = Field(description="Collection name")
    vector_size: int = Field(description="Dimensionality of the vectors")
    distance: str = Field(
        default="Cosine", description="Distance metric: Cosine, Euclid, Dot, Manhattan"
    )


class DeleteCollectionInput(_AuthFields):
    collection_name: str = Field(description="Collection name")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=QueryInput)
@serialize_pydantic_return
async def query(
    auth_type: str,
    auth_data: dict[str, Any],
    collection_name: str,
    query_vector: list[float] | None = None,
    query_text: str | None = None,
    model: str | None = None,
    using: str | None = None,
    limit: int = 5,
    score_threshold: float | None = None,
    filter: dict[str, Any] | None = None,
    with_payload: bool = True,
    with_vector: bool = False,
) -> QueryOutput:
    """Similarity search on a Qdrant collection (POST points/query).

    Provide `query_vector` (works everywhere), or `query_text` + `model`
    (Qdrant Cloud with inference only — self-hosted instances must send a
    vector). Results are Qdrant's native scored points.
    """
    err = _missing_credentials(auth_data)
    if err:
        return QueryOutput(success=False, error=err)
    if (query_vector is None) == (query_text is None):
        return QueryOutput(
            success=False,
            error="Provide exactly one of query_vector or query_text.",
        )
    if query_text is not None and not model:
        return QueryOutput(
            success=False,
            error=(
                "query_text requires `model` (server-side embedding is a "
                "Qdrant Cloud inference feature)."
            ),
        )
    body: dict[str, Any] = {
        "limit": limit,
        "with_payload": with_payload,
        "with_vector": with_vector,
    }
    if query_vector is not None:
        body["query"] = query_vector
    else:
        body["query"] = {"text": query_text, "model": model}
    if using:
        body["using"] = using
    if score_threshold is not None:
        body["score_threshold"] = score_threshold
    if filter:
        body["filter"] = filter
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/collections/{collection_name}/points/query",
                headers=_headers(auth_data),
                json=body,
            )
        if not response.is_success:
            return QueryOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return QueryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return QueryOutput(success=False, error=str(exc))
    return QueryOutput(
        success=True, points=data.get("result", {}).get("points", [])
    )


@tool(args_schema=ListCollectionsInput)
@serialize_pydantic_return
async def list_collections(
    auth_type: str, auth_data: dict[str, Any]
) -> ListCollectionsOutput:
    """List all collections in the Qdrant instance."""
    err = _missing_credentials(auth_data)
    if err:
        return ListCollectionsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/collections",
                headers=_headers(auth_data),
            )
        if not response.is_success:
            return ListCollectionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListCollectionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCollectionsOutput(success=False, error=str(exc))
    return ListCollectionsOutput(
        success=True, collections=data.get("result", {}).get("collections", [])
    )


@tool(args_schema=GetCollectionInfoInput)
@serialize_pydantic_return
async def get_collection_info(
    auth_type: str, auth_data: dict[str, Any], collection_name: str
) -> GetCollectionInfoOutput:
    """Get native info about a collection (status, points_count, config)."""
    err = _missing_credentials(auth_data)
    if err:
        return GetCollectionInfoOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/collections/{collection_name}",
                headers=_headers(auth_data),
            )
        if not response.is_success:
            return GetCollectionInfoOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetCollectionInfoOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCollectionInfoOutput(success=False, error=str(exc))
    return GetCollectionInfoOutput(success=True, data=data.get("result", {}))


@tool(args_schema=UpsertPointsInput)
@serialize_pydantic_return
async def upsert_points(
    auth_type: str,
    auth_data: dict[str, Any],
    collection_name: str,
    points: list[dict[str, Any]],
) -> UpsertPointsOutput:
    """Upsert points into a collection (PUT /points?wait=true).

    Each point is a Qdrant-native object: {id, vector, payload?}. On
    Qdrant Cloud with inference, `vector` may be a {text, model} document
    that the server embeds.
    """
    err = _missing_credentials(auth_data)
    if err:
        return UpsertPointsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_base_url(auth_data)}/collections/{collection_name}/points",
                headers=_headers(auth_data),
                params={"wait": "true"},
                json={"points": points},
            )
        if not response.is_success:
            return UpsertPointsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpsertPointsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpsertPointsOutput(success=False, error=str(exc))
    return UpsertPointsOutput(success=True, data=data.get("result", {}))


@tool(args_schema=DeletePointsInput)
@serialize_pydantic_return
async def delete_points(
    auth_type: str,
    auth_data: dict[str, Any],
    collection_name: str,
    point_ids: list[Any] | None = None,
    filter: dict[str, Any] | None = None,
) -> DeletePointsOutput:
    """Delete points by ID list or by filter (POST /points/delete)."""
    err = _missing_credentials(auth_data)
    if err:
        return DeletePointsOutput(success=False, error=err)
    if (point_ids is None) == (filter is None):
        return DeletePointsOutput(
            success=False, error="Provide exactly one of point_ids or filter."
        )
    body: dict[str, Any] = (
        {"points": point_ids} if point_ids is not None else {"filter": filter}
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/collections/{collection_name}/points/delete",
                headers=_headers(auth_data),
                params={"wait": "true"},
                json=body,
            )
        if not response.is_success:
            return DeletePointsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeletePointsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeletePointsOutput(success=False, error=str(exc))
    return DeletePointsOutput(success=True, data=data.get("result", {}))


@tool(args_schema=CreateCollectionInput)
@serialize_pydantic_return
async def create_collection(
    auth_type: str,
    auth_data: dict[str, Any],
    collection_name: str,
    vector_size: int,
    distance: str = "Cosine",
) -> CreateCollectionOutput:
    """Create a collection with a single unnamed vector config."""
    err = _missing_credentials(auth_data)
    if err:
        return CreateCollectionOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_base_url(auth_data)}/collections/{collection_name}",
                headers=_headers(auth_data),
                json={"vectors": {"size": vector_size, "distance": distance}},
            )
        if not response.is_success:
            return CreateCollectionOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateCollectionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCollectionOutput(success=False, error=str(exc))
    return CreateCollectionOutput(success=True, result=data.get("result"))


@tool(args_schema=DeleteCollectionInput)
@serialize_pydantic_return
async def delete_collection(
    auth_type: str, auth_data: dict[str, Any], collection_name: str
) -> DeleteCollectionOutput:
    """Delete a collection and all its points."""
    err = _missing_credentials(auth_data)
    if err:
        return DeleteCollectionOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_base_url(auth_data)}/collections/{collection_name}",
                headers=_headers(auth_data),
            )
        if not response.is_success:
            return DeleteCollectionOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteCollectionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteCollectionOutput(success=False, error=str(exc))
    return DeleteCollectionOutput(success=True, result=data.get("result"))
