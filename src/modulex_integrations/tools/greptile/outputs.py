"""Pydantic response models for the Greptile integration's @tool functions.

Greptile's tools follow the modulex *api_key* runtime convention: each
function takes ``api_key: str`` directly (the Greptile API key) plus a
``github_token`` field resolved from the credential, instead of an
``auth_type``/``auth_data`` pair.

Error model: the tools wrap every call in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses, timeouts,
and unexpected exceptions. Non-2xx HTTP responses do not raise. Every output
model therefore carries both the success and failure shapes, with permissive
data fields read from the upstream JSON via ``.get()``.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "IndexRepositoryOutput",
    "QueryOutput",
    "QuerySource",
    "SearchOutput",
    "StatusOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class QuerySource(_Base):
    """A single code reference returned by ``query`` and ``search``."""

    repository: str | None = None
    remote: str | None = None
    branch: str | None = None
    filepath: str | None = None
    linestart: int | None = None
    lineend: int | None = None
    summary: str | None = None
    distance: float | None = None


# --- Per-action output models ----------------------------------------------


class QueryOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    sources: list[QuerySource] = Field(default_factory=list)


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    sources: list[QuerySource] = Field(default_factory=list)


class IndexRepositoryOutput(_Base):
    success: bool
    error: str | None = None
    repository_id: str | None = None
    status_endpoint: str | None = None
    message: str | None = None


class StatusOutput(_Base):
    success: bool
    error: str | None = None
    repository: str | None = None
    remote: str | None = None
    branch: str | None = None
    private: bool | None = None
    status: str | None = None
    files_processed: int | None = None
    num_files: int | None = None
    sample_questions: list[str] = Field(default_factory=list)
    sha: str | None = None
    raw: dict[str, Any] | None = None
