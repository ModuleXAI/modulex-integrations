"""Pydantic response models for the fal_ai integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddRequestToQueueOutput",
    "CancelRequestOutput",
    "GetRequestResponseOutput",
    "GetRequestStatusOutput",
    "LogEntry",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class LogEntry(_Base):
    """A log entry from a queued request's status."""

    message: str | None = None
    level: str | None = None
    timestamp: str | None = None


# --- Per-action output models ---------------------------------------------


class AddRequestToQueueOutput(_Base):
    success: bool
    error: str | None = None
    request_id: str | None = None
    response_url: str | None = None
    status_url: str | None = None
    cancel_url: str | None = None


class CancelRequestOutput(_Base):
    success: bool
    error: str | None = None


class GetRequestResponseOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetRequestStatusOutput(_Base):
    success: bool
    error: str | None = None
    status: str | None = None
    queue_position: int | None = None
    logs: list[LogEntry] = Field(default_factory=list)
