"""Pydantic response models for the google_forms integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateFormOutput",
    "CreateTextQuestionOutput",
    "FormInfo",
    "FormResponseSummary",
    "FormSummary",
    "GetFormOutput",
    "GetFormResponseOutput",
    "ListFormResponsesOutput",
    "UpdateFormTitleOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class FormInfo(_Base):
    """The ``info`` subobject embedded in a Google Form resource."""

    title: str | None = None
    documentTitle: str | None = None
    description: str | None = None


class FormSummary(_Base):
    """Slim view of a Google Form resource returned by Get/Create."""

    formId: str | None = None
    responderUri: str | None = None
    revisionId: str | None = None
    info: FormInfo | None = None
    settings: dict[str, Any] | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class FormResponseSummary(_Base):
    """A single response to a Google Form."""

    responseId: str | None = None
    formId: str | None = None
    createTime: str | None = None
    lastSubmittedTime: str | None = None
    respondentEmail: str | None = None
    answers: dict[str, Any] | None = None
    totalScore: float | None = None


# --- Per-action output models ----------------------------------------------


class CreateFormOutput(_Base):
    success: bool
    form: FormSummary | None = None


class CreateTextQuestionOutput(_Base):
    success: bool
    formId: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    form: FormSummary | None = None
    writeControl: dict[str, Any] | None = None


class GetFormOutput(_Base):
    success: bool
    form: FormSummary | None = None


class GetFormResponseOutput(_Base):
    success: bool
    response: FormResponseSummary | None = None


class ListFormResponsesOutput(_Base):
    success: bool
    responses: list[FormResponseSummary] = Field(default_factory=list)
    nextPageToken: str | None = None


class UpdateFormTitleOutput(_Base):
    success: bool
    formId: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    form: FormSummary | None = None
    writeControl: dict[str, Any] | None = None
