"""Pinecone LangChain ``@tool`` functions.

Pure HTTP pass-through over the Pinecone REST API. Token-based runtime
convention (``auth_type, auth_data`` first args) — ``auth_type`` is
informational (modulex schema label ``custom``); the tool body pulls
``api_key`` out of ``auth_data``.

Control-plane calls (index CRUD/listing) go to ``api.pinecone.io``;
data-plane calls resolve the index's own ``host`` via a control-plane
describe first, then hit ``https://{host}/...``. No ModuleX-side
embedding or result normalization: ``query`` takes a query vector and
``search_records`` sends raw text only to integrated-embedding indexes
where Pinecone embeds it server-side.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.pinecone.outputs import (
    CreateIndexOutput,
    DeleteIndexOutput,
    DeleteVectorsOutput,
    DescribeIndexOutput,
    DescribeIndexStatsOutput,
    ListIndexesOutput,
    QueryOutput,
    SearchRecordsOutput,
    UpsertVectorsOutput,
)

__all__ = [
    "create_index",
    "delete_index",
    "delete_vectors",
    "describe_index",
    "describe_index_stats",
    "list_indexes",
    "query",
    "search_records",
    "upsert_vectors",
]

_TIMEOUT = 30.0
_CONTROL_PLANE = "https://api.pinecone.io"
_API_VERSION = "2025-01"


def _headers(auth_data: dict[str, Any]) -> dict[str, str]:
    return {
        "Api-Key": str(auth_data.get("api_key", "")),
        "Content-Type": "application/json",
        "X-Pinecone-Api-Version": _API_VERSION,
    }


async def _resolve_host(
    client: httpx.AsyncClient, headers: dict[str, str], index_name: str
) -> str:
    """Resolve an index's data-plane host via the control plane."""
    response = await client.get(
        f"{_CONTROL_PLANE}/indexes/{index_name}", headers=headers
    )
    if not response.is_success:
        raise RuntimeError(
            f"Failed to resolve host for index '{index_name}': "
            f"API error ({response.status_code}): {response.text}"
        )
    host = str(response.json().get("host", ""))
    if not host:
        raise RuntimeError(
            f"Index '{index_name}' has no data-plane host yet (still initializing?)."
        )
    return f"https://{host}"


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (custom)")
    auth_data: dict[str, Any] = Field(description="api_key")


class QueryInput(_AuthFields):
    index_name: str = Field(description="Index to search")
    query_vector: list[float] = Field(description="Query embedding vector")
    top_k: int = Field(default=5, description="Number of results to return")
    namespace: str | None = Field(
        default=None, description="Namespace within the index"
    )
    filter: dict[str, Any] | None = Field(
        default=None, description="Metadata filter conditions"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata in results"
    )
    include_values: bool = Field(
        default=False, description="Include vector values in results"
    )


class SearchRecordsInput(_AuthFields):
    index_name: str = Field(description="Index to search")
    query_text: str = Field(
        description=(
            "Raw text query — embedded server-side; integrated-embedding "
            "indexes only"
        )
    )
    namespace: str = Field(
        default="__default__", description="Namespace within the index"
    )
    top_k: int = Field(default=5, description="Number of results to return")
    fields: list[str] | None = Field(
        default=None, description="Record fields to return (default: all)"
    )
    filter: dict[str, Any] | None = Field(
        default=None, description="Metadata filter conditions"
    )
    rerank: dict[str, Any] | None = Field(
        default=None,
        description="Optional native rerank spec ({model, rank_fields, top_n, ...})",
    )


class ListIndexesInput(_AuthFields):
    pass


class DescribeIndexInput(_AuthFields):
    index_name: str = Field(description="Index name")


class DescribeIndexStatsInput(_AuthFields):
    index_name: str = Field(description="Index name")


class UpsertVectorsInput(_AuthFields):
    index_name: str = Field(description="Index name")
    vectors: list[dict[str, Any]] = Field(
        description="Pinecone-native {id, values, metadata?} vectors"
    )
    namespace: str | None = Field(
        default=None, description="Namespace to upsert into"
    )


class DeleteVectorsInput(_AuthFields):
    index_name: str = Field(description="Index name")
    ids: list[str] | None = Field(default=None, description="Vector IDs to delete")
    namespace: str | None = Field(
        default=None, description="Namespace to delete from"
    )
    delete_all: bool = Field(
        default=False, description="Delete every vector in the namespace"
    )
    filter: dict[str, Any] | None = Field(
        default=None, description="Metadata filter selecting vectors to delete"
    )


