"""Pydantic response models for the Gamma integration's @tool functions.

Gamma uses the modulex *api_key* runtime convention: each function takes
an ``api_key: str`` directly and authenticates with the ``X-API-KEY``
header. Every output model carries ``success: bool`` + ``error`` so
non-2xx responses, timeouts, and unexpected exceptions surface as
``success=False`` rather than raising.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CheckStatusOutput",
    "FolderItem",
    "GammaCredits",
    "GammaError",
    "GenerateFromTemplateOutput",
    "GenerateOutput",
    "ListFoldersOutput",
    "ListThemesOutput",
    "ThemeItem",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class GammaCredits(_Base):
    """Credit usage reported on a completed generation."""

    deducted: int | None = None
    remaining: int | None = None


class GammaError(_Base):
    """Error details reported on a failed generation."""

    message: str | None = None
    status_code: int | None = None


class ThemeItem(_Base):
    """A single theme in ``list_themes``."""

    id: str | None = None
    name: str | None = None
    type: str | None = None
    color_keywords: list[str] = Field(default_factory=list)
    tone_keywords: list[str] = Field(default_factory=list)


class FolderItem(_Base):
    """A single folder in ``list_folders``."""

    id: str | None = None
    name: str | None = None


# --- Per-action output models ----------------------------------------------


class GenerateOutput(_Base):
    success: bool
    error: str | None = None
    generation_id: str | None = None
    warnings: str | None = None


class GenerateFromTemplateOutput(_Base):
    success: bool
    error: str | None = None
    generation_id: str | None = None
    warnings: str | None = None


class CheckStatusOutput(_Base):
    success: bool
    error: str | None = None
    generation_id: str | None = None
    status: str | None = None
    gamma_url: str | None = None
    gamma_id: str | None = None
    export_url: str | None = None
    credits: GammaCredits | None = None
    generation_error: GammaError | None = None


class ListThemesOutput(_Base):
    success: bool
    error: str | None = None
    themes: list[ThemeItem] = Field(default_factory=list)
    has_more: bool | None = None
    next_cursor: str | None = None


class ListFoldersOutput(_Base):
    success: bool
    error: str | None = None
    folders: list[FolderItem] = Field(default_factory=list)
    has_more: bool | None = None
    next_cursor: str | None = None
