"""Pydantic response models for the Enrow integration's @tool functions.

Enrow's tools follow the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly, which the modulex
``ToolExecutor`` injects by reading the API key from the resolved
``api_key`` credential.

Both actions are asynchronous on Enrow's side — a submit call returns a
job id, then a result endpoint is polled until the search completes.
Each ``@tool`` folds the submit + poll loop into one call and returns a
fully resolved result.

Error model: Enrow returns proper HTTP status codes. Non-2xx responses,
timeouts, and an expired polling window surface as ``success=False`` +
``error`` rather than raising, so every output model carries both shapes.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


__all__ = [
    "FindEmailOutput",
    "VerifyEmailOutput",
]


class FindEmailOutput(_Base):
    """Result of an Enrow find-email search (submit + poll)."""

    success: bool
    error: str | None = None
    id: str | None = None
    email: str | None = None
    qualification: str | None = None
    fullname: str | None = None
    company_name: str | None = None
    company_domain: str | None = None
    linkedin_url: str | None = None


class VerifyEmailOutput(_Base):
    """Result of an Enrow verify-email check (submit + poll)."""

    success: bool
    error: str | None = None
    id: str | None = None
    email: str | None = None
    qualification: str | None = None
