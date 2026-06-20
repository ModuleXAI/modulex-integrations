"""Pydantic response models for the Pulse integration's @tool functions.

Pulse follows the modulex *api_key* runtime convention: each function
signature takes ``api_key: str`` directly and the modulex
``ToolExecutor`` injects it from the resolved credential.

Error model: non-2xx HTTP responses, timeouts, and unexpected
exceptions are caught and surfaced as ``success=False`` + ``error``
rather than raising. Every output model carries both shapes.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ParserOutput",
    "PlanInfo",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class PlanInfo(_Base):
    """Plan usage information returned with each extraction."""

    pages_used: int | None = None
    tier: str | None = None
    note: str | None = None


# --- Per-action output models ----------------------------------------------


class ParserOutput(_Base):
    """Result of parsing a document with Pulse OCR."""

    success: bool
    error: str | None = None
    markdown: str | None = None
    page_count: int | None = None
    job_id: str | None = None
    plan_info: PlanInfo | None = None
    bounding_boxes: dict[str, Any] | None = None
    extraction_url: str | None = None
    html: str | None = None
    structured_output: dict[str, Any] | None = None
    chunks: list[Any] = Field(default_factory=list)
    figures: list[Any] = Field(default_factory=list)
