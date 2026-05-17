"""SendGrid LangChain ``@tool`` functions.

Pure-HTTP integration against the SendGrid v3 REST API. Key-based
runtime convention (``api_key: str`` first arg). Legacy wraps every
action body in ``try/except`` so non-2xx responses, timeouts, and
unexpected exceptions all flow through a unified ``success=False``
envelope — preserved here verbatim.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.sendgrid.outputs import (
    AddEmailToGlobalSuppressionOutput,
    AddOrUpdateContactOutput,
    ContactSummary,
    CreateContactListOutput,
    DeleteBlocksOutput,
    DeleteBouncesOutput,
    DeleteContactsOutput,
    DeleteGlobalSuppressionOutput,
    GetAllBouncesOutput,
    GetContactListsOutput,
    ListBlocksOutput,
    ListGlobalSuppressionsOutput,
    ListSummary,
    RemoveContactFromListOutput,
    SearchContactsOutput,
    SendEmailMultipleRecipientsOutput,
    SendEmailOutput,
    SuppressionRow,
)

__all__ = [
    "add_email_to_global_suppression",
    "add_or_update_contact",
    "create_contact_list",
    "delete_blocks",
    "delete_bounces",
    "delete_contacts",
    "delete_global_suppression",
    "get_all_bounces",
    "get_contact_lists",
    "list_blocks",
    "list_global_suppressions",
    "remove_contact_from_list",
    "search_contacts",
    "send_email",
    "send_email_multiple_recipients",
]

_API = "https://api.sendgrid.com/v3"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _api_err(status: int, body: str) -> str:
    return f"API error {status}: {body}"


# --- Input schemas ---------------------------------------------------------


class _KeyField(BaseModel):
    api_key: str = Field(description="SendGrid API key (auto-injected)")


class SendEmailInput(_KeyField):
    to_email: str = Field(description="Recipient email address")
    from_email: str = Field(description="Sender email address (must be verified)")
    subject: str = Field(description="Email subject line")
    content: str = Field(description="Email body content (plain text or HTML)")
    content_type: str = Field(default="text/plain")
    from_name: str | None = Field(default=None, description="Sender display name")
    to_name: str | None = Field(default=None, description="Recipient display name")
    reply_to_email: str | None = Field(default=None, description="Reply-to email")
    cc_emails: list[str] | None = Field(default=None, description="CC emails")
    bcc_emails: list[str] | None = Field(default=None, description="BCC emails")


class SendEmailMultipleRecipientsInput(_KeyField):
    to_emails: list[str] = Field(description="Recipient email addresses")
    from_email: str = Field(description="Sender email (must be verified)")
    subject: str = Field(description="Email subject line")
    content: str = Field(description="Email body content")
    content_type: str = Field(default="text/plain")
    from_name: str | None = Field(default=None)


class AddOrUpdateContactInput(_KeyField):
    email: str = Field(description="Contact email address")
    first_name: str | None = None
    last_name: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state_province_region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    alternate_emails: list[str] | None = None
    list_ids: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


class SearchContactsInput(_KeyField):
    query: str = Field(description="SGQL query string")


class CreateContactListInput(_KeyField):
    name: str = Field(description="List name (max 100 chars)")


class GetContactListsInput(_KeyField):
    page_size: int | None = Field(default=100, description="Number of lists (max 1000)")


class RemoveContactFromListInput(_KeyField):
    list_id: str = Field(description="ID of the list")
    contact_ids: list[str] = Field(description="Contact IDs to remove")


class DeleteContactsInput(_KeyField):
    contact_ids: list[str] | None = None
    delete_all: bool | None = False


class AddEmailToGlobalSuppressionInput(_KeyField):
    recipient_emails: list[str] = Field(description="Emails to suppress")


class DeleteGlobalSuppressionInput(_KeyField):
    email: str = Field(description="Email to remove from suppression")


class _TimeWindowInput(_KeyField):
    start_time: int | None = None
    end_time: int | None = None


class ListGlobalSuppressionsInput(_TimeWindowInput):
    limit: int | None = Field(default=100)


class GetAllBouncesInput(_TimeWindowInput):
    pass


class DeleteBouncesInput(_KeyField):
    emails: list[str] | None = None
    delete_all: bool | None = False


class ListBlocksInput(_TimeWindowInput):
    limit: int | None = Field(default=100)


class DeleteBlocksInput(_KeyField):
    emails: list[str] | None = None
    delete_all: bool | None = False


# --- Tools -----------------------------------------------------------------


@tool(args_schema=SendEmailInput)
@serialize_pydantic_return
async def send_email(
    api_key: str,
    to_email: str,
    from_email: str,
    subject: str,
    content: str,
    content_type: str = "text/plain",
    from_name: str | None = None,
    to_name: str | None = None,
    reply_to_email: str | None = None,
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
) -> SendEmailOutput:
    """Send a single transactional email."""
    try:
        to_recipient: dict[str, Any] = {"email": to_email}
        if to_name:
            to_recipient["name"] = to_name

        personalization: dict[str, Any] = {"to": [to_recipient]}
        if cc_emails:
            personalization["cc"] = [{"email": e} for e in cc_emails]
        if bcc_emails:
            personalization["bcc"] = [{"email": e} for e in bcc_emails]

        from_data: dict[str, Any] = {"email": from_email}
        if from_name:
            from_data["name"] = from_name

        payload: dict[str, Any] = {
            "personalizations": [personalization],
            "from": from_data,
            "subject": subject,
            "content": [{"type": content_type, "value": content}],
        }
        if reply_to_email:
            payload["reply_to"] = {"email": reply_to_email}

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API}/mail/send", headers=_headers(api_key), json=payload
            )
        if response.status_code != 202:
            return SendEmailOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        return SendEmailOutput(
            success=True,
            message="Email sent successfully",
            to=to_email,
            subject=subject,
            message_id=response.headers.get("X-Message-Id"),
        )
    except httpx.TimeoutException:
        return SendEmailOutput(
            success=False, error="Request timed out while sending email"
        )
    except Exception as exc:
        return SendEmailOutput(success=False, error=str(exc))


@tool(args_schema=SendEmailMultipleRecipientsInput)
@serialize_pydantic_return
async def send_email_multiple_recipients(
    api_key: str,
    to_emails: list[str],
    from_email: str,
    subject: str,
    content: str,
    content_type: str = "text/plain",
    from_name: str | None = None,
) -> SendEmailMultipleRecipientsOutput:
    """Send the same email to multiple recipients individually."""
    try:
        personalizations = [{"to": [{"email": email}]} for email in to_emails]
        from_data: dict[str, Any] = {"email": from_email}
        if from_name:
            from_data["name"] = from_name

        payload: dict[str, Any] = {
            "personalizations": personalizations,
            "from": from_data,
            "subject": subject,
            "content": [{"type": content_type, "value": content}],
        }

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API}/mail/send", headers=_headers(api_key), json=payload
            )
        if response.status_code != 202:
            return SendEmailMultipleRecipientsOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        return SendEmailMultipleRecipientsOutput(
            success=True,
            message="Emails sent successfully",
            recipient_count=len(to_emails),
            recipients=to_emails,
            subject=subject,
            message_id=response.headers.get("X-Message-Id"),
        )
    except httpx.TimeoutException:
        return SendEmailMultipleRecipientsOutput(
            success=False, error="Request timed out while sending emails"
        )
    except Exception as exc:
        return SendEmailMultipleRecipientsOutput(success=False, error=str(exc))


@tool(args_schema=AddOrUpdateContactInput)
@serialize_pydantic_return
async def add_or_update_contact(
    api_key: str,
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    address_line_1: str | None = None,
    address_line_2: str | None = None,
    city: str | None = None,
    state_province_region: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    alternate_emails: list[str] | None = None,
    list_ids: list[str] | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> AddOrUpdateContactOutput:
    """Add a new contact or update an existing one (matched by email)."""
    try:
        contact: dict[str, Any] = {"email": email}
        for field, value in [
            ("first_name", first_name),
            ("last_name", last_name),
            ("address_line_1", address_line_1),
            ("address_line_2", address_line_2),
            ("city", city),
            ("state_province_region", state_province_region),
            ("postal_code", postal_code),
            ("country", country),
            ("alternate_emails", alternate_emails),
            ("custom_fields", custom_fields),
        ]:
            if value:
                contact[field] = value

        payload: dict[str, Any] = {"contacts": [contact]}
        if list_ids:
            payload["list_ids"] = list_ids

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_API}/marketing/contacts",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code not in (200, 202):
            return AddOrUpdateContactOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
        return AddOrUpdateContactOutput(
            success=True,
            message="Contact added/updated successfully",
            job_id=data.get("job_id"),
            email=email,
        )
    except httpx.TimeoutException:
        return AddOrUpdateContactOutput(
            success=False, error="Request timed out while adding/updating contact"
        )
    except Exception as exc:
        return AddOrUpdateContactOutput(success=False, error=str(exc))


@tool(args_schema=SearchContactsInput)
@serialize_pydantic_return
async def search_contacts(api_key: str, query: str) -> SearchContactsOutput:
    """Search contacts using SendGrid Query Language (SGQL)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API}/marketing/contacts/search",
                headers=_headers(api_key),
                json={"query": query},
            )
        if response.status_code != 200:
            return SearchContactsOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
        contacts = [
            ContactSummary(
                id=c.get("id"),
                email=c.get("email"),
                first_name=c.get("first_name"),
                last_name=c.get("last_name"),
                created_at=c.get("created_at"),
                updated_at=c.get("updated_at"),
            )
            for c in data.get("result") or []
        ]
        return SearchContactsOutput(
            success=True,
            contacts=contacts,
            count=len(contacts),
            contact_count=data.get("contact_count", len(contacts)),
        )
    except httpx.TimeoutException:
        return SearchContactsOutput(
            success=False, error="Request timed out while searching contacts"
        )
    except Exception as exc:
        return SearchContactsOutput(success=False, error=str(exc))


