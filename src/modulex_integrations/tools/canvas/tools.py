"""Canvas LMS LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.canvas.outputs import (
    AccountOption,
    AssignmentSummary,
    CourseSummary,
    ListAccountsOutput,
    ListAssignmentsOutput,
    ListCoursesOutput,
    SearchCourseContentOutput,
    SearchResultItem,
    UpdateAssignmentOutput,
)

__all__ = [
    "list_accounts",
    "list_assignments",
    "list_courses",
    "search_course_content",
    "update_assignment",
]

_TIMEOUT = 30.0


def _base_url(auth_data: dict[str, Any]) -> str:
    domain = auth_data.get("domain", "").strip().rstrip("/")
    if not domain:
        return ""
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    return f"{domain}/api/v1"


def _headers(auth_data: dict[str, Any]) -> dict[str, str]:
    token = auth_data.get("access_token", "")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def _validate_auth(auth_data: dict[str, Any]) -> str | None:
    domain = auth_data.get("domain", "")
    token = auth_data.get("access_token", "")
    if not domain or not str(domain).strip():
        return "Canvas domain is missing. Please configure your Canvas instance domain."
    if not token or not str(token).strip():
        return "Access token is missing. Please configure a valid Canvas access token."
    return None


# --- Input schemas --------------------------------------------------------


class ListAccountsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListAssignmentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="The ID of the user whose assignments to list.")
    course_id: str = Field(description="The ID of the course to list assignments from.")


class ListCoursesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="The ID of the user whose courses to list.")


class SearchCourseContentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    course_id: str = Field(description="The ID of the course to search within.")
    query: str = Field(description="The search query string.")


class UpdateAssignmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    course_id: str = Field(description="The ID of the course containing the assignment.")
    assignment_id: str = Field(description="The ID of the assignment to update.")
    name: str | None = Field(default=None, description="The new name of the assignment.")
    description: str | None = Field(default=None, description="The new description of the assignment (supports HTML).")
    submission_type: str | None = Field(default=None, description="Submission type: online_quiz, none, on_paper, discussion_topic, external_tool, online_upload, online_text_entry, online_url, media_recording, student_annotation.")
    notify_of_update: bool | None = Field(default=None, description="Whether to notify students of the update.")
    points_possible: int | None = Field(default=None, description="Maximum points possible on the assignment.")
    grading_type: str | None = Field(default=None, description="Grading strategy: pass_fail, percent, letter_grade, gpa_scale, points, not_graded.")
    due_at: str | None = Field(default=None, description="Due date/time in ISO 8601 format (e.g. 2014-10-21T18:48:00Z).")
    omit_from_final_grade: bool | None = Field(default=None, description="Whether to omit this assignment from the student's final grade.")
    allowed_attempts: int | None = Field(default=None, description="Number of submission attempts allowed (-1 for unlimited).")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ListAccountsInput)
@serialize_pydantic_return
async def list_accounts(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListAccountsOutput:
    """List Canvas accounts accessible to the authenticated user."""
    err = _validate_auth(auth_data)
    if err:
        return ListAccountsOutput(success=False, error=err)
    base = _base_url(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base}/accounts",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return ListAccountsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAccountsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAccountsOutput(success=False, error=f"Call failed: {exc}")

    accounts = [
        AccountOption(id=a.get("id"), name=a.get("name"))
        for a in data
        if isinstance(a, dict)
    ]
    return ListAccountsOutput(success=True, accounts=accounts)


@tool(args_schema=ListAssignmentsInput)
@serialize_pydantic_return
async def list_assignments(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
    course_id: str,
) -> ListAssignmentsOutput:
    """Retrieve a list of assignments for a user in a specific course."""
    err = _validate_auth(auth_data)
    if err:
        return ListAssignmentsOutput(success=False, error=err)
    base = _base_url(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base}/users/{user_id}/courses/{course_id}/assignments",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return ListAssignmentsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAssignmentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAssignmentsOutput(success=False, error=f"Call failed: {exc}")

    assignments = [
        AssignmentSummary(
            id=a.get("id"),
            name=a.get("name"),
            description=a.get("description"),
            due_at=a.get("due_at"),
            points_possible=a.get("points_possible"),
            grading_type=a.get("grading_type"),
            submission_types=a.get("submission_types") or [],
            course_id=a.get("course_id"),
            allowed_attempts=a.get("allowed_attempts"),
            omit_from_final_grade=a.get("omit_from_final_grade"),
        )
        for a in data
        if isinstance(a, dict)
    ]
    return ListAssignmentsOutput(success=True, assignments=assignments)


@tool(args_schema=ListCoursesInput)
@serialize_pydantic_return
async def list_courses(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
) -> ListCoursesOutput:
    """List all courses associated with a given user."""
    err = _validate_auth(auth_data)
    if err:
        return ListCoursesOutput(success=False, error=err)
    base = _base_url(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base}/users/{user_id}/courses",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return ListCoursesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListCoursesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCoursesOutput(success=False, error=f"Call failed: {exc}")

    courses = [
        CourseSummary(
            id=c.get("id"),
            name=c.get("name"),
            course_code=c.get("course_code"),
            workflow_state=c.get("workflow_state"),
            enrollment_term_id=c.get("enrollment_term_id"),
        )
        for c in data
        if isinstance(c, dict)
    ]
    return ListCoursesOutput(success=True, courses=courses)


@tool(args_schema=SearchCourseContentInput)
@serialize_pydantic_return
async def search_course_content(
    auth_type: str,
    auth_data: dict[str, Any],
    course_id: str,
    query: str,
) -> SearchCourseContentOutput:
    """Search for content in a course using Canvas smart search."""
    err = _validate_auth(auth_data)
    if err:
        return SearchCourseContentOutput(success=False, error=err)
    base = _base_url(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base}/courses/{course_id}/smartsearch",
                headers=_headers(auth_data),
                params={"q": query},
            )
        if response.status_code != 200:
            return SearchCourseContentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchCourseContentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchCourseContentOutput(success=False, error=f"Call failed: {exc}")

    results = [
        SearchResultItem(
            content_id=r.get("content_id"),
            content_type=r.get("content_type"),
            title=r.get("title"),
            body=r.get("body"),
            html_url=r.get("html_url"),
            distance=r.get("distance"),
            readable_type=r.get("readable_type"),
            relevance=r.get("relevance"),
        )
        for r in (data if isinstance(data, list) else data.get("results", []))
        if isinstance(r, dict)
    ]
    return SearchCourseContentOutput(success=True, results=results)


@tool(args_schema=UpdateAssignmentInput)
@serialize_pydantic_return
async def update_assignment(
    auth_type: str,
    auth_data: dict[str, Any],
    course_id: str,
    assignment_id: str,
    name: str | None = None,
    description: str | None = None,
    submission_type: str | None = None,
    notify_of_update: bool | None = None,
    points_possible: int | None = None,
    grading_type: str | None = None,
    due_at: str | None = None,
    omit_from_final_grade: bool | None = None,
    allowed_attempts: int | None = None,
) -> UpdateAssignmentOutput:
    """Update an existing assignment in a course."""
    err = _validate_auth(auth_data)
    if err:
        return UpdateAssignmentOutput(success=False, error=err)

    assignment_body: dict[str, Any] = {}
    if name is not None:
        assignment_body["name"] = name
    if description is not None:
        assignment_body["description"] = description
    if submission_type is not None:
        assignment_body["submission_types"] = [submission_type]
    if notify_of_update is not None:
        assignment_body["notify_of_update"] = notify_of_update
    if points_possible is not None:
        assignment_body["points_possible"] = points_possible
    if grading_type is not None:
        assignment_body["grading_type"] = grading_type
    if due_at is not None:
        assignment_body["due_at"] = due_at
    if omit_from_final_grade is not None:
        assignment_body["omit_from_final_grade"] = omit_from_final_grade
    if allowed_attempts is not None:
        assignment_body["allowed_attempts"] = allowed_attempts

    if not assignment_body:
        return UpdateAssignmentOutput(
            success=False,
            error="At least one field to update must be provided.",
        )

    base = _base_url(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{base}/courses/{course_id}/assignments/{assignment_id}",
                headers=_headers(auth_data),
                json={"assignment": assignment_body},
            )
        if response.status_code != 200:
            return UpdateAssignmentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateAssignmentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateAssignmentOutput(success=False, error=f"Call failed: {exc}")

    a = data
    return UpdateAssignmentOutput(
        success=True,
        assignment=AssignmentSummary(
            id=a.get("id"),
            name=a.get("name"),
            description=a.get("description"),
            due_at=a.get("due_at"),
            points_possible=a.get("points_possible"),
            grading_type=a.get("grading_type"),
            submission_types=a.get("submission_types") or [],
            course_id=a.get("course_id"),
            allowed_attempts=a.get("allowed_attempts"),
            omit_from_final_grade=a.get("omit_from_final_grade"),
        ),
    )
