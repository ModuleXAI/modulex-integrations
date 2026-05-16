"""Pydantic response models for the PostHog integration.

PostHog's 78 actions all return raw API data in a uniform envelope
(``{success, action, result}``). Modeling that as one generic output
(``PostHogResult``) preserves the legacy contract — every action's
``result`` field carries the upstream JSON shape (varies by endpoint).
The LLM-facing schema is intentionally permissive (``result: Any``);
per-endpoint shapes are documented in PostHog's API docs.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = ["PostHogResult"]


class PostHogResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None
    result: Any = None
