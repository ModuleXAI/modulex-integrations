"""Weaviate LangChain ``@tool`` functions.

Pure HTTP pass-through over the Weaviate REST + GraphQL APIs.
Token-based runtime convention (``auth_type, auth_data`` first args) —
``auth_type`` is informational (modulex schema label ``custom``); the
tool body pulls ``base_url`` and the optional ``api_key`` out of
``auth_data``.

Search goes through Weaviate's GraphQL ``Get`` endpoint: ``nearVector``
for client-supplied embeddings, ``nearText`` when the collection has a
vectorizer module that embeds the text server-side. No ModuleX-side
embedding or result normalization.

Because GraphQL queries are assembled as text, identifier-shaped inputs
(class names, property names) are validated against a strict pattern
before interpolation, and JSON values are serialized through
``_gql_literal`` (the Weaviate ``operator`` filter field is a GraphQL
enum and is emitted raw).
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.weaviate.outputs import (
    CreateClassOutput,
    DeleteClassOutput,
    DeleteObjectOutput,
    GetClassStatsOutput,
    InsertObjectOutput,
    ListClassesOutput,
    QueryOutput,
)

__all__ = [
    "create_class",
    "delete_class",
    "delete_object",
    "get_class_stats",
    "insert_object",
    "list_classes",
    "query",
]

_TIMEOUT = 30.0

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _base_url(auth_data: dict[str, Any]) -> str:
    return str(auth_data.get("base_url", "") or "").rstrip("/")


def _headers(auth_data: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = auth_data.get("api_key")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _missing_credentials(auth_data: dict[str, Any]) -> str | None:
    if not auth_data.get("base_url"):
        return "Missing Weaviate base URL in credentials."
    return None


def _bad_identifier(kind: str, value: str) -> str | None:
    if not _IDENTIFIER.match(value):
        return f"Invalid {kind} {value!r}: must match [A-Za-z][A-Za-z0-9_]*."
    return None


def _gql_literal(value: Any) -> str:
    """Serialize a JSON value to a GraphQL input literal.

    Dict keys are emitted unquoted (GraphQL object fields); the Weaviate
    ``operator`` filter field is a GraphQL enum, so its string value is
    emitted raw instead of quoted.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_gql_literal(v) for v in value) + "]"
    if isinstance(value, dict):
        parts: list[str] = []
        for key, val in value.items():
            if not _IDENTIFIER.match(str(key)):
                raise ValueError(f"Invalid GraphQL field name: {key!r}")
            if key == "operator" and isinstance(val, str):
                parts.append(f"{key}: {val}")
            else:
                parts.append(f"{key}: {_gql_literal(val)}")
        return "{" + ", ".join(parts) + "}"
    raise ValueError(f"Cannot serialize {type(value).__name__} to GraphQL")


def _graphql_errors(data: dict[str, Any]) -> str | None:
    errors = data.get("errors")
    if errors:
        return "; ".join(
            str(e.get("message", "unknown GraphQL error")) for e in errors
        )
    return None


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (custom)")
    auth_data: dict[str, Any] = Field(description="base_url + optional api_key")


class QueryInput(_AuthFields):
    class_name: str = Field(description="Weaviate class (collection) to search")
    query_vector: list[float] | None = Field(
        default=None, description="Query embedding vector (nearVector)"
    )
    query_text: str | None = Field(
        default=None,
        description=(
            "Raw text query (nearText) — requires the class to have a "
            "vectorizer module"
        ),
    )
    limit: int = Field(default=5, description="Maximum number of results")
    certainty: float | None = Field(
        default=None, description="Minimum certainty threshold (0-1)"
    )
    distance: float | None = Field(
        default=None, description="Maximum distance threshold"
    )
    properties: list[str] | None = Field(
        default=None, description="Object properties to return"
    )
    where: dict[str, Any] | None = Field(
        default=None,
        description="Weaviate where-filter object (path/operator/value*)",
    )
    include_vector: bool = Field(
        default=False, description="Include object vectors in results"
    )


class ListClassesInput(_AuthFields):
    pass


class GetClassStatsInput(_AuthFields):
    class_name: str = Field(description="Class name")


