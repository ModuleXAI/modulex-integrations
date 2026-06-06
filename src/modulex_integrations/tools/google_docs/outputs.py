"""Pydantic response models for the google_docs integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AppendImageOutput",
    "AppendTextOutput",
    "CreateDocumentOutput",
    "GetDocumentOutput",
    "GetTabContentOutput",
    "InsertPageBreakOutput",
    "InsertTableOutput",
    "InsertTextOutput",
    "ReplaceImageOutput",
    "ReplaceTextOutput",
    "TabContent",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class TabContent(_Base):
    """Tab content returned by get_tab_content."""

    tab_id: str | None = None
    title: str | None = None
    body: dict[str, Any] | None = None


class AppendImageOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None


class AppendTextOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None


class CreateDocumentOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None


class GetDocumentOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None
    body: dict[str, Any] | None = None


class GetTabContentOutput(_Base):
    success: bool
    error: str | None = None
    tabs: list[TabContent] = Field(default_factory=list)


class InsertPageBreakOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None


class InsertTableOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None


class InsertTextOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None


class ReplaceImageOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None


class ReplaceTextOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    title: str | None = None
