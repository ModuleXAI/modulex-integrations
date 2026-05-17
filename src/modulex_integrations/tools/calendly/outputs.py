"""Pydantic response models for the Calendly integration.

Calendly's REST API returns JSON shapes that vary per endpoint, but
all follow a JSON-API-ish ``{"resource": {...}}`` (single) or
``{"collection": [...], "pagination": {...}}`` (list) envelope.
Each output model keeps the raw upstream body on ``data`` and pulls
the most useful fields up for ergonomic attribute access.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateInviteeNoShowOutput",
    "CreateSchedulingLinkOutput",
    "GetCurrentUserOutput",
    "GetEventOutput",
    "ListEventInviteesOutput",
    "ListEventTypesOutput",
    "ListEventsOutput",
    "ListGroupsOutput",
    "ListOrganizationMembersOutput",
    "ListUserAvailabilitySchedulesOutput",
    "ListWebhookSubscriptionsOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class GetCurrentUserOutput(_Base):
    resource: dict[str, Any] | None = None


class _ListBase(_Base):
    # Collection responses always carry these; pagination next_page_token
    # is the easiest cursor surface for callers.
    count: int = 0
    next_page_token: str | None = None
    next_page: str | None = None


class ListEventsOutput(_ListBase):
    events: list[dict[str, Any]] = Field(default_factory=list)


class GetEventOutput(_Base):
    resource: dict[str, Any] | None = None


class ListEventInviteesOutput(_ListBase):
    invitees: list[dict[str, Any]] = Field(default_factory=list)


class ListEventTypesOutput(_ListBase):
    event_types: list[dict[str, Any]] = Field(default_factory=list)


class CreateSchedulingLinkOutput(_Base):
    booking_url: str | None = None
    owner: str | None = None
    owner_type: str | None = None


class CreateInviteeNoShowOutput(_Base):
    resource: dict[str, Any] | None = None


class ListUserAvailabilitySchedulesOutput(_Base):
    schedules: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class ListOrganizationMembersOutput(_ListBase):
    members: list[dict[str, Any]] = Field(default_factory=list)


class ListGroupsOutput(_ListBase):
    groups: list[dict[str, Any]] = Field(default_factory=list)


class ListWebhookSubscriptionsOutput(_ListBase):
    webhooks: list[dict[str, Any]] = Field(default_factory=list)
