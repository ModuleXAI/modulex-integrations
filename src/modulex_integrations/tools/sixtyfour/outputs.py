"""Pydantic response models for the Sixtyfour AI integration's @tool functions.

Sixtyfour's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly and the modulex
``ToolExecutor`` injects it from the resolved ``api_key`` credential.

Error model: the tool wraps every call in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses, timeouts,
and unexpected exceptions rather than raising. Every output model carries
both shapes — ``success: bool`` + ``error: str | None`` plus permissive
data fields (scalars default to ``None``, lists/objects to empty).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "EmailEntry",
    "EnrichCompanyOutput",
    "EnrichLeadOutput",
    "FindEmailOutput",
    "FindPhoneOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class EmailEntry(_Base):
    """A single discovered email address with its validation status/type."""

    address: str | None = None
    status: str | None = None
    type: str | None = None


# --- Per-action output models ----------------------------------------------


class FindPhoneOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    company: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None


class FindEmailOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    company: str | None = None
    title: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    emails: list[EmailEntry] = Field(default_factory=list)
    personal_emails: list[EmailEntry] = Field(default_factory=list)


class EnrichLeadOutput(_Base):
    success: bool
    error: str | None = None
    notes: str | None = None
    structured_data: dict[str, Any] = Field(default_factory=dict)
    references: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float | None = None


class EnrichCompanyOutput(_Base):
    success: bool
    error: str | None = None
    notes: str | None = None
    structured_data: dict[str, Any] = Field(default_factory=dict)
    references: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float | None = None
    # org_chart may be returned as an object or a list, depending on the
    # account's schema and whether full_org_chart is enabled.
    org_chart: Any | None = None
