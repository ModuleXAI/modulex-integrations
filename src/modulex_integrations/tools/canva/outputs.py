"""Pydantic response models for the canva integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateDesignImportJobOutput",
    "CreateDesignOutput",
    "DesignSummary",
    "ExportDesignOutput",
    "ExportJob",
    "ImportJob",
    "ListDesignsOutput",
    "UploadAssetOutput",
    "UploadJob",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class DesignSummary(_Base):
    """A design object returned by Canva."""

    id: str | None = None
    title: str | None = None
    owner: dict[str, str | None] | None = None
    thumbnail: dict[str, str | int | None] | None = None
    urls: dict[str, str | None] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ExportJob(_Base):
    """An export job status object."""

    id: str | None = None
    status: str | None = None
    urls: list[str] = Field(default_factory=list)


class ImportJob(_Base):
    """A design import job status object."""

    id: str | None = None
    status: str | None = None
    design_id: str | None = None


class UploadJob(_Base):
    """An asset upload job status object."""

    id: str | None = None
    status: str | None = None
    asset: dict[str, str | None] | None = None


# --- Per-action output models ----------------------------------------------


class CreateDesignOutput(_Base):
    success: bool
    error: str | None = None
    design: DesignSummary | None = None


class CreateDesignImportJobOutput(_Base):
    success: bool
    error: str | None = None
    job: ImportJob | None = None


class ExportDesignOutput(_Base):
    success: bool
    error: str | None = None
    job: ExportJob | None = None


class ListDesignsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[DesignSummary] = Field(default_factory=list)
    continuation: str | None = None


class UploadAssetOutput(_Base):
    success: bool
    error: str | None = None
    job: UploadJob | None = None