@tool(args_schema=CreateContactListInput)
@serialize_pydantic_return
async def create_contact_list(api_key: str, name: str) -> CreateContactListOutput:
    """Create a new contact list."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API}/marketing/lists",
                headers=_headers(api_key),
                json={"name": name},
            )
        if response.status_code not in (200, 201):
            return CreateContactListOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
        return CreateContactListOutput(
            success=True,
            id=data.get("id"),
            name=data.get("name"),
            contact_count=data.get("contact_count", 0),
        )
    except httpx.TimeoutException:
        return CreateContactListOutput(
            success=False, error="Request timed out while creating contact list"
        )
    except Exception as exc:
        return CreateContactListOutput(success=False, error=str(exc))


@tool(args_schema=GetContactListsInput)
@serialize_pydantic_return
async def get_contact_lists(
    api_key: str, page_size: int | None = 100
) -> GetContactListsOutput:
    """Return all contact lists with IDs and counts."""
    try:
        params: dict[str, Any] = {"page_size": min(page_size or 100, 1000)}
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API}/marketing/lists",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetContactListsOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
        lists = [
            ListSummary(
                id=lst.get("id"),
                name=lst.get("name"),
                contact_count=lst.get("contact_count", 0),
            )
            for lst in data.get("result") or []
        ]
        return GetContactListsOutput(success=True, lists=lists, count=len(lists))
    except httpx.TimeoutException:
        return GetContactListsOutput(
            success=False, error="Request timed out while getting contact lists"
        )
    except Exception as exc:
        return GetContactListsOutput(success=False, error=str(exc))


@tool(args_schema=RemoveContactFromListInput)
@serialize_pydantic_return
async def remove_contact_from_list(
    api_key: str, list_id: str, contact_ids: list[str]
) -> RemoveContactFromListOutput:
    """Remove contacts from a list (does not delete them)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_API}/marketing/lists/{list_id}/contacts",
                headers=_headers(api_key),
                params={"contact_ids": ",".join(contact_ids)},
            )
        if response.status_code not in (200, 202, 204):
            return RemoveContactFromListOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        return RemoveContactFromListOutput(
            success=True,
            message="Contacts removed from list successfully",
            list_id=list_id,
            contacts_removed=len(contact_ids),
        )
    except httpx.TimeoutException:
        return RemoveContactFromListOutput(
            success=False,
            error="Request timed out while removing contacts from list",
        )
    except Exception as exc:
        return RemoveContactFromListOutput(success=False, error=str(exc))


