"""Pydantic response models for the pinecone integration's @tool functions.

Pass-through by design: fields mirror Pinecone's native response shapes
(control-plane index models, data-plane matches/hits) without any
ModuleX-side normalization.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "CreateIndexOutput",
    "DeleteIndexOutput",
    "DeleteVectorsOutput",
    "DescribeIndexOutput",
    "DescribeIndexStatsOutput",
    "ListIndexesOutput",
    "QueryOutput",
    "SearchRecordsOutput",
    "UpsertVectorsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class QueryOutput(_Base):
    success: bool
    error: str | None = None
    # Native /query response — matches carry {id, score, values?, metadata?}.
    matches: list[dict[str, Any]] | None = None
    namespace: str | None = None
    usage: dict[str, Any] | None = None


class SearchRecordsOutput(_Base):
    success: bool
    error: str | None = None
    # ``result.hits`` from the records search API — {_id, _score, fields}.
    hits: list[dict[str, Any]] | None = None
    usage: dict[str, Any] | None = None


class ListIndexesOutput(_Base):
    success: bool
    error: str | None = None
    indexes: list[dict[str, Any]] | None = None


class DescribeIndexOutput(_Base):
    success: bool
    error: str | None = None
    # Native index model (name, dimension, metric, host, spec, status, ...).
    data: dict[str, Any] | None = None


class DescribeIndexStatsOutput(_Base):
    success: bool
    error: str | None = None
    # Native stats (namespaces, dimension, indexFullness, totalVectorCount).
    data: dict[str, Any] | None = None


class UpsertVectorsOutput(_Base):
    success: bool
    error: str | None = None
    # Native response — {"upsertedCount": N}.
    data: dict[str, Any] | None = None


class DeleteVectorsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateIndexOutput(_Base):
    success: bool
    error: str | None = None
    # Native index model of the created index.
    data: dict[str, Any] | None = None


class DeleteIndexOutput(_Base):
    success: bool
    error: str | None = None
