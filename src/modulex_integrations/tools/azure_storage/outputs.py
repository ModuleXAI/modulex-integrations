"""Pydantic response models for the azure_storage integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateContainerOutput",
    "DeleteBlobOutput",
    "ListContainersOutput",
    "UploadBlobOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreateContainerOutput(_Base):
    success: bool
    error: str | None = None


class DeleteBlobOutput(_Base):
    success: bool
    error: str | None = None


class ListContainersOutput(_Base):
    success: bool
    error: str | None = None
    containers: list[str] = Field(default_factory=list)


class UploadBlobOutput(_Base):
    success: bool
    error: str | None = None