@tool(args_schema=DeleteContactsInput)
@serialize_pydantic_return
async def delete_contacts(
    api_key: str,
    contact_ids: list[str] | None = None,
    delete_all: bool | None = False,
) -> DeleteContactsOutput:
    """Permanently delete specified contacts (or all)."""
    if delete_all and contact_ids:
        return DeleteContactsOutput(
            success=False, error="Cannot specify both delete_all and contact_ids"
        )
    if not delete_all and not contact_ids:
        return DeleteContactsOutput(
            success=False, error="Must specify either contact_ids or delete_all=True"
        )
    try:
        params: dict[str, Any] = (
            {"delete_all_contacts": "true"}
            if delete_all
            else {"ids": ",".join(contact_ids or [])}
        )
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_API}/marketing/contacts",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code not in (200, 202):
            return DeleteContactsOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
        return DeleteContactsOutput(
            success=True,
            message="Contact deletion initiated",
            job_id=data.get("job_id"),
            deleted_count=len(contact_ids) if contact_ids else "all",
        )
    except httpx.TimeoutException:
        return DeleteContactsOutput(
            success=False, error="Request timed out while deleting contacts"
        )
    except Exception as exc:
        return DeleteContactsOutput(success=False, error=str(exc))


@tool(args_schema=AddEmailToGlobalSuppressionInput)
@serialize_pydantic_return
async def add_email_to_global_suppression(
    api_key: str, recipient_emails: list[str]
) -> AddEmailToGlobalSuppressionOutput:
    """Add emails to the global suppression group."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API}/asm/suppressions/global",
                headers=_headers(api_key),
                json={"recipient_emails": recipient_emails},
            )
        if response.status_code not in (200, 201):
            return AddEmailToGlobalSuppressionOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
        return AddEmailToGlobalSuppressionOutput(
            success=True,
            message="Emails added to global suppression",
            suppressed_emails=data.get("recipient_emails", recipient_emails),
        )
    except httpx.TimeoutException:
        return AddEmailToGlobalSuppressionOutput(
            success=False, error="Request timed out while adding to global suppression"
        )
    except Exception as exc:
        return AddEmailToGlobalSuppressionOutput(success=False, error=str(exc))


@tool(args_schema=DeleteGlobalSuppressionInput)
@serialize_pydantic_return
async def delete_global_suppression(
    api_key: str, email: str
) -> DeleteGlobalSuppressionOutput:
    """Remove an email from the global suppression group."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_API}/asm/suppressions/global/{email}",
                headers=_headers(api_key),
            )
        if response.status_code != 204:
            return DeleteGlobalSuppressionOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        return DeleteGlobalSuppressionOutput(
            success=True,
            message="Email removed from global suppression",
            email=email,
        )
    except httpx.TimeoutException:
        return DeleteGlobalSuppressionOutput(
            success=False,
            error="Request timed out while removing from global suppression",
        )
    except Exception as exc:
        return DeleteGlobalSuppressionOutput(success=False, error=str(exc))


