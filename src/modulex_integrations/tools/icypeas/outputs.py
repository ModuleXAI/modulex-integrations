"""Pydantic response models for the Icypeas integration's @tool functions.

Icypeas follows the modulex *api_key* runtime convention: each function
signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair). The modulex ``ToolExecutor`` injects
it by reading the API key from the resolved ``api_key`` credential.

Both actions are asynchronous: they submit a job and poll a read
endpoint until a terminal status is reached. Error model: non-2xx
responses, timeouts, and a polling window that expires all surface as
``success=False`` + ``error`` rather than raising. Every output model
carries both shapes.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "FindEmailOutput",
    "VerifyEmailOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ----------------------------------------------


class FindEmailOutput(_Base):
    success: bool
    error: str | None = None
    search_id: str | None = None
    status: str | None = None
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    item: dict[str, Any] | None = None


class VerifyEmailOutput(_Base):
    success: bool
    error: str | None = None
    search_id: str | None = None
    status: str | None = None
    email: str | None = None
    valid: bool | None = None
    item: dict[str, Any] | None = None
