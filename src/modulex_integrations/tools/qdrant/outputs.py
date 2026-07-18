"""Pydantic response models for the qdrant integration's @tool functions.

Pass-through by design: fields mirror the ``result`` payload of the
Qdrant REST API responses (points, collections, update results) without
any ModuleX-side normalization.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "CreateCollectionOutput",
    "DeleteCollectionOutput",
    "DeletePointsOutput",
    "GetCollectionInfoOutput",
    "ListCollectionsOutput",
    "QueryOutput",
    "UpsertPointsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class QueryOutput(_Base):
    success: bool
    error: str | None = None
    # ``result.points`` from POST /collections/{name}/points/query —
    # each point is Qdrant's native {id, version?, score, payload?, vector?}.
    points: list[dict[str, Any]] | None = None


class ListCollectionsOutput(_Base):
    success: bool
    error: str | None = None
    # ``result.collections`` from GET /collections — [{"name": ...}, ...].
    collections: list[dict[str, Any]] | None = None


class GetCollectionInfoOutput(_Base):
    success: bool
    error: str | None = None
    # Full native ``result`` object from GET /collections/{name}
    # (status, points_count, config, payload_schema, ...).
    data: dict[str, Any] | None = None


class UpsertPointsOutput(_Base):
    success: bool
    error: str | None = None
    # Native update result — {"operation_id": ..., "status": ...}.
    data: dict[str, Any] | None = None


class DeletePointsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateCollectionOutput(_Base):
    success: bool
    error: str | None = None
    # Qdrant returns a bare boolean in ``result`` for collection DDL.
    result: bool | None = None


class DeleteCollectionOutput(_Base):
    success: bool
    error: str | None = None
    result: bool | None = None
