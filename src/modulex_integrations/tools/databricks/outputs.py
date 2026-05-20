"""Pydantic response models for the databricks integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CancelAllRunsOutput",
    "CancelRunOutput",
    "CreateEndpointOutput",
    "CreateJobOutput",
    "CreateSqlWarehouseOutput",
    "CreateVectorSearchIndexOutput",
    "DeleteEndpointOutput",
    "DeleteJobOutput",
    "DeleteRunOutput",
    "DeleteSqlWarehouseOutput",
    "DeleteVectorSearchIndexDataOutput",
    "DeleteVectorSearchIndexOutput",
    "EditSqlWarehouseOutput",
    "ExportRunOutput",
    "GetEndpointOutput",
    "GetJobOutput",
    "GetJobPermissionsOutput",
    "GetRunOutput",
    "GetRunOutputOutput",
    "GetSqlWarehouseConfigOutput",
    "GetSqlWarehouseOutput",
    "GetSqlWarehousePermissionsOutput",
    "GetVectorSearchIndexOutput",
    "ListEndpointsOutput",
    "ListJobsOutput",
    "ListRunsOutput",
    "ListSqlWarehousesOutput",
    "ListVectorSearchIndexesOutput",
    "QueryVectorSearchIndexOutput",
    "RepairRunOutput",
    "ResetJobOutput",
    "RunJobNowOutput",
    "ScanVectorSearchIndexOutput",
    "SetJobPermissionsOutput",
    "SetSqlWarehouseConfigOutput",
    "SetSqlWarehousePermissionsOutput",
    "StartSqlWarehouseOutput",
    "StopSqlWarehouseOutput",
    "SyncVectorSearchIndexOutput",
    "UpdateJobOutput",
    "UpsertVectorSearchIndexDataOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CancelAllRunsOutput(_Base):
    success: bool
    error: str | None = None


class CancelRunOutput(_Base):
    success: bool
    error: str | None = None


class CreateEndpointOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateJobOutput(_Base):
    success: bool
    error: str | None = None
    job_id: str | None = None


class CreateSqlWarehouseOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateVectorSearchIndexOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class DeleteEndpointOutput(_Base):
    success: bool
    error: str | None = None


class DeleteJobOutput(_Base):
    success: bool
    error: str | None = None


class DeleteRunOutput(_Base):
    success: bool
    error: str | None = None


class DeleteSqlWarehouseOutput(_Base):
    success: bool
    error: str | None = None


class DeleteVectorSearchIndexOutput(_Base):
    success: bool
    error: str | None = None


class DeleteVectorSearchIndexDataOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class EditSqlWarehouseOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ExportRunOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetEndpointOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetJobOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetJobPermissionsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetRunOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetRunOutputOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetSqlWarehouseOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetSqlWarehouseConfigOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetSqlWarehousePermissionsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetVectorSearchIndexOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ListEndpointsOutput(_Base):
    success: bool
    error: str | None = None
    endpoints: list[dict[str, Any]] = Field(default_factory=list)


class ListJobsOutput(_Base):
    success: bool
    error: str | None = None
    jobs: list[dict[str, Any]] = Field(default_factory=list)


class ListRunsOutput(_Base):
    success: bool
    error: str | None = None
    runs: list[dict[str, Any]] = Field(default_factory=list)


class ListSqlWarehousesOutput(_Base):
    success: bool
    error: str | None = None
    warehouses: list[dict[str, Any]] = Field(default_factory=list)


class ListVectorSearchIndexesOutput(_Base):
    success: bool
    error: str | None = None
    indexes: list[dict[str, Any]] = Field(default_factory=list)


class QueryVectorSearchIndexOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class RepairRunOutput(_Base):
    success: bool
    error: str | None = None
    repair_id: str | None = None


class ResetJobOutput(_Base):
    success: bool
    error: str | None = None


class RunJobNowOutput(_Base):
    success: bool
    error: str | None = None
    run_id: str | None = None
    number_in_job: int | None = None


class ScanVectorSearchIndexOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class SetJobPermissionsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class SetSqlWarehouseConfigOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class SetSqlWarehousePermissionsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class StartSqlWarehouseOutput(_Base):
    success: bool
    error: str | None = None


class StopSqlWarehouseOutput(_Base):
    success: bool
    error: str | None = None


class SyncVectorSearchIndexOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateJobOutput(_Base):
    success: bool
    error: str | None = None


class UpsertVectorSearchIndexDataOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None
