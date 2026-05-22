"""Pydantic response models for the google_ads integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AccessibleCustomer",
    "AddContactToListByEmailOutput",
    "CreateAdGroupReportOutput",
    "CreateAdReportOutput",
    "CreateCampaignReportOutput",
    "CreateCustomerListOutput",
    "CreateCustomerReportOutput",
    "CreateReportOutput",
    "GenerateKeywordIdeasOutput",
    "ListAccountIdOptionsOutput",
    "SendOfflineConversionOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class AccessibleCustomer(_Base):
    """One entry returned from ``customers:listAccessibleCustomers``."""

    resource_name: str | None = None
    customer_id: str | None = None


# --- Per-action output models ---------------------------------------------


class AddContactToListByEmailOutput(_Base):
    success: bool
    error: str | None = None
    offline_user_data_job_resource_name: str | None = None
    operation_resource_name: str | None = None


class CreateAdGroupReportOutput(_Base):
    success: bool
    error: str | None = None
    query: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    field_mask: str | None = None
    request_id: str | None = None


class CreateAdReportOutput(_Base):
    success: bool
    error: str | None = None
    query: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    field_mask: str | None = None
    request_id: str | None = None


class CreateCampaignReportOutput(_Base):
    success: bool
    error: str | None = None
    query: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    field_mask: str | None = None
    request_id: str | None = None


class CreateCustomerListOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    resource_name: str | None = None


class CreateCustomerReportOutput(_Base):
    success: bool
    error: str | None = None
    query: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    field_mask: str | None = None
    request_id: str | None = None


class CreateReportOutput(_Base):
    success: bool
    error: str | None = None
    query: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    field_mask: str | None = None
    request_id: str | None = None


class GenerateKeywordIdeasOutput(_Base):
    success: bool
    error: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    total_size: int | None = None
    next_page_token: str | None = None


class ListAccountIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    customers: list[AccessibleCustomer] = Field(default_factory=list)


class SendOfflineConversionOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    resource_name: str | None = None