class InsertObjectInput(_AuthFields):
    class_name: str = Field(description="Class name")
    properties: dict[str, Any] = Field(description="Object properties")
    object_id: str | None = Field(
        default=None, description="Optional object UUID (server-generated if omitted)"
    )
    vector: list[float] | None = Field(
        default=None,
        description="Object vector (omit when the class has a vectorizer)",
    )


class DeleteObjectInput(_AuthFields):
    class_name: str = Field(description="Class name")
    object_id: str = Field(description="Object UUID")


class CreateClassInput(_AuthFields):
    class_name: str = Field(description="Class name")
    description: str | None = Field(default=None, description="Class description")
    vectorizer: str | None = Field(
        default=None,
        description="Vectorizer module (e.g. text2vec-openai; omit for none)",
    )
    properties: list[dict[str, Any]] | None = Field(
        default=None,
        description="Weaviate-native property definitions ({name, dataType, ...})",
    )


class DeleteClassInput(_AuthFields):
    class_name: str = Field(description="Class name")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=QueryInput)
@serialize_pydantic_return
async def query(
    auth_type: str,
    auth_data: dict[str, Any],
    class_name: str,
    query_vector: list[float] | None = None,
    query_text: str | None = None,
    limit: int = 5,
    certainty: float | None = None,
    distance: float | None = None,
    properties: list[str] | None = None,
    where: dict[str, Any] | None = None,
    include_vector: bool = False,
) -> QueryOutput:
    """Similarity search on a Weaviate class via GraphQL Get.

    Provide `query_vector` (nearVector — works on every class), or
    `query_text` (nearText — ONLY on classes configured with a
    vectorizer module that embeds the text server-side). Results are
    Weaviate's native objects with `_additional {id certainty distance}`.
    """
    err = _missing_credentials(auth_data) or _bad_identifier("class name", class_name)
    if err:
        return QueryOutput(success=False, error=err)
    if (query_vector is None) == (query_text is None):
        return QueryOutput(
            success=False,
            error="Provide exactly one of query_vector or query_text.",
        )
    for prop in properties or []:
        prop_err = _bad_identifier("property name", prop)
        if prop_err:
            return QueryOutput(success=False, error=prop_err)

    near: dict[str, Any] = {}
    if certainty is not None:
        near["certainty"] = certainty
    if distance is not None:
        near["distance"] = distance
    if query_vector is not None:
        near["vector"] = query_vector
        search_arg = f"nearVector: {_gql_literal(near)}"
    else:
        near["concepts"] = [query_text]
        search_arg = f"nearText: {_gql_literal(near)}"

    args = [search_arg, f"limit: {limit}"]
    if where:
        try:
            args.append(f"where: {_gql_literal(where)}")
        except ValueError as exc:
            return QueryOutput(success=False, error=str(exc))

    additional = "id certainty distance" + (" vector" if include_vector else "")
    props = " ".join(properties or [])
    gql = (
        f"{{ Get {{ {class_name}({', '.join(args)}) "
        f"{{ {props} _additional {{ {additional} }} }} }} }}"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/v1/graphql",
                headers=_headers(auth_data),
                json={"query": gql},
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
    gql_err = _graphql_errors(data)
    if gql_err:
        return QueryOutput(success=False, error=gql_err)
    objects = data.get("data", {}).get("Get", {}).get(class_name) or []
    return QueryOutput(success=True, objects=objects)


@tool(args_schema=ListClassesInput)
@serialize_pydantic_return
async def list_classes(
    auth_type: str, auth_data: dict[str, Any]
) -> ListClassesOutput:
    """List all classes (collections) in the Weaviate schema."""
    err = _missing_credentials(auth_data)
    if err:
        return ListClassesOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/v1/schema",
                headers=_headers(auth_data),
            )
        if not response.is_success:
            return ListClassesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListClassesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListClassesOutput(success=False, error=str(exc))
    return ListClassesOutput(success=True, classes=data.get("classes", []))


