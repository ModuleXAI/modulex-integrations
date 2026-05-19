"""Mailgun LangChain @tool functions."""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.mailgun.outputs import (
    CreateMailinglistMemberOutput,
    CreateRouteOutput,
    DeleteMailinglistMemberOutput,
    DomainSummary,
    EmailVerificationResult,
    ListDomainsOutput,
    ListMailinglistMembersOutput,
    MailinglistMember,
    RetrieveMailinglistMemberOutput,
    SendEmailOutput,
    SuppressEmailOutput,
    VerifyEmailOutput,
)

__all__ = [
    "create_mailinglist_member",
    "create_route",
    "delete_mailinglist_member",
    "list_domains",
    "list_mailinglist_members",
    "retrieve_mailinglist_member",
    "send_email",
    "suppress_email",
    "verify_email",
]

_TIMEOUT = 30.0


def _base_url(region: str) -> str:
    if region.upper() == "EU":
        return "https://api.eu.mailgun.net"
    return "https://api.mailgun.net"


def _auth(api_key: str) -> httpx.BasicAuth:
    return httpx.BasicAuth(username="api", password=api_key)


# --- Input schemas --------------------------------------------------------


class SendEmailInput(BaseModel):
    domain: str = Field(description="Mailgun domain name to send from")
    from_name: str = Field(description="Sender display name")
    from_email: str = Field(description="Sender email address")
    to: list[str] = Field(description="Recipient email address(es)")
    subject: str = Field(description="Email subject line")
    text: str | None = Field(default=None, description="Plain text message body")
    html: str | None = Field(default=None, description="HTML message body")
    reply_to: str | None = Field(default=None, description="Reply-to email address")
    test_mode: bool = Field(default=True, description="Enable Mailgun test mode")
    dkim: bool = Field(default=True, description="Enable or disable DKIM signatures")
    tracking: bool = Field(default=True, description="Enable or disable tracking")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


class VerifyEmailInput(BaseModel):
    email: str = Field(description="Email address to verify")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


class CreateMailinglistMemberInput(BaseModel):
    list_address: str = Field(description="Mailing list address")
    address: str = Field(description="Email address of the member to add")
    name: str | None = Field(default=None, description="Display name of the member")
    vars: dict[str, Any] | None = Field(default=None, description="Extra member data as a JSON object")
    subscribed: str = Field(default="yes", description="Subscription status: yes or no")
    upsert: str = Field(default="no", description="If 'yes', update existing member; if 'no', error on duplicate")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


class CreateRouteInput(BaseModel):
    priority: int = Field(description="Route priority (lower numbers evaluated first)")
    description: str = Field(description="Human-readable description of the route")
    expression: str = Field(description="Mailgun route filter expression")
    action: list[str] = Field(description="List of route action strings")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


class DeleteMailinglistMemberInput(BaseModel):
    list_address: str = Field(description="Mailing list address")
    address: str = Field(description="Email address of the member to remove")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


class ListDomainsInput(BaseModel):
    state: str = Field(default="active", description="Filter by domain state: active, unverified, disabled")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


class ListMailinglistMembersInput(BaseModel):
    list_address: str = Field(description="Mailing list address")
    subscribed: str | None = Field(default=None, description="Filter: 'true' for subscribed, 'false' for unsubscribed, omit for all")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


class RetrieveMailinglistMemberInput(BaseModel):
    list_address: str = Field(description="Mailing list address")
    address: str = Field(description="Email address of the member to retrieve")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


class SuppressEmailInput(BaseModel):
    domain: str = Field(description="Mailgun domain name")
    email: str = Field(description="Email address to suppress")
    category: str = Field(description="Suppression category: bounces, unsubscribes, or complaints")
    bounce_error_code: str = Field(default="550", description="Bounce error code (only for bounces)")
    bounce_error_message: str | None = Field(default=None, description="Bounce error message (only for bounces)")
    unsubscribe_tag: str = Field(default="*", description="Tag to unsubscribe from (only for unsubscribes)")
    api_key: str = Field(description="Mailgun API key")
    region: str = Field(default="US", description="Mailgun region: US or EU")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=SendEmailInput)
