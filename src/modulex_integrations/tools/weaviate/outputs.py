"""Pydantic response models for the weaviate integration's @tool functions.

Pass-through by design: fields mirror Weaviate's native GraphQL / REST
response shapes without any ModuleX-side normalization.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "CreateClassOutput",
    "DeleteClassOutput",
    "DeleteObjectOutput",
    "GetClassStatsOutput",
    "InsertObjectOutput",
    "ListClassesOutput",
    "QueryOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class QueryOutput(_Base):
    success: bool
    error: str | None = None
    # ``data.Get.<Class>`` from the GraphQL response — each object carries
    # the requested properties plus ``_additional {id certainty distance}``.
    objects: list[dict[str, Any]] | None = None


class ListClassesOutput(_Base):
    success: bool
    error: str | None = None
    # Native ``classes`` array from GET /v1/schema.
    classes: list[dict[str, Any]] | None = None


class GetClassStatsOutput(_Base):
    success: bool
    error: str | None = None
    class_name: str | None = None
    # ``data.Aggregate.<Class>[0].meta.count`` from the GraphQL response.
    count: int | None = None


class InsertObjectOutput(_Base):
    success: bool
    error: str | None = None
    # Native created-object body from POST /v1/objects.
    data: dict[str, Any] | None = None


class DeleteObjectOutput(_Base):
    success: bool
    error: str | None = None


class CreateClassOutput(_Base):
    success: bool
    error: str | None = None
    # Native created-class body from POST /v1/schema.
    data: dict[str, Any] | None = None


class DeleteClassOutput(_Base):
    success: bool
    error: str | None = None
