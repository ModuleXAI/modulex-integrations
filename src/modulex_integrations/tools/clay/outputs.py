"""Pydantic response models for the Clay integration's @tool functions.

Clay's ``populate`` action sends a record to a table's inbound webhook
URL over HTTP POST. The webhook acknowledges receipt; the actual
enrichment runs asynchronously inside Clay, so the immediate response
carries only an acknowledgment payload plus transport metadata (the
HTTP status, headers, and a call-time timestamp).

Error model: the tool wraps the HTTP call in a try/except so non-2xx
responses, timeouts, and unexpected exceptions surface as
``success=False`` + ``error`` rather than raising. Every model carries
both shapes.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["PopulateMetadata", "PopulateOutput"]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PopulateMetadata(_Base):
    """Transport-level metadata about the webhook response."""

    status: int | None = None
    status_text: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    timestamp: str | None = None
    content_type: str | None = None


class PopulateOutput(_Base):
    """Result of pushing a record to a Clay table webhook."""

    success: bool
    error: str | None = None
    # The webhook acknowledgment body. JSON responses are returned as-is
    # (object or array); a non-JSON response is wrapped as
    # ``{"message": "<text>"}`` so the field is always JSON-serializable.
    data: Any | None = None
    metadata: PopulateMetadata | None = None
