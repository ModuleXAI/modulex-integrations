"""Pydantic response models for the Customer.io integration."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "AddCustomersToSegmentOutput",
    "CreateOrUpdateCustomerOutput",
    "SendEventOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateOrUpdateCustomerOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    customer_id: str | None = None
    email: str | None = None


class SendEventOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    customer_id: str | None = None
    event_name: str | None = None


class AddCustomersToSegmentOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    segment_id: str | None = None
    customer_count: int | None = None
    id_type: str | None = None
