"""Pydantic response models for the microsoft_power_bi integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddRowsToPushDatasetOutput",
    "ExecuteDaxQueryOutput",
    "ExportReportOutput",
    "GetRefreshHistoryOutput",
    "GetReportsByIdOutput",
    "ListDashboardsOutput",
    "ListDatasetsOutput",
    "ListReportsOutput",
    "ListWorkspacesOutput",
    "RefreshDatasetOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ----------------------------------------------


class AddRowsToPushDatasetOutput(_Base):
    success: bool
    error: str | None = None
    rows_added: int | None = None


class ExecuteDaxQueryOutput(_Base):
    success: bool
    error: str | None = None
    results: list[dict] = Field(default_factory=list)  # type: ignore[type-arg]


class ExportReportOutput(_Base):
    success: bool
    error: str | None = None
    export_id: str | None = None
    status: str | None = None
    report_id: str | None = None
    format: str | None = None
    resource_file_extension: str | None = None
    resource_location: str | None = None
    file_size_bytes: int | None = None
    file_base64: str | None = None
    percent_complete: int | None = None


class GetRefreshHistoryOutput(_Base):
    success: bool
    error: str | None = None
    refreshes: list[dict] = Field(default_factory=list)  # type: ignore[type-arg]


class GetReportsByIdOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    web_url: str | None = None
    embed_url: str | None = None
    dataset_id: str | None = None
    report_type: str | None = None


class ListDashboardsOutput(_Base):
    success: bool
    error: str | None = None
    dashboards: list[dict] = Field(default_factory=list)  # type: ignore[type-arg]


class ListDatasetsOutput(_Base):
    success: bool
    error: str | None = None
    datasets: list[dict] = Field(default_factory=list)  # type: ignore[type-arg]


class ListReportsOutput(_Base):
    success: bool
    error: str | None = None
    reports: list[dict] = Field(default_factory=list)  # type: ignore[type-arg]


class ListWorkspacesOutput(_Base):
    success: bool
    error: str | None = None
    workspaces: list[dict] = Field(default_factory=list)  # type: ignore[type-arg]


class RefreshDatasetOutput(_Base):
    success: bool
    error: str | None = None
    status_code: int | None = None
    request_id: str | None = None
    dataset_id: str | None = None
    location: str | None = None
