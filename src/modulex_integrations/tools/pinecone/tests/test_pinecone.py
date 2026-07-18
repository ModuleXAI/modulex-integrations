"""Happy-path tests for every pinecone @tool, plus a manifest sanity check."""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.pinecone import (
    TOOLS,
    create_index,
    delete_index,
    delete_vectors,
    describe_index,
    describe_index_stats,
    list_indexes,
    manifest,
    query,
    search_records,
    upsert_vectors,
)
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

CONTROL = "https://api.pinecone.io"
HOST = "docs-abc123.svc.aped-4627-b74a.pinecone.io"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {"api_key": "pcsk_fake"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


def _mock_describe(httpx_mock: Any, index_name: str = "docs") -> None:
    """Register the control-plane describe used for host resolution."""
    httpx_mock.add_response(
        method="GET",
        url=f"{CONTROL}/indexes/{index_name}",
        json={"name": index_name, "dimension": 3, "metric": "cosine", "host": HOST},
    )


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_nine_actions(self) -> None:
        assert len(manifest.actions) == 9

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}

    def test_manifest_first_category_is_vector_database(self) -> None:
        assert manifest.categories[0] == "Vector Database"


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_query(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_describe(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"https://{HOST}/query",
        json={
            "matches": [
                {"id": "a", "score": 0.93, "metadata": {"text": "hello"}},
            ],
            "namespace": "ns1",
            "usage": {"readUnits": 5},
        },
    )
    result_dict = await query.ainvoke(
        _args(index_name="docs", query_vector=[0.1, 0.2, 0.3], namespace="ns1")
    )
    assert isinstance(result_dict, dict)
    result = QueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.matches is not None
    assert result.matches[0]["id"] == "a"
    assert result.namespace == "ns1"


@pytest.mark.asyncio
async def test_query_host_resolution_failure_surfaces(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{CONTROL}/indexes/missing",
        status_code=404,
        text='{"error":{"code":"NOT_FOUND"}}',
    )
    result = QueryOutput.model_validate(
        await query.ainvoke(_args(index_name="missing", query_vector=[0.1]))
    )
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error


@pytest.mark.asyncio
async def test_search_records(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_describe(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"https://{HOST}/records/namespaces/__default__/search",
        json={
            "result": {
                "hits": [
                    {"_id": "r1", "_score": 0.88, "fields": {"chunk_text": "hi"}},
                ]
            },
            "usage": {"readUnits": 6, "embedTotalTokens": 12},
        },
    )
    result = SearchRecordsOutput.model_validate(
        await search_records.ainvoke(_args(index_name="docs", query_text="greeting"))
    )
    assert result.success is True
    assert result.hits is not None
    assert result.hits[0]["_id"] == "r1"
    request = httpx_mock.get_requests()[-1]
    body = json.loads(request.content)
    assert body["query"]["inputs"] == {"text": "greeting"}


@pytest.mark.asyncio
async def test_list_indexes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{CONTROL}/indexes",
        json={"indexes": [{"name": "docs", "dimension": 3, "host": HOST}]},
    )
    result = ListIndexesOutput.model_validate(await list_indexes.ainvoke(_args()))
    assert result.success is True
    assert result.indexes is not None
    assert result.indexes[0]["name"] == "docs"


@pytest.mark.asyncio
async def test_describe_index(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_describe(httpx_mock)
    result = DescribeIndexOutput.model_validate(
        await describe_index.ainvoke(_args(index_name="docs"))
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["host"] == HOST


@pytest.mark.asyncio
async def test_describe_index_stats(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_describe(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"https://{HOST}/describe_index_stats",
        json={"namespaces": {"ns1": {"vectorCount": 10}}, "totalVectorCount": 10},
    )
    result = DescribeIndexStatsOutput.model_validate(
        await describe_index_stats.ainvoke(_args(index_name="docs"))
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["totalVectorCount"] == 10


@pytest.mark.asyncio
async def test_upsert_vectors(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_describe(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"https://{HOST}/vectors/upsert",
        json={"upsertedCount": 2},
    )
    result = UpsertVectorsOutput.model_validate(
        await upsert_vectors.ainvoke(
            _args(
                index_name="docs",
                vectors=[
                    {"id": "a", "values": [0.1, 0.2, 0.3]},
                    {"id": "b", "values": [0.4, 0.5, 0.6]},
                ],
            )
        )
    )
    assert result.success is True
    assert result.data == {"upsertedCount": 2}


@pytest.mark.asyncio
async def test_delete_vectors_by_ids(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_describe(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"https://{HOST}/vectors/delete",
        json={},
    )
    result = DeleteVectorsOutput.model_validate(
        await delete_vectors.ainvoke(_args(index_name="docs", ids=["a", "b"]))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_vectors_requires_selector() -> None:
    result = DeleteVectorsOutput.model_validate(
        await delete_vectors.ainvoke(_args(index_name="docs"))
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_create_index(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{CONTROL}/indexes",
        json={
            "name": "docs",
            "dimension": 3,
            "metric": "cosine",
            "spec": {"serverless": {"cloud": "aws", "region": "us-east-1"}},
            "status": {"ready": False, "state": "Initializing"},
        },
    )
    result = CreateIndexOutput.model_validate(
        await create_index.ainvoke(_args(name="docs", dimension=3))
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["name"] == "docs"


@pytest.mark.asyncio
async def test_delete_index(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{CONTROL}/indexes/docs",
        status_code=202,
    )
    result = DeleteIndexOutput.model_validate(
        await delete_index.ainvoke(_args(index_name="docs"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_missing_api_key_short_circuits() -> None:
    result = ListIndexesOutput.model_validate(
        await list_indexes.ainvoke({"auth_type": "custom", "auth_data": {}})
    )
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
