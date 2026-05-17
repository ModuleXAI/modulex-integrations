"""Pydantic response models for the Lemon Squeezy integration.

Lemon Squeezy returns JSON:API responses ({"data": ..., "meta": {...}}).
The legacy implementation forwarded the entire upstream JSON body as
the action's ``result``; we preserve that by surfacing ``data`` (object
or list) and ``meta`` (paginated list responses only) unchanged. Each
action gets its own subclass so the runtime can derive distinct
JSONSchemas, but they share fields.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "ListCustomersOutput",
    "ListOrdersOutput",
    "ListProductsOutput",
    "ListStoresOutput",
    "ListSubscriptionsOutput",
    "RetrieveCustomerOutput",
    "RetrieveOrderOutput",
    "RetrieveProductOutput",
    "RetrieveStoreOutput",
    "RetrieveSubscriptionOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None
    # Lists carry a JSON:API array under "data"; retrievals carry a
    # single object. We keep the broad type to mirror the upstream.
    data: Any = None
    # "meta" is present on list responses; absent on retrievals.
    meta: dict[str, Any] | None = None


class ListCustomersOutput(_Base):
    pass


class RetrieveCustomerOutput(_Base):
    pass


class ListOrdersOutput(_Base):
    pass


class RetrieveOrderOutput(_Base):
    pass


class ListProductsOutput(_Base):
    pass


class RetrieveProductOutput(_Base):
    pass


class ListSubscriptionsOutput(_Base):
    pass


class RetrieveSubscriptionOutput(_Base):
    pass


class ListStoresOutput(_Base):
    pass


class RetrieveStoreOutput(_Base):
    pass
