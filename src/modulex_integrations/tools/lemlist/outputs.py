"""Pydantic response models for the Lemlist integration's @tool functions.

Lemlist's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it from the resolved ``api_key`` credential.

Error model: the tools wrap every call in try/except, returning the
typed output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions rather than raising. Every output
model carries both the success and failure shapes.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ActivityItem",
    "GetActivitiesOutput",
    "GetLeadOutput",
    "SendEmailOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class ActivityItem(_Base):
    """A single activity row in ``get_activities``."""

    id: str | None = None
    type: str | None = None
    lead_id: str | None = None
    campaign_id: str | None = None
    sequence_id: str | None = None
    step_id: str | None = None
    created_at: str | None = None


# --- Per-action output models ----------------------------------------------


class GetActivitiesOutput(_Base):
    success: bool
    error: str | None = None
    activities: list[ActivityItem] = Field(default_factory=list)
    count: int = 0


class GetLeadOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    company_domain: str | None = None
    is_paused: bool | None = None
    campaign_id: str | None = None
    contact_id: str | None = None
    email_status: str | None = None


class SendEmailOutput(_Base):
    success: bool
    error: str | None = None
    ok: bool | None = None