@tool(args_schema=GetClassStatsInput)
@serialize_pydantic_return
async def get_class_stats(
    auth_type: str, auth_data: dict[str, Any], class_name: str
) -> GetClassStatsOutput:
    """Get the object count of a class via GraphQL Aggregate."""
    err = _missing_credentials(auth_data) or _bad_identifier("class name", class_name)
    if err:
        return GetClassStatsOutput(success=False, error=err)
    gql = f"{{ Aggregate {{ {class_name} {{ meta {{ count }} }} }} }}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/v1/graphql",
                headers=_headers(auth_data),
                json={"query": gql},
            )
        if not response.is_success:
            return GetClassStatsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetClassStatsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetClassStatsOutput(success=False, error=str(exc))
    gql_err = _graphql_errors(data)
    if gql_err:
        return GetClassStatsOutput(success=False, error=gql_err)
    aggregates = data.get("data", {}).get("Aggregate", {}).get(class_name) or []
    count = aggregates[0].get("meta", {}).get("count") if aggregates else None
    return GetClassStatsOutput(success=True, class_name=class_name, count=count)


@tool(args_schema=InsertObjectInput)
@serialize_pydantic_return
async def insert_object(
    auth_type: str,
    auth_data: dict[str, Any],
    class_name: str,
    properties: dict[str, Any],
    object_id: str | None = None,
    vector: list[float] | None = None,
) -> InsertObjectOutput:
    """Insert one object into a class (POST /v1/objects).

    Omit `vector` when the class has a vectorizer module — Weaviate
    embeds the properties server-side.
    """
    err = _missing_credentials(auth_data)
    if err:
        return InsertObjectOutput(success=False, error=err)
    body: dict[str, Any] = {"class": class_name, "properties": properties}
    if object_id:
        body["id"] = object_id
    if vector is not None:
        body["vector"] = vector
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/v1/objects",
                headers=_headers(auth_data),
                json=body,
            )
        if not response.is_success:
            return InsertObjectOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InsertObjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertObjectOutput(success=False, error=str(exc))
    return InsertObjectOutput(success=True, data=data)


@tool(args_schema=DeleteObjectInput)
@serialize_pydantic_return
async def delete_object(
    auth_type: str, auth_data: dict[str, Any], class_name: str, object_id: str
) -> DeleteObjectOutput:
    """Delete one object by UUID (DELETE /v1/objects/{class}/{id})."""
    err = _missing_credentials(auth_data)
    if err:
        return DeleteObjectOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_base_url(auth_data)}/v1/objects/{class_name}/{object_id}",
                headers=_headers(auth_data),
            )
        if not response.is_success:
            return DeleteObjectOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteObjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteObjectOutput(success=False, error=str(exc))
    return DeleteObjectOutput(success=True)


@tool(args_schema=CreateClassInput)
@serialize_pydantic_return
async def create_class(
    auth_type: str,
    auth_data: dict[str, Any],
    class_name: str,
    description: str | None = None,
    vectorizer: str | None = None,
    properties: list[dict[str, Any]] | None = None,
) -> CreateClassOutput:
    """Create a class (collection) in the Weaviate schema."""
    err = _missing_credentials(auth_data)
    if err:
        return CreateClassOutput(success=False, error=err)
    body: dict[str, Any] = {"class": class_name}
    if description:
        body["description"] = description
    if vectorizer:
        body["vectorizer"] = vectorizer
    if properties is not None:
        body["properties"] = properties
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/v1/schema",
                headers=_headers(auth_data),
                json=body,
            )
        if not response.is_success:
            return CreateClassOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateClassOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateClassOutput(success=False, error=str(exc))
    return CreateClassOutput(success=True, data=data)


@tool(args_schema=DeleteClassInput)
@serialize_pydantic_return
async def delete_class(
    auth_type: str, auth_data: dict[str, Any], class_name: str
) -> DeleteClassOutput:
    """Delete a class and all its objects (DELETE /v1/schema/{class})."""
    err = _missing_credentials(auth_data)
    if err:
        return DeleteClassOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_base_url(auth_data)}/v1/schema/{class_name}",
                headers=_headers(auth_data),
            )
        if not response.is_success:
            return DeleteClassOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteClassOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteClassOutput(success=False, error=str(exc))
    return DeleteClassOutput(success=True)
