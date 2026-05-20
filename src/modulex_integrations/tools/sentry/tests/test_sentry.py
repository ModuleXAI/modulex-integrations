"""Happy-path tests for every sentry @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.sentry import (
    TOOLS,
    list_issue_events,
    list_project_events,
    list_project_issues,
    manifest,
    update_issue,
)
from modulex_integrations.tools.sentry.outputs import (
    ListIssueEventsOutput,
    ListProjectEventsOutput,
    ListProjectIssuesOutput,
    UpdateIssueOutput,
)

API = "https://sentry.io/api/0"

_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "fake_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_bearer_token_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"bearer_token"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_list_issue_events(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/issues/12345/events/",
        json=[
            {
                "eventID": "evt-1",
                "title": "ZeroDivisionError",
                "message": "division by zero",
                "platform": "python",
                "dateCreated": "2026-01-01T00:00:00Z",
                "dateReceived": "2026-01-01T00:00:01Z",
                "tags": [{"key": "level", "value": "error"}],
            },
        ],
    )

    result_dict = await list_issue_events.ainvoke(_args(issue_id="12345"))

    assert isinstance(result_dict, dict)
    result = ListIssueEventsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.events) == 1
    assert result.events[0].event_id == "evt-1"


@pytest.mark.asyncio
async def test_list_project_events(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects/my-org/my-project/events/",
        json=[
            {
                "eventID": "evt-2",
                "title": "TypeError",
                "message": "cannot read property",
                "platform": "javascript",
                "dateCreated": "2026-01-02T00:00:00Z",
                "dateReceived": "2026-01-02T00:00:01Z",
                "tags": [],
            },
        ],
    )

    result_dict = await list_project_events.ainvoke(
        _args(organization_slug="my-org", project_slug="my-project")
    )

    assert isinstance(result_dict, dict)
    result = ListProjectEventsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.events) == 1
    assert result.events[0].event_id == "evt-2"


@pytest.mark.asyncio
async def test_list_project_issues(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects/my-org/my-project/issues/",
        json=[
            {
                "id": "99",
                "title": "NullPointerException",
                "shortId": "MY-PROJECT-99",
                "status": "unresolved",
                "level": "error",
                "permalink": "https://sentry.io/issues/99/",
                "assignedTo": None,
                "hasSeen": False,
                "isBookmarked": False,
                "isPublic": False,
                "count": "42",
                "firstSeen": "2026-01-01T00:00:00Z",
                "lastSeen": "2026-01-05T00:00:00Z",
            },
        ],
    )

    result_dict = await list_project_issues.ainvoke(
        _args(organization_slug="my-org", project_slug="my-project")
    )

    assert isinstance(result_dict, dict)
    result = ListProjectIssuesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.issues) == 1
    assert result.issues[0].id == "99"


@pytest.mark.asyncio
async def test_update_issue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/issues/99/",
        json={
            "id": "99",
            "title": "NullPointerException",
            "shortId": "MY-PROJECT-99",
            "status": "resolved",
            "level": "error",
            "permalink": "https://sentry.io/issues/99/",
            "assignedTo": None,
            "hasSeen": True,
            "isBookmarked": False,
            "isPublic": False,
            "count": "42",
            "firstSeen": "2026-01-01T00:00:00Z",
            "lastSeen": "2026-01-05T00:00:00Z",
        },
    )

    result_dict = await update_issue.ainvoke(
        _args(issue_id="99", status="resolved")
    )

    assert isinstance(result_dict, dict)
    result = UpdateIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.issue is not None
    assert result.issue.status == "resolved"


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_list_issue_events_empty_token():  # type: ignore[no-untyped-def]
    """Empty token should return success=False without hitting the wire."""
    result_dict = await list_issue_events.ainvoke(
        {"auth_type": "bearer_token", "auth_data": {"token": ""}, "issue_id": "12345"}
    )
    assert isinstance(result_dict, dict)
    result = ListIssueEventsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "token" in result.error.lower()
