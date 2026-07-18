"""Pydantic response models for the mongodb_atlas integration's @tool functions.

Pass-through by design: documents are returned in MongoDB Relaxed
Extended JSON (BSON types like ObjectId become ``{"$oid": ...}``), with
no ModuleX-side normalization.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "DeleteDocumentsOutput",
    "InsertDocumentsOutput",
    "ListCollectionsOutput",
    "ListDatabasesOutput",
    "ListSearchIndexesOutput",
    "QueryOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class QueryOutput(_Base):
    success: bool
    error: str | None = None
    # Native documents from the $vectorSearch aggregation, each with a
    # ``score`` field added via {"$meta": "vectorSearchScore"}.
    documents: list[dict[str, Any]] | None = None


class ListDatabasesOutput(_Base):
    success: bool
    error: str | None = None
    # Native listDatabases entries — {name, sizeOnDisk, empty}.
    databases: list[dict[str, Any]] | None = None


class ListCollectionsOutput(_Base):
    success: bool
    error: str | None = None
    # Native listCollections entries — {name, type, options, info}.
    collections: list[dict[str, Any]] | None = None


class ListSearchIndexesOutput(_Base):
    success: bool
    error: str | None = None
    # Native Atlas Search / Vector Search index definitions.
    indexes: list[dict[str, Any]] | None = None


class InsertDocumentsOutput(_Base):
    success: bool
    error: str | None = None
    inserted_ids: list[str] | None = None
    inserted_count: int | None = None


class DeleteDocumentsOutput(_Base):
    success: bool
    error: str | None = None
    deleted_count: int | None = None
