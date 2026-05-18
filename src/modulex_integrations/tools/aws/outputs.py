"""Pydantic response models for the aws integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CloudwatchLogsPutLogEventOutput",
    "DynamodbCreateTableOutput",
    "DynamodbExecuteStatementOutput",
    "DynamodbGetItemOutput",
    "DynamodbPutItemOutput",
    "DynamodbQueryOutput",
    "DynamodbScanOutput",
    "DynamodbUpdateItemOutput",
    "DynamodbUpdateTableOutput",
    "EventbridgeSendEventOutput",
    "LambdaCreateFunctionOutput",
    "LambdaInvokeFunctionOutput",
    "ListRegionOptionsOutput",
    "RedshiftCreateRowsOutput",
    "RedshiftDeleteRowsOutput",
    "RedshiftQueryDatabaseOutput",
    "RedshiftUpdateRowsOutput",
    "RegionInfo",
    "S3GeneratePresignedUrlOutput",
    "S3UploadBase64AsFileOutput",
    "SnsSendMessageOutput",
    "SqsSendMessageOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models --------------------------------------------------


class RegionInfo(_Base):
    region_name: str | None = None
    endpoint: str | None = None
    opt_in_status: str | None = None


# --- Per-action output models ------------------------------------------------


class CloudwatchLogsPutLogEventOutput(_Base):
    success: bool
    error: str | None = None
    next_sequence_token: str | None = None
    rejected_log_events_info: dict[str, Any] | None = None


class DynamodbCreateTableOutput(_Base):
    success: bool
    error: str | None = None
    table_description: dict[str, Any] | None = None


class DynamodbExecuteStatementOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class DynamodbGetItemOutput(_Base):
    success: bool
    error: str | None = None
    item: dict[str, Any] | None = None


class DynamodbPutItemOutput(_Base):
    success: bool
    error: str | None = None
    attributes: dict[str, Any] | None = None


class DynamodbQueryOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int | None = None
    scanned_count: int | None = None


class DynamodbScanOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int | None = None
    scanned_count: int | None = None


class DynamodbUpdateItemOutput(_Base):
    success: bool
    error: str | None = None
    attributes: dict[str, Any] | None = None


class DynamodbUpdateTableOutput(_Base):
    success: bool
    error: str | None = None
    table_description: dict[str, Any] | None = None


class EventbridgeSendEventOutput(_Base):
    success: bool
    error: str | None = None
    failed_entry_count: int | None = None
    entries: list[dict[str, Any]] = Field(default_factory=list)


class LambdaCreateFunctionOutput(_Base):
    success: bool
    error: str | None = None
    function_name: str | None = None
    function_arn: str | None = None
    runtime: str | None = None
    role: str | None = None
    handler: str | None = None
    code_size: int | None = None
    last_modified: str | None = None
    state: str | None = None


class LambdaInvokeFunctionOutput(_Base):
    success: bool
    error: str | None = None
    status_code: int | None = None
    payload: Any = None
    function_error: str | None = None
    executed_version: str | None = None


class ListRegionOptionsOutput(_Base):
    success: bool
    error: str | None = None
    regions: list[RegionInfo] = Field(default_factory=list)


class RedshiftCreateRowsOutput(_Base):
    success: bool
    error: str | None = None
    statement_id: str | None = None


class RedshiftDeleteRowsOutput(_Base):
    success: bool
    error: str | None = None
    statement_id: str | None = None


class RedshiftQueryDatabaseOutput(_Base):
    success: bool
    error: str | None = None
    records: list[list[dict[str, Any]]] = Field(default_factory=list)
    total_num_rows: int | None = None
    column_metadata: list[dict[str, Any]] = Field(default_factory=list)


class RedshiftUpdateRowsOutput(_Base):
    success: bool
    error: str | None = None
    statement_id: str | None = None


class S3GeneratePresignedUrlOutput(_Base):
    success: bool
    error: str | None = None
    url: str | None = None


class S3UploadBase64AsFileOutput(_Base):
    success: bool
    error: str | None = None
    bucket: str | None = None
    key: str | None = None


class SnsSendMessageOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None


class SqsSendMessageOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None
    md5_of_message_body: str | None = None
    sequence_number: str | None = None