class CreateIndexInput(_AuthFields):
    name: str = Field(description="Index name")
    dimension: int = Field(description="Dimensionality of the vectors")
    metric: str = Field(
        default="cosine", description="Distance metric: cosine, euclidean, dotproduct"
    )
    cloud: str = Field(default="aws", description="Serverless cloud provider")
    region: str = Field(default="us-east-1", description="Serverless region")


class DeleteIndexInput(_AuthFields):
    index_name: str = Field(description="Index name")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=QueryInput)
@serialize_pydantic_return
async def query(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
    query_vector: list[float],
    top_k: int = 5,
    namespace: str | None = None,
    filter: dict[str, Any] | None = None,
    include_metadata: bool = True,
    include_values: bool = False,
) -> QueryOutput:
    """Vector similarity search on a Pinecone index (POST /query).

    Takes a query vector — works on every index type. For raw-text
    queries on integrated-embedding indexes, use `search_records`.
    """
    if not auth_data.get("api_key"):
        return QueryOutput(success=False, error="Missing Pinecone API key.")
    body: dict[str, Any] = {
        "vector": query_vector,
        "topK": top_k,
        "includeMetadata": include_metadata,
        "includeValues": include_values,
    }
    if namespace:
        body["namespace"] = namespace
    if filter:
        body["filter"] = filter
    try:
        headers = _headers(auth_data)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            host = await _resolve_host(client, headers, index_name)
            response = await client.post(f"{host}/query", headers=headers, json=body)
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
        success=True,
        matches=data.get("matches", []),
        namespace=data.get("namespace"),
        usage=data.get("usage"),
    )


@tool(args_schema=SearchRecordsInput)
@serialize_pydantic_return
async def search_records(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
    query_text: str,
    namespace: str = "__default__",
    top_k: int = 5,
    fields: list[str] | None = None,
    filter: dict[str, Any] | None = None,
    rerank: dict[str, Any] | None = None,
) -> SearchRecordsOutput:
    """Raw-text search on an integrated-embedding Pinecone index.

    Pinecone embeds `query_text` server-side — this works ONLY on
    indexes created with integrated embedding. For all other indexes
    use `query` with a vector.
    """
    if not auth_data.get("api_key"):
        return SearchRecordsOutput(success=False, error="Missing Pinecone API key.")
    query_obj: dict[str, Any] = {"top_k": top_k, "inputs": {"text": query_text}}
    if filter:
        query_obj["filter"] = filter
    body: dict[str, Any] = {"query": query_obj}
    if fields is not None:
        body["fields"] = fields
    if rerank is not None:
        body["rerank"] = rerank
    try:
        headers = _headers(auth_data)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            host = await _resolve_host(client, headers, index_name)
            response = await client.post(
                f"{host}/records/namespaces/{namespace}/search",
                headers=headers,
                json=body,
            )
        if not response.is_success:
            return SearchRecordsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchRecordsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchRecordsOutput(success=False, error=str(exc))
    return SearchRecordsOutput(
        success=True,
        hits=data.get("result", {}).get("hits", []),
        usage=data.get("usage"),
    )


@tool(args_schema=ListIndexesInput)
@serialize_pydantic_return
async def list_indexes(
    auth_type: str, auth_data: dict[str, Any]
) -> ListIndexesOutput:
    """List all indexes in the Pinecone project."""
    if not auth_data.get("api_key"):
        return ListIndexesOutput(success=False, error="Missing Pinecone API key.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_CONTROL_PLANE}/indexes", headers=_headers(auth_data)
            )
        if not response.is_success:
            return ListIndexesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListIndexesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListIndexesOutput(success=False, error=str(exc))
    return ListIndexesOutput(success=True, indexes=data.get("indexes", []))


@tool(args_schema=DescribeIndexInput)
@serialize_pydantic_return
async def describe_index(
    auth_type: str, auth_data: dict[str, Any], index_name: str
) -> DescribeIndexOutput:
    """Get an index's native config (dimension, metric, host, spec, status)."""
    if not auth_data.get("api_key"):
        return DescribeIndexOutput(success=False, error="Missing Pinecone API key.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_CONTROL_PLANE}/indexes/{index_name}", headers=_headers(auth_data)
            )
        if not response.is_success:
            return DescribeIndexOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DescribeIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DescribeIndexOutput(success=False, error=str(exc))
    return DescribeIndexOutput(success=True, data=data)