async def _list_suppression_rows(
    api_key: str,
    path: str,
    start_time: int | None,
    end_time: int | None,
    limit: int | None,
) -> tuple[bool, str | None, list[dict[str, Any]]]:
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API}/{path}", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return False, _api_err(response.status_code, response.text), []
        data = response.json() or []
    except httpx.TimeoutException:
        return False, "Request timed out", []
    except Exception as exc:
        return False, str(exc), []
    return True, None, list(data) if isinstance(data, list) else []


@tool(args_schema=ListGlobalSuppressionsInput)
@serialize_pydantic_return
async def list_global_suppressions(
    api_key: str,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int | None = 100,
) -> ListGlobalSuppressionsOutput:
    """List all globally suppressed (unsubscribed) email addresses."""
    ok, err, rows = await _list_suppression_rows(
        api_key, "suppression/unsubscribes", start_time, end_time, limit
    )
    if not ok:
        return ListGlobalSuppressionsOutput(success=False, error=err)
    suppressions = [
        SuppressionRow(email=r.get("email"), created=r.get("created")) for r in rows
    ]
    return ListGlobalSuppressionsOutput(
        success=True, suppressions=suppressions, count=len(suppressions)
    )


@tool(args_schema=GetAllBouncesInput)
@serialize_pydantic_return
async def get_all_bounces(
    api_key: str,
    start_time: int | None = None,
    end_time: int | None = None,
) -> GetAllBouncesOutput:
    """Get all bounced email addresses."""
    ok, err, rows = await _list_suppression_rows(
        api_key, "suppression/bounces", start_time, end_time, None
    )
    if not ok:
        return GetAllBouncesOutput(success=False, error=err)
    bounces = [
        SuppressionRow(
            email=r.get("email"),
            reason=r.get("reason"),
            status=r.get("status"),
            created=r.get("created"),
        )
        for r in rows
    ]
    return GetAllBouncesOutput(success=True, bounces=bounces, count=len(bounces))


