"""Gmail LangChain ``@tool`` functions.

Pure HTTP integration against Gmail REST v1 (the legacy implementation
also uses raw httpx rather than the Google Python SDK — preserved
verbatim to keep the dependency surface tiny). Token-based runtime
convention with paired oauth2 + bearer_token auth schemas.

Two list-style actions (``search_messages``, ``list_messages``) use an
N+1 metadata-fetch pattern: list message IDs first, then GET each
message in ``metadata`` format to pick up the subject/from/date headers.
Preserved from legacy — the alternative (``history.list``) needs a
different OAuth scope.
"""
from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.gmail.outputs import (
    AddLabelOutput,
    ArchiveMessageOutput,
    CreateDraftOutput,
    DeleteMessageOutput,
    GmailMessageSummary,
    ListLabelsOutput,
    ListMessagesOutput,
    MarkAsReadOutput,
    MarkAsUnreadOutput,
    ReadMessageOutput,
    RemoveLabelOutput,
    SearchMessagesOutput,
    SendMessageOutput,
    UnarchiveMessageOutput,
)

__all__ = [
    "add_label",
    "archive_message",
    "create_draft",
    "delete_message",
    "list_labels",
    "list_messages",
    "mark_as_read",
    "mark_as_unread",
    "read_message",
    "remove_label",
    "search_messages",
    "send_message",
    "unarchive_message",
]

_API_BASE = "https://www.googleapis.com/gmail/v1"
_TIMEOUT = 30.0
_SEND_TIMEOUT = 60.0


def _headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if auth_type == "oauth2":
        token = auth_data.get("access_token")
    elif auth_type == "bearer_token":
        token = auth_data.get("token") or auth_data.get("bearer_token")
    else:
        token = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _validate(auth_data: dict[str, Any], name: str) -> str | None:
    if not (
        auth_data.get("access_token")
        or auth_data.get("token")
        or auth_data.get("bearer_token")
    ):
        return (
            f"Gmail access token missing for {name}. "
            "Configure a valid credential."
        )
    return None


def _build_raw_message(
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    is_html: bool = False,
) -> str:
    """Build a base64url-encoded MIME message for the Gmail API."""
    if is_html:
        message: Any = MIMEMultipart("alternative")
        message.attach(MIMEText(body, "html"))
    else:
        message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc
    return base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")


def _parse_payload(payload: dict[str, Any]) -> tuple[dict[str, str], str]:
    """Pull headers + plaintext body out of a Gmail ``payload`` block."""
    headers = {
        str(h.get("name", "")).lower(): str(h.get("value", ""))
        for h in payload.get("headers") or []
    }

    body = ""
    parts = payload.get("parts")
    if isinstance(parts, list) and parts:
        for part in parts:
            mime = part.get("mimeType")
            data = (part.get("body") or {}).get("data") or ""
            if mime == "text/plain" and data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                break
            if mime == "text/html" and data and not body:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    else:
        data = (payload.get("body") or {}).get("data") or ""
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return headers, body


def _api_err(action: str, response: httpx.Response) -> str:
    return f"{action} failed: {response.status_code} - {response.text}"


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2 or bearer_token)")
    auth_data: dict[str, Any] = Field(description="Auth data carrying access_token/token")


class SendMessageInput(_AuthFields):
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    cc: str | None = Field(default=None, description="CC recipients (comma-separated)")
    bcc: str | None = Field(default=None, description="BCC recipients (comma-separated)")
    is_html: bool = Field(default=False, description="Whether body is HTML")


class ReadMessageInput(_AuthFields):
    message_id: str = Field(description="The ID of the message to read")
    format: str = Field(default="full", description="'minimal', 'full', 'raw', or 'metadata'")


class SearchMessagesInput(_AuthFields):
    query: str = Field(description="Gmail search query")
    max_results: int = Field(default=10, description="Maximum messages (max 500)")
    page_token: str | None = Field(default=None, description="Pagination token")
    label_ids: list[str] | None = Field(default=None, description="Filter by label IDs")