@tool(args_schema=DescribeIndexStatsInput)
@serialize_pydantic_return
async def describe_index_stats(
    auth_type: str, auth_data: dict[str, Any], index_name: str
) -> DescribeIndexStatsOutput:
    """Get an index's stats (namespaces, dimension, totalVectorCount)."""
    if not auth_data.get("api_key"):
        return DescribeIndexStatsOutput(
            success=False, error="Missing Pinecone API key."
        )
    try:
        headers = _headers(auth_data)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            host = await _resolve_host(client, headers, index_name)
            response = await client.post(
                f"{host}/describe_index_stats", headers=headers, json={}
            )
        if not response.is_success:
            return DescribeIndexStatsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DescribeIndexStatsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DescribeIndexStatsOutput(success=False, error=str(exc))
    return DescribeIndexStatsOutput(success=True, data=data)


@tool(args_schema=UpsertVectorsInput)
@serialize_pydantic_return
async def upsert_vectors(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
    vectors: list[dict[str, Any]],
    namespace: str | None = None,
) -> UpsertVectorsOutput:
    """Upsert native {id, values, metadata?} vectors into an index."""
    if not auth_data.get("api_key"):
        return UpsertVectorsOutput(success=False, error="Missing Pinecone API key.")
    body: dict[str, Any] = {"vectors": vectors}
    if namespace:
        body["namespace"] = namespace
    try:
        headers = _headers(auth_data)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            host = await _resolve_host(client, headers, index_name)
            response = await client.post(
                f"{host}/vectors/upsert", headers=headers, json=body
            )
        if not response.is_success:
            return UpsertVectorsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpsertVectorsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpsertVectorsOutput(success=False, error=str(exc))
    return UpsertVectorsOutput(success=True, data=data)


@tool(args_schema=DeleteVectorsInput)
@serialize_pydantic_return
async def delete_vectors(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
    ids: list[str] | None = None,
    namespace: str | None = None,
    delete_all: bool = False,
    filter: dict[str, Any] | None = None,
) -> DeleteVectorsOutput:
    """Delete vectors by IDs, by metadata filter, or all in a namespace."""
    if not auth_data.get("api_key"):
        return DeleteVectorsOutput(success=False, error="Missing Pinecone API key.")
    if not ids and not delete_all and not filter:
        return DeleteVectorsOutput(
            success=False, error="Provide ids, filter, or delete_all=true."
        )
    body: dict[str, Any] = {}
    if ids:
        body["ids"] = ids
    if delete_all:
        body["deleteAll"] = True
    if filter:
        body["filter"] = filter
    if namespace:
        body["namespace"] = namespace
    try:
        headers = _headers(auth_data)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            host = await _resolve_host(client, headers, index_name)
            response = await client.post(
                f"{host}/vectors/delete", headers=headers, json=body
            )
        if not response.is_success:
            return DeleteVectorsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json() if response.content else {}
    except httpx.TimeoutException:
        return DeleteVectorsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteVectorsOutput(success=False, error=str(exc))
    return DeleteVectorsOutput(success=True, data=data)


@tool(args_schema=CreateIndexInput)
@serialize_pydantic_return
async def create_index(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    dimension: int,
    metric: str = "cosine",
    cloud: str = "aws",
    region: str = "us-east-1",
) -> CreateIndexOutput:
    """Create a serverless index."""
    if not auth_data.get("api_key"):
        return CreateIndexOutput(success=False, error="Missing Pinecone API key.")
    body: dict[str, Any] = {
        "name": name,
        "dimension": dimension,
        "metric": metric,
        "spec": {"serverless": {"cloud": cloud, "region": region}},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_CONTROL_PLANE}/indexes", headers=_headers(auth_data), json=body
            )
        if not response.is_success:
            return CreateIndexOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateIndexOutput(success=False, error=str(exc))
    return CreateIndexOutput(success=True, data=data)


@tool(args_schema=DeleteIndexInput)
@serialize_pydantic_return
async def delete_index(
    auth_type: str, auth_data: dict[str, Any], index_name: str
) -> DeleteIndexOutput:
    """Delete an index."""
    if not auth_data.get("api_key"):
        return DeleteIndexOutput(success=False, error="Missing Pinecone API key.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_CONTROL_PLANE}/indexes/{index_name}", headers=_headers(auth_data)
            )
        if not response.is_success:
            return DeleteIndexOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteIndexOutput(success=False, error=str(exc))
    return DeleteIndexOutput(success=True)
