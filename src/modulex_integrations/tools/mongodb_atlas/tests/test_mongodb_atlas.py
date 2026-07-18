"""Tests for the MongoDB Atlas integration.

Database integration: the PyMongo ``AsyncMongoClient`` is mocked via
``unittest.mock.patch`` on the local ``_client`` helper. The mock is a
``MagicMock`` whose ``client[db][coll]`` chain resolves naturally and
whose driver coroutines are ``AsyncMock``s configured per test.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from modulex_integrations.tools.mongodb_atlas import (
    TOOLS,
    delete_documents,
    insert_documents,
    list_collections,
    list_databases,
    list_search_indexes,
    manifest,
    query,
)
from modulex_integrations.tools.mongodb_atlas.outputs import (
    DeleteDocumentsOutput,
    InsertDocumentsOutput,
    ListCollectionsOutput,
    ListDatabasesOutput,
    ListSearchIndexesOutput,
    QueryOutput,
)

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "connection_string": "mongodb+srv://user:pass@cluster.mongodb.net/"
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


def _mock_client(**collection_methods: Any) -> MagicMock:
    """Build a client mock; ``collection_methods`` land on the collection."""
    client = MagicMock()
    client.close = AsyncMock()
    collection = client.__getitem__.return_value.__getitem__.return_value
    for name, mock in collection_methods.items():
        setattr(collection, name, mock)
    return client


def _cursor(docs: list[dict[str, Any]]) -> MagicMock:
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=docs)
    return cursor


def _patched(client: MagicMock) -> Any:
    return patch(
        "modulex_integrations.tools.mongodb_atlas.tools._client",
        return_value=client,
    )


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_six_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}

    def test_manifest_first_category_is_vector_database(self) -> None:
        assert manifest.categories[0] == "Vector Database"


# --- Per-action tests ---------------------------------------------------------


@pytest.mark.asyncio
async def test_query_runs_vector_search_pipeline() -> None:
    oid = ObjectId()
    client = _mock_client(
        aggregate=AsyncMock(
            return_value=_cursor([{"_id": oid, "title": "Doc", "score": 0.91}])
        )
    )
    with _patched(client):
        result_dict = await query.ainvoke(
            _args(
                database="db",
                collection="articles",
                index_name="vector_index",
                query_vector=[0.1, 0.2],
                path="embedding",
            )
        )
    assert isinstance(result_dict, dict)
    result = QueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.documents is not None
    assert result.documents[0]["title"] == "Doc"
    # ObjectId survives as Relaxed Extended JSON.
    assert result.documents[0]["_id"] == {"$oid": str(oid)}

    collection = client.__getitem__.return_value.__getitem__.return_value
    pipeline = collection.aggregate.call_args.args[0]
    assert pipeline[0]["$vectorSearch"]["index"] == "vector_index"
    assert pipeline[0]["$vectorSearch"]["queryVector"] == [0.1, 0.2]
    assert pipeline[1] == {"$addFields": {"score": {"$meta": "vectorSearchScore"}}}
    # include_vectors defaults to False -> vector path projected out.
    assert pipeline[2] == {"$project": {"embedding": 0}}
    client.close.assert_awaited()


@pytest.mark.asyncio
async def test_query_failure_surfaces() -> None:
    client = _mock_client(
        aggregate=AsyncMock(side_effect=RuntimeError("index not found"))
    )
    with _patched(client):
        result = QueryOutput.model_validate(
            await query.ainvoke(
                _args(
                    database="db",
                    collection="articles",
                    index_name="missing",
                    query_vector=[0.1],
                    path="embedding",
                )
            )
        )
    assert result.success is False
    assert result.error == "index not found"


@pytest.mark.asyncio
async def test_list_databases() -> None:
    client = MagicMock()
    client.close = AsyncMock()
    client.list_databases = AsyncMock(
        return_value=_cursor([{"name": "db", "sizeOnDisk": 1024, "empty": False}])
    )
    with _patched(client):
        result = ListDatabasesOutput.model_validate(
            await list_databases.ainvoke(_args())
        )
    assert result.success is True
    assert result.databases == [{"name": "db", "sizeOnDisk": 1024, "empty": False}]


@pytest.mark.asyncio
async def test_list_collections() -> None:
    client = MagicMock()
    client.close = AsyncMock()
    db = client.__getitem__.return_value
    db.list_collections = AsyncMock(
        return_value=_cursor([{"name": "articles", "type": "collection"}])
    )
    with _patched(client):
        result = ListCollectionsOutput.model_validate(
            await list_collections.ainvoke(_args(database="db"))
        )
    assert result.success is True
    assert result.collections is not None
    assert result.collections[0]["name"] == "articles"


@pytest.mark.asyncio
async def test_list_search_indexes() -> None:
    client = _mock_client(
        list_search_indexes=AsyncMock(
            return_value=_cursor(
                [
                    {
                        "name": "vector_index",
                        "type": "vectorSearch",
                        "latestDefinition": {
                            "fields": [
                                {
                                    "type": "vector",
                                    "path": "embedding",
                                    "numDimensions": 384,
                                }
                            ]
                        },
                    }
                ]
            )
        )
    )
    with _patched(client):
        result = ListSearchIndexesOutput.model_validate(
            await list_search_indexes.ainvoke(
                _args(database="db", collection="articles")
            )
        )
    assert result.success is True
    assert result.indexes is not None
    assert result.indexes[0]["name"] == "vector_index"


@pytest.mark.asyncio
async def test_insert_documents() -> None:
    ids = [ObjectId(), ObjectId()]
    insert_result = MagicMock()
    insert_result.inserted_ids = ids
    client = _mock_client(insert_many=AsyncMock(return_value=insert_result))
    with _patched(client):
        result = InsertDocumentsOutput.model_validate(
            await insert_documents.ainvoke(
                _args(
                    database="db",
                    collection="articles",
                    documents=[{"a": 1}, {"a": 2}],
                )
            )
        )
    assert result.success is True
    assert result.inserted_count == 2
    assert result.inserted_ids == [str(i) for i in ids]


@pytest.mark.asyncio
async def test_delete_documents() -> None:
    delete_result = MagicMock()
    delete_result.deleted_count = 3
    client = _mock_client(delete_many=AsyncMock(return_value=delete_result))
    with _patched(client):
        result = DeleteDocumentsOutput.model_validate(
            await delete_documents.ainvoke(
                _args(database="db", collection="articles", filter={"a": 1})
            )
        )
    assert result.success is True
    assert result.deleted_count == 3


@pytest.mark.asyncio
async def test_delete_documents_rejects_empty_filter() -> None:
    result = DeleteDocumentsOutput.model_validate(
        await delete_documents.ainvoke(
            _args(database="db", collection="articles", filter={})
        )
    )
    assert result.success is False
    assert result.error is not None
    assert "empty filter" in result.error


@pytest.mark.asyncio
async def test_missing_connection_string_short_circuits() -> None:
    result = ListDatabasesOutput.model_validate(
        await list_databases.ainvoke({"auth_type": "custom", "auth_data": {}})
    )
    assert result.success is False
    assert result.error is not None
    assert "connection string" in result.error
