"""Happy-path tests for every qdrant @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.qdrant import (
    TOOLS,
    create_collection,
    delete_collection,
    delete_points,
    get_collection_info,
    list_collections,
    manifest,
    query,
    upsert_points,
)
from modulex_integrations.tools.qdrant.outputs import (
    CreateCollectionOutput,
    DeleteCollectionOutput,
    DeletePointsOutput,
    GetCollectionInfoOutput,
    ListCollectionsOutput,
    QueryOutput,
    UpsertPointsOutput,
)

API = "https://qdrant.example.com:6333"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {"base_url": API, "api_key": "fake_key"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_seven_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}

    def test_manifest_first_category_is_vector_database(self) -> None:
        assert manifest.categories[0] == "Vector Database"


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_query_with_vector(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/collections/docs/points/query",
        json={
            "result": {
                "points": [
                    {"id": 1, "score": 0.98, "payload": {"text": "hello"}},
                    {"id": 2, "score": 0.87, "payload": {"text": "world"}},
                ]
            },
            "status": "ok",
            "time": 0.001,
        },
    )
    result_dict = await query.ainvoke(
        _args(collection_name="docs", query_vector=[0.1, 0.2, 0.3])
    )
    assert isinstance(result_dict, dict)
    result = QueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.points is not None
    assert len(result.points) == 2
    assert result.points[0]["payload"] == {"text": "hello"}


@pytest.mark.asyncio
async def test_query_with_text_uses_inference_document(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/collections/docs/points/query",
        json={"result": {"points": []}, "status": "ok"},
    )
    result_dict = await query.ainvoke(
        _args(
            collection_name="docs",
            query_text="how to bake cookies",
            model="sentence-transformers/all-minilm-l6-v2",
        )
    )
    result = QueryOutput.model_validate(result_dict)
    assert result.success is True
    request = httpx_mock.get_requests()[0]
    import json

    body = json.loads(request.content)
    assert body["query"] == {
        "text": "how to bake cookies",
        "model": "sentence-transformers/all-minilm-l6-v2",
    }


@pytest.mark.asyncio
async def test_query_rejects_text_without_model() -> None:
    result = QueryOutput.model_validate(
        await query.ainvoke(_args(collection_name="docs", query_text="hello"))
    )
    assert result.success is False
    assert result.error is not None
    assert "model" in result.error


@pytest.mark.asyncio
async def test_query_rejects_vector_and_text_together() -> None:
    result = QueryOutput.model_validate(
        await query.ainvoke(
            _args(collection_name="docs", query_vector=[0.1], query_text="x", model="m")
        )
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_query_api_error_surfaces(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/collections/docs/points/query",
        status_code=404,
        text="Not found: Collection `docs` doesn't exist!",
    )
    result = QueryOutput.model_validate(
        await query.ainvoke(_args(collection_name="docs", query_vector=[0.1]))
    )
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error


@pytest.mark.asyncio
async def test_list_collections(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/collections",
        json={"result": {"collections": [{"name": "docs"}, {"name": "faq"}]}},
    )
    result = ListCollectionsOutput.model_validate(await list_collections.ainvoke(_args()))
    assert result.success is True
    assert result.collections == [{"name": "docs"}, {"name": "faq"}]


@pytest.mark.asyncio
async def test_get_collection_info(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/collections/docs",
        json={
            "result": {
                "status": "green",
                "points_count": 42,
                "config": {"params": {"vectors": {"size": 384, "distance": "Cosine"}}},
            }
        },
    )
    result = GetCollectionInfoOutput.model_validate(
        await get_collection_info.ainvoke(_args(collection_name="docs"))
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["points_count"] == 42


@pytest.mark.asyncio
async def test_upsert_points(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/collections/docs/points?wait=true",
        json={"result": {"operation_id": 7, "status": "completed"}},
    )
    result = UpsertPointsOutput.model_validate(
        await upsert_points.ainvoke(
            _args(
                collection_name="docs",
                points=[{"id": 1, "vector": [0.1, 0.2], "payload": {"a": 1}}],
            )
        )
    )
    assert result.success is True
    assert result.data == {"operation_id": 7, "status": "completed"}


@pytest.mark.asyncio
async def test_delete_points_by_ids(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/collections/docs/points/delete?wait=true",
        json={"result": {"operation_id": 8, "status": "acknowledged"}},
    )
    result = DeletePointsOutput.model_validate(
        await delete_points.ainvoke(_args(collection_name="docs", point_ids=[1, 2]))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_points_requires_ids_or_filter() -> None:
    result = DeletePointsOutput.model_validate(
        await delete_points.ainvoke(_args(collection_name="docs"))
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_create_collection(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/collections/docs",
        json={"result": True, "status": "ok"},
    )
    result = CreateCollectionOutput.model_validate(
        await create_collection.ainvoke(_args(collection_name="docs", vector_size=384))
    )
    assert result.success is True
    assert result.result is True


@pytest.mark.asyncio
async def test_delete_collection(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/collections/docs",
        json={"result": True, "status": "ok"},
    )
    result = DeleteCollectionOutput.model_validate(
        await delete_collection.ainvoke(_args(collection_name="docs"))
    )
    assert result.success is True
    assert result.result is True


@pytest.mark.asyncio
async def test_missing_base_url_short_circuits() -> None:
    result = ListCollectionsOutput.model_validate(
        await list_collections.ainvoke(
            {"auth_type": "custom", "auth_data": {"api_key": "k"}}
        )
    )
    assert result.success is False
    assert result.error is not None
    assert "base URL" in result.error
