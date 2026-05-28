"""Help Scout LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.help_scout.outputs import (
    AddNoteOutput,
    ConversationDetail,
    CreateCustomerOutput,
    GetConversationDetailsOutput,
    GetConversationThreadsOutput,
    GetTagByIdOutput,
    ListTagsOutput,
    PaginationInfo,
    SendReplyOutput,
    TagItem,
    ThreadItem,
    UpdateConversationOutput,
)

__all__ = [
    "add_note",
    "create_customer",
    "get_conversation_details",
    "get_conversation_threads",
    "get_tag_by_id",
    "list_tags",
    "send_reply",
    "update_conversation",
]

_BASE_URL = "https://api.helpscout.net/v2"
_TIMEOUT = 30.0

_CONVERSATION_OPERATIONS: dict[str, dict[str, str]] = {
    "Change subject": {"op": "replace", "path": "/subject"},
    "Change customer": {"op": "replace", "path": "/primaryCustomer.id"},
    "Publish draft": {"op": "replace", "path": "/draft"},
    "Move conversation to another inbox": {"op": "move", "path": "/mailboxId"},
    "Change conversation status": {"op": "replace", "path": "/status"},
    "Change conversation owner": {"op": "replace", "path": "/assignTo"},
    "Un-assign conversation": {"op": "remove", "path": "/assignTo"},
}


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class AddNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(description="The unique identifier of the conversation")
    text: str = Field(description="The content of the note")
    user_id: str | None = Field(default=None, description="The unique identifier of the user creating the note")


class CreateCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    first_name: str | None = Field(default=None, description="First name of the customer (1-40 characters)")
    last_name: str | None = Field(default=None, description="Last name of the customer (1-40 characters)")
    phone: str | None = Field(default=None, description="Phone number for the new customer")
    photo_url: str | None = Field(default=None, description="URL of the customer's photo (max 200 characters)")
    job_title: str | None = Field(default=None, description="Job title (max 60 characters)")
    photo_type: str | None = Field(default=None, description="Type of photo: unknown, gravatar, twitter, facebook, googleprofile, googleplus, linkedin, instagram")
    background: str | None = Field(default=None, description="Notes field content (max 200 characters)")
    location: str | None = Field(default=None, description="Location of the customer (max 60 characters)")
    organization: str | None = Field(default=None, description="Organization name (max 60 characters)")
    gender: str | None = Field(default=None, description="Gender: male, female, unknown")
    age: str | None = Field(default=None, description="Customer's age")
    emails: list[dict[str, str]] | None = Field(default=None, description="List of email entries with 'type' and 'value' fields")
    phones: list[dict[str, str]] | None = Field(default=None, description="List of phone entries with 'type' and 'value' fields")
    chats: list[dict[str, str]] | None = Field(default=None, description="List of chat entries with 'type' and 'value' fields")
    social_profiles: list[dict[str, str]] | None = Field(default=None, description="List of social profile entries with 'type' and 'value' fields")
    websites: list[dict[str, str]] | None = Field(default=None, description="List of website entries with 'value' field")
    address_city: str | None = Field(default=None, description="City of the customer's address")
    address_state: str | None = Field(default=None, description="State of the customer's address")
    address_postal_code: str | None = Field(default=None, description="Postal code of the customer's address")
    address_country: str | None = Field(default=None, description="ISO 3166 Alpha-2 country code")
    address_lines: list[str] | None = Field(default=None, description="List of address line strings")
    properties: list[dict[str, Any]] | None = Field(default=None, description="List of property entries as JSON objects")


class GetConversationDetailsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(description="The unique identifier of the conversation")
    embed: bool | None = Field(default=None, description="If true, include threads in the response")


class GetConversationThreadsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(description="The unique identifier of the conversation")
    page: int = Field(default=1, description="Page number to retrieve (25 threads per page)")


class GetTagByIdInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    tag_id: str = Field(description="The unique identifier of the tag")


class ListTagsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    page: int = Field(default=1, description="The page number to return")


class SendReplyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(description="The unique identifier of the conversation")
    customer_id: str = Field(description="The unique identifier of the customer")
    text: str = Field(description="The content of the reply")
    draft: bool = Field(default=False, description="If true, a draft reply is created instead of sending")


class UpdateConversationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(description="The unique identifier of the conversation")
    operation: str = Field(description="Operation to perform: Change subject, Change customer, Publish draft, Move conversation to another inbox, Change conversation status, Change conversation owner, Un-assign conversation")
    value: str = Field(description="Value for the operation")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddNoteInput)
@serialize_pydantic_return
async def add_note(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    text: str,
    user_id: str | None = None,
) -> AddNoteOutput:
    """Adds a note to an existing conversation in Help Scout"""
    if not auth_data.get("access_token"):
        return AddNoteOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"text": text}
    if user_id:
        body["user"] = user_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/conversations/{conversation_id}/notes",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return AddNoteOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return AddNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddNoteOutput(success=False, error=f"Call failed: {exc}")
    return AddNoteOutput(success=True, conversation_id=conversation_id)


@tool(args_schema=CreateCustomerInput)
@serialize_pydantic_return
async def create_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    photo_url: str | None = None,
    job_title: str | None = None,
    photo_type: str | None = None,
    background: str | None = None,
    location: str | None = None,
    organization: str | None = None,
    gender: str | None = None,
    age: str | None = None,
    emails: list[dict[str, str]] | None = None,
    phones: list[dict[str, str]] | None = None,
    chats: list[dict[str, str]] | None = None,
    social_profiles: list[dict[str, str]] | None = None,
    websites: list[dict[str, str]] | None = None,
    address_city: str | None = None,
    address_state: str | None = None,
    address_postal_code: str | None = None,
    address_country: str | None = None,
    address_lines: list[str] | None = None,
    properties: list[dict[str, Any]] | None = None,
) -> CreateCustomerOutput:
    """Creates a new customer record in Help Scout"""
    if not auth_data.get("access_token"):
        return CreateCustomerOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if first_name is not None:
        body["firstName"] = first_name
    if last_name is not None:
        body["lastName"] = last_name
    if phone is not None:
        body["phone"] = phone
    if photo_url is not None:
        body["photoUrl"] = photo_url
    if job_title is not None:
        body["jobTitle"] = job_title
    if photo_type is not None:
        body["photoType"] = photo_type
    if background is not None:
        body["background"] = background
    if location is not None:
        body["location"] = location
    if organization is not None:
        body["organization"] = organization
    if gender is not None:
        body["gender"] = gender
    if age is not None:
        body["age"] = age
    if emails is not None:
        body["emails"] = emails
    if phones is not None:
        body["phones"] = phones
    if chats is not None:
        body["chats"] = chats
    if social_profiles is not None:
        body["socialProfiles"] = social_profiles
    if websites is not None:
        body["websites"] = websites
    if properties is not None:
        body["properties"] = properties
    address: dict[str, Any] = {}
    if address_city is not None:
        address["city"] = address_city
    if address_state is not None:
        address["state"] = address_state
    if address_postal_code is not None:
        address["postalCode"] = address_postal_code
    if address_country is not None:
        address["country"] = address_country
    if address_lines is not None:
        address["lines"] = address_lines
    if address:
        body["address"] = address
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/customers",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateCustomerOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return CreateCustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCustomerOutput(success=False, error=f"Call failed: {exc}")
    resource_id = response.headers.get("Resource-Id")
    return CreateCustomerOutput(success=True, customer_id=resource_id)


@tool(args_schema=GetConversationDetailsInput)
@serialize_pydantic_return
async def get_conversation_details(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    embed: bool | None = None,
) -> GetConversationDetailsOutput:
    """Retrieves the details of a specific conversation"""
    if not auth_data.get("access_token"):
        return GetConversationDetailsOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {}
    if embed:
        params["embed"] = "threads"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/conversations/{conversation_id}",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return GetConversationDetailsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetConversationDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetConversationDetailsOutput(success=False, error=f"Call failed: {exc}")
    embedded = data.get("_embedded", {})
    return GetConversationDetailsOutput(
        success=True,
        conversation=ConversationDetail(
            id=data.get("id"),
            number=data.get("number"),
            subject=data.get("subject"),
            status=data.get("status"),
            mailbox_id=data.get("mailboxId"),
            primary_customer=data.get("primaryCustomer"),
            threads=embedded.get("threads", []),
            tags=data.get("tags", []),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            closed_at=data.get("closedAt"),
        ),
    )


@tool(args_schema=GetConversationThreadsInput)
@serialize_pydantic_return
async def get_conversation_threads(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    page: int = 1,
) -> GetConversationThreadsOutput:
    """Retrieves the threads of a specific conversation"""
    if not auth_data.get("access_token"):
        return GetConversationThreadsOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"page": page}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/conversations/{conversation_id}/threads",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return GetConversationThreadsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetConversationThreadsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetConversationThreadsOutput(success=False, error=f"Call failed: {exc}")
    embedded = data.get("_embedded", {})
    raw_threads = embedded.get("threads", [])
    threads = [
        ThreadItem(
            id=t.get("id"),
            type=t.get("type"),
            status=t.get("status"),
            state=t.get("state"),
            body=t.get("body"),
            source=t.get("source"),
            customer=t.get("customer"),
            created_by=t.get("createdBy"),
            assigned_to=t.get("assignedTo"),
            created_at=t.get("createdAt"),
        )
        for t in raw_threads
    ]
    page_info = data.get("page")
    pagination = None
    if page_info:
        pagination = PaginationInfo(
            size=page_info.get("size"),
            total_elements=page_info.get("totalElements"),
            total_pages=page_info.get("totalPages"),
            number=page_info.get("number"),
        )
    return GetConversationThreadsOutput(
        success=True,
        threads=threads,
        pagination=pagination,
    )


@tool(args_schema=GetTagByIdInput)
@serialize_pydantic_return
async def get_tag_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    tag_id: str,
) -> GetTagByIdOutput:
    """Gets a tag by its ID"""
    if not auth_data.get("access_token"):
        return GetTagByIdOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/tags/{tag_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetTagByIdOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetTagByIdOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTagByIdOutput(success=False, error=f"Call failed: {exc}")
    return GetTagByIdOutput(
        success=True,
        tag=TagItem(
            id=data.get("id"),
            name=data.get("name"),
            slug=data.get("slug"),
            color=data.get("color"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            ticket_count=data.get("ticketCount"),
        ),
    )


@tool(args_schema=ListTagsInput)
@serialize_pydantic_return
async def list_tags(
    auth_type: str,
    auth_data: dict[str, Any],
    page: int = 1,
) -> ListTagsOutput:
    """Lists all tags in Help Scout"""
    if not auth_data.get("access_token"):
        return ListTagsOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"page": page}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/tags",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListTagsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListTagsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTagsOutput(success=False, error=f"Call failed: {exc}")
    embedded = data.get("_embedded", {})
    raw_tags = embedded.get("tags", [])
    tags = [
        TagItem(
            id=t.get("id"),
            name=t.get("name"),
            slug=t.get("slug"),
            color=t.get("color"),
            created_at=t.get("createdAt"),
            updated_at=t.get("updatedAt"),
            ticket_count=t.get("ticketCount"),
        )
        for t in raw_tags
    ]
    page_info = data.get("page")
    pagination = None
    if page_info:
        pagination = PaginationInfo(
            size=page_info.get("size"),
            total_elements=page_info.get("totalElements"),
            total_pages=page_info.get("totalPages"),
            number=page_info.get("number"),
        )
    return ListTagsOutput(success=True, tags=tags, pagination=pagination)


@tool(args_schema=SendReplyInput)
@serialize_pydantic_return
async def send_reply(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    customer_id: str,
    text: str,
    draft: bool = False,
) -> SendReplyOutput:
    """Sends a reply to a conversation (sends an actual email to the customer)"""
    if not auth_data.get("access_token"):
        return SendReplyOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {
        "customer": {"id": customer_id},
        "text": text,
        "draft": draft,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/conversations/{conversation_id}/reply",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return SendReplyOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return SendReplyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendReplyOutput(success=False, error=f"Call failed: {exc}")
    return SendReplyOutput(success=True, conversation_id=conversation_id)


@tool(args_schema=UpdateConversationInput)
@serialize_pydantic_return
async def update_conversation(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    operation: str,
    value: str,
) -> UpdateConversationOutput:
    """Updates a conversation using a specified operation"""
    if not auth_data.get("access_token"):
        return UpdateConversationOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    op_config = _CONVERSATION_OPERATIONS.get(operation)
    if not op_config:
        return UpdateConversationOutput(
            success=False,
            error=f"Unknown operation: {operation}. Valid: {', '.join(_CONVERSATION_OPERATIONS.keys())}",
        )
    patch_body: dict[str, Any] = {
        "op": op_config["op"],
        "path": op_config["path"],
        "value": value,
    }
    if operation == "Un-assign conversation":
        patch_body.pop("value", None)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/conversations/{conversation_id}",
                headers=headers,
                json=patch_body,
            )
        if response.status_code not in (200, 204):
            return UpdateConversationOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return UpdateConversationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateConversationOutput(success=False, error=f"Call failed: {exc}")
    return UpdateConversationOutput(success=True, conversation_id=conversation_id)
