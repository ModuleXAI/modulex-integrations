"""LangChain ``@tool`` functions for the Instantly integration.

Thirteen async tools wrapping the Instantly V2 REST API
(``https://api.instantly.ai/api/v2``). The modulex ``ToolExecutor``
injects ``api_key: str`` directly (key-based convention); each tool
builds an ``Authorization: Bearer <api_key>`` header.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do not
raise.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.instantly.outputs import (
    ActivateCampaignOutput,
    CampaignDetail,
    CreateCampaignOutput,
    CreateLeadListOutput,
    CreateLeadOutput,
    DeleteLeadsOutput,
    EmailBody,
    EmailDetail,
    GetLeadOutput,
    LeadDetail,
    LeadListDetail,
    ListCampaignsOutput,
    ListEmailsOutput,
    ListLeadListsOutput,
    ListLeadsOutput,
    PatchCampaignOutput,
    ReplyToEmailOutput,
    UpdateLeadInterestStatusOutput,
)

__all__ = [
    "activate_campaign",
    "create_campaign",
    "create_lead",
    "create_lead_list",
    "delete_leads",
    "get_lead",
    "list_campaigns",
    "list_emails",
    "list_lead_lists",
    "list_leads",
    "patch_campaign",
    "reply_to_email",
    "update_lead_interest_status",
]

_BASE_URL = "https://api.instantly.ai/api/v2"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = (
    "Instantly API key is empty. Please configure a valid Instantly credential."
)


# --- Auth / request helpers ------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }


def _as_record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _items(value: Any) -> list[dict[str, Any]]:
    data = _as_record(value)
    items = data.get("items")
    return [_as_record(item) for item in items] if isinstance(items, list) else []


def _next_starting_after(value: Any) -> str | None:
    cursor = _as_record(value).get("next_starting_after")
    return cursor if isinstance(cursor, str) else None


def _str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _int(value: Any) -> int | None:
    return value if isinstance(value, bool) is False and isinstance(value, int) else None


def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _error_message(data: Any, fallback: str) -> str:
    record = _as_record(data)
    message = record.get("message")
    if isinstance(message, str):
        return message
    err = record.get("error")
    if isinstance(err, str):
        return err
    return fallback


# --- Domain object mappers -------------------------------------------------


def _map_lead(value: Any) -> LeadDetail:
    lead = _as_record(value)
    payload = lead.get("payload")
    return LeadDetail(
        id=_str(lead.get("id")),
        timestamp_created=_str(lead.get("timestamp_created")),
        timestamp_updated=_str(lead.get("timestamp_updated")),
        organization=_str(lead.get("organization")),
        campaign=_str(lead.get("campaign")),
        status=_int(lead.get("status")),
        email=_str(lead.get("email")),
        personalization=_str(lead.get("personalization")),
        website=_str(lead.get("website")),
        last_name=_str(lead.get("last_name")),
        first_name=_str(lead.get("first_name")),
        company_name=_str(lead.get("company_name")),
        job_title=_str(lead.get("job_title")),
        phone=_str(lead.get("phone")),
        email_open_count=_int(lead.get("email_open_count")),
        email_reply_count=_int(lead.get("email_reply_count")),
        email_click_count=_int(lead.get("email_click_count")),
        company_domain=_str(lead.get("company_domain")),
        payload=payload if isinstance(payload, dict) else None,
        lt_interest_status=_int(lead.get("lt_interest_status")),
    )


def _map_campaign(value: Any) -> CampaignDetail:
    campaign = _as_record(value)
    sequences = campaign.get("sequences")
    schedule = campaign.get("campaign_schedule")
    return CampaignDetail(
        id=_str(campaign.get("id")),
        name=_str(campaign.get("name")),
        pl_value=_num(campaign.get("pl_value")),
        status=_int(campaign.get("status")),
        is_evergreen=_bool(campaign.get("is_evergreen")),
        timestamp_created=_str(campaign.get("timestamp_created")),
        timestamp_updated=_str(campaign.get("timestamp_updated")),
        email_gap=_int(campaign.get("email_gap")),
        daily_limit=_int(campaign.get("daily_limit")),
        daily_max_leads=_int(campaign.get("daily_max_leads")),
        open_tracking=_bool(campaign.get("open_tracking")),
        stop_on_reply=_bool(campaign.get("stop_on_reply")),
        sequences=sequences if isinstance(sequences, list) else [],
        campaign_schedule=schedule if isinstance(schedule, dict) else None,
    )


def _map_email(value: Any) -> EmailDetail:
    email = _as_record(value)
    body = _as_record(email.get("body"))
    return EmailDetail(
        id=_str(email.get("id")),
        timestamp_created=_str(email.get("timestamp_created")),
        timestamp_email=_str(email.get("timestamp_email")),
        message_id=_str(email.get("message_id")),
        subject=_str(email.get("subject")),
        from_address_email=_str(email.get("from_address_email")),
        to_address_email_list=_str(email.get("to_address_email_list")),
        cc_address_email_list=_str(email.get("cc_address_email_list")),
        bcc_address_email_list=_str(email.get("bcc_address_email_list")),
        reply_to=_str(email.get("reply_to")),
        body=EmailBody(text=_str(body.get("text")), html=_str(body.get("html"))),
        organization_id=_str(email.get("organization_id")),
        campaign_id=_str(email.get("campaign_id")),
        subsequence_id=_str(email.get("subsequence_id")),
        list_id=_str(email.get("list_id")),
        lead=_str(email.get("lead")),
        lead_id=_str(email.get("lead_id")),
        eaccount=_str(email.get("eaccount")),
        ue_type=_int(email.get("ue_type")),
        is_unread=_int(email.get("is_unread")),
        is_auto_reply=_int(email.get("is_auto_reply")),
        i_status=_int(email.get("i_status")),
        thread_id=_str(email.get("thread_id")),
        content_preview=_str(email.get("content_preview")),
    )


def _map_lead_list(value: Any) -> LeadListDetail:
    lead_list = _as_record(value)
    return LeadListDetail(
        id=_str(lead_list.get("id")),
        organization_id=_str(lead_list.get("organization_id")),
        has_enrichment_task=_bool(lead_list.get("has_enrichment_task")),
        owned_by=_str(lead_list.get("owned_by")),
        name=_str(lead_list.get("name")),
        timestamp_created=_str(lead_list.get("timestamp_created")),
    )


def _compact(values: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if v is not None}


def _query(values: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key, value in values.items():
        if value is None or value == "":
            continue
        params[key] = str(value).lower() if isinstance(value, bool) else value
    return params


# --- Input schemas ---------------------------------------------------------


class ListLeadsInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    search: str | None = Field(
        default=None, description="Search by first name, last name, or email"
    )
    filter: str | None = Field(
        default=None,
        description="Lead filter value, such as FILTER_VAL_CONTACTED or FILTER_VAL_ACTIVE",
    )
    campaign: str | None = Field(default=None, description="Campaign ID to filter leads")
    list_id: str | None = Field(default=None, description="Lead list ID to filter leads")
    in_campaign: bool | None = Field(default=None, description="Whether the lead is in a campaign")
    in_list: bool | None = Field(default=None, description="Whether the lead is in a list")
    ids: list[str] | None = Field(default=None, description="Lead IDs to include")
    excluded_ids: list[str] | None = Field(default=None, description="Lead IDs to exclude")
    contacts: list[str] | None = Field(default=None, description="Lead email addresses to include")
    organization_user_ids: list[str] | None = Field(
        default=None, description="Organization user IDs to filter leads"
    )
    smart_view_id: str | None = Field(default=None, description="Smart view ID to filter leads")
    is_website_visitor: bool | None = Field(
        default=None, description="Whether the lead is a website visitor"
    )
    distinct_contacts: bool | None = Field(
        default=None, description="Whether to return distinct contacts"
    )
    enrichment_status: int | None = Field(default=None, description="Enrichment status filter")
    esg_code: str | None = Field(default=None, description="Email security gateway code filter")
    limit: int | None = Field(default=None, description="Number of leads to return, from 1 to 100")
    starting_after: str | None = Field(
        default=None, description="Forward pagination cursor from next_starting_after"
    )


class GetLeadInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    lead_id: str = Field(description="Lead ID")


class CreateLeadInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    campaign: str | None = Field(default=None, description="Campaign ID associated with the lead")
    list_id: str | None = Field(default=None, description="Lead list ID associated with the lead")
    email: str | None = Field(
        default=None, description="Lead email address. Required when adding to a campaign."
    )
    first_name: str | None = Field(default=None, description="Lead first name")
    last_name: str | None = Field(default=None, description="Lead last name")
    company_name: str | None = Field(default=None, description="Lead company name")
    job_title: str | None = Field(default=None, description="Lead job title")
    phone: str | None = Field(default=None, description="Lead phone number")
    website: str | None = Field(default=None, description="Lead website")
    personalization: str | None = Field(default=None, description="Lead personalization text")
    lt_interest_status: int | None = Field(
        default=None, description="Lead interest status value"
    )
    pl_value_lead: str | None = Field(default=None, description="Potential value of the lead")
    assigned_to: str | None = Field(
        default=None, description="Organization user ID assigned to the lead"
    )
    skip_if_in_workspace: bool | None = Field(
        default=None, description="Skip if the lead already exists in the workspace"
    )
    skip_if_in_campaign: bool | None = Field(
        default=None, description="Skip if the lead already exists in the campaign"
    )
    skip_if_in_list: bool | None = Field(
        default=None, description="Skip if the lead already exists in the list"
    )
    blocklist_id: str | None = Field(default=None, description="Blocklist ID to check for the lead")
    verify_leads_for_lead_finder: bool | None = Field(
        default=None, description="Whether to verify leads imported from Lead Finder"
    )
    verify_leads_on_import: bool | None = Field(
        default=None, description="Whether to verify leads on import"
    )
    custom_variables: dict[str, Any] | None = Field(
        default=None,
        description="Custom variable object with string, number, boolean, or null values",
    )


class DeleteLeadsInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    campaign_id: str | None = Field(
        default=None,
        description="Campaign ID to delete leads from. Required if list_id is not provided.",
    )
    list_id: str | None = Field(
        default=None,
        description="Lead list ID to delete leads from. Required if campaign_id is not provided.",
    )
    status: int | None = Field(default=None, description="Optional lead status filter")
    ids: list[str] | None = Field(default=None, description="Specific lead IDs to delete")
    limit: int | None = Field(
        default=None, description="Maximum number of matching leads to delete, up to 10000"
    )


class UpdateLeadInterestStatusInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    lead_email: str = Field(description="Lead email address")
    interest_value: int | None = Field(
        default=None,
        description="Interest status value. Pass null to reset to Lead.",
    )
    campaign_id: str | None = Field(default=None, description="Campaign ID for the lead")
    list_id: str | None = Field(default=None, description="Lead list ID for the lead")
    ai_interest_value: int | None = Field(
        default=None, description="AI interest value to set for the lead"
    )
    disable_auto_interest: bool | None = Field(
        default=None, description="Whether to disable auto interest"
    )


class ListCampaignsInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    limit: int | None = Field(
        default=None, description="Number of campaigns to return, from 1 to 100"
    )
    starting_after: str | None = Field(
        default=None, description="Pagination cursor from next_starting_after"
    )
    search: str | None = Field(default=None, description="Search by campaign name")
    tag_ids: str | None = Field(default=None, description="Comma-separated campaign tag IDs")
    ai_sales_agent_id: str | None = Field(default=None, description="AI Sales Agent ID filter")
    status: int | None = Field(default=None, description="Campaign status enum value")


class CreateCampaignInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    name: str = Field(description="Campaign name")
    campaign_schedule: dict[str, Any] = Field(
        description="Campaign schedule object with schedules array"
    )
    sequences: list[Any] | None = Field(
        default=None, description="Campaign sequence definitions"
    )
    email_list: list[str] | None = Field(default=None, description="Sending email accounts")
    daily_limit: int | None = Field(default=None, description="Daily sending limit")
    daily_max_leads: int | None = Field(
        default=None, description="Daily maximum new leads to contact"
    )
    open_tracking: bool | None = Field(default=None, description="Whether to track opens")
    stop_on_reply: bool | None = Field(
        default=None, description="Whether to stop the campaign on reply"
    )
    link_tracking: bool | None = Field(default=None, description="Whether to track links")
    text_only: bool | None = Field(default=None, description="Whether the campaign is text only")
    email_gap: int | None = Field(default=None, description="Gap between emails in minutes")
    pl_value: float | None = Field(default=None, description="Value of every positive lead")


class PatchCampaignInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    campaign_id: str = Field(description="Campaign ID")
    name: str | None = Field(default=None, description="Campaign name")
    campaign_schedule: dict[str, Any] | None = Field(
        default=None, description="Campaign schedule object with schedules array"
    )
    sequences: list[Any] | None = Field(
        default=None, description="Campaign sequence definitions"
    )
    email_list: list[str] | None = Field(default=None, description="Sending email accounts")
    daily_limit: int | None = Field(default=None, description="Daily sending limit")
    daily_max_leads: int | None = Field(
        default=None, description="Daily maximum new leads to contact"
    )
    open_tracking: bool | None = Field(default=None, description="Whether to track opens")
    stop_on_reply: bool | None = Field(
        default=None, description="Whether to stop the campaign on reply"
    )
    link_tracking: bool | None = Field(default=None, description="Whether to track links")
    text_only: bool | None = Field(default=None, description="Whether the campaign is text only")
    email_gap: int | None = Field(default=None, description="Gap between emails in minutes")
    pl_value: float | None = Field(default=None, description="Value of every positive lead")


class ActivateCampaignInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    campaign_id: str = Field(description="Campaign ID")


class ListEmailsInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    limit: int | None = Field(
        default=None, description="Number of emails to return, from 1 to 100"
    )
    starting_after: str | None = Field(
        default=None, description="Pagination cursor from next_starting_after"
    )
    search: str | None = Field(
        default=None, description="Search query, email address, or thread:<thread-id>"
    )
    campaign_id: str | None = Field(default=None, description="Campaign ID filter")
    list_id: str | None = Field(default=None, description="Lead list ID filter")
    i_status: int | None = Field(default=None, description="Email interest status filter")
    eaccount: str | None = Field(default=None, description="Sending email account filter")
    lead: str | None = Field(default=None, description="Lead email address filter")
    is_unread: bool | None = Field(default=None, description="Unread status filter")


class ReplyToEmailInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    eaccount: str = Field(description="Connected email account used to send the reply")
    reply_to_uuid: str = Field(description="Email ID to reply to")
    subject: str = Field(description="Reply subject")
    body_text: str | None = Field(default=None, description="Reply body as plain text")
    body_html: str | None = Field(default=None, description="Reply body as HTML")
    cc_address_email_list: str | None = Field(
        default=None, description="Comma-separated CC email addresses"
    )
    bcc_address_email_list: str | None = Field(
        default=None, description="Comma-separated BCC email addresses"
    )


class ListLeadListsInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    limit: int | None = Field(
        default=None, description="Number of lead lists to return, from 1 to 100"
    )
    starting_after: str | None = Field(
        default=None, description="Starting-after cursor from next_starting_after"
    )
    has_enrichment_task: bool | None = Field(
        default=None, description="Filter by enrichment task setting"
    )
    search: str | None = Field(
        default=None, description="Search query to filter lead lists by name"
    )


class CreateLeadListInput(BaseModel):
    api_key: str = Field(description="Instantly API key (provided by credential system)")
    name: str = Field(description="Lead list name")
    has_enrichment_task: bool | None = Field(
        default=None, description="Whether this list runs enrichment for every added lead"
    )
    owned_by: str | None = Field(default=None, description="User ID of the lead list owner")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListLeadsInput)
@serialize_pydantic_return
async def list_leads(
    api_key: str,
    search: str | None = None,
    filter: str | None = None,
    campaign: str | None = None,
    list_id: str | None = None,
    in_campaign: bool | None = None,
    in_list: bool | None = None,
    ids: list[str] | None = None,
    excluded_ids: list[str] | None = None,
    contacts: list[str] | None = None,
    organization_user_ids: list[str] | None = None,
    smart_view_id: str | None = None,
    is_website_visitor: bool | None = None,
    distinct_contacts: bool | None = None,
    enrichment_status: int | None = None,
    esg_code: str | None = None,
    limit: int | None = None,
    starting_after: str | None = None,
) -> ListLeadsOutput:
    """Retrieves Instantly V2 leads with search, campaign, list, and pagination filters."""
    if not api_key or not api_key.strip():
        return ListLeadsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body = _compact(
        {
            "search": search,
            "filter": filter,
            "campaign": campaign,
            "list_id": list_id,
            "in_campaign": in_campaign,
            "in_list": in_list,
            "ids": ids,
            "excluded_ids": excluded_ids,
            "contacts": contacts,
            "limit": limit,
            "starting_after": starting_after,
            "organization_user_ids": organization_user_ids,
            "smart_view_id": smart_view_id,
            "is_website_visitor": is_website_visitor,
            "distinct_contacts": distinct_contacts,
            "enrichment_status": enrichment_status,
            "esg_code": esg_code,
        }
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/leads/list", headers=_headers(api_key), json=body
            )
        if response.status_code not in (200, 201):
            return ListLeadsOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListLeadsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListLeadsOutput(success=False, error=f"list_leads failed: {exc}")

    leads = [_map_lead(item) for item in _items(data)]
    return ListLeadsOutput(
        success=True,
        leads=leads,
        count=len(leads),
        next_starting_after=_next_starting_after(data),
    )


@tool(args_schema=GetLeadInput)
@serialize_pydantic_return
async def get_lead(api_key: str, lead_id: str) -> GetLeadOutput:
    """Retrieves an Instantly V2 lead by ID."""
    if not api_key or not api_key.strip():
        return GetLeadOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/leads/{lead_id.strip()}", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return GetLeadOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetLeadOutput(success=False, error=f"get_lead failed: {exc}")

    lead = _map_lead(data)
    return GetLeadOutput(
        success=True,
        lead=lead,
        id=lead.id,
        email_address=lead.email,
        first_name=lead.first_name,
        last_name=lead.last_name,
        campaign=lead.campaign,
        status=lead.status,
    )


@tool(args_schema=CreateLeadInput)
@serialize_pydantic_return
async def create_lead(
    api_key: str,
    campaign: str | None = None,
    list_id: str | None = None,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    company_name: str | None = None,
    job_title: str | None = None,
    phone: str | None = None,
    website: str | None = None,
    personalization: str | None = None,
    lt_interest_status: int | None = None,
    pl_value_lead: str | None = None,
    assigned_to: str | None = None,
    skip_if_in_workspace: bool | None = None,
    skip_if_in_campaign: bool | None = None,
    skip_if_in_list: bool | None = None,
    blocklist_id: str | None = None,
    verify_leads_for_lead_finder: bool | None = None,
    verify_leads_on_import: bool | None = None,
    custom_variables: dict[str, Any] | None = None,
) -> CreateLeadOutput:
    """Creates an Instantly V2 lead in a campaign or lead list."""
    if not api_key or not api_key.strip():
        return CreateLeadOutput(success=False, error=_EMPTY_KEY_ERROR)

    body = _compact(
        {
            "campaign": campaign,
            "list_id": list_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "company_name": company_name,
            "job_title": job_title,
            "phone": phone,
            "website": website,
            "personalization": personalization,
            "lt_interest_status": lt_interest_status,
            "pl_value_lead": pl_value_lead,
            "assigned_to": assigned_to,
            "skip_if_in_workspace": skip_if_in_workspace,
            "skip_if_in_campaign": skip_if_in_campaign,
            "skip_if_in_list": skip_if_in_list,
            "blocklist_id": blocklist_id,
            "verify_leads_for_lead_finder": verify_leads_for_lead_finder,
            "verify_leads_on_import": verify_leads_on_import,
            "custom_variables": custom_variables,
        }
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/leads", headers=_headers(api_key), json=body
            )
        if response.status_code not in (200, 201):
            return CreateLeadOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateLeadOutput(success=False, error=f"create_lead failed: {exc}")

    lead = _map_lead(data)
    return CreateLeadOutput(
        success=True,
        lead=lead,
        id=lead.id,
        email_address=lead.email,
        first_name=lead.first_name,
        last_name=lead.last_name,
        campaign=lead.campaign,
        status=lead.status,
    )


@tool(args_schema=DeleteLeadsInput)
@serialize_pydantic_return
async def delete_leads(
    api_key: str,
    campaign_id: str | None = None,
    list_id: str | None = None,
    status: int | None = None,
    ids: list[str] | None = None,
    limit: int | None = None,
) -> DeleteLeadsOutput:
    """Deletes Instantly V2 leads in bulk from a campaign or lead list."""
    if not api_key or not api_key.strip():
        return DeleteLeadsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body = _compact(
        {
            "campaign_id": campaign_id,
            "list_id": list_id,
            "status": status,
            "ids": ids,
            "limit": limit,
        }
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                "DELETE", f"{_BASE_URL}/leads", headers=_headers(api_key), json=body
            )
        if response.status_code not in (200, 201, 202, 204):
            return DeleteLeadsOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = _safe_json(response)
    except httpx.TimeoutException:
        return DeleteLeadsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteLeadsOutput(success=False, error=f"delete_leads failed: {exc}")

    return DeleteLeadsOutput(success=True, count=_int(_as_record(data).get("count")))


@tool(args_schema=UpdateLeadInterestStatusInput)
@serialize_pydantic_return
async def update_lead_interest_status(
    api_key: str,
    lead_email: str,
    interest_value: int | None = None,
    campaign_id: str | None = None,
    list_id: str | None = None,
    ai_interest_value: int | None = None,
    disable_auto_interest: bool | None = None,
) -> UpdateLeadInterestStatusOutput:
    """Submits an Instantly V2 background job to update a lead interest status."""
    if not api_key or not api_key.strip():
        return UpdateLeadInterestStatusOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"lead_email": lead_email, "interest_value": interest_value}
    body.update(
        _compact(
            {
                "campaign_id": campaign_id,
                "list_id": list_id,
                "ai_interest_value": ai_interest_value,
                "disable_auto_interest": disable_auto_interest,
            }
        )
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/leads/update-interest-status",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201, 202):
            return UpdateLeadInterestStatusOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = _safe_json(response)
    except httpx.TimeoutException:
        return UpdateLeadInterestStatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateLeadInterestStatusOutput(
            success=False, error=f"update_lead_interest_status failed: {exc}"
        )

    return UpdateLeadInterestStatusOutput(
        success=True, message=_str(_as_record(data).get("message"))
    )


@tool(args_schema=ListCampaignsInput)
@serialize_pydantic_return
async def list_campaigns(
    api_key: str,
    limit: int | None = None,
    starting_after: str | None = None,
    search: str | None = None,
    tag_ids: str | None = None,
    ai_sales_agent_id: str | None = None,
    status: int | None = None,
) -> ListCampaignsOutput:
    """Retrieves Instantly V2 campaigns with search, status, tag, and pagination filters."""
    if not api_key or not api_key.strip():
        return ListCampaignsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params = _query(
        {
            "limit": limit,
            "starting_after": starting_after,
            "search": search,
            "tag_ids": tag_ids,
            "ai_sales_agent_id": ai_sales_agent_id,
            "status": status,
        }
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/campaigns", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListCampaignsOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListCampaignsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCampaignsOutput(success=False, error=f"list_campaigns failed: {exc}")

    campaigns = [_map_campaign(item) for item in _items(data)]
    return ListCampaignsOutput(
        success=True,
        campaigns=campaigns,
        count=len(campaigns),
        next_starting_after=_next_starting_after(data),
    )


@tool(args_schema=CreateCampaignInput)
@serialize_pydantic_return
async def create_campaign(
    api_key: str,
    name: str,
    campaign_schedule: dict[str, Any],
    sequences: list[Any] | None = None,
    email_list: list[str] | None = None,
    daily_limit: int | None = None,
    daily_max_leads: int | None = None,
    open_tracking: bool | None = None,
    stop_on_reply: bool | None = None,
    link_tracking: bool | None = None,
    text_only: bool | None = None,
    email_gap: int | None = None,
    pl_value: float | None = None,
) -> CreateCampaignOutput:
    """Creates an Instantly V2 campaign using the documented campaign schedule schema."""
    if not api_key or not api_key.strip():
        return CreateCampaignOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"name": name, "campaign_schedule": campaign_schedule}
    body.update(
        _compact(
            {
                "sequences": sequences,
                "pl_value": pl_value,
                "email_gap": email_gap,
                "text_only": text_only,
                "email_list": email_list,
                "daily_limit": daily_limit,
                "stop_on_reply": stop_on_reply,
                "link_tracking": link_tracking,
                "open_tracking": open_tracking,
                "daily_max_leads": daily_max_leads,
            }
        )
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/campaigns", headers=_headers(api_key), json=body
            )
        if response.status_code not in (200, 201):
            return CreateCampaignOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateCampaignOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCampaignOutput(success=False, error=f"create_campaign failed: {exc}")

    campaign = _map_campaign(data)
    return CreateCampaignOutput(
        success=True, campaign=campaign, id=campaign.id, name=campaign.name, status=campaign.status
    )


@tool(args_schema=PatchCampaignInput)
@serialize_pydantic_return
async def patch_campaign(
    api_key: str,
    campaign_id: str,
    name: str | None = None,
    campaign_schedule: dict[str, Any] | None = None,
    sequences: list[Any] | None = None,
    email_list: list[str] | None = None,
    daily_limit: int | None = None,
    daily_max_leads: int | None = None,
    open_tracking: bool | None = None,
    stop_on_reply: bool | None = None,
    link_tracking: bool | None = None,
    text_only: bool | None = None,
    email_gap: int | None = None,
    pl_value: float | None = None,
) -> PatchCampaignOutput:
    """Updates documented Instantly V2 campaign fields."""
    if not api_key or not api_key.strip():
        return PatchCampaignOutput(success=False, error=_EMPTY_KEY_ERROR)

    body = _compact(
        {
            "name": name,
            "campaign_schedule": campaign_schedule,
            "sequences": sequences,
            "pl_value": pl_value,
            "email_gap": email_gap,
            "text_only": text_only,
            "email_list": email_list,
            "daily_limit": daily_limit,
            "stop_on_reply": stop_on_reply,
            "link_tracking": link_tracking,
            "open_tracking": open_tracking,
            "daily_max_leads": daily_max_leads,
        }
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/campaigns/{campaign_id.strip()}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return PatchCampaignOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return PatchCampaignOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PatchCampaignOutput(success=False, error=f"patch_campaign failed: {exc}")

    campaign = _map_campaign(data)
    return PatchCampaignOutput(
        success=True, campaign=campaign, id=campaign.id, name=campaign.name, status=campaign.status
    )


@tool(args_schema=ActivateCampaignInput)
@serialize_pydantic_return
async def activate_campaign(api_key: str, campaign_id: str) -> ActivateCampaignOutput:
    """Activates, starts, or resumes an Instantly V2 campaign."""
    if not api_key or not api_key.strip():
        return ActivateCampaignOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/campaigns/{campaign_id.strip()}/activate",
                headers=_headers(api_key),
            )
        if response.status_code not in (200, 201):
            return ActivateCampaignOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return ActivateCampaignOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ActivateCampaignOutput(success=False, error=f"activate_campaign failed: {exc}")

    campaign = _map_campaign(data)
    return ActivateCampaignOutput(
        success=True, campaign=campaign, id=campaign.id, name=campaign.name, status=campaign.status
    )


@tool(args_schema=ListEmailsInput)
@serialize_pydantic_return
async def list_emails(
    api_key: str,
    limit: int | None = None,
    starting_after: str | None = None,
    search: str | None = None,
    campaign_id: str | None = None,
    list_id: str | None = None,
    i_status: int | None = None,
    eaccount: str | None = None,
    lead: str | None = None,
    is_unread: bool | None = None,
) -> ListEmailsOutput:
    """Retrieves Instantly V2 Unibox emails with search and pagination filters."""
    if not api_key or not api_key.strip():
        return ListEmailsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params = _query(
        {
            "limit": limit,
            "starting_after": starting_after,
            "search": search,
            "campaign_id": campaign_id,
            "list_id": list_id,
            "i_status": i_status,
            "eaccount": eaccount,
            "lead": lead,
            "is_unread": is_unread,
        }
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/emails", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListEmailsOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListEmailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEmailsOutput(success=False, error=f"list_emails failed: {exc}")

    emails = [_map_email(item) for item in _items(data)]
    return ListEmailsOutput(
        success=True,
        emails=emails,
        count=len(emails),
        next_starting_after=_next_starting_after(data),
    )


@tool(args_schema=ReplyToEmailInput)
@serialize_pydantic_return
async def reply_to_email(
    api_key: str,
    eaccount: str,
    reply_to_uuid: str,
    subject: str,
    body_text: str | None = None,
    body_html: str | None = None,
    cc_address_email_list: str | None = None,
    bcc_address_email_list: str | None = None,
) -> ReplyToEmailOutput:
    """Sends an Instantly V2 reply to an existing Unibox email."""
    if not api_key or not api_key.strip():
        return ReplyToEmailOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "eaccount": eaccount,
        "reply_to_uuid": reply_to_uuid,
        "subject": subject,
        "body": _compact({"text": body_text, "html": body_html}),
    }
    body.update(
        _compact(
            {
                "cc_address_email_list": cc_address_email_list,
                "bcc_address_email_list": bcc_address_email_list,
            }
        )
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/emails/reply", headers=_headers(api_key), json=body
            )
        if response.status_code not in (200, 201):
            return ReplyToEmailOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return ReplyToEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ReplyToEmailOutput(success=False, error=f"reply_to_email failed: {exc}")

    email = _map_email(data)
    return ReplyToEmailOutput(
        success=True, email=email, id=email.id, subject=email.subject, thread_id=email.thread_id
    )


@tool(args_schema=ListLeadListsInput)
@serialize_pydantic_return
async def list_lead_lists(
    api_key: str,
    limit: int | None = None,
    starting_after: str | None = None,
    has_enrichment_task: bool | None = None,
    search: str | None = None,
) -> ListLeadListsOutput:
    """Retrieves Instantly V2 lead lists with search and pagination filters."""
    if not api_key or not api_key.strip():
        return ListLeadListsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params = _query(
        {
            "limit": limit,
            "starting_after": starting_after,
            "has_enrichment_task": has_enrichment_task,
            "search": search,
        }
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/lead-lists", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListLeadListsOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListLeadListsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListLeadListsOutput(success=False, error=f"list_lead_lists failed: {exc}")

    lead_lists = [_map_lead_list(item) for item in _items(data)]
    return ListLeadListsOutput(
        success=True,
        lead_lists=lead_lists,
        count=len(lead_lists),
        next_starting_after=_next_starting_after(data),
    )


@tool(args_schema=CreateLeadListInput)
@serialize_pydantic_return
async def create_lead_list(
    api_key: str,
    name: str,
    has_enrichment_task: bool | None = None,
    owned_by: str | None = None,
) -> CreateLeadListOutput:
    """Creates an Instantly V2 lead list."""
    if not api_key or not api_key.strip():
        return CreateLeadListOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"name": name}
    body.update(_compact({"has_enrichment_task": has_enrichment_task, "owned_by": owned_by}))
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/lead-lists", headers=_headers(api_key), json=body
            )
        if response.status_code not in (200, 201):
            return CreateLeadListOutput(
                success=False,
                error=_error_message(
                    _safe_json(response), f"Instantly API error ({response.status_code})"
                ),
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateLeadListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateLeadListOutput(success=False, error=f"create_lead_list failed: {exc}")

    lead_list = _map_lead_list(data)
    return CreateLeadListOutput(
        success=True, lead_list=lead_list, id=lead_list.id, name=lead_list.name
    )


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
