"""Pydantic response models for the google_analytics integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AccountSummary",
    "CreateGa4PropertyOutput",
    "CreateKeyEventOutput",
    "KeyEventResource",
    "ListAccountOptionsOutput",
    "ListPropertyOptionsOutput",
    "PropertyResource",
    "PropertySummary",
    "RunReportInGa4Output",
    "RunReportOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class AccountSummary(_Base):
    """A Google Analytics account (admin API)."""

    name: str | None = None
    display_name: str | None = None
    account: str | None = None


class PropertySummary(_Base):
    """A Google Analytics property summary (admin API)."""

    property: str | None = None
    display_name: str | None = None
    property_type: str | None = None
    parent: str | None = None


class PropertyResource(_Base):
    """A full GA4 property resource (admin API)."""

    name: str | None = None
    parent: str | None = None
    display_name: str | None = None
    industry_category: str | None = None
    time_zone: str | None = None
    currency_code: str | None = None
    property_type: str | None = None
    create_time: str | None = None
    update_time: str | None = None


class KeyEventResource(_Base):
    """A GA4 key event resource (admin API)."""

    name: str | None = None
    event_name: str | None = None
    counting_method: str | None = None
    create_time: str | None = None
    deletable: bool | None = None
    custom: bool | None = None


# --- Per-action output models ---------------------------------------------


class CreateGa4PropertyOutput(_Base):
    success: bool
    error: str | None = None
    property: PropertyResource | None = None
    raw: dict[str, Any] | None = None


class CreateKeyEventOutput(_Base):
    success: bool
    error: str | None = None
    key_event: KeyEventResource | None = None
    raw: dict[str, Any] | None = None


class ListAccountOptionsOutput(_Base):
    success: bool
    error: str | None = None
    accounts: list[AccountSummary] = Field(default_factory=list)
    next_page_token: str | None = None


class ListPropertyOptionsOutput(_Base):
    success: bool
    error: str | None = None
    properties: list[PropertySummary] = Field(default_factory=list)


class RunReportInGa4Output(_Base):
    success: bool
    error: str | None = None
    row_count: int | None = None
    dimension_headers: list[dict[str, Any]] = Field(default_factory=list)
    metric_headers: list[dict[str, Any]] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    totals: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] | None = None


class RunReportOutput(_Base):
    success: bool
    error: str | None = None
    reports: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] | None = None
