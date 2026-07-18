"""MongoDB Atlas LangChain ``@tool`` functions.

Pure SDK integration over PyMongo's async API (``AsyncMongoClient``).
Token-based runtime convention (``auth_type, auth_data`` first args) —
``auth_type`` is informational (modulex schema label ``custom``); the
tool body pulls ``connection_string`` out of ``auth_data``.

Every action opens a fresh client (no pool kept across calls) and
closes it in a ``finally`` block. Vector search is a pass-through
``$vectorSearch`` aggregation with the user's own index/path/vector —
no ModuleX-side embedding or result normalization. Documents are
serialized to MongoDB Relaxed Extended JSON (ObjectId → {"$oid": ...},
dates → {"$date": ...}) so results stay JSON-serializable.

Note: ``pymongo`` is imported lazily inside the helpers so the
integration's manifest can still be inspected when the driver is not
installed (useful for the modulex-side package_loader cold-start).
"""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.mongodb_atlas.outputs import (
    DeleteDocumentsOutput,
    InsertDocumentsOutput,
    ListCollectionsOutput,
    ListDatabasesOutput,
    ListSearchIndexesOutput,
    QueryOutput,
)

__all__ = [
    "delete_documents",
    "insert_documents",
    "list_collections",
    "list_databases",
    "list_search_indexes",
    "query",
]

_TIMEOUT_MS = 30000


def _client(auth_data: dict[str, Any]) -> Any:
    """Open an async MongoDB client from the connection string."""
    from pymongo import AsyncMongoClient

    return AsyncMongoClient(
        auth_data.get("connection_string"),
        serverSelectionTimeoutMS=_TIMEOUT_MS,
    )


def _to_jsonable(value: Any) -> Any:
    """Convert BSON values to MongoDB Relaxed Extended JSON."""
    from bson import json_util

    return json.loads(
        json_util.dumps(value, json_options=json_util.RELAXED_JSON_OPTIONS)
    )


def _missing_credentials(auth_data: dict[str, Any]) -> str | None:
    if not auth_data.get("connection_string"):
        return "Missing MongoDB Atlas connection string in credentials."
    return None


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (custom)")
    auth_data: dict[str, Any] = Field(description="connection_string")


class QueryInput(_AuthFields):
    database: str = Field(description="Database name")
    collection: str = Field(description="Collection name")
    index_name: str = Field(description="Atlas Vector Search index name")
    query_vector: list[float] = Field(description="Query embedding vector")
    path: str = Field(description="Document field that holds the vectors")
    num_candidates: int = Field(
        default=100, description="Candidates considered by the ANN search"
    )
    limit: int = Field(default=5, description="Maximum number of results")
    filter: dict[str, Any] | None = Field(
        default=None, description="Pre-filter (MQL match expression)"
    )
    include_vectors: bool = Field(
        default=False, description="Keep the vector field in the results"
    )


class ListDatabasesInput(_AuthFields):
    pass


class ListCollectionsInput(_AuthFields):
    database: str = Field(description="Database name")


class ListSearchIndexesInput(_AuthFields):
    database: str = Field(description="Database name")
    collection: str = Field(description="Collection name")


class InsertDocumentsInput(_AuthFields):
    database: str = Field(description="Database name")
    collection: str = Field(description="Collection name")
    documents: list[dict[str, Any]] = Field(description="Documents to insert")


class DeleteDocumentsInput(_AuthFields):
    database: str = Field(description="Database name")
    collection: str = Field(description="Collection name")
    filter: dict[str, Any] = Field(
        description="MQL filter selecting documents to delete (must be non-empty)"
    )


# --- Tools -----------------------------------------------------------------


@tool(args_schema=QueryInput)
@serialize_pydantic_return
async def query(
    auth_type: str,
    auth_data: dict[str, Any],
    database: str,
    collection: str,
    index_name: str,
    query_vector: list[float],
    path: str,
    num_candidates: int = 100,
    limit: int = 5,
    filter: dict[str, Any] | None = None,
    include_vectors: bool = False,
) -> QueryOutput:
    """Vector similarity search via a $vectorSearch aggregation.

    Atlas Vector Search takes a query vector — there is no server-side
    text embedding; embed your query before calling. Results are the
    native documents plus a `score` field (vectorSearchScore), in
    MongoDB Relaxed Extended JSON.
    """
    err = _missing_credentials(auth_data)
    if err:
        return QueryOutput(success=False, error=err)
    vector_search: dict[str, Any] = {
        "index": index_name,
        "path": path,
        "queryVector": query_vector,
        "numCandidates": num_candidates,
        "limit": limit,
    }
    if filter:
        vector_search["filter"] = filter
    pipeline: list[dict[str, Any]] = [
        {"$vectorSearch": vector_search},
        {"$addFields": {"score": {"$meta": "vectorSearchScore"}}},
    ]
    if not include_vectors:
        pipeline.append({"$project": {path: 0}})
    try:
        client = _client(auth_data)
        try:
            cursor = await client[database][collection].aggregate(pipeline)
            documents = await cursor.to_list(None)
        finally:
            await client.close()
    except Exception as exc:
        return QueryOutput(success=False, error=str(exc))
    return QueryOutput(success=True, documents=_to_jsonable(documents))