class ListMessagesInput(_AuthFields):
    label_ids: list[str] = Field(default=["INBOX"], description="Label IDs to list from")
    query: str | None = Field(default=None, description="Optional Gmail query filter")
    max_results: int = Field(default=20, description="Maximum messages to return")
    page_token: str | None = Field(default=None, description="Pagination token")
    include_spam_trash: bool = Field(default=False, description="Include SPAM/TRASH")


class CreateDraftInput(_AuthFields):
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    cc: str | None = Field(default=None, description="CC recipients")
    bcc: str | None = Field(default=None, description="BCC recipients")
    is_html: bool = Field(default=False, description="Whether body is HTML")


class _MessageIdOnly(_AuthFields):
    message_id: str = Field(description="The ID of the message")


class AddLabelInput(_AuthFields):
    message_id: str = Field(description="The ID of the message")
    label_ids: list[str] = Field(description="Label IDs to add")


class RemoveLabelInput(_AuthFields):
    message_id: str = Field(description="The ID of the message")
    label_ids: list[str] = Field(description="Label IDs to remove")


class ListLabelsInput(_AuthFields):
    pass


# --- Tools -----------------------------------------------------------------


@tool(args_schema=SendMessageInput)
@serialize_pydantic_return
async def send_message(
    auth_type: str,
    auth_data: dict[str, Any],
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    is_html: bool = False,
) -> SendMessageOutput:
    """Send a new email via Gmail."""
    err = _validate(auth_data, "send_message")
    if err:
        return SendMessageOutput(success=False, error=err)

    raw = _build_raw_message(to, subject, body, cc, bcc, is_html)
    try:
        async with httpx.AsyncClient(timeout=_SEND_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/users/me/messages/send",
                headers=_headers(auth_type, auth_data),
                json={"raw": raw},
            )
        if response.status_code != 200:
            return SendMessageOutput(
                success=False, error=_api_err("send_message", response)
            )
        data = response.json() or {}
    except Exception as exc:
        return SendMessageOutput(success=False, error=f"send_message failed: {exc}")

    return SendMessageOutput(
        success=True,
        id=data.get("id"),
        thread_id=data.get("threadId"),
        label_ids=data.get("labelIds") or [],
    )


@tool(args_schema=ReadMessageInput)
@serialize_pydantic_return
async def read_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    format: str = "full",
) -> ReadMessageOutput:
    """Read a specific email by ID."""
    err = _validate(auth_data, "read_message")
    if err:
        return ReadMessageOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/users/me/messages/{message_id}",
                headers=_headers(auth_type, auth_data),
                params={"format": format},
            )
        if response.status_code != 200:
            return ReadMessageOutput(
                success=False, error=_api_err("read_message", response)
            )
        data = response.json() or {}
    except Exception as exc:
        return ReadMessageOutput(success=False, error=f"read_message failed: {exc}")

    payload = data.get("payload") or {}
    headers, body = _parse_payload(payload)
    return ReadMessageOutput(
        success=True,
        id=data.get("id"),
        thread_id=data.get("threadId"),
        label_ids=data.get("labelIds") or [],
        snippet=data.get("snippet"),
        subject=headers.get("subject"),
        from_address=headers.get("from"),
        to=headers.get("to"),
        cc=headers.get("cc"),
        date=headers.get("date"),
        body=body,
        internal_date=data.get("internalDate"),
        size_estimate=data.get("sizeEstimate"),
    )