@serialize_pydantic_return
async def send_email(
    domain: str,
    from_name: str,
    from_email: str,
    to: list[str],
    subject: str,
    api_key: str,
    text: str | None = None,
    html: str | None = None,
    reply_to: str | None = None,
    test_mode: bool = True,
    dkim: bool = True,
    tracking: bool = True,
    region: str = "US",
) -> SendEmailOutput:
    """Send an email via Mailgun."""
    if not api_key or not api_key.strip():
        return SendEmailOutput(success=False, error="API key is empty. Please configure a valid credential.")
    data: dict[str, Any] = {
        "from": f"{from_name} <{from_email}>",
        "to": to,
        "subject": subject,
        "o:testmode": "yes" if test_mode else "no",
        "o:dkim": "yes" if dkim else "no",
        "o:tracking": "yes" if tracking else "no",
    }
    if text:
        data["text"] = text
    if html:
        data["html"] = html
    if reply_to:
        data["h:Reply-To"] = reply_to
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(region)}/v3/{domain}/messages",
                auth=_auth(api_key),
                data=data,
            )
        if response.status_code != 200:
            return SendEmailOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        result = response.json()
    except httpx.TimeoutException:
        return SendEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendEmailOutput(success=False, error=f"Call failed: {exc}")
    return SendEmailOutput(
        success=True,
        id=result.get("id"),
        message=result.get("message"),
    )


@tool(args_schema=VerifyEmailInput)
@serialize_pydantic_return
async def verify_email(
    email: str,
    api_key: str,
    region: str = "US",
) -> VerifyEmailOutput:
    """Verify an email address for deliverability using Mailgun's validation API."""
    if not api_key or not api_key.strip():
        return VerifyEmailOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(region)}/v4/address/validate",
                auth=_auth(api_key),
                params={"address": email},
            )
        if response.status_code != 200:
            return VerifyEmailOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return VerifyEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VerifyEmailOutput(success=False, error=f"Call failed: {exc}")
    return VerifyEmailOutput(
        success=True,
        verification=EmailVerificationResult(
            address=data.get("address"),
            did_you_mean=data.get("did_you_mean"),
            is_disposable_address=data.get("is_disposable_address"),
            is_role_address=data.get("is_role_address"),
            reason=data.get("reason") or [],
            result=data.get("result"),
            risk=data.get("risk"),
        ),
    )


@tool(args_schema=CreateMailinglistMemberInput)
@serialize_pydantic_return
async def create_mailinglist_member(
    list_address: str,
    address: str,
    api_key: str,
    name: str | None = None,
    vars: dict[str, Any] | None = None,
    subscribed: str = "yes",
    upsert: str = "no",
    region: str = "US",
) -> CreateMailinglistMemberOutput:
    """Add a member to an existing Mailgun mailing list."""
    if not api_key or not api_key.strip():
        return CreateMailinglistMemberOutput(success=False, error="API key is empty. Please configure a valid credential.")
    form_data: dict[str, Any] = {
        "address": address,
        "subscribed": subscribed,
        "upsert": upsert,
    }
    if name:
        form_data["name"] = name
    if vars:
        form_data["vars"] = json.dumps(vars)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(region)}/v3/lists/{list_address}/members",
                auth=_auth(api_key),
                data=form_data,
            )
        if response.status_code not in (200, 201):
            return CreateMailinglistMemberOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
        member_data = data.get("member", {})
    except httpx.TimeoutException:
        return CreateMailinglistMemberOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateMailinglistMemberOutput(success=False, error=f"Call failed: {exc}")
    return CreateMailinglistMemberOutput(
        success=True,
        member=MailinglistMember(
            address=member_data.get("address"),
            name=member_data.get("name"),
            subscribed=member_data.get("subscribed"),
            vars=member_data.get("vars"),
        ),
    )


@tool(args_schema=CreateRouteInput)
@serialize_pydantic_return
async def create_route(
    priority: int,
    description: str,
    expression: str,
    action: list[str],
    api_key: str,
    region: str = "US",
) -> CreateRouteOutput:
    """Create a new Mailgun route for email matching and forwarding."""
    if not api_key or not api_key.strip():
        return CreateRouteOutput(success=False, error="API key is empty. Please configure a valid credential.")
    form_pairs: list[tuple[str, str]] = [
        ("priority", str(priority)),
        ("description", description),
        ("expression", expression),
    ]
    for a in action:
        form_pairs.append(("action", a))
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(region)}/v3/routes",
                auth=_auth(api_key),
                content=urlencode(form_pairs),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if response.status_code not in (200, 201):
            return CreateRouteOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
        route = data.get("route", {})
    except httpx.TimeoutException:
        return CreateRouteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateRouteOutput(success=False, error=f"Call failed: {exc}")
    return CreateRouteOutput(
        success=True,
        route_id=route.get("id"),
        route_message=data.get("message"),
    )


@tool(args_schema=DeleteMailinglistMemberInput)
@serialize_pydantic_return
async def delete_mailinglist_member(
    list_address: str,
    address: str,
    api_key: str,
    region: str = "US",
) -> DeleteMailinglistMemberOutput:
    """Delete a member from a Mailgun mailing list by email address."""
    if not api_key or not api_key.strip():
        return DeleteMailinglistMemberOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_base_url(region)}/v3/lists/{list_address}/members/{address}",
                auth=_auth(api_key),
            )
        if response.status_code != 200:
            return DeleteMailinglistMemberOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return DeleteMailinglistMemberOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteMailinglistMemberOutput(success=False, error=f"Call failed: {exc}")
    return DeleteMailinglistMemberOutput(
        success=True,
        member_address=data.get("member", {}).get("address"),
        message=data.get("message"),
    )


