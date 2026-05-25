"""Pydantic response models for the microsoft_dynamics_365_sales integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateAppointmentOutput",
    "CreateCustomEntityOutput",
    "FindContactOutput",
    "GetAccountOutput",
    "ListAccountsOutput",
    "ListAppointmentCategoriesOutput",
    "ListAppointmentCategoryOptionsOutput",
    "ListAppointmentsOutput",
    "ListSolutionIdOptionsOutput",
    "SearchAccountsOutput",
    "UpdateAppointmentOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ----------------------------------------------


class CreateAppointmentOutput(_Base):
    success: bool
    error: str | None = None
    appointment_id: str | None = None
    deep_link: str | None = None
    appointment: dict[str, Any] | None = None


class CreateCustomEntityOutput(_Base):
    success: bool
    error: str | None = None
    entity: dict[str, Any] | None = None


class FindContactOutput(_Base):
    success: bool
    error: str | None = None
    contacts: list[dict[str, Any]] = Field(default_factory=list)


class GetAccountOutput(_Base):
    success: bool
    error: str | None = None
    account: dict[str, Any] | None = None


class ListAccountsOutput(_Base):
    success: bool
    error: str | None = None
    accounts: list[dict[str, Any]] = Field(default_factory=list)


class ListAppointmentCategoriesOutput(_Base):
    success: bool
    error: str | None = None
    category_type: str | None = None
    categories: list[dict[str, Any]] = Field(default_factory=list)


class ListAppointmentCategoryOptionsOutput(_Base):
    success: bool
    error: str | None = None
    options: list[dict[str, Any]] = Field(default_factory=list)


class ListAppointmentsOutput(_Base):
    success: bool
    error: str | None = None
    appointments: list[dict[str, Any]] = Field(default_factory=list)


class ListSolutionIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    solutions: list[dict[str, Any]] = Field(default_factory=list)


class SearchAccountsOutput(_Base):
    success: bool
    error: str | None = None
    accounts: list[dict[str, Any]] = Field(default_factory=list)


class UpdateAppointmentOutput(_Base):
    success: bool
    error: str | None = None
    appointment_id: str | None = None
    updated_fields: list[str] = Field(default_factory=list)
