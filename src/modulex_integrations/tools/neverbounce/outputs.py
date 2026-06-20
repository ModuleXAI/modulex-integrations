"""Pydantic response models for the NeverBounce integration's @tool functions.

NeverBounce's tools follow the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor`` injects
it by reading the resolved ``api_key`` credential.

Error model: the NeverBounce v4 REST API returns HTTP 200 even for
API-level failures and signals the outcome through an envelope ``status``
field (``"success"`` vs. ``"auth_failure"``/``"general_failure"``/etc.).
Every output model carries ``success: bool`` + ``error: str | None`` so a
caller sees a uniform shape regardless of how the failure surfaced.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetCreditsOutput",
    "VerifyEmailOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ----------------------------------------------


class VerifyEmailOutput(_Base):
    """Result of verifying a single email address."""

    success: bool
    error: str | None = None
    email: str | None = None
    # Normalized verification status: valid, invalid, catch_all, disposable,
    # unknown (mapped from NeverBounce's raw ``result``).
    status: str | None = None
    deliverable: bool | None = None
    role_account: bool | None = None
    free_email: bool | None = None
    did_you_mean: str | None = None
    flags: list[str] = Field(default_factory=list)
    # Raw NeverBounce verification ``result`` value (valid, invalid,
    # catchall, disposable, unknown).
    result: str | None = None


class GetCreditsOutput(_Base):
    """Remaining verification credits for the account."""

    success: bool
    error: str | None = None
    credits: int | None = None
    free_credits: int | None = None
