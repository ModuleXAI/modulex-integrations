"""Intercom LangChain ``@tool`` functions.

Token-based runtime convention with paired oauth2 + bearer_token
schemas. The local ``_headers`` helper accepts either ``access_token``
(oauth2) or ``token`` (bearer_token) out of ``auth_data`` — same code
path for both schemas. Every request carries the
``Intercom-Version: 2.12`` header.

Three actions internally chain two API calls — preserved verbatim
from the legacy implementation:

- ``upsert_contact``: searches by email, then PUTs the existing row
  or POSTs a new one.
- ``create_note``: GETs ``/me`` to find the current admin's id, then
  POSTs the note attributed to that admin.
- ``send_incoming_message``: GETs the contact to discover whether it
  is a ``user`` or ``lead``, then POSTs the conversation start.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.intercom.outputs import (
    AddTagToContactOutput,
    CreateNoteOutput,
    GetContactOutput,
    GetConversationOutput,
    ListAdminsOutput,
    ListConversationsOutput,
    ListTagsOutput,
    ReplyToConversationOutput,
    SearchContactsOutput,
    SearchConversationsOutput,
    SendIncomingMessageOutput,
    SendMessageToContactOutput,
    UpsertContactOutput,
)

__all__ = [
    "add_tag_to_contact",
    "create_note",
    "get_contact",
    "get_conversation",
    "list_admins",
    "list_conversations",
    "list_tags",
    "reply_to_conversation",
    "search_contacts",
    "search_conversations",
    "send_incoming_message",
    "send_message_to_contact",
    "upsert_contact",
]

_API_BASE = "https://api.intercom.io"
_API_VERSION = "2.12"
_TIMEOUT = 30.0


def _headers(auth_data: dict[str, Any]) -> dict[str, str]:
    token = auth_data.get("access_token") or auth_data.get("token") or ""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Intercom-Version": _API_VERSION,
    }


def _validate(auth_data: dict[str, Any], name: str) -> str | None:
    if not (auth_data.get("access_token") or auth_data.get("token")):
        return (
            f"Intercom access token missing for {name}. "
            "Configure a valid credential."
        )
    return None


def _api_err(action: str, response: httpx.Response) -> str:
    return f"API error in {action}: {response.status_code} - {response.text}"


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (bearer_token)")
    auth_data: dict[str, Any] = Field(description="Auth data carrying access_token/token")


class GetContactInput(_AuthFields):
    contact_id: str = Field(description="Unique identifier for the contact")


class SearchContactsInput(_AuthFields):
    query_field: str = Field(default="email", description="Field to search by")
    query_operator: str = Field(default="=", description="Query operator")
    query_value: str = Field(description="Value to search for")
    per_page: int = Field(default=50, description="Results per page (max 150)")


class UpsertContactInput(_AuthFields):
    email: str = Field(description="The contact's email address")
    role: str | None = Field(default=None, description="'user' or 'lead'")
    external_id: str | None = Field(default=None, description="Your system's ID")
    phone: str | None = Field(default=None, description="Phone number")
    name: str | None = Field(default=None, description="Contact name")
    avatar: str | None = Field(default=None, description="Avatar URL")
    unsubscribed_from_emails: bool | None = Field(
        default=None, description="Email-unsub flag"
    )
    custom_attributes: dict[str, Any] | None = Field(
        default=None, description="Custom attribute dict"
    )


class CreateNoteInput(_AuthFields):
    contact_id: str = Field(description="The contact's unique identifier")
    body: str = Field(description="The note content (HTML supported)")


class AddTagToContactInput(_AuthFields):
    contact_id: str = Field(description="The contact's unique identifier")
    tag_id: str = Field(description="The tag's unique identifier")


class ListTagsInput(_AuthFields):
    pass


class ListAdminsInput(_AuthFields):
    pass


class GetConversationInput(_AuthFields):
    conversation_id: str = Field(description="The conversation's unique identifier")


class ListConversationsInput(_AuthFields):
    per_page: int = Field(default=20, description="Per page (max 150)")
    starting_after: str | None = Field(default=None, description="Pagination cursor")


class SearchConversationsInput(_AuthFields):
    query_field: str = Field(default="created_at", description="Field to search by")
    query_operator: str = Field(default=">", description="Query operator")
    query_value: str = Field(description="Value to search for")
    per_page: int = Field(default=20, description="Per page (max 150)")


class SendIncomingMessageInput(_AuthFields):
    contact_id: str = Field(description="The contact's unique identifier")
    body: str = Field(description="The message content")


class SendMessageToContactInput(_AuthFields):
    from_admin_id: str = Field(description="The admin's unique identifier")
    to_contact_id: str = Field(description="The contact's unique identifier")
    to_type: str = Field(default="user", description="'user' or 'lead'")
    message_type: str = Field(default="in_app", description="'in_app' or 'email'")
    subject: str = Field(description="Subject/title of the message")
    body: str = Field(description="Message content (HTML and plaintext supported)")
    template: str = Field(default="personal", description="'plain' or 'personal'")


class ReplyToConversationInput(_AuthFields):
    conversation_id: str = Field(description="The conversation's unique identifier")
    reply_type: str = Field(description="'user' or 'admin'")
    message_type: str = Field(default="comment", description="'comment' or 'note'")
    body: str = Field(description="The reply content")
    admin_id: str | None = Field(default=None, description="Admin ID for admin replies")
    intercom_user_id: str | None = Field(default=None, description="User ID for user replies")
    attachment_urls: list[str] | None = Field(
        default=None, description="Image URLs to attach (max 10)"
    )


# --- Tools -----------------------------------------------------------------


@tool(args_schema=GetContactInput)
@serialize_pydantic_return
async def get_contact(
    auth_type: str, auth_data: dict[str, Any], contact_id: str
) -> GetContactOutput:
    """Get a contact by their unique Intercom ID."""
    err = _validate(auth_data, "get_contact")
    if err:
        return GetContactOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/contacts/{contact_id}", headers=_headers(auth_data)
            )
        if response.status_code != 200:
            return GetContactOutput(success=False, error=_api_err("get_contact", response))
        body = response.json()
    except Exception as exc:
        return GetContactOutput(success=False, error=f"get_contact failed: {exc}")

    return GetContactOutput(success=True, result=body)


@tool(args_schema=SearchContactsInput)
@serialize_pydantic_return
async def search_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    query_value: str,
    query_field: str = "email",
    query_operator: str = "=",
    per_page: int = 50,
) -> SearchContactsOutput:
    """Search Intercom contacts by field+operator+value."""
    err = _validate(auth_data, "search_contacts")
    if err:
        return SearchContactsOutput(success=False, error=err)

    payload = {
        "query": {
            "field": query_field,
            "operator": query_operator,
            "value": query_value,
        },
        "pagination": {"per_page": min(per_page, 150)},
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/contacts/search",
                headers=_headers(auth_data),
                json=payload,
            )
        if response.status_code != 200:
            return SearchContactsOutput(
                success=False, error=_api_err("search_contacts", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return SearchContactsOutput(success=False, error=f"search_contacts failed: {exc}")

    return SearchContactsOutput(
        success=True,
        contacts=body.get("data") or [],
        total_count=body.get("total_count", 0),
        pages=body.get("pages"),
    )


@tool(args_schema=UpsertContactInput)
@serialize_pydantic_return
async def upsert_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    email: str,
    role: str | None = None,
    external_id: str | None = None,
    phone: str | None = None,
    name: str | None = None,
    avatar: str | None = None,
    unsubscribed_from_emails: bool | None = None,
    custom_attributes: dict[str, Any] | None = None,
) -> UpsertContactOutput:
    """Create or update a contact by email (two-call workflow)."""
    err = _validate(auth_data, "upsert_contact")
    if err:
        return UpsertContactOutput(success=False, error=err)

    body: dict[str, Any] = {"email": email}
    if role:
        body["role"] = role
    if external_id:
        body["external_id"] = external_id
    if phone:
        body["phone"] = phone
    if name:
        body["name"] = name
    if avatar:
        body["avatar"] = avatar
    if unsubscribed_from_emails is not None:
        body["unsubscribed_from_emails"] = unsubscribed_from_emails
    if custom_attributes:
        body["custom_attributes"] = custom_attributes

    headers = _headers(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            search = await client.post(
                f"{_API_BASE}/contacts/search",
                headers=headers,
                json={
                    "query": {
                        "operator": "AND",
                        "value": [
                            {"field": "email", "operator": "=", "value": email}
                        ],
                    },
                    "pagination": {"per_page": 1},
                },
            )
            existing = (search.json() or {}).get("data") or []

            if existing:
                contact_id = existing[0].get("id")
                response = await client.put(
                    f"{_API_BASE}/contacts/{contact_id}",
                    headers=headers,
                    json=body,
                )
                action_type = "updated"
            else:
                response = await client.post(
                    f"{_API_BASE}/contacts", headers=headers, json=body
                )
                action_type = "created"

        if response.status_code not in (200, 201):
            return UpsertContactOutput(
                success=False, error=_api_err("upsert_contact", response)
            )
        contact = response.json()
    except Exception as exc:
        return UpsertContactOutput(success=False, error=f"upsert_contact failed: {exc}")

    return UpsertContactOutput(success=True, action_type=action_type, contact=contact)


@tool(args_schema=CreateNoteInput)
@serialize_pydantic_return
async def create_note(
    auth_type: str, auth_data: dict[str, Any], contact_id: str, body: str
) -> CreateNoteOutput:
    """Create a note on a contact (auto-attributes to /me admin)."""
    err = _validate(auth_data, "create_note")
    if err:
        return CreateNoteOutput(success=False, error=err)

    headers = _headers(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            me = await client.get(f"{_API_BASE}/me", headers=headers)
            if me.status_code != 200:
                return CreateNoteOutput(
                    success=False,
                    error=f"create_note failed to fetch admin: {me.status_code}",
                )
            admin_id = (me.json() or {}).get("id")

            response = await client.post(
                f"{_API_BASE}/contacts/{contact_id}/notes",
                headers=headers,
                json={"body": body, "admin_id": admin_id},
            )
        if response.status_code not in (200, 201):
            return CreateNoteOutput(success=False, error=_api_err("create_note", response))
        result = response.json()
    except Exception as exc:
        return CreateNoteOutput(success=False, error=f"create_note failed: {exc}")

    return CreateNoteOutput(success=True, result=result)


@tool(args_schema=AddTagToContactInput)
@serialize_pydantic_return
async def add_tag_to_contact(
    auth_type: str, auth_data: dict[str, Any], contact_id: str, tag_id: str
) -> AddTagToContactOutput:
    """Add a tag to a contact."""
    err = _validate(auth_data, "add_tag_to_contact")
    if err:
        return AddTagToContactOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/contacts/{contact_id}/tags",
                headers=_headers(auth_data),
                json={"id": tag_id},
            )
        if response.status_code not in (200, 201):
            return AddTagToContactOutput(
                success=False, error=_api_err("add_tag_to_contact", response)
            )
        result = response.json()
    except Exception as exc:
        return AddTagToContactOutput(
            success=False, error=f"add_tag_to_contact failed: {exc}"
        )

    return AddTagToContactOutput(success=True, result=result)


@tool(args_schema=ListTagsInput)
@serialize_pydantic_return
async def list_tags(auth_type: str, auth_data: dict[str, Any]) -> ListTagsOutput:
    """List all tags in the Intercom workspace."""
    err = _validate(auth_data, "list_tags")
    if err:
        return ListTagsOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/tags", headers=_headers(auth_data)
            )
        if response.status_code != 200:
            return ListTagsOutput(success=False, error=_api_err("list_tags", response))
        result = response.json()
    except Exception as exc:
        return ListTagsOutput(success=False, error=f"list_tags failed: {exc}")

    return ListTagsOutput(success=True, result=result)


@tool(args_schema=ListAdminsInput)
@serialize_pydantic_return
async def list_admins(auth_type: str, auth_data: dict[str, Any]) -> ListAdminsOutput:
    """List all admins/teammates in the Intercom workspace."""
    err = _validate(auth_data, "list_admins")
    if err:
        return ListAdminsOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/admins", headers=_headers(auth_data)
            )
        if response.status_code != 200:
            return ListAdminsOutput(success=False, error=_api_err("list_admins", response))
        result = response.json()
    except Exception as exc:
        return ListAdminsOutput(success=False, error=f"list_admins failed: {exc}")

    return ListAdminsOutput(success=True, result=result)


@tool(args_schema=GetConversationInput)
@serialize_pydantic_return
async def get_conversation(
    auth_type: str, auth_data: dict[str, Any], conversation_id: str
) -> GetConversationOutput:
    """Get a conversation by its unique ID."""
    err = _validate(auth_data, "get_conversation")
    if err:
        return GetConversationOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/conversations/{conversation_id}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return GetConversationOutput(
                success=False, error=_api_err("get_conversation", response)
            )
        result = response.json()
    except Exception as exc:
        return GetConversationOutput(
            success=False, error=f"get_conversation failed: {exc}"
        )

    return GetConversationOutput(success=True, result=result)


@tool(args_schema=ListConversationsInput)
@serialize_pydantic_return
async def list_conversations(
    auth_type: str,
    auth_data: dict[str, Any],
    per_page: int = 20,
    starting_after: str | None = None,
) -> ListConversationsOutput:
    """List Intercom conversations with cursor pagination."""
    err = _validate(auth_data, "list_conversations")
    if err:
        return ListConversationsOutput(success=False, error=err)

    params: dict[str, Any] = {"per_page": min(per_page, 150)}
    if starting_after:
        params["starting_after"] = starting_after

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/conversations",
                headers=_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return ListConversationsOutput(
                success=False, error=_api_err("list_conversations", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return ListConversationsOutput(
            success=False, error=f"list_conversations failed: {exc}"
        )

    return ListConversationsOutput(
        success=True,
        conversations=body.get("conversations") or [],
        pages=body.get("pages"),
    )


@tool(args_schema=SearchConversationsInput)
@serialize_pydantic_return
async def search_conversations(
    auth_type: str,
    auth_data: dict[str, Any],
    query_value: str,
    query_field: str = "created_at",
    query_operator: str = ">",
    per_page: int = 20,
) -> SearchConversationsOutput:
    """Search Intercom conversations by field+operator+value."""
    err = _validate(auth_data, "search_conversations")
    if err:
        return SearchConversationsOutput(success=False, error=err)

    payload = {
        "query": {
            "field": query_field,
            "operator": query_operator,
            "value": query_value,
        },
        "pagination": {"per_page": min(per_page, 150)},
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/conversations/search",
                headers=_headers(auth_data),
                json=payload,
            )
        if response.status_code != 200:
            return SearchConversationsOutput(
                success=False, error=_api_err("search_conversations", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return SearchConversationsOutput(
            success=False, error=f"search_conversations failed: {exc}"
        )

    return SearchConversationsOutput(
        success=True,
        conversations=body.get("conversations") or [],
        total_count=body.get("total_count", 0),
        pages=body.get("pages"),
    )


@tool(args_schema=SendIncomingMessageInput)
@serialize_pydantic_return
async def send_incoming_message(
    auth_type: str, auth_data: dict[str, Any], contact_id: str, body: str
) -> SendIncomingMessageOutput:
    """Send a user-initiated message (auto-detects user vs lead role)."""
    err = _validate(auth_data, "send_incoming_message")
    if err:
        return SendIncomingMessageOutput(success=False, error=err)

    headers = _headers(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            contact = await client.get(
                f"{_API_BASE}/contacts/{contact_id}", headers=headers
            )
            if contact.status_code != 200:
                return SendIncomingMessageOutput(
                    success=False,
                    error=(
                        f"send_incoming_message failed to fetch contact: "
                        f"{contact.status_code}"
                    ),
                )
            role = (contact.json() or {}).get("role", "user")

            response = await client.post(
                f"{_API_BASE}/conversations",
                headers=headers,
                json={"from": {"type": role, "id": contact_id}, "body": body},
            )
        if response.status_code not in (200, 201):
            return SendIncomingMessageOutput(
                success=False, error=_api_err("send_incoming_message", response)
            )
        result = response.json()
    except Exception as exc:
        return SendIncomingMessageOutput(
            success=False, error=f"send_incoming_message failed: {exc}"
        )

    return SendIncomingMessageOutput(success=True, result=result)


@tool(args_schema=SendMessageToContactInput)
@serialize_pydantic_return
async def send_message_to_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    from_admin_id: str,
    to_contact_id: str,
    subject: str,
    body: str,
    to_type: str = "user",
    message_type: str = "in_app",
    template: str = "personal",
) -> SendMessageToContactOutput:
    """Send an admin-initiated message to a contact."""
    err = _validate(auth_data, "send_message_to_contact")
    if err:
        return SendMessageToContactOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/messages",
                headers=_headers(auth_data),
                json={
                    "message_type": message_type,
                    "subject": subject,
                    "body": body,
                    "template": template,
                    "from": {"type": "admin", "id": from_admin_id},
                    "to": {"type": to_type, "id": to_contact_id},
                },
            )
        if response.status_code not in (200, 201):
            return SendMessageToContactOutput(
                success=False, error=_api_err("send_message_to_contact", response)
            )
        result = response.json()
    except Exception as exc:
        return SendMessageToContactOutput(
            success=False, error=f"send_message_to_contact failed: {exc}"
        )

    return SendMessageToContactOutput(success=True, result=result)


@tool(args_schema=ReplyToConversationInput)
@serialize_pydantic_return
async def reply_to_conversation(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    reply_type: str,
    body: str,
    message_type: str = "comment",
    admin_id: str | None = None,
    intercom_user_id: str | None = None,
    attachment_urls: list[str] | None = None,
) -> ReplyToConversationOutput:
    """Reply to an existing Intercom conversation."""
    err = _validate(auth_data, "reply_to_conversation")
    if err:
        return ReplyToConversationOutput(success=False, error=err)

    payload: dict[str, Any] = {
        "body": body,
        "message_type": message_type,
        "type": reply_type,
    }
    if reply_type == "admin" and admin_id:
        payload["admin_id"] = admin_id
    elif reply_type == "user" and intercom_user_id:
        payload["intercom_user_id"] = intercom_user_id
    if attachment_urls:
        # Max 10 attachments per Intercom limit.
        payload["attachment_urls"] = attachment_urls[:10]

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/conversations/{conversation_id}/parts",
                headers=_headers(auth_data),
                json=payload,
            )
        if response.status_code not in (200, 201):
            return ReplyToConversationOutput(
                success=False, error=_api_err("reply_to_conversation", response)
            )
        result = response.json()
    except Exception as exc:
        return ReplyToConversationOutput(
            success=False, error=f"reply_to_conversation failed: {exc}"
        )

    return ReplyToConversationOutput(success=True, result=result)
