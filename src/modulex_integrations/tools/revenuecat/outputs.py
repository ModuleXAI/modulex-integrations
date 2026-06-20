"""Pydantic response models for the RevenueCat integration's @tool functions.

RevenueCat's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it from the resolved credential.

Error model: every output model carries ``success: bool`` plus
``error: str | None``. Non-2xx HTTP responses, timeouts, and unexpected
exceptions are caught and surfaced as ``success=False`` + ``error``
rather than raising.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreatePurchaseOutput",
    "DeferGoogleSubscriptionOutput",
    "DeleteCustomerOutput",
    "GetCustomerOutput",
    "GrantEntitlementOutput",
    "ListOfferingsOutput",
    "Offering",
    "OfferingPackage",
    "OfferingsMetadata",
    "RefundGoogleSubscriptionOutput",
    "RevokeEntitlementOutput",
    "RevokeGoogleSubscriptionOutput",
    "Subscriber",
    "SubscriberMetadata",
    "UpdateSubscriberAttributesOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class Subscriber(_Base):
    """A RevenueCat subscriber object.

    ``subscriptions`` and ``entitlements`` are maps keyed by product /
    entitlement identifier; their values are left as opaque dicts so the
    upstream shape is preserved verbatim.
    """

    first_seen: str | None = None
    last_seen: str | None = None
    original_app_user_id: str | None = None
    original_application_version: str | None = None
    original_purchase_date: str | None = None
    management_url: str | None = None
    subscriptions: dict[str, Any] = Field(default_factory=dict)
    entitlements: dict[str, Any] = Field(default_factory=dict)
    non_subscriptions: dict[str, Any] = Field(default_factory=dict)
    other_purchases: dict[str, Any] = Field(default_factory=dict)
    subscriber_attributes: dict[str, Any] | None = None


class SubscriberMetadata(_Base):
    """Summary metadata derived from a subscriber payload."""

    app_user_id: str | None = None
    first_seen: str | None = None
    active_entitlements: int | None = None
    active_subscriptions: int | None = None


class OfferingPackage(_Base):
    """A single package inside an offering."""

    identifier: str | None = None
    platform_product_identifier: str | None = None


class Offering(_Base):
    """A single offering configured for the project."""

    identifier: str | None = None
    description: str | None = None
    packages: list[OfferingPackage] = Field(default_factory=list)


class OfferingsMetadata(_Base):
    """Summary metadata for a list-offerings response."""

    count: int | None = None
    current_offering_id: str | None = None


# --- Per-action output models ----------------------------------------------


class GetCustomerOutput(_Base):
    success: bool
    error: str | None = None
    subscriber: Subscriber | None = None
    metadata: SubscriberMetadata | None = None


class DeleteCustomerOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None
    app_user_id: str | None = None


class CreatePurchaseOutput(_Base):
    success: bool
    error: str | None = None
    customer: dict[str, Any] | None = None
    subscriber: Subscriber | None = None


class GrantEntitlementOutput(_Base):
    success: bool
    error: str | None = None
    subscriber: Subscriber | None = None


class RevokeEntitlementOutput(_Base):
    success: bool
    error: str | None = None
    subscriber: Subscriber | None = None


class ListOfferingsOutput(_Base):
    success: bool
    error: str | None = None
    current_offering_id: str | None = None
    offerings: list[Offering] = Field(default_factory=list)
    metadata: OfferingsMetadata | None = None


class UpdateSubscriberAttributesOutput(_Base):
    success: bool
    error: str | None = None
    updated: bool | None = None
    app_user_id: str | None = None


class DeferGoogleSubscriptionOutput(_Base):
    success: bool
    error: str | None = None
    subscriber: Subscriber | None = None


class RefundGoogleSubscriptionOutput(_Base):
    success: bool
    error: str | None = None
    subscriber: Subscriber | None = None


class RevokeGoogleSubscriptionOutput(_Base):
    success: bool
    error: str | None = None
    subscriber: Subscriber | None = None
