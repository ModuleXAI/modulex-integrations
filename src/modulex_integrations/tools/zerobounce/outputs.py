"""Pydantic response models for the ZeroBounce integration's @tool functions.

ZeroBounce follows the modulex *api_key* runtime convention: each function
signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor`` injects
it by reading the API key from the resolved ``api_key`` credential.

Error model: ZeroBounce can return HTTP 200 with an ``{"error": ...}``
envelope (invalid key / out of credits) as well as proper non-2xx codes.
Both surface as ``success=False`` + ``error`` rather than raising — every
output model carries both shapes.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "GetCreditsOutput",
    "VerifyEmailOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ----------------------------------------------


class VerifyEmailOutput(_Base):
    success: bool
    error: str | None = None
    email: str | None = None
    status: str | None = None
    deliverable: bool | None = None
    sub_status: str | None = None
    free_email: bool | None = None
    did_you_mean: str | None = None


class GetCreditsOutput(_Base):
    success: bool
    error: str | None = None
    credits: int | None = None
