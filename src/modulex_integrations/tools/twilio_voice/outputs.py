"""Pydantic response models for the Twilio Voice integration's @tool functions.

Twilio Voice follows the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly (the Twilio Auth
Token) plus a separate ``account_sid`` parameter resolved from the
credential. The modulex ``ToolExecutor`` injects ``api_key`` and fills
``account_sid`` from the credential's ``auth_data`` by exact name.

Error model: the underlying tools wrap every call in try/except,
returning the typed output with ``success=False`` + ``error`` for
non-2xx responses, timeouts, and unexpected exceptions. Twilio also
returns an ``error_code`` / ``message`` field on logical failures, which
is surfaced the same way. Non-2xx HTTP responses do *not* raise.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CallListItem",
    "GetRecordingOutput",
    "ListCallsOutput",
    "MakeCallOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class CallListItem(_Base):
    """A single call row in ``list_calls``."""

    call_sid: str | None = None
    from_: str | None = Field(default=None, serialization_alias="from")
    to: str | None = None
    status: str | None = None
    direction: str | None = None
    duration: int | None = None
    price: str | None = None
    price_unit: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    date_created: str | None = None
    recording_sids: list[str] = Field(default_factory=list)


# --- Per-action output models ----------------------------------------------


class MakeCallOutput(_Base):
    success: bool
    error: str | None = None
    call_sid: str | None = None
    status: str | None = None
    direction: str | None = None
    from_: str | None = Field(default=None, serialization_alias="from")
    to: str | None = None
    duration: int | None = None
    price: str | None = None
    price_unit: str | None = None


class ListCallsOutput(_Base):
    success: bool
    error: str | None = None
    calls: list[CallListItem] = Field(default_factory=list)
    total: int = 0
    page: int | None = None
    page_size: int | None = None


class GetRecordingOutput(_Base):
    success: bool
    error: str | None = None
    recording_sid: str | None = None
    call_sid: str | None = None
    duration: int | None = None
    status: str | None = None
    channels: int | None = None
    source: str | None = None
    media_url: str | None = None
    price: str | None = None
    price_unit: str | None = None
    uri: str | None = None
    transcription_text: str | None = None
    transcription_status: str | None = None
    transcription_price: str | None = None
    transcription_price_unit: str | None = None