@tool(args_schema=ListDatabasesInput)
@serialize_pydantic_return
async def list_databases(
    auth_type: str, auth_data: dict[str, Any]
) -> ListDatabasesOutput:
    """List all databases in the cluster."""
    err = _missing_credentials(auth_data)
    if err:
        return ListDatabasesOutput(success=False, error=err)
    try:
        client = _client(auth_data)
        try:
            cursor = await client.list_databases()
            databases = await cursor.to_list(None)
        finally:
            await client.close()
    except Exception as exc:
        return ListDatabasesOutput(success=False, error=str(exc))
    return ListDatabasesOutput(success=True, databases=_to_jsonable(databases))


@tool(args_schema=ListCollectionsInput)
@serialize_pydantic_return
async def list_collections(
    auth_type: str, auth_data: dict[str, Any], database: str
) -> ListCollectionsOutput:
    """List collections in a database (native listCollections entries)."""
    err = _missing_credentials(auth_data)
    if err:
        return ListCollectionsOutput(success=False, error=err)
    try:
        client = _client(auth_data)
        try:
            cursor = await client[database].list_collections()
            collections = await cursor.to_list(None)
        finally:
            await client.close()
    except Exception as exc:
        return ListCollectionsOutput(success=False, error=str(exc))
    return ListCollectionsOutput(success=True, collections=_to_jsonable(collections))


@tool(args_schema=ListSearchIndexesInput)
@serialize_pydantic_return
async def list_search_indexes(
    auth_type: str,
    auth_data: dict[str, Any],
    database: str,
    collection: str,
) -> ListSearchIndexesOutput:
    """List Atlas Search / Vector Search indexes on a collection.

    Use this to discover the index name, vector path, and dimensions
    needed by `query`.
    """
    err = _missing_credentials(auth_data)
    if err:
        return ListSearchIndexesOutput(success=False, error=err)
    try:
        client = _client(auth_data)
        try:
            cursor = await client[database][collection].list_search_indexes()
            indexes = await cursor.to_list(None)
        finally:
            await client.close()
    except Exception as exc:
        return ListSearchIndexesOutput(success=False, error=str(exc))
    return ListSearchIndexesOutput(success=True, indexes=_to_jsonable(indexes))


@tool(args_schema=InsertDocumentsInput)
@serialize_pydantic_return
async def insert_documents(
    auth_type: str,
    auth_data: dict[str, Any],
    database: str,
    collection: str,
    documents: list[dict[str, Any]],
) -> InsertDocumentsOutput:
    """Insert documents into a collection (insert_many)."""
    err = _missing_credentials(auth_data)
    if err:
        return InsertDocumentsOutput(success=False, error=err)
    if not documents:
        return InsertDocumentsOutput(success=False, error="documents is empty.")
    try:
        client = _client(auth_data)
        try:
            result = await client[database][collection].insert_many(documents)
        finally:
            await client.close()
    except Exception as exc:
        return InsertDocumentsOutput(success=False, error=str(exc))
    inserted = [str(i) for i in result.inserted_ids]
    return InsertDocumentsOutput(
        success=True, inserted_ids=inserted, inserted_count=len(inserted)
    )


@tool(args_schema=DeleteDocumentsInput)
@serialize_pydantic_return
async def delete_documents(
    auth_type: str,
    auth_data: dict[str, Any],
    database: str,
    collection: str,
    filter: dict[str, Any],
) -> DeleteDocumentsOutput:
    """Delete documents matching a non-empty MQL filter (delete_many).

    An empty filter is rejected — it would delete every document in the
    collection.
    """
    err = _missing_credentials(auth_data)
    if err:
        return DeleteDocumentsOutput(success=False, error=err)
    if not filter:
        return DeleteDocumentsOutput(
            success=False,
            error=(
                "Refusing to delete with an empty filter (it would match "
                "every document)."
            ),
        )
    try:
        client = _client(auth_data)
        try:
            result = await client[database][collection].delete_many(filter)
        finally:
            await client.close()
    except Exception as exc:
        return DeleteDocumentsOutput(success=False, error=str(exc))
    return DeleteDocumentsOutput(success=True, deleted_count=result.deleted_count)
