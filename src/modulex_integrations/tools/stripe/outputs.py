"""Pydantic response models for the Stripe integration's @tool functions.

Stripe's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it from the resolved ``api_key`` credential.

Error model: non-2xx responses, timeouts, and unexpected exceptions are
caught and surfaced as ``success=False`` + ``error`` rather than raising.
Every output model carries both shapes.

The full Stripe resource objects are large and permissive, so each single
resource is kept as a free-form ``dict[str, Any]`` and only the small
summary ``metadata`` block is modeled with typed fields (every field
optional, GitHub-style permissive).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ChargeListOutput",
    "ChargeMetadata",
    "ChargeOutput",
    "CustomerDeleteOutput",
    "CustomerListOutput",
    "CustomerMetadata",
    "CustomerOutput",
    "EventListOutput",
    "EventMetadata",
    "EventOutput",
    "InvoiceDeleteOutput",
    "InvoiceListOutput",
    "InvoiceMetadata",
    "InvoiceOutput",
    "ListMetadata",
    "PaymentIntentListOutput",
    "PaymentIntentMetadata",
    "PaymentIntentOutput",
    "PriceListOutput",
    "PriceMetadata",
    "PriceOutput",
    "ProductDeleteOutput",
    "ProductListOutput",
    "ProductMetadata",
    "ProductOutput",
    "SubscriptionListOutput",
    "SubscriptionMetadata",
    "SubscriptionOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Summary metadata models -----------------------------------------------


class ListMetadata(_Base):
    """Pagination summary for list/search responses."""

    count: int | None = None
    has_more: bool | None = None


class PaymentIntentMetadata(_Base):
    id: str | None = None
    status: str | None = None
    amount: int | None = None
    currency: str | None = None


class CustomerMetadata(_Base):
    id: str | None = None
    email: str | None = None
    name: str | None = None


class SubscriptionMetadata(_Base):
    id: str | None = None
    status: str | None = None
    customer: str | None = None


class InvoiceMetadata(_Base):
    id: str | None = None
    status: str | None = None
    amount_due: int | None = None
    currency: str | None = None


class ChargeMetadata(_Base):
    id: str | None = None
    status: str | None = None
    amount: int | None = None
    currency: str | None = None
    paid: bool | None = None


class ProductMetadata(_Base):
    id: str | None = None
    name: str | None = None
    active: bool | None = None


class PriceMetadata(_Base):
    id: str | None = None
    product: str | None = None
    unit_amount: int | None = None
    currency: str | None = None


class EventMetadata(_Base):
    id: str | None = None
    type: str | None = None
    created: int | None = None


# --- Payment Intent --------------------------------------------------------


class PaymentIntentOutput(_Base):
    success: bool
    error: str | None = None
    payment_intent: dict[str, Any] | None = None
    metadata: PaymentIntentMetadata | None = None


class PaymentIntentListOutput(_Base):
    success: bool
    error: str | None = None
    payment_intents: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ListMetadata | None = None


# --- Customer --------------------------------------------------------------


class CustomerOutput(_Base):
    success: bool
    error: str | None = None
    customer: dict[str, Any] | None = None
    metadata: CustomerMetadata | None = None


class CustomerListOutput(_Base):
    success: bool
    error: str | None = None
    customers: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ListMetadata | None = None


class CustomerDeleteOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None
    id: str | None = None


# --- Subscription ----------------------------------------------------------


class SubscriptionOutput(_Base):
    success: bool
    error: str | None = None
    subscription: dict[str, Any] | None = None
    metadata: SubscriptionMetadata | None = None


class SubscriptionListOutput(_Base):
    success: bool
    error: str | None = None
    subscriptions: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ListMetadata | None = None


# --- Invoice ---------------------------------------------------------------


class InvoiceOutput(_Base):
    success: bool
    error: str | None = None
    invoice: dict[str, Any] | None = None
    metadata: InvoiceMetadata | None = None


class InvoiceListOutput(_Base):
    success: bool
    error: str | None = None
    invoices: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ListMetadata | None = None


class InvoiceDeleteOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None
    id: str | None = None


# --- Charge ----------------------------------------------------------------


class ChargeOutput(_Base):
    success: bool
    error: str | None = None
    charge: dict[str, Any] | None = None
    metadata: ChargeMetadata | None = None


class ChargeListOutput(_Base):
    success: bool
    error: str | None = None
    charges: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ListMetadata | None = None


# --- Product ---------------------------------------------------------------


class ProductOutput(_Base):
    success: bool
    error: str | None = None
    product: dict[str, Any] | None = None
    metadata: ProductMetadata | None = None


class ProductListOutput(_Base):
    success: bool
    error: str | None = None
    products: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ListMetadata | None = None


class ProductDeleteOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None
    id: str | None = None


# --- Price -----------------------------------------------------------------


class PriceOutput(_Base):
    success: bool
    error: str | None = None
    price: dict[str, Any] | None = None
    metadata: PriceMetadata | None = None


class PriceListOutput(_Base):
    success: bool
    error: str | None = None
    prices: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ListMetadata | None = None


# --- Event -----------------------------------------------------------------


class EventOutput(_Base):
    success: bool
    error: str | None = None
    event: dict[str, Any] | None = None
    metadata: EventMetadata | None = None


class EventListOutput(_Base):
    success: bool
    error: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ListMetadata | None = None
