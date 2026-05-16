"""Pydantic response models for the Mailchimp integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddMemberToSegmentOutput",
    "AddNoteToSubscriberOutput",
    "AddOrUpdateSubscriberOutput",
    "CreateCampaignOutput",
    "CreateListOutput",
    "DeleteCampaignOutput",
    "DeleteListOutput",
    "DeleteSubscriberOutput",
    "GetCampaignOutput",
    "GetCampaignReportOutput",
    "GetCampaignsOutput",
    "GetListMembersOutput",
    "GetListOutput",
    "GetListsOutput",
    "GetMemberTagsOutput",
    "GetSegmentsOutput",
    "GetSubscriberOutput",
    "SendCampaignOutput",
    "UpdateMemberTagsOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class GetListsOutput(_Base):
    lists: list[dict[str, Any]] = Field(default_factory=list)
    total_items: int = 0


class GetListOutput(_Base):
    id: str | None = None
    name: str | None = None
    permission_reminder: str | None = None
    contact: dict[str, Any] | None = None
    campaign_defaults: dict[str, Any] | None = None
    stats: dict[str, Any] | None = None
    date_created: str | None = None


class CreateListOutput(_Base):
    id: str | None = None
    name: str | None = None
    date_created: str | None = None
    message: str | None = None


class DeleteListOutput(_Base):
    message: str | None = None
    list_id: str | None = None


class GetListMembersOutput(_Base):
    members: list[dict[str, Any]] = Field(default_factory=list)
    total_items: int = 0


class GetSubscriberOutput(_Base):
    id: str | None = None
    email_address: str | None = None
    status: str | None = None
    merge_fields: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    vip: bool = False
    language: str | None = None
    timestamp_signup: str | None = None
    last_changed: str | None = None


class AddOrUpdateSubscriberOutput(_Base):
    id: str | None = None
    email_address: str | None = None
    status: str | None = None
    merge_fields: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None


class DeleteSubscriberOutput(_Base):
    message: str | None = None
    email: str | None = None
    list_id: str | None = None


class GetCampaignsOutput(_Base):
    campaigns: list[dict[str, Any]] = Field(default_factory=list)
    total_items: int = 0


class GetCampaignOutput(_Base):
    result: dict[str, Any] | None = None


class CreateCampaignOutput(_Base):
    id: str | None = None
    type: str | None = None
    status: str | None = None
    message: str | None = None


class DeleteCampaignOutput(_Base):
    message: str | None = None
    campaign_id: str | None = None


class SendCampaignOutput(_Base):
    message: str | None = None
    campaign_id: str | None = None


class GetCampaignReportOutput(_Base):
    result: dict[str, Any] | None = None


class GetMemberTagsOutput(_Base):
    tags: list[dict[str, Any]] = Field(default_factory=list)
    total_items: int = 0


class UpdateMemberTagsOutput(_Base):
    message: str | None = None
    email: str | None = None


class AddNoteToSubscriberOutput(_Base):
    id: int | None = None
    note: str | None = None
    email: str | None = None
    created_at: str | None = None


class GetSegmentsOutput(_Base):
    segments: list[dict[str, Any]] = Field(default_factory=list)
    total_items: int = 0


class AddMemberToSegmentOutput(_Base):
    message: str | None = None
    email: str | None = None
    segment_id: str | None = None
