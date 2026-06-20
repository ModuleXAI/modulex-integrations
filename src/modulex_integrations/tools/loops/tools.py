"""Loops LangChain ``@tool`` functions.

Ten async tools wrapping the Loops REST API (``app.loops.so/api/v1``).
The calling convention is the modulex *api_key* style: the runtime
injects ``api_key: str`` directly (resolved from the user's ``api_key``
credential). The API key is presented as ``Authorization: Bearer
<api_key>`` on every request.

Error model: every call is wrapped in a try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions — non-2xx HTTP responses do *not*
raise. Mutating endpoints additionally return a JSON body carrying its
own ``success`` flag; when that flag is false the tool surfaces the
upstream ``message`` as the error.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.loops.outputs import (
    Contact,
    ContactProperty,
    CreateContactOutput,
    CreateContactPropertyOutput,
    DeleteContactOutput,
    FindContactOutput,
    ListContactPropertiesOutput,
    ListMailingListsOutput,
    ListTransactionalEmailsOutput,
    MailingList,
    Pagination,
    SendEventOutput,
    SendTransactionalEmailOutput,
    TransactionalEmail,
    UpdateContactOutput,
)

__all__ = [
    "create_contact",
    "create_contact_property",
    "delete_contact",
    "find_contact",
    "list_contact_properties",
    "list_mailing_lists",
    "list_transactional_emails",
    "send_event",
    "send_transactional_email",
    "update_contact",
]

_BASE_URL = "https://app.loops.so/api/v1"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = "Loops API key is empty. Please configure a valid Loops credential."

# The ``list_contact_properties`` action takes a parameter named ``list``
# (mirroring the upstream query param), which shadows the builtin inside
# that function. Keep a module-level alias for type checks there.
_list = list


# --- Auth + helpers --------------------------------------------------------


def _headers(api_key: str, *, json_body: bool = False) -> dict[str, str]:
    headers: dict[str, str] = {"Authorization": f"Bearer {api_key}"}
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _coerce_object(value: Any) -> Any:
    """Accept a JSON-encoded string or an already-parsed object/array."""
    if isinstance(value, str):
        return json.loads(value)
    return value


# --- Input schemas (args_schema for each @tool) ----------------------------


class CreateContactInput(BaseModel):
    email: str = Field(description="The email address for the new contact")
    api_key: str = Field(description="Loops API key (provided by credential system)")
    first_name: str | None = Field(default=None, description="The contact first name")
    last_name: str | None = Field(default=None, description="The contact last name")
    source: str | None = Field(
        default=None, description='Custom source value replacing the default "API"'
    )
    subscribed: bool | None = Field(
        default=None,
        description="Whether the contact receives campaign emails (defaults to true)",
    )
    user_group: str | None = Field(
        default=None,
        description="Group to segment the contact into (one group per contact)",
    )
    user_id: str | None = Field(
        default=None, description="Unique user identifier from your application"
    )
    mailing_lists: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Mailing list IDs mapped to boolean values "
            "(true to subscribe, false to unsubscribe)"
        ),
    )
    custom_properties: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Custom contact properties as key-value pairs "
            "(string, number, boolean, or date values)"
        ),
    )


class UpdateContactInput(BaseModel):
    api_key: str = Field(description="Loops API key (provided by credential system)")
    email: str | None = Field(
        default=None,
        description="The contact email address (at least one of email or user_id is required)",
    )
    user_id: str | None = Field(
        default=None,
        description="The contact userId (at least one of email or user_id is required)",
    )
    first_name: str | None = Field(default=None, description="The contact first name")
    last_name: str | None = Field(default=None, description="The contact last name")
    source: str | None = Field(
        default=None, description='Custom source value replacing the default "API"'
    )
    subscribed: bool | None = Field(
        default=None,
        description=(
            "Whether the contact receives campaign emails "
            "(sending true re-subscribes unsubscribed contacts)"
        ),
    )
    user_group: str | None = Field(
        default=None,
        description="Group to segment the contact into (one group per contact)",
    )
    mailing_lists: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Mailing list IDs mapped to boolean values "
            "(true to subscribe, false to unsubscribe)"
        ),
    )
    custom_properties: dict[str, Any] | None = Field(
        default=None,
        description="Custom contact properties as key-value pairs (send null to reset a property)",
    )


class FindContactInput(BaseModel):
    api_key: str = Field(description="Loops API key (provided by credential system)")
    email: str | None = Field(
        default=None,
        description=(
            "The contact email address to search for "
            "(at least one of email or user_id is required)"
        ),
    )
    user_id: str | None = Field(
        default=None,
        description=(
            "The contact userId to search for "
            "(at least one of email or user_id is required)"
        ),
    )


class DeleteContactInput(BaseModel):
    api_key: str = Field(description="Loops API key (provided by credential system)")
    email: str | None = Field(
        default=None,
        description=(
            "The email address of the contact to delete "
            "(at least one of email or user_id is required)"
        ),
    )
    user_id: str | None = Field(
        default=None,
        description=(
            "The userId of the contact to delete "
            "(at least one of email or user_id is required)"
        ),
    )


class SendTransactionalEmailInput(BaseModel):
    email: str = Field(description="The email address of the recipient")
    transactional_id: str = Field(
        description="The ID of the transactional email template to send"
    )
    api_key: str = Field(description="Loops API key (provided by credential system)")
    data_variables: dict[str, Any] | None = Field(
        default=None,
        description="Template data variables as key-value pairs (string or number values)",
    )
    add_to_audience: bool | None = Field(
        default=None,
        description=(
            "Whether to create the recipient as a contact if they do not "
            "already exist (default: false)"
        ),
    )
    attachments: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Array of file attachments. Each object must have filename "
            "(string), contentType (MIME type string), and data "
            "(base64-encoded string)."
        ),
    )


class SendEventInput(BaseModel):
    event_name: str = Field(description="The name of the event to trigger")
    api_key: str = Field(description="Loops API key (provided by credential system)")
    email: str | None = Field(
        default=None,
        description=(
            "The email address of the contact "
            "(at least one of email or user_id is required)"
        ),
    )
    user_id: str | None = Field(
        default=None,
        description="The userId of the contact (at least one of email or user_id is required)",
    )
    event_properties: dict[str, Any] | None = Field(
        default=None,
        description="Event data as key-value pairs (string, number, boolean, or date values)",
    )
    mailing_lists: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Mailing list IDs mapped to boolean values "
            "(true to subscribe, false to unsubscribe)"
        ),
    )


class ListMailingListsInput(BaseModel):
    api_key: str = Field(description="Loops API key (provided by credential system)")


class ListTransactionalEmailsInput(BaseModel):
    api_key: str = Field(description="Loops API key (provided by credential system)")
    per_page: str | None = Field(
        default=None, description="Number of results per page (10-50, default: 20)"
    )
    cursor: str | None = Field(
        default=None,
        description="Pagination cursor from a previous response to fetch the next page",
    )


class CreateContactPropertyInput(BaseModel):
    name: str = Field(
        description='The property name in camelCase format (e.g., "favoriteColor")'
    )
    type: str = Field(
        description='The property data type (e.g., "string", "number", "boolean", "date")'
    )
    api_key: str = Field(description="Loops API key (provided by credential system)")


class ListContactPropertiesInput(BaseModel):
    api_key: str = Field(description="Loops API key (provided by credential system)")
    list: str | None = Field(
        default=None,
        description=(
            'Filter type: "all" for all properties (default) or '
            '"custom" for custom properties only'
        ),
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    email: str,
    api_key: str,
    first_name: str | None = None,
    last_name: str | None = None,
    source: str | None = None,
    subscribed: bool | None = None,
    user_group: str | None = None,
    user_id: str | None = None,
    mailing_lists: dict[str, Any] | None = None,
    custom_properties: dict[str, Any] | None = None,
) -> CreateContactOutput:
    """Create a new contact in your Loops audience with an email address and optional
    properties like name, user group, and mailing list subscriptions."""
    if not api_key or not api_key.strip():
        return CreateContactOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    try:
        if custom_properties:
            body.update(_coerce_object(custom_properties))
    except (json.JSONDecodeError, TypeError) as exc:
        return CreateContactOutput(success=False, error=f"Invalid custom_properties JSON: {exc}")

    body["email"] = email.strip()
    if first_name:
        body["firstName"] = first_name.strip()
    if last_name:
        body["lastName"] = last_name.strip()
    if source:
        body["source"] = source.strip()
    if subscribed is not None:
        body["subscribed"] = subscribed
    if user_group:
        body["userGroup"] = user_group.strip()
    if user_id:
        body["userId"] = user_id.strip()
    if mailing_lists:
        try:
            body["mailingLists"] = _coerce_object(mailing_lists)
        except (json.JSONDecodeError, TypeError) as exc:
            return CreateContactOutput(success=False, error=f"Invalid mailing_lists JSON: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/contacts/create",
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return CreateContactOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContactOutput(success=False, error=f"Create contact failed: {exc}")

    if not data.get("success"):
        return CreateContactOutput(
            success=False, error=data.get("message") or "Failed to create contact"
        )
    return CreateContactOutput(success=True, id=data.get("id"))


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    api_key: str,
    email: str | None = None,
    user_id: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    source: str | None = None,
    subscribed: bool | None = None,
    user_group: str | None = None,
    mailing_lists: dict[str, Any] | None = None,
    custom_properties: dict[str, Any] | None = None,
) -> UpdateContactOutput:
    """Update an existing contact in Loops by email or userId. Creates a new contact if
    no match is found (upsert). Can update name, subscription status, user group, mailing
    lists, and custom properties."""
    if not api_key or not api_key.strip():
        return UpdateContactOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not email and not user_id:
        return UpdateContactOutput(
            success=False,
            error="At least one of email or user_id is required to update a contact.",
        )

    body: dict[str, Any] = {}
    try:
        if custom_properties:
            body.update(_coerce_object(custom_properties))
    except (json.JSONDecodeError, TypeError) as exc:
        return UpdateContactOutput(success=False, error=f"Invalid custom_properties JSON: {exc}")

    if email:
        body["email"] = email.strip()
    if user_id:
        body["userId"] = user_id.strip()
    if first_name:
        body["firstName"] = first_name.strip()
    if last_name:
        body["lastName"] = last_name.strip()
    if source:
        body["source"] = source.strip()
    if subscribed is not None:
        body["subscribed"] = subscribed
    if user_group:
        body["userGroup"] = user_group.strip()
    if mailing_lists:
        try:
            body["mailingLists"] = _coerce_object(mailing_lists)
        except (json.JSONDecodeError, TypeError) as exc:
            return UpdateContactOutput(success=False, error=f"Invalid mailing_lists JSON: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/contacts/update",
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return UpdateContactOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateContactOutput(success=False, error=f"Update contact failed: {exc}")

    if not data.get("success"):
        return UpdateContactOutput(
            success=False, error=data.get("message") or "Failed to update contact"
        )
    return UpdateContactOutput(success=True, id=data.get("id"))


@tool(args_schema=FindContactInput)
@serialize_pydantic_return
async def find_contact(
    api_key: str,
    email: str | None = None,
    user_id: str | None = None,
) -> FindContactOutput:
    """Find a contact in Loops by email address or userId. Returns an array of matching
    contacts with all their properties including name, subscription status, user group,
    and mailing lists."""
    if not api_key or not api_key.strip():
        return FindContactOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not email and not user_id:
        return FindContactOutput(
            success=False,
            error="At least one of email or user_id is required to find a contact.",
        )

    params: dict[str, Any] = {}
    if email:
        params["email"] = email.strip()
    else:
        params["userId"] = user_id.strip() if user_id else ""

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/contacts/find",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return FindContactOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return FindContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindContactOutput(success=False, error=f"Find contact failed: {exc}")

    if not isinstance(data, list):
        message = data.get("message") if isinstance(data, dict) else None
        return FindContactOutput(success=False, error=message or "Failed to find contact")

    return FindContactOutput(
        success=True,
        contacts=[
            Contact(
                id=contact.get("id"),
                email=contact.get("email"),
                first_name=contact.get("firstName"),
                last_name=contact.get("lastName"),
                source=contact.get("source"),
                subscribed=contact.get("subscribed"),
                user_group=contact.get("userGroup"),
                user_id=contact.get("userId"),
                mailing_lists=contact.get("mailingLists") or {},
                opt_in_status=contact.get("optInStatus"),
            )
            for contact in data
        ],
    )


@tool(args_schema=DeleteContactInput)
@serialize_pydantic_return
async def delete_contact(
    api_key: str,
    email: str | None = None,
    user_id: str | None = None,
) -> DeleteContactOutput:
    """Delete a contact from Loops by email address or userId. At least one identifier
    must be provided."""
    if not api_key or not api_key.strip():
        return DeleteContactOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not email and not user_id:
        return DeleteContactOutput(
            success=False,
            error="At least one of email or user_id is required to delete a contact.",
        )

    body: dict[str, Any] = {}
    if email:
        body["email"] = email.strip()
    if user_id:
        body["userId"] = user_id.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/contacts/delete",
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return DeleteContactOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteContactOutput(success=False, error=f"Delete contact failed: {exc}")

    if not data.get("success"):
        return DeleteContactOutput(
            success=False, error=data.get("message") or "Failed to delete contact"
        )
    return DeleteContactOutput(success=True, message=data.get("message") or "Contact deleted.")


@tool(args_schema=SendTransactionalEmailInput)
@serialize_pydantic_return
async def send_transactional_email(
    email: str,
    transactional_id: str,
    api_key: str,
    data_variables: dict[str, Any] | None = None,
    add_to_audience: bool | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> SendTransactionalEmailOutput:
    """Send a transactional email to a recipient using a Loops template. Supports dynamic
    data variables for personalization and optionally adds the recipient to your audience."""
    if not api_key or not api_key.strip():
        return SendTransactionalEmailOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "email": email.strip(),
        "transactionalId": transactional_id.strip(),
    }
    if data_variables:
        try:
            body["dataVariables"] = _coerce_object(data_variables)
        except (json.JSONDecodeError, TypeError) as exc:
            return SendTransactionalEmailOutput(
                success=False, error=f"Invalid data_variables JSON: {exc}"
            )
    if add_to_audience is not None:
        body["addToAudience"] = add_to_audience
    if attachments:
        try:
            body["attachments"] = _coerce_object(attachments)
        except (json.JSONDecodeError, TypeError) as exc:
            return SendTransactionalEmailOutput(
                success=False, error=f"Invalid attachments JSON: {exc}"
            )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/transactional",
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return SendTransactionalEmailOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendTransactionalEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendTransactionalEmailOutput(
            success=False, error=f"Send transactional email failed: {exc}"
        )

    if not data.get("success"):
        return SendTransactionalEmailOutput(
            success=False, error=data.get("message") or "Failed to send transactional email"
        )
    return SendTransactionalEmailOutput(success=True)


@tool(args_schema=SendEventInput)
@serialize_pydantic_return
async def send_event(
    event_name: str,
    api_key: str,
    email: str | None = None,
    user_id: str | None = None,
    event_properties: dict[str, Any] | None = None,
    mailing_lists: dict[str, Any] | None = None,
) -> SendEventOutput:
    """Send an event to Loops to trigger automated email sequences for a contact. Identify
    the contact by email or userId and include optional event properties and mailing list
    changes."""
    if not api_key or not api_key.strip():
        return SendEventOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not email and not user_id:
        return SendEventOutput(
            success=False,
            error="At least one of email or user_id is required to send an event.",
        )

    body: dict[str, Any] = {"eventName": event_name.strip()}
    if email:
        body["email"] = email.strip()
    if user_id:
        body["userId"] = user_id.strip()
    if event_properties:
        try:
            body["eventProperties"] = _coerce_object(event_properties)
        except (json.JSONDecodeError, TypeError) as exc:
            return SendEventOutput(success=False, error=f"Invalid event_properties JSON: {exc}")
    if mailing_lists:
        try:
            body["mailingLists"] = _coerce_object(mailing_lists)
        except (json.JSONDecodeError, TypeError) as exc:
            return SendEventOutput(success=False, error=f"Invalid mailing_lists JSON: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/events/send",
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return SendEventOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendEventOutput(success=False, error=f"Send event failed: {exc}")

    if not data.get("success"):
        return SendEventOutput(
            success=False, error=data.get("message") or "Failed to send event"
        )
    return SendEventOutput(success=True)


@tool(args_schema=ListMailingListsInput)
@serialize_pydantic_return
async def list_mailing_lists(api_key: str) -> ListMailingListsOutput:
    """Retrieve all mailing lists from your Loops account. Returns each list with its ID,
    name, description, and public/private status."""
    if not api_key or not api_key.strip():
        return ListMailingListsOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/lists",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return ListMailingListsOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListMailingListsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMailingListsOutput(success=False, error=f"List mailing lists failed: {exc}")

    if not isinstance(data, list):
        message = data.get("message") if isinstance(data, dict) else None
        return ListMailingListsOutput(
            success=False, error=message or "Failed to list mailing lists"
        )

    return ListMailingListsOutput(
        success=True,
        mailing_lists=[
            MailingList(
                id=item.get("id"),
                name=item.get("name"),
                description=item.get("description"),
                is_public=item.get("isPublic"),
            )
            for item in data
        ],
    )


@tool(args_schema=ListTransactionalEmailsInput)
@serialize_pydantic_return
async def list_transactional_emails(
    api_key: str,
    per_page: str | None = None,
    cursor: str | None = None,
) -> ListTransactionalEmailsOutput:
    """Retrieve a list of published transactional email templates from your Loops account.
    Returns each template with its ID, name, last updated timestamp, and data variables."""
    if not api_key or not api_key.strip():
        return ListTransactionalEmailsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if per_page:
        params["perPage"] = per_page
    if cursor:
        params["cursor"] = cursor

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/transactional",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListTransactionalEmailsOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListTransactionalEmailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTransactionalEmailsOutput(
            success=False, error=f"List transactional emails failed: {exc}"
        )

    if isinstance(data, dict):
        emails = data.get("data") or []
        raw_pagination = data.get("pagination") or {}
    elif isinstance(data, list):
        emails = data
        raw_pagination = {}
    else:
        return ListTransactionalEmailsOutput(
            success=False, error="Failed to list transactional emails"
        )

    return ListTransactionalEmailsOutput(
        success=True,
        transactional_emails=[
            TransactionalEmail(
                id=email.get("id"),
                name=email.get("name"),
                last_updated=email.get("lastUpdated") or email.get("updatedAt"),
                data_variables=email.get("dataVariables") or [],
            )
            for email in emails
        ],
        pagination=Pagination(
            total_results=raw_pagination.get("totalResults"),
            returned_results=raw_pagination.get("returnedResults"),
            per_page=raw_pagination.get("perPage"),
            total_pages=raw_pagination.get("totalPages"),
            next_cursor=raw_pagination.get("nextCursor"),
            next_page=raw_pagination.get("nextPage"),
        ),
    )


@tool(args_schema=CreateContactPropertyInput)
@serialize_pydantic_return
async def create_contact_property(
    name: str,
    type: str,
    api_key: str,
) -> CreateContactPropertyOutput:
    """Create a new custom contact property in your Loops account. The property name must
    be in camelCase format."""
    if not api_key or not api_key.strip():
        return CreateContactPropertyOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"name": name, "type": type}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/contacts/properties",
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return CreateContactPropertyOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateContactPropertyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContactPropertyOutput(
            success=False, error=f"Create contact property failed: {exc}"
        )

    if not data.get("success"):
        return CreateContactPropertyOutput(
            success=False, error=data.get("message") or "Failed to create contact property"
        )
    return CreateContactPropertyOutput(success=True)


@tool(args_schema=ListContactPropertiesInput)
@serialize_pydantic_return
async def list_contact_properties(
    api_key: str,
    list: str | None = None,
) -> ListContactPropertiesOutput:
    """Retrieve a list of contact properties from your Loops account. Returns each property
    with its key, label, and data type. Can filter to show all properties or only custom ones."""
    if not api_key or not api_key.strip():
        return ListContactPropertiesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if list:
        params["list"] = list

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/contacts/properties",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListContactPropertiesOutput(
                success=False,
                error=f"Loops API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListContactPropertiesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListContactPropertiesOutput(
            success=False, error=f"List contact properties failed: {exc}"
        )

    if not isinstance(data, _list):
        message = data.get("message") if isinstance(data, dict) else None
        return ListContactPropertiesOutput(
            success=False, error=message or "Failed to list contact properties"
        )

    return ListContactPropertiesOutput(
        success=True,
        properties=[
            ContactProperty(
                key=prop.get("key"),
                label=prop.get("label"),
                type=prop.get("type"),
            )
            for prop in data
        ],
    )