async def _fetch_summary(
    client: httpx.AsyncClient,
    msg: dict[str, Any],
    headers: dict[str, str],
) -> GmailMessageSummary:
    """Fetch metadata for one message and turn it into a summary row."""
    msg_id = msg.get("id")
    if not msg_id:
        return GmailMessageSummary()
    try:
        response = await client.get(
            f"{_API_BASE}/users/me/messages/{msg_id}",
            headers=headers,
            params={
                "format": "metadata",
                "metadataHeaders": ["Subject", "From", "Date"],
            },
        )
        if response.status_code != 200:
            return GmailMessageSummary(id=msg_id, thread_id=msg.get("threadId"))
        body = response.json() or {}
    except Exception:
        return GmailMessageSummary(id=msg_id, thread_id=msg.get("threadId"))

    msg_headers = {
        str(h.get("name", "")).lower(): str(h.get("value", ""))
        for h in (body.get("payload") or {}).get("headers") or []
    }
    return GmailMessageSummary(
        id=msg_id,
        thread_id=msg.get("threadId"),
        snippet=body.get("snippet"),
        subject=msg_headers.get("subject"),
        from_address=msg_headers.get("from"),
        date=msg_headers.get("date"),
        label_ids=body.get("labelIds") or [],
    )


@tool(args_schema=SearchMessagesInput)
@serialize_pydantic_return
async def search_messages(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    max_results: int = 10,
    page_token: str | None = None,
    label_ids: list[str] | None = None,
) -> SearchMessagesOutput:
    """Search Gmail messages using Gmail's query syntax (N+1 metadata fetch)."""
    err = _validate(auth_data, "search_messages")
    if err:
        return SearchMessagesOutput(success=False, error=err)

    params: dict[str, Any] = {"q": query, "maxResults": min(max_results, 500)}
    if page_token:
        params["pageToken"] = page_token
    if label_ids:
        params["labelIds"] = label_ids

    headers = _headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/users/me/messages", headers=headers, params=params
            )
            if response.status_code != 200:
                return SearchMessagesOutput(
                    success=False, error=_api_err("search_messages", response)
                )
            data = response.json() or {}
            raw_messages = data.get("messages") or []
            summaries = [
                await _fetch_summary(client, m, headers)
                for m in raw_messages[:max_results]
            ]
    except Exception as exc:
        return SearchMessagesOutput(
            success=False, error=f"search_messages failed: {exc}"
        )

    return SearchMessagesOutput(
        success=True,
        messages=summaries,
        total=len(summaries),
        result_size_estimate=data.get("resultSizeEstimate"),
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=ListMessagesInput)
@serialize_pydantic_return
async def list_messages(
    auth_type: str,
    auth_data: dict[str, Any],
    label_ids: list[str] | None = None,
    query: str | None = None,
    max_results: int = 20,
    page_token: str | None = None,
    include_spam_trash: bool = False,
) -> ListMessagesOutput:
    """List messages from one or more labels (N+1 metadata fetch)."""
    err = _validate(auth_data, "list_messages")
    if err:
        return ListMessagesOutput(success=False, error=err)

    params: dict[str, Any] = {
        "labelIds": label_ids or ["INBOX"],
        "maxResults": min(max_results, 500),
        "includeSpamTrash": include_spam_trash,
    }
    if query:
        params["q"] = query
    if page_token:
        params["pageToken"] = page_token

    headers = _headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/users/me/messages", headers=headers, params=params
            )
            if response.status_code != 200:
                return ListMessagesOutput(
                    success=False, error=_api_err("list_messages", response)
                )
            data = response.json() or {}
            summaries = [
                await _fetch_summary(client, m, headers)
                for m in data.get("messages") or []
            ]
    except Exception as exc:
        return ListMessagesOutput(
            success=False, error=f"list_messages failed: {exc}"
        )

    return ListMessagesOutput(
        success=True,
        messages=summaries,
        total=len(summaries),
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=CreateDraftInput)
@serialize_pydantic_return
async def create_draft(
    auth_type: str,
    auth_data: dict[str, Any],
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    is_html: bool = False,
) -> CreateDraftOutput:
    """Create an email draft in Gmail."""
    err = _validate(auth_data, "create_draft")
    if err:
        return CreateDraftOutput(success=False, error=err)

    raw = _build_raw_message(to, subject, body, cc, bcc, is_html)
    try:
        async with httpx.AsyncClient(timeout=_SEND_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/users/me/drafts",
                headers=_headers(auth_type, auth_data),
                json={"message": {"raw": raw}},
            )
        if response.status_code not in (200, 201):
            return CreateDraftOutput(
                success=False, error=_api_err("create_draft", response)
            )
        data = response.json() or {}
    except Exception as exc:
        return CreateDraftOutput(success=False, error=f"create_draft failed: {exc}")

    message = data.get("message") or {}
    return CreateDraftOutput(
        success=True,
        draft_id=data.get("id"),
        message_id=message.get("id"),
        thread_id=message.get("threadId"),
    )


