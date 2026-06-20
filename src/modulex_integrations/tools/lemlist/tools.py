"""Lemlist LangChain ``@tool`` functions.

Three async tools wrapping the Lemlist REST API. The calling convention
is the modulex *api_key* one: the ``ToolExecutor`` injects an
``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair.

Lemlist authenticates with HTTP Basic auth where the username is empty
and the API key is the password — i.e. ``Authorization: Basic
<base64(":" + api_key)>``.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions rather than raising.
"""
from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.lemlist.outputs import (
    ActivityItem,
    GetActivitiesOutput,
    GetLeadOutput,
    SendEmailOutput,
)

__all__ = ["get_activities", "get_lead", "send_email"]

_LEMLIST_API_BASE = "https://api.lemlist.com/api"
_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    # Lemlist Basic auth: empty username, api_key as password ->
    # base64(":" + api_key). The leading colon is required.
    token = base64.b64encode(f":{api_key}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class GetActivitiesInput(BaseModel):
    api_key: str = Field(description="Lemlist API key (provided by credential system)")
    type: str | None = Field(
        default=None,
        description=(
            "Filter by activity type (e.g., emailOpened, emailClicked, "
            "emailReplied, paused)"
        ),
    )
    campaign_id: str | None = Field(
        default=None, description='Filter by campaign ID (e.g., "cam_abc123def456")'
    )
    lead_id: str | None = Field(
        default=None, description='Filter by lead ID (e.g., "lea_abc123def456")'
    )
    is_first: bool | None = Field(
        default=None, description="Filter for first activity only"
    )
    limit: int | None = Field(
        default=None,
        description="Number of results per request (max 100, default 100)",
    )
    offset: int | None = Field(
        default=None,
        description="Number of records to skip for pagination (e.g., 0, 100, 200)",
    )


class GetLeadInput(BaseModel):
    lead_identifier: str = Field(
        description=(
            'Lead email address (e.g., "john@example.com") or lead ID '
            '(e.g., "lea_abc123def456")'
        )
    )
    api_key: str = Field(description="Lemlist API key (provided by credential system)")


class SendEmailInput(BaseModel):
    send_user_id: str = Field(
        description='Identifier for the user sending the message (e.g., "usr_abc123def456")'
    )
    send_user_email: str = Field(
        description='Email address of the sender (e.g., "sales@company.com")'
    )
    send_user_mailbox_id: str = Field(
        description='Mailbox identifier for the sender (e.g., "mbx_abc123def456")'
    )
    contact_id: str = Field(
        description='Recipient contact identifier (e.g., "con_abc123def456")'
    )
    lead_id: str = Field(
        description='Associated lead identifier (e.g., "lea_abc123def456")'
    )
    subject: str = Field(description="Email subject line")
    message: str = Field(description="Email message body in HTML format")
    api_key: str = Field(description="Lemlist API key (provided by credential system)")
    cc: list[str] | None = Field(
        default=None, description="Array of CC email addresses"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=GetActivitiesInput)
@serialize_pydantic_return
async def get_activities(
    api_key: str,
    type: str | None = None,
    campaign_id: str | None = None,
    lead_id: str | None = None,
    is_first: bool | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> GetActivitiesOutput:
    """Retrieves campaign activities and steps performed, including email opens,
    clicks, replies, and other events."""
    if not api_key or not api_key.strip():
        return GetActivitiesOutput(
            success=False,
            error="Lemlist API key is empty. Please configure a valid Lemlist credential.",
        )

    params: dict[str, Any] = {"version": "v2"}
    if type:
        params["type"] = type
    if campaign_id:
        params["campaignId"] = campaign_id
    if lead_id:
        params["leadId"] = lead_id
    if is_first is not None:
        params["isFirst"] = str(is_first).lower()
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_LEMLIST_API_BASE}/activities",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetActivitiesOutput(
                success=False,
                error=f"Lemlist API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetActivitiesOutput(
            success=False, error="Request timed out. Try reducing the limit."
        )
    except Exception as exc:
        return GetActivitiesOutput(success=False, error=f"Get activities failed: {exc}")

    activities = data if isinstance(data, list) else []
    return GetActivitiesOutput(
        success=True,
        activities=[
            ActivityItem(
                id=item.get("_id"),
                type=item.get("type"),
                lead_id=item.get("leadId"),
                campaign_id=item.get("campaignId"),
                sequence_id=item.get("sequenceId"),
                step_id=item.get("stepId"),
                created_at=item.get("createdAt"),
            )
            for item in activities
            if isinstance(item, dict)
        ],
        count=len(activities),
    )


@tool(args_schema=GetLeadInput)
@serialize_pydantic_return
async def get_lead(lead_identifier: str, api_key: str) -> GetLeadOutput:
    """Retrieves lead information by email address or lead ID."""
    if not api_key or not api_key.strip():
        return GetLeadOutput(
            success=False,
            error="Lemlist API key is empty. Please configure a valid Lemlist credential.",
        )
    if not lead_identifier or not lead_identifier.strip():
        return GetLeadOutput(success=False, error="lead_identifier is required.")

    identifier = lead_identifier.strip()
    if "@" in identifier:
        url = f"{_LEMLIST_API_BASE}/leads/{quote(identifier, safe='')}"
        params: dict[str, Any] = {}
    else:
        url = f"{_LEMLIST_API_BASE}/leads"
        params = {"id": identifier}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                url, headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return GetLeadOutput(
                success=False,
                error=f"Lemlist API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetLeadOutput(success=False, error=f"Get lead failed: {exc}")

    if not isinstance(data, dict):
        return GetLeadOutput(
            success=False, error="Unexpected response shape from Lemlist."
        )

    return GetLeadOutput(
        success=True,
        id=data.get("_id"),
        email=data.get("email"),
        first_name=data.get("firstName"),
        last_name=data.get("lastName"),
        company_name=data.get("companyName"),
        job_title=data.get("jobTitle"),
        company_domain=data.get("companyDomain"),
        is_paused=data.get("isPaused"),
        campaign_id=data.get("campaignId"),
        contact_id=data.get("contactId"),
        email_status=data.get("emailStatus"),
    )


@tool(args_schema=SendEmailInput)
@serialize_pydantic_return
async def send_email(
    send_user_id: str,
    send_user_email: str,
    send_user_mailbox_id: str,
    contact_id: str,
    lead_id: str,
    subject: str,
    message: str,
    api_key: str,
    cc: list[str] | None = None,
) -> SendEmailOutput:
    """Sends an email to a contact through the Lemlist inbox."""
    if not api_key or not api_key.strip():
        return SendEmailOutput(
            success=False,
            error="Lemlist API key is empty. Please configure a valid Lemlist credential.",
        )

    body: dict[str, Any] = {
        "sendUserId": send_user_id.strip(),
        "sendUserEmail": send_user_email.strip(),
        "sendUserMailboxId": send_user_mailbox_id.strip(),
        "contactId": contact_id.strip(),
        "leadId": lead_id.strip(),
        "subject": subject.strip(),
        "message": message,
        "cc": cc or [],
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_LEMLIST_API_BASE}/inbox/email",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return SendEmailOutput(
                success=False,
                error=f"Lemlist API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendEmailOutput(success=False, error=f"Send email failed: {exc}")

    ok = data.get("ok", True) if isinstance(data, dict) else True
    return SendEmailOutput(success=True, ok=ok)
