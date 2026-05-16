"""Pydantic response models for the Jina AI integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ClassifyOutput",
    "DeepSearchOutput",
    "GenerateEmbeddingsOutput",
    "ReadWebpageOutput",
    "RerankDocumentsOutput",
    "SegmentTextOutput",
    "WebSearchOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None
    # Upstream JSON body, mirrored on ``data`` so callers can read the
    # full Jina response without us re-modelling every endpoint shape.
    data: dict[str, Any] | None = None


class GenerateEmbeddingsOutput(_Base):
    pass


class RerankDocumentsOutput(_Base):
    pass


class ReadWebpageOutput(_Base):
    # read_webpage's legacy implementation flattens a few useful fields
    # out of the upstream `data` blob for ergonomic access. We mirror
    # that here while keeping the raw blob on ``data``.
    title: str | None = None
    description: str | None = None
    url: str | None = None
    content: str | None = None
    links: dict[str, Any] | None = None
    images: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None


class WebSearchOutput(_Base):
    results: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class DeepSearchOutput(_Base):
    pass


class SegmentTextOutput(_Base):
    num_tokens: int | None = None
    num_chunks: int | None = None
    chunks: list[str] | None = None
    chunk_positions: list[list[int]] | None = None
    tokens: list[Any] | None = None
    tokenizer: str | None = None
    usage: dict[str, Any] | None = None


class ClassifyOutput(_Base):
    classifications: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, Any] | None = None
