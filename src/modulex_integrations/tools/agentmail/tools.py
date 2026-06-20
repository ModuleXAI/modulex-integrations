"""AgentMail LangChain ``@tool`` functions.

Twenty-one async tools wrapping the AgentMail REST API
(``https://api.agentmail.to/v0``). The calling convention is
*key-based*: the modulex ``ToolExecutor`` injects an ``api_key: str``
directly (resolved from the user's credential), not an
``auth_type``/``auth_data`` pair. The key is sent as
``Authorization: Bearer <api_key>``.

Error model: every call is guarded so non-2xx HTTP responses, timeouts,
and unexpected exceptions return the typed output with ``success=False``
+ ``error`` instead of raising. Responses are parsed permissively with
``.get()``.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.agentmail.outputs import (
    CreateDraftOutput,
    CreateInboxOutput,
    DeleteDraftOutput,
    DeleteInboxOutput,
    DeleteThreadOutput,
    DraftSummary,
    ForwardMessageOutput,
    GetDraftOutput,
    GetInboxOutput,
    GetMessageOutput,
    GetThreadOutput,
    InboxSummary,
    ListDraftsOutput,
    ListInboxesOutput,
    ListMessagesOutput,
    ListThreadsOutput,
    MessageSummary,
    ReplyMessageOutput,
    SendDraftOutput,
    SendMessageOutput,
    ThreadMessage,
    ThreadSummary,
    UpdateDraftOutput,
    UpdateInboxOutput,
    UpdateMessageOutput,
    UpdateThreadOutput,
)

__all__ = [
    "create_draft",
    "create_inbox",
    "delete_draft",
    "delete_inbox",
    "delete_thread",
    "forward_message",
    "get_draft",
    "get_inbox",
    "get_message",
    "get_thread",
    "list_drafts",
    "list_inboxes",
    "list_messages",
    "list_threads",
    "reply_message",
    "send_draft",
    "send_message",
    "update_draft",
    "update_inbox",
    "update_message",
    "update_thread",
]

_API_BASE = "https://api.agentmail.to/v0"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = "AgentMail API key is empty. Please configure a valid AgentMail credential."


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


# --- Input schemas (args_schema for each @tool) ----------------------------


class CreateInboxInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    username: str | None = Field(default=None, description="Username for the inbox email address")
    domain: str | None = Field(default=None, description="Domain for the inbox email address")
    display_name: str | None = Field(default=None, description="Display name for the inbox")


class ListInboxesInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Maximum number of inboxes to return")
    page_token: str | None = Field(
        default=None, description="Pagination token for the next page of results"
    )


class GetInboxInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to retrieve")


class UpdateInboxInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to update")
    display_name: str = Field(description="New display name for the inbox")


class DeleteInboxInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to delete")


class SendMessageInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to send from")
    to: str = Field(description="Recipient email address (comma-separated for multiple)")
    subject: str = Field(description="Email subject line")
    text: str | None = Field(default=None, description="Plain text email body")
    html: str | None = Field(default=None, description="HTML email body")
    cc: str | None = Field(
        default=None, description="CC recipient email addresses (comma-separated)"
    )
    bcc: str | None = Field(
        default=None, description="BCC recipient email addresses (comma-separated)"
    )


class ReplyMessageInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to reply from")
    message_id: str = Field(description="ID of the message to reply to")
    text: str | None = Field(default=None, description="Plain text reply body")
    html: str | None = Field(default=None, description="HTML reply body")
    to: str | None = Field(
        default=None, description="Override recipient email addresses (comma-separated)"
    )
    cc: str | None = Field(default=None, description="CC email addresses (comma-separated)")
    bcc: str | None = Field(default=None, description="BCC email addresses (comma-separated)")
    reply_all: bool = Field(
        default=False, description="Reply to all recipients of the original message"
    )


class ForwardMessageInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the message")
    message_id: str = Field(description="ID of the message to forward")
    to: str = Field(description="Recipient email addresses (comma-separated)")
    subject: str | None = Field(default=None, description="Override subject line")
    text: str | None = Field(default=None, description="Additional plain text to prepend")
    html: str | None = Field(default=None, description="Additional HTML to prepend")
    cc: str | None = Field(
        default=None, description="CC recipient email addresses (comma-separated)"
    )
    bcc: str | None = Field(
        default=None, description="BCC recipient email addresses (comma-separated)"
    )


class ListMessagesInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to list messages from")
    limit: int | None = Field(default=None, description="Maximum number of messages to return")
    page_token: str | None = Field(
        default=None, description="Pagination token for the next page of results"
    )


class GetMessageInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the message")
    message_id: str = Field(description="ID of the message to retrieve")


class UpdateMessageInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the message")
    message_id: str = Field(description="ID of the message to update")
    add_labels: str | None = Field(
        default=None, description="Comma-separated labels to add to the message"
    )
    remove_labels: str | None = Field(
        default=None, description="Comma-separated labels to remove from the message"
    )


class ListThreadsInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to list threads from")
    limit: int | None = Field(default=None, description="Maximum number of threads to return")
    page_token: str | None = Field(
        default=None, description="Pagination token for the next page of results"
    )
    labels: str | None = Field(
        default=None, description="Comma-separated labels to filter threads by"
    )
    before: str | None = Field(
        default=None, description="Filter threads before this ISO 8601 timestamp"
    )
    after: str | None = Field(
        default=None, description="Filter threads after this ISO 8601 timestamp"
    )


class GetThreadInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the thread")
    thread_id: str = Field(description="ID of the thread to retrieve")


class UpdateThreadInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the thread")
    thread_id: str = Field(description="ID of the thread to update")
    add_labels: str | None = Field(
        default=None, description="Comma-separated labels to add to the thread"
    )
    remove_labels: str | None = Field(
        default=None, description="Comma-separated labels to remove from the thread"
    )


class DeleteThreadInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the thread")
    thread_id: str = Field(description="ID of the thread to delete")
    permanent: bool = Field(
        default=False, description="Force permanent deletion instead of moving to trash"
    )


class CreateDraftInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to create the draft in")
    to: str | None = Field(default=None, description="Recipient email addresses (comma-separated)")
    subject: str | None = Field(default=None, description="Draft subject line")
    text: str | None = Field(default=None, description="Plain text draft body")
    html: str | None = Field(default=None, description="HTML draft body")
    cc: str | None = Field(
        default=None, description="CC recipient email addresses (comma-separated)"
    )
    bcc: str | None = Field(
        default=None, description="BCC recipient email addresses (comma-separated)"
    )
    in_reply_to: str | None = Field(default=None, description="ID of message being replied to")
    send_at: str | None = Field(
        default=None, description="ISO 8601 timestamp to schedule sending"
    )


class UpdateDraftInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the draft")
    draft_id: str = Field(description="ID of the draft to update")
    to: str | None = Field(default=None, description="Recipient email addresses (comma-separated)")
    subject: str | None = Field(default=None, description="Draft subject line")
    text: str | None = Field(default=None, description="Plain text draft body")
    html: str | None = Field(default=None, description="HTML draft body")
    cc: str | None = Field(
        default=None, description="CC recipient email addresses (comma-separated)"
    )
    bcc: str | None = Field(
        default=None, description="BCC recipient email addresses (comma-separated)"
    )
    send_at: str | None = Field(
        default=None, description="ISO 8601 timestamp to schedule sending"
    )


class GetDraftInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox the draft belongs to")
    draft_id: str = Field(description="ID of the draft to retrieve")


class ListDraftsInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox to list drafts from")
    limit: int | None = Field(default=None, description="Maximum number of drafts to return")
    page_token: str | None = Field(
        default=None, description="Pagination token for the next page of results"
    )


class DeleteDraftInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the draft")
    draft_id: str = Field(description="ID of the draft to delete")


class SendDraftInput(BaseModel):
    api_key: str = Field(description="AgentMail API key (provided by credential system)")
    inbox_id: str = Field(description="ID of the inbox containing the draft")
    draft_id: str = Field(description="ID of the draft to send")


# --- Inbox @tool functions -------------------------------------------------


@tool(args_schema=CreateInboxInput)
@serialize_pydantic_return
async def create_inbox(
    api_key: str,
    username: str | None = None,
    domain: str | None = None,
    display_name: str | None = None,
) -> CreateInboxOutput:
    """Create a new email inbox with AgentMail."""
    if not api_key or not api_key.strip():
        return CreateInboxOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if username:
        body["username"] = username
    if domain:
        body["domain"] = domain
    if display_name:
        body["display_name"] = display_name

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/inboxes", headers=_headers(api_key), json=body
            )
        if response.status_code not in (200, 201):
            return CreateInboxOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateInboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateInboxOutput(success=False, error=f"Create inbox failed: {exc}")

    return CreateInboxOutput(
        success=True,
        inbox_id=data.get("inbox_id"),
        email=data.get("email"),
        display_name=data.get("display_name"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


@tool(args_schema=ListInboxesInput)
@serialize_pydantic_return
async def list_inboxes(
    api_key: str,
    limit: int | None = None,
    page_token: str | None = None,
) -> ListInboxesOutput:
    """List all email inboxes in AgentMail."""
    if not api_key or not api_key.strip():
        return ListInboxesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if page_token:
        params["page_token"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/inboxes", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListInboxesOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListInboxesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListInboxesOutput(success=False, error=f"List inboxes failed: {exc}")

    return ListInboxesOutput(
        success=True,
        inboxes=[
            InboxSummary(
                inbox_id=inbox.get("inbox_id"),
                email=inbox.get("email"),
                display_name=inbox.get("display_name"),
                created_at=inbox.get("created_at"),
                updated_at=inbox.get("updated_at"),
            )
            for inbox in data.get("inboxes") or []
        ],
        count=data.get("count"),
        next_page_token=data.get("next_page_token"),
    )


@tool(args_schema=GetInboxInput)
@serialize_pydantic_return
async def get_inbox(api_key: str, inbox_id: str) -> GetInboxOutput:
    """Get details of a specific email inbox in AgentMail."""
    if not api_key or not api_key.strip():
        return GetInboxOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return GetInboxOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetInboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetInboxOutput(success=False, error=f"Get inbox failed: {exc}")

    return GetInboxOutput(
        success=True,
        inbox_id=data.get("inbox_id"),
        email=data.get("email"),
        display_name=data.get("display_name"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


@tool(args_schema=UpdateInboxInput)
@serialize_pydantic_return
async def update_inbox(api_key: str, inbox_id: str, display_name: str) -> UpdateInboxOutput:
    """Update the display name of an email inbox in AgentMail."""
    if not api_key or not api_key.strip():
        return UpdateInboxOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"display_name": display_name}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return UpdateInboxOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateInboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateInboxOutput(success=False, error=f"Update inbox failed: {exc}")

    return UpdateInboxOutput(
        success=True,
        inbox_id=data.get("inbox_id"),
        email=data.get("email"),
        display_name=data.get("display_name"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


@tool(args_schema=DeleteInboxInput)
@serialize_pydantic_return
async def delete_inbox(api_key: str, inbox_id: str) -> DeleteInboxOutput:
    """Delete an email inbox in AgentMail."""
    if not api_key or not api_key.strip():
        return DeleteInboxOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}", headers=_headers(api_key)
            )
        if response.status_code not in (200, 204):
            return DeleteInboxOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteInboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteInboxOutput(success=False, error=f"Delete inbox failed: {exc}")

    return DeleteInboxOutput(success=True, deleted=True)


# --- Message @tool functions -----------------------------------------------


@tool(args_schema=SendMessageInput)
@serialize_pydantic_return
async def send_message(
    api_key: str,
    inbox_id: str,
    to: str,
    subject: str,
    text: str | None = None,
    html: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
) -> SendMessageOutput:
    """Send an email message from an AgentMail inbox."""
    if not api_key or not api_key.strip():
        return SendMessageOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "to": _split_csv(to),
        "subject": subject,
    }
    if text:
        body["text"] = text
    if html:
        body["html"] = html
    if cc:
        body["cc"] = _split_csv(cc)
    if bcc:
        body["bcc"] = _split_csv(bcc)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/messages/send",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return SendMessageOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendMessageOutput(success=False, error=f"Send message failed: {exc}")

    return SendMessageOutput(
        success=True,
        thread_id=data.get("thread_id"),
        message_id=data.get("message_id"),
        subject=subject,
        to=to,
    )


@tool(args_schema=ReplyMessageInput)
@serialize_pydantic_return
async def reply_message(
    api_key: str,
    inbox_id: str,
    message_id: str,
    text: str | None = None,
    html: str | None = None,
    to: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
    reply_all: bool = False,
) -> ReplyMessageOutput:
    """Reply to an existing email message in AgentMail."""
    if not api_key or not api_key.strip():
        return ReplyMessageOutput(success=False, error=_EMPTY_KEY_ERROR)

    endpoint = "reply-all" if reply_all else "reply"
    body: dict[str, Any] = {}
    if text:
        body["text"] = text
    if html:
        body["html"] = html
    # The /reply-all endpoint auto-determines recipients; only /reply accepts to/cc/bcc.
    if not reply_all:
        if to:
            body["to"] = _split_csv(to)
        if cc:
            body["cc"] = _split_csv(cc)
        if bcc:
            body["bcc"] = _split_csv(bcc)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/messages/{message_id.strip()}/{endpoint}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return ReplyMessageOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ReplyMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ReplyMessageOutput(success=False, error=f"Reply message failed: {exc}")

    return ReplyMessageOutput(
        success=True,
        message_id=data.get("message_id"),
        thread_id=data.get("thread_id"),
    )


@tool(args_schema=ForwardMessageInput)
@serialize_pydantic_return
async def forward_message(
    api_key: str,
    inbox_id: str,
    message_id: str,
    to: str,
    subject: str | None = None,
    text: str | None = None,
    html: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
) -> ForwardMessageOutput:
    """Forward an email message to new recipients in AgentMail."""
    if not api_key or not api_key.strip():
        return ForwardMessageOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"to": _split_csv(to)}
    if subject:
        body["subject"] = subject
    if text:
        body["text"] = text
    if html:
        body["html"] = html
    if cc:
        body["cc"] = _split_csv(cc)
    if bcc:
        body["bcc"] = _split_csv(bcc)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/messages/{message_id.strip()}/forward",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return ForwardMessageOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ForwardMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ForwardMessageOutput(success=False, error=f"Forward message failed: {exc}")

    return ForwardMessageOutput(
        success=True,
        message_id=data.get("message_id"),
        thread_id=data.get("thread_id"),
    )


@tool(args_schema=ListMessagesInput)
@serialize_pydantic_return
async def list_messages(
    api_key: str,
    inbox_id: str,
    limit: int | None = None,
    page_token: str | None = None,
) -> ListMessagesOutput:
    """List messages in an inbox in AgentMail."""
    if not api_key or not api_key.strip():
        return ListMessagesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if page_token:
        params["page_token"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/messages",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListMessagesOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListMessagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMessagesOutput(success=False, error=f"List messages failed: {exc}")

    return ListMessagesOutput(
        success=True,
        messages=[
            MessageSummary(
                message_id=msg.get("message_id"),
                from_=msg.get("from"),
                to=msg.get("to") or [],
                subject=msg.get("subject"),
                preview=msg.get("preview"),
                timestamp=msg.get("timestamp"),
                created_at=msg.get("created_at"),
            )
            for msg in data.get("messages") or []
        ],
        count=data.get("count"),
        next_page_token=data.get("next_page_token"),
    )


@tool(args_schema=GetMessageInput)
@serialize_pydantic_return
async def get_message(api_key: str, inbox_id: str, message_id: str) -> GetMessageOutput:
    """Get details of a specific email message in AgentMail."""
    if not api_key or not api_key.strip():
        return GetMessageOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/messages/{message_id.strip()}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetMessageOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMessageOutput(success=False, error=f"Get message failed: {exc}")

    return GetMessageOutput(
        success=True,
        message_id=data.get("message_id"),
        thread_id=data.get("thread_id"),
        from_=data.get("from"),
        to=data.get("to") or [],
        cc=data.get("cc") or [],
        bcc=data.get("bcc") or [],
        subject=data.get("subject"),
        text=data.get("text"),
        html=data.get("html"),
        labels=data.get("labels") or [],
        timestamp=data.get("timestamp"),
        created_at=data.get("created_at"),
    )


@tool(args_schema=UpdateMessageInput)
@serialize_pydantic_return
async def update_message(
    api_key: str,
    inbox_id: str,
    message_id: str,
    add_labels: str | None = None,
    remove_labels: str | None = None,
) -> UpdateMessageOutput:
    """Add or remove labels on an email message in AgentMail."""
    if not api_key or not api_key.strip():
        return UpdateMessageOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if add_labels:
        body["add_labels"] = _split_csv(add_labels)
    if remove_labels:
        body["remove_labels"] = _split_csv(remove_labels)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/messages/{message_id.strip()}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return UpdateMessageOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateMessageOutput(success=False, error=f"Update message failed: {exc}")

    return UpdateMessageOutput(
        success=True,
        message_id=data.get("message_id"),
        labels=data.get("labels") or [],
    )


# --- Thread @tool functions ------------------------------------------------


@tool(args_schema=ListThreadsInput)
@serialize_pydantic_return
async def list_threads(
    api_key: str,
    inbox_id: str,
    limit: int | None = None,
    page_token: str | None = None,
    labels: str | None = None,
    before: str | None = None,
    after: str | None = None,
) -> ListThreadsOutput:
    """List email threads in AgentMail."""
    if not api_key or not api_key.strip():
        return ListThreadsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: list[tuple[str, Any]] = []
    if limit is not None:
        params.append(("limit", str(limit)))
    if page_token:
        params.append(("page_token", page_token))
    if labels:
        for label in _split_csv(labels):
            params.append(("labels", label))
    if before:
        params.append(("before", before))
    if after:
        params.append(("after", after))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/threads",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListThreadsOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListThreadsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListThreadsOutput(success=False, error=f"List threads failed: {exc}")

    return ListThreadsOutput(
        success=True,
        threads=[
            ThreadSummary(
                thread_id=thread.get("thread_id"),
                subject=thread.get("subject"),
                senders=thread.get("senders") or [],
                recipients=thread.get("recipients") or [],
                message_count=thread.get("message_count"),
                last_message_at=thread.get("timestamp"),
                created_at=thread.get("created_at"),
                updated_at=thread.get("updated_at"),
            )
            for thread in data.get("threads") or []
        ],
        count=data.get("count"),
        next_page_token=data.get("next_page_token"),
    )


@tool(args_schema=GetThreadInput)
@serialize_pydantic_return
async def get_thread(api_key: str, inbox_id: str, thread_id: str) -> GetThreadOutput:
    """Get details of a specific email thread including messages in AgentMail."""
    if not api_key or not api_key.strip():
        return GetThreadOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/threads/{thread_id.strip()}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetThreadOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetThreadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetThreadOutput(success=False, error=f"Get thread failed: {exc}")

    return GetThreadOutput(
        success=True,
        thread_id=data.get("thread_id"),
        subject=data.get("subject"),
        senders=data.get("senders") or [],
        recipients=data.get("recipients") or [],
        message_count=data.get("message_count"),
        labels=data.get("labels") or [],
        last_message_at=data.get("timestamp"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        messages=[
            ThreadMessage(
                message_id=msg.get("message_id"),
                from_=msg.get("from"),
                to=msg.get("to") or [],
                cc=msg.get("cc") or [],
                bcc=msg.get("bcc") or [],
                subject=msg.get("subject"),
                text=msg.get("text"),
                html=msg.get("html"),
                labels=msg.get("labels") or [],
                timestamp=msg.get("timestamp"),
                created_at=msg.get("created_at"),
            )
            for msg in data.get("messages") or []
        ],
    )


@tool(args_schema=UpdateThreadInput)
@serialize_pydantic_return
async def update_thread(
    api_key: str,
    inbox_id: str,
    thread_id: str,
    add_labels: str | None = None,
    remove_labels: str | None = None,
) -> UpdateThreadOutput:
    """Add or remove labels on an email thread in AgentMail."""
    if not api_key or not api_key.strip():
        return UpdateThreadOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if add_labels:
        body["add_labels"] = _split_csv(add_labels)
    if remove_labels:
        body["remove_labels"] = _split_csv(remove_labels)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/threads/{thread_id.strip()}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return UpdateThreadOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateThreadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateThreadOutput(success=False, error=f"Update thread failed: {exc}")

    return UpdateThreadOutput(
        success=True,
        thread_id=data.get("thread_id"),
        labels=data.get("labels") or [],
    )


@tool(args_schema=DeleteThreadInput)
@serialize_pydantic_return
async def delete_thread(
    api_key: str,
    inbox_id: str,
    thread_id: str,
    permanent: bool = False,
) -> DeleteThreadOutput:
    """Delete an email thread in AgentMail.

    Moves the thread to trash, or permanently deletes it if already in trash.
    """
    if not api_key or not api_key.strip():
        return DeleteThreadOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if permanent:
        params["permanent"] = "true"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/threads/{thread_id.strip()}",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code not in (200, 204):
            return DeleteThreadOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteThreadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteThreadOutput(success=False, error=f"Delete thread failed: {exc}")

    return DeleteThreadOutput(success=True, deleted=True)


# --- Draft @tool functions -------------------------------------------------


@tool(args_schema=CreateDraftInput)
@serialize_pydantic_return
async def create_draft(
    api_key: str,
    inbox_id: str,
    to: str | None = None,
    subject: str | None = None,
    text: str | None = None,
    html: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
    in_reply_to: str | None = None,
    send_at: str | None = None,
) -> CreateDraftOutput:
    """Create a new email draft in AgentMail."""
    if not api_key or not api_key.strip():
        return CreateDraftOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if to:
        body["to"] = _split_csv(to)
    if subject:
        body["subject"] = subject
    if text:
        body["text"] = text
    if html:
        body["html"] = html
    if cc:
        body["cc"] = _split_csv(cc)
    if bcc:
        body["bcc"] = _split_csv(bcc)
    if in_reply_to:
        body["in_reply_to"] = in_reply_to
    if send_at:
        body["send_at"] = send_at

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/drafts",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateDraftOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDraftOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDraftOutput(success=False, error=f"Create draft failed: {exc}")

    return CreateDraftOutput(
        success=True,
        draft_id=data.get("draft_id"),
        inbox_id=data.get("inbox_id"),
        subject=data.get("subject"),
        to=data.get("to") or [],
        cc=data.get("cc") or [],
        bcc=data.get("bcc") or [],
        text=data.get("text"),
        html=data.get("html"),
        preview=data.get("preview"),
        labels=data.get("labels") or [],
        in_reply_to=data.get("in_reply_to"),
        send_status=data.get("send_status"),
        send_at=data.get("send_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


@tool(args_schema=UpdateDraftInput)
@serialize_pydantic_return
async def update_draft(
    api_key: str,
    inbox_id: str,
    draft_id: str,
    to: str | None = None,
    subject: str | None = None,
    text: str | None = None,
    html: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
    send_at: str | None = None,
) -> UpdateDraftOutput:
    """Update an existing email draft in AgentMail."""
    if not api_key or not api_key.strip():
        return UpdateDraftOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if to:
        body["to"] = _split_csv(to)
    if subject:
        body["subject"] = subject
    if text:
        body["text"] = text
    if html:
        body["html"] = html
    if cc:
        body["cc"] = _split_csv(cc)
    if bcc:
        body["bcc"] = _split_csv(bcc)
    if send_at:
        body["send_at"] = send_at

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/drafts/{draft_id.strip()}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return UpdateDraftOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateDraftOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateDraftOutput(success=False, error=f"Update draft failed: {exc}")

    return UpdateDraftOutput(
        success=True,
        draft_id=data.get("draft_id"),
        inbox_id=data.get("inbox_id"),
        subject=data.get("subject"),
        to=data.get("to") or [],
        cc=data.get("cc") or [],
        bcc=data.get("bcc") or [],
        text=data.get("text"),
        html=data.get("html"),
        preview=data.get("preview"),
        labels=data.get("labels") or [],
        in_reply_to=data.get("in_reply_to"),
        send_status=data.get("send_status"),
        send_at=data.get("send_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


@tool(args_schema=GetDraftInput)
@serialize_pydantic_return
async def get_draft(api_key: str, inbox_id: str, draft_id: str) -> GetDraftOutput:
    """Get details of a specific email draft in AgentMail."""
    if not api_key or not api_key.strip():
        return GetDraftOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/drafts/{draft_id.strip()}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetDraftOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetDraftOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDraftOutput(success=False, error=f"Get draft failed: {exc}")

    return GetDraftOutput(
        success=True,
        draft_id=data.get("draft_id"),
        inbox_id=data.get("inbox_id"),
        subject=data.get("subject"),
        to=data.get("to") or [],
        cc=data.get("cc") or [],
        bcc=data.get("bcc") or [],
        text=data.get("text"),
        html=data.get("html"),
        preview=data.get("preview"),
        labels=data.get("labels") or [],
        in_reply_to=data.get("in_reply_to"),
        send_status=data.get("send_status"),
        send_at=data.get("send_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


@tool(args_schema=ListDraftsInput)
@serialize_pydantic_return
async def list_drafts(
    api_key: str,
    inbox_id: str,
    limit: int | None = None,
    page_token: str | None = None,
) -> ListDraftsOutput:
    """List email drafts in an inbox in AgentMail."""
    if not api_key or not api_key.strip():
        return ListDraftsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if page_token:
        params["page_token"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/drafts",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListDraftsOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDraftsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDraftsOutput(success=False, error=f"List drafts failed: {exc}")

    return ListDraftsOutput(
        success=True,
        drafts=[
            DraftSummary(
                draft_id=draft.get("draft_id"),
                inbox_id=draft.get("inbox_id"),
                subject=draft.get("subject"),
                to=draft.get("to") or [],
                cc=draft.get("cc") or [],
                bcc=draft.get("bcc") or [],
                preview=draft.get("preview"),
                send_status=draft.get("send_status"),
                send_at=draft.get("send_at"),
                created_at=draft.get("created_at"),
                updated_at=draft.get("updated_at"),
            )
            for draft in data.get("drafts") or []
        ],
        count=data.get("count"),
        next_page_token=data.get("next_page_token"),
    )


@tool(args_schema=DeleteDraftInput)
@serialize_pydantic_return
async def delete_draft(api_key: str, inbox_id: str, draft_id: str) -> DeleteDraftOutput:
    """Delete an email draft in AgentMail."""
    if not api_key or not api_key.strip():
        return DeleteDraftOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/drafts/{draft_id.strip()}",
                headers=_headers(api_key),
            )
        if response.status_code not in (200, 204):
            return DeleteDraftOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteDraftOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteDraftOutput(success=False, error=f"Delete draft failed: {exc}")

    return DeleteDraftOutput(success=True, deleted=True)


@tool(args_schema=SendDraftInput)
@serialize_pydantic_return
async def send_draft(api_key: str, inbox_id: str, draft_id: str) -> SendDraftOutput:
    """Send an existing email draft in AgentMail."""
    if not api_key or not api_key.strip():
        return SendDraftOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/inboxes/{inbox_id.strip()}/drafts/{draft_id.strip()}/send",
                headers=_headers(api_key),
                json={},
            )
        if response.status_code not in (200, 201):
            return SendDraftOutput(
                success=False,
                error=f"AgentMail API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendDraftOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendDraftOutput(success=False, error=f"Send draft failed: {exc}")

    return SendDraftOutput(
        success=True,
        message_id=data.get("message_id"),
        thread_id=data.get("thread_id"),
    )