async def _modify_message(
    action: str,
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    add: list[str] | None = None,
    remove: list[str] | None = None,
) -> tuple[bool, str | None, dict[str, Any]]:
    payload: dict[str, Any] = {}
    if add:
        payload["addLabelIds"] = add
    if remove:
        payload["removeLabelIds"] = remove
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/users/me/messages/{message_id}/modify",
                headers=_headers(auth_type, auth_data),
                json=payload,
            )
        if response.status_code != 200:
            return False, _api_err(action, response), {}
        body = response.json() or {}
    except Exception as exc:
        return False, f"{action} failed: {exc}", {}
    return True, None, body


@tool(args_schema=_MessageIdOnly)
@serialize_pydantic_return
async def mark_as_read(
    auth_type: str, auth_data: dict[str, Any], message_id: str
) -> MarkAsReadOutput:
    """Mark a Gmail message as read."""
    err = _validate(auth_data, "mark_as_read")
    if err:
        return MarkAsReadOutput(success=False, error=err)
    ok, e, body = await _modify_message(
        "mark_as_read", auth_type, auth_data, message_id, remove=["UNREAD"]
    )
    if not ok:
        return MarkAsReadOutput(success=False, error=e)
    return MarkAsReadOutput(
        success=True,
        id=body.get("id"),
        thread_id=body.get("threadId"),
        label_ids=body.get("labelIds") or [],
    )


@tool(args_schema=_MessageIdOnly)
@serialize_pydantic_return
async def mark_as_unread(
    auth_type: str, auth_data: dict[str, Any], message_id: str
) -> MarkAsUnreadOutput:
    """Mark a Gmail message as unread."""
    err = _validate(auth_data, "mark_as_unread")
    if err:
        return MarkAsUnreadOutput(success=False, error=err)
    ok, e, body = await _modify_message(
        "mark_as_unread", auth_type, auth_data, message_id, add=["UNREAD"]
    )
    if not ok:
        return MarkAsUnreadOutput(success=False, error=e)
    return MarkAsUnreadOutput(
        success=True,
        id=body.get("id"),
        thread_id=body.get("threadId"),
        label_ids=body.get("labelIds") or [],
    )


@tool(args_schema=_MessageIdOnly)
@serialize_pydantic_return
async def archive_message(
    auth_type: str, auth_data: dict[str, Any], message_id: str
) -> ArchiveMessageOutput:
    """Archive a Gmail message (remove from INBOX)."""
    err = _validate(auth_data, "archive_message")
    if err:
        return ArchiveMessageOutput(success=False, error=err)
    ok, e, body = await _modify_message(
        "archive_message", auth_type, auth_data, message_id, remove=["INBOX"]
    )
    if not ok:
        return ArchiveMessageOutput(success=False, error=e)
    return ArchiveMessageOutput(
        success=True,
        id=body.get("id"),
        thread_id=body.get("threadId"),
        label_ids=body.get("labelIds") or [],
        message="Message archived successfully",
    )


