"""Gmail LangChain ``@tool`` functions.

Pure HTTP integration against Gmail REST v1 (the legacy implementation
also uses raw httpx rather than the Google Python SDK — preserved
verbatim to keep the dependency surface tiny). Token-based runtime
convention with paired oauth2 + bearer_token auth schemas.

Scope-trimmed to send + label management only: ``send_message`` builds
a base64url MIME message locally, ``list_labels`` reads the account's
labels. Read/search/modify actions were removed alongside the
``gmail.readonly`` and ``gmail.modify`` OAuth scopes.
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
    ListLabelsOutput,
    SendMessageOutput,
)

__all__ = [
    "list_labels",
    "send_message",
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
