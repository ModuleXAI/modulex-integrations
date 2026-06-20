"""Resend LangChain ``@tool`` functions.

Eight async tools wrapping the Resend REST API (``api.resend.com``).
These follow the modulex *api_key* calling convention: the modulex
``ToolExecutor`` injects an ``api_key: str`` directly (resolved from the
user's Resend API key credential), not an ``auth_type``/``auth_data``
pair. The key is sent as ``Authorization: Bearer <api_key>``.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.resend.outputs import (
    ContactItem,
    CreateContactOutput,
    DeleteContactOutput,
    DomainItem,
    EmailTag,
    GetContactOutput,
    GetEmailOutput,
    ListContactsOutput,
    ListDomainsOutput,
    SendOutput,
    UpdateContactOutput,
)

__all__ = [
    "create_contact",
    "delete_contact",
    "get_contact",
    "get_email",
    "list_contacts",
    "list_domains",
    "send",
    "update_contact",
]

_RESEND_API_BASE = "https://api.resend.com"
_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _parse_tags(tags: str) -> list[dict[str, str]]:
    """Parse ``"category:welcome,type:onboarding"`` into Resend tag objects."""
    parsed: list[dict[str, str]] = []
    for pair in tags.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        name, _, value = pair.partition(":")
        parsed.append({"name": name.strip(), "value": value.strip()})
    return parsed


# --- Input schemas (args_schema for each @tool) ----------------------------


class SendInput(BaseModel):
    from_address: str = Field(
        description=(
            'Email address to send from (e.g. "sender@example.com" or '
            '"Sender Name <sender@example.com>")'
        )
    )
    to: str = Field(
        description=(
            'Recipient email address (e.g. "recipient@example.com" or '
            '"Recipient Name <recipient@example.com>")'
        )
    )
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content (plain text or HTML based on content_type)")
    api_key: str = Field(description="Resend API key (provided by credential system)")
    content_type: str = Field(
        default="text",
        description='Content type for the body: "text" for plain text or "html" for HTML',
    )
    cc: str | None = Field(default=None, description="Carbon copy recipient email address")
    bcc: str | None = Field(default=None, description="Blind carbon copy recipient email address")
    reply_to: str | None = Field(default=None, description="Reply-to email address")
    scheduled_at: str | None = Field(
        default=None, description="Schedule email to be sent later in ISO 8601 format"
    )
    tags: str | None = Field(
        default=None,
        description=(
            'Comma-separated key:value pairs for email tags '
            '(e.g. "category:welcome,type:onboarding")'
        ),
    )


class GetEmailInput(BaseModel):
    email_id: str = Field(description="The ID of the email to retrieve")
    api_key: str = Field(description="Resend API key (provided by credential system)")


class CreateContactInput(BaseModel):
    email: str = Field(description="Email address of the contact")
    api_key: str = Field(description="Resend API key (provided by credential system)")
    first_name: str | None = Field(default=None, description="First name of the contact")
    last_name: str | None = Field(default=None, description="Last name of the contact")
    unsubscribed: bool | None = Field(
        default=None, description="Whether the contact is unsubscribed from all broadcasts"
    )


class ListContactsInput(BaseModel):
    api_key: str = Field(description="Resend API key (provided by credential system)")


class GetContactInput(BaseModel):
    contact_id: str = Field(description="The contact ID or email address to retrieve")
    api_key: str = Field(description="Resend API key (provided by credential system)")


class UpdateContactInput(BaseModel):
    contact_id: str = Field(description="The contact ID or email address to update")
    api_key: str = Field(description="Resend API key (provided by credential system)")
    first_name: str | None = Field(default=None, description="Updated first name")
    last_name: str | None = Field(default=None, description="Updated last name")
    unsubscribed: bool | None = Field(
        default=None,
        description="Whether the contact should be unsubscribed from all broadcasts",
    )


class DeleteContactInput(BaseModel):
    contact_id: str = Field(description="The contact ID or email address to delete")
    api_key: str = Field(description="Resend API key (provided by credential system)")


class ListDomainsInput(BaseModel):
    api_key: str = Field(description="Resend API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SendInput)
@serialize_pydantic_return
async def send(
    from_address: str,
    to: str,
    subject: str,
    body: str,
    api_key: str,
    content_type: str = "text",
    cc: str | None = None,
    bcc: str | None = None,
    reply_to: str | None = None,
    scheduled_at: str | None = None,
    tags: str | None = None,
) -> SendOutput:
    """Send an email using your Resend API key and from address."""
    if not api_key or not api_key.strip():
        return SendOutput(
            success=False,
            error="Resend API key is empty. Please configure a valid Resend credential.",
        )

    payload: dict[str, Any] = {
        "from": from_address,
        "to": to,
        "subject": subject,
    }
    if content_type == "html":
        payload["html"] = body
    else:
        payload["text"] = body
    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc
    if reply_to:
        payload["reply_to"] = reply_to
    if scheduled_at:
        payload["scheduled_at"] = scheduled_at
    if tags:
        parsed_tags = _parse_tags(tags)
        if parsed_tags:
            payload["tags"] = parsed_tags

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_RESEND_API_BASE}/emails", headers=_headers(api_key), json=payload
            )
        if response.status_code not in (200, 201):
            return SendOutput(
                success=False,
                error=f"Resend API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendOutput(success=False, error=f"Send email failed: {exc}")

    return SendOutput(
        success=True,
        id=data.get("id") or "",
        to=to,
        subject=subject,
        body=body,
    )


@tool(args_schema=GetEmailInput)
@serialize_pydantic_return
async def get_email(email_id: str, api_key: str) -> GetEmailOutput:
    """Retrieve details of a previously sent email by its ID."""
    if not api_key or not api_key.strip():
        return GetEmailOutput(
            success=False,
            error="Resend API key is empty. Please configure a valid Resend credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_RESEND_API_BASE}/emails/{email_id.strip()}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetEmailOutput(
                success=False,
                error=f"Resend API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEmailOutput(success=False, error=f"Get email failed: {exc}")

    if not data.get("id"):
        return GetEmailOutput(
            success=False,
            error=data.get("message") or "Failed to retrieve email",
        )

    return GetEmailOutput(
        success=True,
        id=data.get("id"),
        sender=data.get("from"),
        to=data.get("to") or [],
        subject=data.get("subject"),
        html=data.get("html"),
        text=data.get("text"),
        cc=data.get("cc") or [],
        bcc=data.get("bcc") or [],
        reply_to=data.get("reply_to") or [],
        last_event=data.get("last_event"),
        created_at=data.get("created_at"),
        scheduled_at=data.get("scheduled_at"),
        tags=[
            EmailTag(name=tag.get("name"), value=tag.get("value"))
            for tag in data.get("tags") or []
        ],
    )


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    email: str,
    api_key: str,
    first_name: str | None = None,
    last_name: str | None = None,
    unsubscribed: bool | None = None,
) -> CreateContactOutput:
    """Create a new contact in Resend."""
    if not api_key or not api_key.strip():
        return CreateContactOutput(
            success=False,
            error="Resend API key is empty. Please configure a valid Resend credential.",
        )

    payload: dict[str, Any] = {"email": email}
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    if unsubscribed is not None:
        payload["unsubscribed"] = unsubscribed

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_RESEND_API_BASE}/contacts", headers=_headers(api_key), json=payload
            )
        if response.status_code not in (200, 201):
            return CreateContactOutput(
                success=False,
                error=f"Resend API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContactOutput(success=False, error=f"Create contact failed: {exc}")

    if not data.get("id"):
        return CreateContactOutput(
            success=False,
            error=data.get("message") or "Failed to create contact",
        )

    return CreateContactOutput(success=True, id=data.get("id"))


@tool(args_schema=ListContactsInput)
@serialize_pydantic_return
async def list_contacts(api_key: str) -> ListContactsOutput:
    """List all contacts in Resend."""
    if not api_key or not api_key.strip():
        return ListContactsOutput(
            success=False,
            error="Resend API key is empty. Please configure a valid Resend credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_RESEND_API_BASE}/contacts", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return ListContactsOutput(
                success=False,
                error=f"Resend API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListContactsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListContactsOutput(success=False, error=f"List contacts failed: {exc}")

    if data.get("message"):
        return ListContactsOutput(
            success=False,
            error=data.get("message") or "Failed to list contacts",
        )

    return ListContactsOutput(
        success=True,
        contacts=[
            ContactItem(
                id=item.get("id"),
                email=item.get("email"),
                first_name=item.get("first_name"),
                last_name=item.get("last_name"),
                created_at=item.get("created_at"),
                unsubscribed=item.get("unsubscribed"),
            )
            for item in data.get("data") or []
        ],
        has_more=data.get("has_more") or False,
    )


@tool(args_schema=GetContactInput)
@serialize_pydantic_return
async def get_contact(contact_id: str, api_key: str) -> GetContactOutput:
    """Retrieve details of a contact by ID or email."""
    if not api_key or not api_key.strip():
        return GetContactOutput(
            success=False,
            error="Resend API key is empty. Please configure a valid Resend credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_RESEND_API_BASE}/contacts/{quote(contact_id.strip(), safe='')}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetContactOutput(
                success=False,
                error=f"Resend API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetContactOutput(success=False, error=f"Get contact failed: {exc}")

    if not data.get("id"):
        return GetContactOutput(
            success=False,
            error=data.get("message") or "Failed to retrieve contact",
        )

    return GetContactOutput(
        success=True,
        id=data.get("id"),
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        created_at=data.get("created_at"),
        unsubscribed=data.get("unsubscribed"),
    )


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    contact_id: str,
    api_key: str,
    first_name: str | None = None,
    last_name: str | None = None,
    unsubscribed: bool | None = None,
) -> UpdateContactOutput:
    """Update an existing contact in Resend."""
    if not api_key or not api_key.strip():
        return UpdateContactOutput(
            success=False,
            error="Resend API key is empty. Please configure a valid Resend credential.",
        )

    payload: dict[str, Any] = {}
    if first_name is not None:
        payload["first_name"] = first_name
    if last_name is not None:
        payload["last_name"] = last_name
    if unsubscribed is not None:
        payload["unsubscribed"] = unsubscribed

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_RESEND_API_BASE}/contacts/{quote(contact_id.strip(), safe='')}",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return UpdateContactOutput(
                success=False,
                error=f"Resend API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateContactOutput(success=False, error=f"Update contact failed: {exc}")

    if not data.get("id"):
        return UpdateContactOutput(
            success=False,
            error=data.get("message") or "Failed to update contact",
        )

    return UpdateContactOutput(success=True, id=data.get("id"))


@tool(args_schema=DeleteContactInput)
@serialize_pydantic_return
async def delete_contact(contact_id: str, api_key: str) -> DeleteContactOutput:
    """Delete a contact from Resend by ID or email."""
    if not api_key or not api_key.strip():
        return DeleteContactOutput(
            success=False,
            error="Resend API key is empty. Please configure a valid Resend credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_RESEND_API_BASE}/contacts/{quote(contact_id.strip(), safe='')}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return DeleteContactOutput(
                success=False,
                error=f"Resend API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteContactOutput(success=False, error=f"Delete contact failed: {exc}")

    if data.get("message") and not data.get("deleted"):
        return DeleteContactOutput(
            success=False,
            error=data.get("message") or "Failed to delete contact",
        )

    return DeleteContactOutput(
        success=True,
        id=data.get("contact") or data.get("id") or "",
        deleted=data.get("deleted") if data.get("deleted") is not None else True,
    )


@tool(args_schema=ListDomainsInput)
@serialize_pydantic_return
async def list_domains(api_key: str) -> ListDomainsOutput:
    """List all domains in your Resend account."""
    if not api_key or not api_key.strip():
        return ListDomainsOutput(
            success=False,
            error="Resend API key is empty. Please configure a valid Resend credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_RESEND_API_BASE}/domains", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return ListDomainsOutput(
                success=False,
                error=f"Resend API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDomainsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDomainsOutput(success=False, error=f"List domains failed: {exc}")

    if data.get("message"):
        return ListDomainsOutput(
            success=False,
            error=data.get("message") or "Failed to list domains",
        )

    return ListDomainsOutput(
        success=True,
        domains=[
            DomainItem(
                id=item.get("id"),
                name=item.get("name"),
                status=item.get("status"),
                region=item.get("region"),
                created_at=item.get("created_at"),
            )
            for item in data.get("data") or []
        ],
        has_more=data.get("has_more") or False,
    )
