"""Pydantic response models for the pagerduty integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AcknowledgeIncidentOutput",
    "FindOncallUserOutput",
    "IncidentSummary",
    "OncallUser",
    "ResolveIncidentOutput",
    "TriggerIncidentOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class IncidentSummary(_Base):
    """Core fields returned for an incident by the PagerDuty API."""

    id: str | None = None
    type: str | None = None
    summary: str | None = None
    status: str | None = None
    title: str | None = None
    urgency: str | None = None
    incident_key: str | None = None
    html_url: str | None = None
    created_at: str | None = None
    service: dict[str, Any] | None = None
    escalation_policy: dict[str, Any] | None = None
    assignments: list[dict[str, Any]] = Field(default_factory=list)


class OncallUser(_Base):
    """A user found on-call for a schedule."""

    id: str | None = None
    name: str | None = None
    email: str | None = None
    type: str | None = None
    html_url: str | None = None


# --- Per-action output models ----------------------------------------------


class TriggerIncidentOutput(_Base):
    success: bool
    incident: IncidentSummary | None = None


class AcknowledgeIncidentOutput(_Base):
    success: bool
    incident: IncidentSummary | None = None


class ResolveIncidentOutput(_Base):
    success: bool
    incident: IncidentSummary | None = None


class FindOncallUserOutput(_Base):
    success: bool
    found: bool = False
    user: OncallUser | None = None
