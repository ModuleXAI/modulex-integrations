"""Pydantic response models for the google_cloud integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BigqueryInsertRowsOutput",
    "BucketMetadata",
    "CreateBucketOutput",
    "CreateScheduledQueryOutput",
    "GetBucketOutput",
    "GetObjectOutput",
    "ListBucketsOutput",
    "LoggingWriteLogOutput",
    "ObjectMetadata",
    "RunQueryOutput",
    "SearchObjectsOutput",
    "SwitchInstanceBootStatusOutput",
    "TransferConfig",
    "UploadObjectOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ---------------------------------------------------


class BucketMetadata(_Base):
    """Metadata for a Google Cloud Storage bucket."""

    id: str | None = None
    name: str | None = None
    location: str | None = None
    storage_class: str | None = None
    time_created: str | None = None
    updated: str | None = None
    project_number: str | None = None


class ObjectMetadata(_Base):
    """Metadata for a Google Cloud Storage object."""

    name: str | None = None
    bucket: str | None = None
    size: str | None = None
    content_type: str | None = None
    time_created: str | None = None
    updated: str | None = None
    md5_hash: str | None = None


class TransferConfig(_Base):
    """A BigQuery Data Transfer scheduled query config."""

    name: str | None = None
    display_name: str | None = None
    data_source_id: str | None = None
    schedule: str | None = None
    state: str | None = None
    destination_dataset_id: str | None = None


# --- Per-action output models -------------------------------------------------


class CreateBucketOutput(_Base):
    success: bool
    error: str | None = None
    bucket: BucketMetadata | None = None


class GetBucketOutput(_Base):
    success: bool
    error: str | None = None
    bucket: BucketMetadata | None = None


class ListBucketsOutput(_Base):
    success: bool
    error: str | None = None
    buckets: list[BucketMetadata] = Field(default_factory=list)


class SearchObjectsOutput(_Base):
    success: bool
    error: str | None = None
    objects: list[ObjectMetadata] = Field(default_factory=list)


class GetObjectOutput(_Base):
    success: bool
    error: str | None = None
    metadata: ObjectMetadata | None = None


class UploadObjectOutput(_Base):
    success: bool
    error: str | None = None
    object_name: str | None = None
    bucket: str | None = None


class LoggingWriteLogOutput(_Base):
    success: bool
    error: str | None = None


class RunQueryOutput(_Base):
    success: bool
    error: str | None = None
    rows: list[dict[str, str | int | float | bool | None]] = Field(default_factory=list)
    total_rows: int | None = None


class BigqueryInsertRowsOutput(_Base):
    success: bool
    error: str | None = None
    inserted_count: int | None = None


class CreateScheduledQueryOutput(_Base):
    success: bool
    error: str | None = None
    transfer_config: TransferConfig | None = None


class SwitchInstanceBootStatusOutput(_Base):
    success: bool
    error: str | None = None
    operation_name: str | None = None
    status: str | None = None
