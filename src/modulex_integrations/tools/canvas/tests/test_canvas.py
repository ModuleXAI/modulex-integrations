"""Happy-path tests for every canvas @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.canvas import (
    TOOLS,
    list_accounts,
    list_assignments,
    list_courses,
    manifest,
    search_course_content,
    update_assignment,
)
from modulex_integrations.tools.canvas.outputs import (
    ListAccountsOutput,
    ListAssignmentsOutput,
    ListCoursesOutput,
    SearchCourseContentOutput,
    UpdateAssignmentOutput,
)

API = "https://myschool.instructure.com/api/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "domain": "myschool.instructure.com",
        "access_token": "fake_token",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_5_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_list_accounts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts",
        json=[
            # TODO: fill in a representative response shape from the Canvas API docs
            {"id": 1, "name": "Default Account"},
        ],
    )

    result_dict = await list_accounts.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAccountsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.accounts) == 1
    assert result.accounts[0].id == 1


@pytest.mark.asyncio
async def test_list_assignments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/42/courses/101/assignments",
        json=[
            # TODO: fill in a representative response shape from the Canvas API docs
            {
                "id": 1,
                "name": "Homework 1",
                "due_at": "2024-10-21T18:48:00Z",
                "points_possible": 100,
                "grading_type": "points",
                "submission_types": ["online_upload"],
                "course_id": 101,
            },
        ],
    )

    result_dict = await list_assignments.ainvoke(_args(user_id="42", course_id="101"))

    assert isinstance(result_dict, dict)
    result = ListAssignmentsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.assignments) == 1
    assert result.assignments[0].name == "Homework 1"


@pytest.mark.asyncio
async def test_list_courses(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/42/courses",
        json=[
            # TODO: fill in a representative response shape from the Canvas API docs
            {
                "id": 101,
                "name": "Introduction to AI",
                "course_code": "CS101",
                "workflow_state": "available",
                "enrollment_term_id": 1,
            },
        ],
    )

    result_dict = await list_courses.ainvoke(_args(user_id="42"))

    assert isinstance(result_dict, dict)
    result = ListCoursesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.courses) == 1
    assert result.courses[0].name == "Introduction to AI"


@pytest.mark.asyncio
async def test_search_course_content(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/courses/101/smartsearch?q=machine+learning",
        json=[
            # TODO: fill in a representative response shape from the Canvas API docs
            {
                "content_id": 5,
                "content_type": "WikiPage",
                "title": "Machine Learning Basics",
                "body": "An introduction to ML...",
                "html_url": "https://myschool.instructure.com/courses/101/pages/ml-basics",
                "relevance": 0.95,
            },
        ],
    )

    result_dict = await search_course_content.ainvoke(
        _args(course_id="101", query="machine learning")
    )

    assert isinstance(result_dict, dict)
    result = SearchCourseContentOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.results) == 1
    assert result.results[0].title == "Machine Learning Basics"


@pytest.mark.asyncio
async def test_update_assignment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/courses/101/assignments/1",
        json={
            # TODO: fill in a representative response shape from the Canvas API docs
            "id": 1,
            "name": "Updated Homework",
            "description": "New description",
            "due_at": "2024-11-01T23:59:00Z",
            "points_possible": 150,
            "grading_type": "points",
            "submission_types": ["online_upload"],
            "course_id": 101,
            "allowed_attempts": 3,
            "omit_from_final_grade": False,
        },
    )

    result_dict = await update_assignment.ainvoke(
        _args(
            course_id="101",
            assignment_id="1",
            name="Updated Homework",
            points_possible=150,
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateAssignmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.assignment is not None
    assert result.assignment.name == "Updated Homework"
    assert result.assignment.points_possible == 150


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_list_accounts_empty_credentials() -> None:
    """Empty credentials should return success=False without hitting the wire."""
    result_dict = await list_accounts.ainvoke(
        {"auth_type": "custom", "auth_data": {"domain": "", "access_token": ""}}
    )

    assert isinstance(result_dict, dict)
    result = ListAccountsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
