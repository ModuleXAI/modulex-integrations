"""Pydantic response models for the datadog integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetAccountInfoOutput",
    "GetMetricDataOutput",
    "PostMetricDataOutput",
    "SearchDashboardsOutput",
    "SearchEventsOutput",
    "SearchHostsOutput",
    "SearchIncidentsOutput",
    "SearchLogsOutput",
    "SearchMetricsOutput",
    "SearchMonitorsOutput",
    "SearchServicesOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class GetAccountInfoOutput(_Base):
    success: bool
    error: str | None = None
    region: str | None = None
    label: str | None = None
    api_url: str | None = None


class GetMetricDataOutput(_Base):
    success: bool
    error: str | None = None
    series: list[dict[str, Any]] = Field(default_factory=list)
    from_date: int | None = None
    to_date: int | None = None
    query: str | None = None


class PostMetricDataOutput(_Base):
    success: bool
    error: str | None = None
    errors: list[str] = Field(default_factory=list)


class SearchDashboardsOutput(_Base):
    success: bool
    error: str | None = None
    dashboards: list[dict[str, Any]] = Field(default_factory=list)


class SearchEventsOutput(_Base):
    success: bool
    error: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)


class SearchHostsOutput(_Base):
    success: bool
    error: str | None = None
    host_list: list[dict[str, Any]] = Field(default_factory=list)
    total_matching: int | None = None


class SearchIncidentsOutput(_Base):
    success: bool
    error: str | None = None
    incidents: list[dict[str, Any]] = Field(default_factory=list)


class SearchLogsOutput(_Base):
    success: bool
    error: str | None = None
    logs: list[dict[str, Any]] = Field(default_factory=list)


class SearchMetricsOutput(_Base):
    success: bool
    error: str | None = None
    metrics: list[str] = Field(default_factory=list)


class SearchMonitorsOutput(_Base):
    success: bool
    error: str | None = None
    monitors: list[dict[str, Any]] = Field(default_factory=list)


class SearchServicesOutput(_Base):
    success: bool
    error: str | None = None
    services: list[dict[str, Any]] = Field(default_factory=list)
