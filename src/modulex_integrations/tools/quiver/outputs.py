"""Pydantic response models for the Quiver integration's @tool functions.

Quiver's tools follow the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it by reading the API key from the resolved
``api_key`` credential.

Error model: the tools wrap every call in try/except so non-2xx
responses and timeouts surface as ``success=False`` + ``error`` rather
than raising. Every output model carries both shapes — ``success: bool``
and ``error: str | None`` — and all data fields stay permissive.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ImageToSvgOutput",
    "ListModelsOutput",
    "ModelInfo",
    "SvgArtifact",
    "TextToSvgOutput",
    "UsageInfo",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class SvgArtifact(_Base):
    """A single generated SVG returned in the response ``data`` array."""

    svg: str | None = None
    mime_type: str | None = None


class UsageInfo(_Base):
    """Token usage statistics returned alongside an SVG response.

    Quiver retains these fields for compatibility; they may be zeroed.
    Billing is reported via ``credits`` on the parent output.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ModelInfo(_Base):
    """A single available model row in ``list_models``."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    created: int | None = None
    owned_by: str | None = None
    input_modalities: list[str] = Field(default_factory=list)
    output_modalities: list[str] = Field(default_factory=list)
    context_length: int | None = None
    max_output_length: int | None = None
    supported_operations: list[str] = Field(default_factory=list)
    supported_sampling_parameters: list[str] = Field(default_factory=list)


# --- Per-action output models ----------------------------------------------


class TextToSvgOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    created: int | None = None
    svg_content: str | None = None
    artifacts: list[SvgArtifact] = Field(default_factory=list)
    credits: int | None = None
    usage: UsageInfo | None = None


class ImageToSvgOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    created: int | None = None
    svg_content: str | None = None
    artifacts: list[SvgArtifact] = Field(default_factory=list)
    credits: int | None = None
    usage: UsageInfo | None = None


class ListModelsOutput(_Base):
    success: bool
    error: str | None = None
    models: list[ModelInfo] = Field(default_factory=list)
    total_models: int = 0
    raw: dict[str, Any] | None = None
