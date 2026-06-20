"""WhatsApp LangChain ``@tool`` functions.

One async tool wrapping the WhatsApp Cloud API (``graph.facebook.com``).
The modulex ``ToolExecutor`` injects an ``api_key: str`` directly
(resolved from the user's ``api_key`` credential). For WhatsApp the
credential IS the WhatsApp Business API access token, which is sent as
``Authorization: Bearer <api_key>``.

Error model: non-2xx HTTP responses and timeouts are caught and returned
as the typed output with ``success=False`` + ``error`` rather than
raising — the same defensive behavior used across the package.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.whatsapp.outputs import (
    MessageContact,
    SendMessageOutput,
)

__all__ = ["send_message"]

_GRAPH_API_BASE = "https://graph.facebook.com/v25.0"
_SEND_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class SendMessageInput(BaseModel):
    phone_number: str = Field(
        description="Recipient phone number with country code (e.g., +14155552671)"
    )
    message: str = Field(description="Plain text message content to send")
    phone_number_id: str = Field(
        description="WhatsApp Business Phone Number ID (from Meta Business Suite)"
    )
    api_key: str = Field(
        description=(
            "WhatsApp Business API access token, sent as the bearer credential "
            "(provided by credential system)"
        )
    )
    preview_url: bool | None = Field(
        default=None,
        description=(
            "Whether WhatsApp should try to render a link preview for the first "
            "URL in the message"
        ),
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SendMessageInput)
@serialize_pydantic_return
async def send_message(
    phone_number: str,
    message: str,
    phone_number_id: str,
    api_key: str,
    preview_url: bool | None = None,
) -> SendMessageOutput:
    """Send a text message through the WhatsApp Cloud API."""
    if not api_key or not api_key.strip():
        return SendMessageOutput(
            success=False,
            error="WhatsApp access token is empty. Please configure a valid credential.",
        )
    if not phone_number or not phone_number.strip():
        return SendMessageOutput(
            success=False,
            error="Recipient phone number is required but was not provided.",
        )
    if not message:
        return SendMessageOutput(
            success=False,
            error="Message content is required but was not provided.",
        )
    if not phone_number_id or not phone_number_id.strip():
        return SendMessageOutput(
            success=False,
            error="WhatsApp Phone Number ID is required but was not provided.",
        )

    text: dict[str, Any] = {"body": message}
    if preview_url is not None:
        text["preview_url"] = preview_url

    body: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number.strip(),
        "type": "text",
        "text": text,
    }

    url = f"{_GRAPH_API_BASE}/{phone_number_id.strip()}/messages"

    try:
        async with httpx.AsyncClient(timeout=_SEND_TIMEOUT) as client:
            response = await client.post(url, headers=_headers(api_key), json=body)
        if response.status_code != 200:
            return SendMessageOutput(
                success=False,
                error=_format_api_error(response),
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendMessageOutput(success=False, error=f"Send message failed: {exc}")

    contacts_raw = data.get("contacts") or []
    contacts = [
        MessageContact(
            input=contact.get("input"),
            wa_id=contact.get("wa_id"),
        )
        for contact in contacts_raw
        if isinstance(contact, dict)
    ]

    messages_raw = data.get("messages") or []
    first_message = messages_raw[0] if messages_raw and isinstance(messages_raw[0], dict) else {}
    message_id = first_message.get("id")

    if not message_id:
        return SendMessageOutput(
            success=False,
            error="WhatsApp API response did not include a message ID.",
        )

    first_contact = contacts[0] if contacts else None

    return SendMessageOutput(
        success=True,
        message_id=message_id,
        message_status=first_message.get("message_status"),
        messaging_product=data.get("messaging_product"),
        input_phone_number=first_contact.input if first_contact else None,
        whatsapp_user_id=first_contact.wa_id if first_contact else None,
        contacts=contacts,
    )


def _format_api_error(response: httpx.Response) -> str:
    """Build a human-readable error string from a non-2xx WhatsApp response.

    The Cloud API returns errors as ``{"error": {"message": ..., ...}}``;
    fall back to the raw body when the shape is unexpected.
    """
    try:
        payload = response.json()
    except Exception:
        return f"WhatsApp API error ({response.status_code}): {response.text}"

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        detail = (
            error.get("message")
            or error.get("error_user_msg")
            or (
                error.get("error_data", {}).get("details")
                if isinstance(error.get("error_data"), dict)
                else None
            )
        )
        if detail:
            return f"WhatsApp API error ({response.status_code}): {detail}"
    return f"WhatsApp API error ({response.status_code}): {response.text}"