async def _delete_with_emails(
    api_key: str,
    path: str,
    emails: list[str] | None,
    delete_all: bool | None,
) -> tuple[bool, str | None]:
    if delete_all and emails:
        return False, "Cannot specify both delete_all and emails"
    payload: dict[str, Any] = (
        {"delete_all": True} if delete_all else {"emails": emails or []}
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                "DELETE",
                f"{_API}/{path}",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 204:
            return False, _api_err(response.status_code, response.text)
    except httpx.TimeoutException:
        return False, "Request timed out"
    except Exception as exc:
        return False, str(exc)
    return True, None


@tool(args_schema=DeleteBouncesInput)
@serialize_pydantic_return
async def delete_bounces(
    api_key: str,
    emails: list[str] | None = None,
    delete_all: bool | None = False,
) -> DeleteBouncesOutput:
    """Remove emails from the bounces list."""
    ok, err = await _delete_with_emails(
        api_key, "suppression/bounces", emails, delete_all
    )
    if not ok:
        return DeleteBouncesOutput(success=False, error=err)
    return DeleteBouncesOutput(
        success=True,
        message="Bounces deleted successfully",
        deleted_count=len(emails) if emails else "all",
    )


@tool(args_schema=ListBlocksInput)
@serialize_pydantic_return
async def list_blocks(
    api_key: str,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int | None = 100,
) -> ListBlocksOutput:
    """List all blocked email addresses."""
    ok, err, rows = await _list_suppression_rows(
        api_key, "suppression/blocks", start_time, end_time, limit
    )
    if not ok:
        return ListBlocksOutput(success=False, error=err)
    blocks = [
        SuppressionRow(
            email=r.get("email"),
            reason=r.get("reason"),
            status=r.get("status"),
            created=r.get("created"),
        )
        for r in rows
    ]
    return ListBlocksOutput(success=True, blocks=blocks, count=len(blocks))


@tool(args_schema=DeleteBlocksInput)
@serialize_pydantic_return
async def delete_blocks(
    api_key: str,
    emails: list[str] | None = None,
    delete_all: bool | None = False,
) -> DeleteBlocksOutput:
    """Remove emails from the blocks list."""
    ok, err = await _delete_with_emails(
        api_key, "suppression/blocks", emails, delete_all
    )
    if not ok:
        return DeleteBlocksOutput(success=False, error=err)
    return DeleteBlocksOutput(
        success=True,
        message="Blocks deleted successfully",
        deleted_count=len(emails) if emails else "all",
    )