@tool(args_schema=ListDomainsInput)
@serialize_pydantic_return
async def list_domains(
    api_key: str,
    state: str = "active",
    region: str = "US",
) -> ListDomainsOutput:
    """List all domains configured in the Mailgun account."""
    if not api_key or not api_key.strip():
        return ListDomainsOutput(success=False, error="API key is empty. Please configure a valid credential.")
    all_domains: list[DomainSummary] = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            params: dict[str, str] = {"state": state}
            response = await client.get(
                f"{_base_url(region)}/v3/domains",
                auth=_auth(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListDomainsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
        for d in data.get("items", []):
            all_domains.append(
                DomainSummary(
                    name=d.get("name"),
                    state=d.get("state"),
                    type=d.get("type"),
                    created_at=d.get("created_at"),
                    smtp_login=d.get("smtp_login"),
                    web_prefix=d.get("web_prefix"),
                )
            )
    except httpx.TimeoutException:
        return ListDomainsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDomainsOutput(success=False, error=f"Call failed: {exc}")
    return ListDomainsOutput(
        success=True,
        domains=all_domains,
        total_count=len(all_domains),
    )


@tool(args_schema=ListMailinglistMembersInput)
@serialize_pydantic_return
async def list_mailinglist_members(
    list_address: str,
    api_key: str,
    subscribed: str | None = None,
    region: str = "US",
) -> ListMailinglistMembersOutput:
    """List all members of a Mailgun mailing list."""
    if not api_key or not api_key.strip():
        return ListMailinglistMembersOutput(success=False, error="API key is empty. Please configure a valid credential.")
    all_members: list[MailinglistMember] = []
    try:
        params: dict[str, str] = {}
        if subscribed is not None:
            params["subscribed"] = subscribed
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(region)}/v3/lists/{list_address}/members/pages",
                auth=_auth(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListMailinglistMembersOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
        for m in data.get("items", []):
            all_members.append(
                MailinglistMember(
                    address=m.get("address"),
                    name=m.get("name"),
                    subscribed=m.get("subscribed"),
                    vars=m.get("vars"),
                )
            )
    except httpx.TimeoutException:
        return ListMailinglistMembersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMailinglistMembersOutput(success=False, error=f"Call failed: {exc}")
    return ListMailinglistMembersOutput(
        success=True,
        members=all_members,
        total_count=len(all_members),
    )


@tool(args_schema=RetrieveMailinglistMemberInput)
@serialize_pydantic_return
async def retrieve_mailinglist_member(
    list_address: str,
    address: str,
    api_key: str,
    region: str = "US",
) -> RetrieveMailinglistMemberOutput:
    """Get details of a specific mailing list member by email address."""
    if not api_key or not api_key.strip():
        return RetrieveMailinglistMemberOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(region)}/v3/lists/{list_address}/members/{address}",
                auth=_auth(api_key),
            )
        if response.status_code != 200:
            return RetrieveMailinglistMemberOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
        member_data = data.get("member", {})
    except httpx.TimeoutException:
        return RetrieveMailinglistMemberOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RetrieveMailinglistMemberOutput(success=False, error=f"Call failed: {exc}")
    return RetrieveMailinglistMemberOutput(
        success=True,
        member=MailinglistMember(
            address=member_data.get("address"),
            name=member_data.get("name"),
            subscribed=member_data.get("subscribed"),
            vars=member_data.get("vars"),
        ),
    )


@tool(args_schema=SuppressEmailInput)
@serialize_pydantic_return
async def suppress_email(
    domain: str,
    email: str,
    category: str,
    api_key: str,
    bounce_error_code: str = "550",
    bounce_error_message: str | None = None,
    unsubscribe_tag: str = "*",
    region: str = "US",
) -> SuppressEmailOutput:
    """Add an email address to a Mailgun suppression list (bounces, unsubscribes, or complaints)."""
    if not api_key or not api_key.strip():
        return SuppressEmailOutput(success=False, error="API key is empty. Please configure a valid credential.")
    form_data: dict[str, str] = {"address": email}
    if category == "bounces":
        form_data["code"] = bounce_error_code
        if bounce_error_message:
            form_data["error"] = bounce_error_message
    elif category == "unsubscribes":
        form_data["tag"] = unsubscribe_tag
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(region)}/v3/{domain}/{category}",
                auth=_auth(api_key),
                data=form_data,
            )
        if response.status_code not in (200, 201):
            return SuppressEmailOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return SuppressEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SuppressEmailOutput(success=False, error=f"Call failed: {exc}")
    return SuppressEmailOutput(
        success=True,
        message=data.get("message"),
    )
