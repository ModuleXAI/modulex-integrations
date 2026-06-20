"""Pydantic response models for the Instantly integration.

Every action returns a ``*Output`` model carrying ``success: bool`` +
``error: str | None``, then the action-specific data fields. Fields are
permissive (``<type> | None = None``, lists default to empty) because the
upstream API is read with ``.get()`` everywhere — preserve whatever the
service returns rather than over-tightening.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ActivateCampaignOutput",
    "CampaignDetail",
    "CreateCampaignOutput",
    "CreateLeadListOutput",
    "CreateLeadOutput",
    "DeleteLeadsOutput",
    "EmailDetail",
    "GetLeadOutput",
    "LeadDetail",
    "LeadListDetail",
    "ListCampaignsOutput",
    "ListEmailsOutput",
    "ListLeadListsOutput",
    "ListLeadsOutput",
    "PatchCampaignOutput",
    "ReplyToEmailOutput",
    "UpdateLeadInterestStatusOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LeadDetail(_Base):
    id: str | None = None
    timestamp_created: str | None = None
    timestamp_updated: str | None = None
    organization: str | None = None
    campaign: str | None = None
    status: int | None = None
    email: str | None = None
    personalization: str | None = None
    website: str | None = None
    last_name: str | None = None
    first_name: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    phone: str | None = None
    email_open_count: int | None = None
    email_reply_count: int | None = None
    email_click_count: int | None = None
    company_domain: str | None = None
    payload: dict[str, Any] | None = None
    lt_interest_status: int | None = None


class CampaignDetail(_Base):
    id: str | None = None
    name: str | None = None
    pl_value: float | None = None
    status: int | None = None
    is_evergreen: bool | None = None
    timestamp_created: str | None = None
    timestamp_updated: str | None = None
    email_gap: int | None = None
    daily_limit: int | None = None
    daily_max_leads: int | None = None
    open_tracking: bool | None = None
    stop_on_reply: bool | None = None
    sequences: list[Any] = Field(default_factory=list)
    campaign_schedule: dict[str, Any] | None = None


class EmailBody(_Base):
    text: str | None = None
    html: str | None = None


class EmailDetail(_Base):
    id: str | None = None
    timestamp_created: str | None = None
    timestamp_email: str | None = None
    message_id: str | None = None
    subject: str | None = None
    from_address_email: str | None = None
    to_address_email_list: str | None = None
    cc_address_email_list: str | None = None
    bcc_address_email_list: str | None = None
    reply_to: str | None = None
    body: EmailBody | None = None
    organization_id: str | None = None
    campaign_id: str | None = None
    subsequence_id: str | None = None
    list_id: str | None = None
    lead: str | None = None
    lead_id: str | None = None
    eaccount: str | None = None
    ue_type: int | None = None
    is_unread: int | None = None
    is_auto_reply: int | None = None
    i_status: int | None = None
    thread_id: str | None = None
    content_preview: str | None = None


class LeadListDetail(_Base):
    id: str | None = None
    organization_id: str | None = None
    has_enrichment_task: bool | None = None
    owned_by: str | None = None
    name: str | None = None
    timestamp_created: str | None = None


class ListLeadsOutput(_Base):
    success: bool
    error: str | None = None
    leads: list[LeadDetail] = Field(default_factory=list)
    count: int | None = None
    next_starting_after: str | None = None


class GetLeadOutput(_Base):
    success: bool
    error: str | None = None
    lead: LeadDetail | None = None
    id: str | None = None
    email_address: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    campaign: str | None = None
    status: int | None = None


class CreateLeadOutput(_Base):
    success: bool
    error: str | None = None
    lead: LeadDetail | None = None
    id: str | None = None
    email_address: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    campaign: str | None = None
    status: int | None = None


class DeleteLeadsOutput(_Base):
    success: bool
    error: str | None = None
    count: int | None = None


class UpdateLeadInterestStatusOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None


class ListCampaignsOutput(_Base):
    success: bool
    error: str | None = None
    campaigns: list[CampaignDetail] = Field(default_factory=list)
    count: int | None = None
    next_starting_after: str | None = None


class CreateCampaignOutput(_Base):
    success: bool
    error: str | None = None
    campaign: CampaignDetail | None = None
    id: str | None = None
    name: str | None = None
    status: int | None = None


class PatchCampaignOutput(_Base):
    success: bool
    error: str | None = None
    campaign: CampaignDetail | None = None
    id: str | None = None
    name: str | None = None
    status: int | None = None


class ActivateCampaignOutput(_Base):
    success: bool
    error: str | None = None
    campaign: CampaignDetail | None = None
    id: str | None = None
    name: str | None = None
    status: int | None = None


class ListEmailsOutput(_Base):
    success: bool
    error: str | None = None
    emails: list[EmailDetail] = Field(default_factory=list)
    count: int | None = None
    next_starting_after: str | None = None


class ReplyToEmailOutput(_Base):
    success: bool
    error: str | None = None
    email: EmailDetail | None = None
    id: str | None = None
    subject: str | None = None
    thread_id: str | None = None


class ListLeadListsOutput(_Base):
    success: bool
    error: str | None = None
    lead_lists: list[LeadListDetail] = Field(default_factory=list)
    count: int | None = None
    next_starting_after: str | None = None


class CreateLeadListOutput(_Base):
    success: bool
    error: str | None = None
    lead_list: LeadListDetail | None = None
    id: str | None = None
    name: str | None = None
