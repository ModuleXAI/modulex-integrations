"""Pydantic response models for the ConvertAPI integration."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ConvertBase64FileOutput",
    "ConvertFileOutput",
    "ConvertWebUrlOutput",
    "ConvertedFile",
    "GetSupportedFormatsOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConvertedFile(_Base):
    filename: str | None = None
    file_size: int | None = None
    file_url: str | None = None
    file_data_base64: str | None = None


class ConvertFileOutput(_Base):
    success: bool
    error: str | None = None
    conversion_cost: int | None = None
    files: list[ConvertedFile] = Field(default_factory=list)
    format_from: str | None = None
    format_to: str | None = None


class ConvertBase64FileOutput(_Base):
    success: bool
    error: str | None = None
    conversion_cost: int | None = None
    files: list[ConvertedFile] = Field(default_factory=list)
    format_from: str | None = None
    format_to: str | None = None


class ConvertWebUrlOutput(_Base):
    success: bool
    error: str | None = None
    conversion_cost: int | None = None
    files: list[ConvertedFile] = Field(default_factory=list)
    source_url: str | None = None
    format_to: str | None = None


class GetSupportedFormatsOutput(_Base):
    success: bool
    error: str | None = None
    format_from: str | None = None
    supported_formats: list[str] = Field(default_factory=list)
    count: int = 0