@tool(args_schema=_MessageIdOnly)
@serialize_pydantic_return
async def unarchive_message(
    auth_type: str, auth_data: dict[str, Any], message_id: str
) -> UnarchiveMessageOutput:
    """Move an archived Gmail message back to INBOX."""
    err = _validate(auth_data, "unarchive_message")
    if err:
        return UnarchiveMessageOutput(success=False, error=err)
    ok, e, body = await _modify_message(
        "unarchive_message", auth_type, auth_data, message_id, add=["INBOX"]
    )
    if not ok:
        return UnarchiveMessageOutput(success=False, error=e)
    return UnarchiveMessageOutput(
        success=True,
        id=body.get("id"),
        thread_id=body.get("threadId"),
        label_ids=body.get("labelIds") or [],
        message="Message moved to inbox",
    )


@tool(args_schema=_MessageIdOnly)
@serialize_pydantic_return
async def delete_message(
    auth_type: str, auth_data: dict[str, Any], message_id: str
) -> DeleteMessageOutput:
    """Move a Gmail message to Trash."""
    err = _validate(auth_data, "delete_message")
    if err:
        return DeleteMessageOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/users/me/messages/{message_id}/trash",
                headers=_headers(auth_type, auth_data),
            )
        if response.status_code != 200:
            return DeleteMessageOutput(
                success=False, error=_api_err("delete_message", response)
            )
        data = response.json() or {}
    except Exception as exc:
        return DeleteMessageOutput(success=False, error=f"delete_message failed: {exc}")

    return DeleteMessageOutput(
        success=True,
        id=data.get("id"),
        thread_id=data.get("threadId"),
        message="Message moved to trash",
    )


@tool(args_schema=AddLabelInput)
@serialize_pydantic_return
async def add_label(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    label_ids: list[str],
) -> AddLabelOutput:
    """Add one or more labels to a Gmail message."""
    err = _validate(auth_data, "add_label")
    if err:
        return AddLabelOutput(success=False, error=err)
    ok, e, body = await _modify_message(
        "add_label", auth_type, auth_data, message_id, add=label_ids
    )
    if not ok:
        return AddLabelOutput(success=False, error=e)
    return AddLabelOutput(
        success=True,
        id=body.get("id"),
        thread_id=body.get("threadId"),
        label_ids=body.get("labelIds") or [],
        added_labels=label_ids,
    )


@tool(args_schema=RemoveLabelInput)
@serialize_pydantic_return
async def remove_label(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    label_ids: list[str],
) -> RemoveLabelOutput:
    """Remove one or more labels from a Gmail message."""
    err = _validate(auth_data, "remove_label")
    if err:
        return RemoveLabelOutput(success=False, error=err)
    ok, e, body = await _modify_message(
        "remove_label", auth_type, auth_data, message_id, remove=label_ids
    )
    if not ok:
        return RemoveLabelOutput(success=False, error=e)
    return RemoveLabelOutput(
        success=True,
        id=body.get("id"),
        thread_id=body.get("threadId"),
        label_ids=body.get("labelIds") or [],
        removed_labels=label_ids,
    )


@tool(args_schema=ListLabelsInput)
@serialize_pydantic_return
async def list_labels(
    auth_type: str, auth_data: dict[str, Any]
) -> ListLabelsOutput:
    """List all labels in the Gmail account."""
    err = _validate(auth_data, "list_labels")
    if err:
        return ListLabelsOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/users/me/labels",
                headers=_headers(auth_type, auth_data),
            )
        if response.status_code != 200:
            return ListLabelsOutput(
                success=False, error=_api_err("list_labels", response)
            )
        data = response.json() or {}
    except Exception as exc:
        return ListLabelsOutput(success=False, error=f"list_labels failed: {exc}")

    raw_labels = data.get("labels") or []
    labels = [
        {
            "id": label.get("id"),
            "name": label.get("name"),
            "type": label.get("type"),
            "message_list_visibility": label.get("messageListVisibility"),
            "label_list_visibility": label.get("labelListVisibility"),
        }
        for label in raw_labels
        if isinstance(label, dict)
    ]
    return ListLabelsOutput(success=True, labels=labels, total=len(labels))
