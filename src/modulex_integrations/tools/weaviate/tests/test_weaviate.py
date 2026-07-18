"""Happy-path tests for every weaviate @tool, plus a manifest sanity check."""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.weaviate import (
    TOOLS,
    create_class,
    delete_class,
    delete_object,
    get_class_stats,
    insert_object,
    list_classes,
    manifest,
    query,
)
from modulex_integrations.tools.weaviate.outputs import (
    CreateClassOutput,
    DeleteClassOutput,
    DeleteObjectOutput,
    GetClassStatsOutput,
    InsertObjectOutput,
    ListClassesOutput,
    QueryOutput,
)
from modulex_integrations.tools.weaviate.tools import _gql_literal

API = "https://cluster.weaviate.example"

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


# --- GraphQL literal serializer -----------------------------------------------


def test_gql_literal_emits_operator_as_enum() -> None:
    where = {"path": ["title"], "operator": "Equal", "valueText": "hello"}
    assert (
        _gql_literal(where)
        == '{path: ["title"], operator: Equal, valueText: "hello"}'
    )


def test_gql_literal_nested_operands() -> None:
    where = {
        "operator": "And",
        "operands": [
            {"path": ["year"], "operator": "GreaterThan", "valueInt": 2020},
            {"path": ["draft"], "operator": "Equal", "valueBoolean": False},
        ],
    }
    out = _gql_literal(where)
    assert "operator: And" in out
    assert "valueInt: 2020" in out
    assert "valueBoolean: false" in out


def test_gql_literal_rejects_bad_field_name() -> None:
    with pytest.raises(ValueError, match="Invalid GraphQL field name"):
        _gql_literal({"bad key!": 1})


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_query_with_vector(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/graphql",
        json={
            "data": {
                "Get": {
                    "Article": [
                        {
                            "title": "Hello",
                            "_additional": {
                                "id": "uuid-1",
                                "certainty": 0.95,
                                "distance": 0.1,
                            },
                        }
                    ]
                }
            }
        },
    )
    result_dict = await query.ainvoke(
        _args(
            class_name="Article",
            query_vector=[0.1, 0.2],
            properties=["title"],
        )
    )
    assert isinstance(result_dict, dict)
    result = QueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.objects is not None
    assert result.objects[0]["title"] == "Hello"
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert "nearVector" in body["query"]
    assert "title" in body["query"]


@pytest.mark.asyncio
async def test_query_with_text_uses_near_text(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/graphql",
        json={"data": {"Get": {"Article": []}}},
    )
    result = QueryOutput.model_validate(
        await query.ainvoke(_args(class_name="Article", query_text="greetings"))
    )
    assert result.success is True
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert 'nearText: {concepts: ["greetings"]}' in body["query"]


@pytest.mark.asyncio
async def test_query_graphql_errors_surface(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/graphql",
        json={
            "errors": [
                {"message": "explorer: vectorize params: no vectorizer module"}
            ]
        },
    )
    result = QueryOutput.model_validate(
        await query.ainvoke(_args(class_name="Article", query_text="hi"))
    )
    assert result.success is False
    assert result.error is not None
    assert "vectorizer" in result.error


@pytest.mark.asyncio
async def test_query_rejects_invalid_class_name() -> None:
    result = QueryOutput.model_validate(
        await query.ainvoke(
            _args(class_name="Bad Class!", query_vector=[0.1])
        )
    )
    assert result.success is False
    assert result.error is not None
    assert "class name" in result.error


@pytest.mark.asyncio
async def test_query_requires_vector_or_text() -> None:
    result = QueryOutput.model_validate(
        await query.ainvoke(_args(class_name="Article"))
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_list_classes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/schema",
        json={
            "classes": [
                {"class": "Article", "vectorizer": "text2vec-openai"},
                {"class": "Author", "vectorizer": "none"},
            ]
        },
    )
    result = ListClassesOutput.model_validate(await list_classes.ainvoke(_args()))
    assert result.success is True
    assert result.classes is not None
    assert len(result.classes) == 2


@pytest.mark.asyncio
async def test_get_class_stats(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/graphql",
        json={"data": {"Aggregate": {"Article": [{"meta": {"count": 128}}]}}},
    )
    result = GetClassStatsOutput.model_validate(
        await get_class_stats.ainvoke(_args(class_name="Article"))
    )
    assert result.success is True
    assert result.count == 128
    assert result.class_name == "Article"


@pytest.mark.asyncio
async def test_insert_object(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/objects",
        json={
            "id": "uuid-9",
            "class": "Article",
            "properties": {"title": "New"},
        },
    )
    result = InsertObjectOutput.model_validate(
        await insert_object.ainvoke(
            _args(class_name="Article", properties={"title": "New"})
        )
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "uuid-9"


@pytest.mark.asyncio
async def test_delete_object(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/v1/objects/Article/uuid-9",
        status_code=204,
    )
    result = DeleteObjectOutput.model_validate(
        await delete_object.ainvoke(_args(class_name="Article", object_id="uuid-9"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_class(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/schema",
        json={"class": "Article", "vectorizer": "text2vec-openai"},
    )
    result = CreateClassOutput.model_validate(
        await create_class.ainvoke(
            _args(class_name="Article", vectorizer="text2vec-openai")
        )
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["class"] == "Article"


@pytest.mark.asyncio
async def test_delete_class(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/v1/schema/Article",
        status_code=200,
    )
    result = DeleteClassOutput.model_validate(
        await delete_class.ainvoke(_args(class_name="Article"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_missing_base_url_short_circuits() -> None:
    result = ListClassesOutput.model_validate(
        await list_classes.ainvoke(
            {"auth_type": "custom", "auth_data": {"api_key": "k"}}
        )
    )
    assert result.success is False
    assert result.error is not None
    assert "base URL" in result.error
