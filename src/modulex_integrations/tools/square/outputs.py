"""Pydantic response models for the square integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateCustomerOutput",
    "CreateInvoiceOutput",
    "CreateOrderOutput",
    "CustomerResource",
    "InvoiceResource",
    "ListEventTypesOptionsOutput",
    "ListLocationOptionsOutput",
    "LocationOption",
    "OrderResource",
    "SendInvoiceOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CustomerResource(_Base):
    id: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    company_name: str | None = None
    email_address: str | None = None
    phone_number: str | None = None
    reference_id: str | None = None
    note: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class InvoiceResource(_Base):
    id: str | None = None
    version: int | None = None
    location_id: str | None = None
    order_id: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class OrderResource(_Base):
    id: str | None = None
    location_id: str | None = None
    reference_id: str | None = None
    state: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class LocationOption(_Base):
    id: str | None = None
    name: str | None = None
    status: str | None = None


class CreateCustomerOutput(_Base):
    success: bool
    error: str | None = None
    customer: CustomerResource | None = None


class CreateInvoiceOutput(_Base):
    success: bool
    error: str | None = None
    invoice: InvoiceResource | None = None


class CreateOrderOutput(_Base):
    success: bool
    error: str | None = None
    order: OrderResource | None = None


class ListEventTypesOptionsOutput(_Base):
    success: bool
    error: str | None = None
    event_types: list[str] = Field(default_factory=list)


class ListLocationOptionsOutput(_Base):
    success: bool
    error: str | None = None
    locations: list[LocationOption] = Field(default_factory=list)


class SendInvoiceOutput(_Base):
    success: bool
    error: str | None = None
    invoice: InvoiceResource | None = None
