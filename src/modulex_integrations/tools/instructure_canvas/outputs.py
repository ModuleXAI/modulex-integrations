"""Pydantic response models for the instructure_canvas integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AccountOption",
    "AssignmentSummary",
    "CourseSummary",
    "ListAccountsOutput",
    "ListAssignmentsOutput",
    "ListCoursesOutput",
    "SearchCourseContentOutput",
    "SearchResultItem",
    "UpdateAssignmentOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class AccountOption(_Base):
    """A Canvas account option."""

    id: int | None = None
    name: str | None = None


class AssignmentSummary(_Base):
    """A Canvas assignment."""

    id: int | None = None
    name: str | None = None
    description: str | None = None
    due_at: str | None = None
    points_possible: float | None = None
    grading_type: str | None = None
    submission_types: list[str] = Field(default_factory=list)
    course_id: int | None = None
    allowed_attempts: int | None = None
    omit_from_final_grade: bool | None = None


class CourseSummary(_Base):
    """A Canvas course."""

    id: int | None = None
    name: str | None = None
    course_code: str | None = None
    workflow_state: str | None = None
    enrollment_term_id: int | None = None


class SearchResultItem(_Base):
    """A search result from Canvas smart search."""

    content_id: int | None = None
    content_type: str | None = None
    title: str | None = None
    body: str | None = None
    html_url: str | None = None
    distance: float | None = None
    readable_type: str | None = None
    relevance: float | None = None


class ListAccountsOutput(_Base):
    success: bool
    error: str | None = None
    accounts: list[AccountOption] = Field(default_factory=list)


class ListAssignmentsOutput(_Base):
    success: bool
    error: str | None = None
    assignments: list[AssignmentSummary] = Field(default_factory=list)


class ListCoursesOutput(_Base):
    success: bool
    error: str | None = None
    courses: list[CourseSummary] = Field(default_factory=list)


class SearchCourseContentOutput(_Base):
    success: bool
    error: str | None = None
    results: list[SearchResultItem] = Field(default_factory=list)


class UpdateAssignmentOutput(_Base):
    success: bool
    error: str | None = None
    assignment: AssignmentSummary | None = None
