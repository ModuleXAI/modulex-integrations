"""Pydantic response models for the WhatsApp integration's @tool functions.

WhatsApp's tool follows the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly (the WhatsApp Business
API access token, sent as the ``Authorization: Bearer`` credential), and
the modulex ``ToolExecutor`` injects it by reading the resolved
``api_key`` credential.

Error model: the WhatsApp Cloud API returns proper HTTP status codes, but
each tool wraps everything in try/except so non-2xx responses and timeouts
surface as ``success=False`` + ``error`` rather than exceptions. Every
output model carries both shapes. Fields are permissive (``| None``) since
the upstream payload is read with ``.get()``.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "MessageContact",
    "SendMessageOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class MessageContact(_Base):
    """A single recipient contact record returned by the send API."""

    input: str | None = None
    wa_id: str | None = None


# --- Per-action output models ----------------------------------------------


class SendMessageOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None
    message_status: str | None = None
    messaging_product: str | None = None
    input_phone_number: str | None = None
    whatsapp_user_id: str | None = None
    contacts: list[MessageContact] = Field(default_factory=list)
