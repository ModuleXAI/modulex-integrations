"""Tests for the Linear integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.linear import (
    TOOLS,
    create_issue,
    create_project,
    get_issue,
    get_teams,
    list_projects,
    manifest,
    search_issues,
    update_issue,
)
from modulex_integrations.tools.linear.outputs import (
    CreateIssueOutput,
    CreateProjectOutput,
    GetIssueOutput,
    GetTeamsOutput,
    ListProjectsOutput,
    SearchIssuesOutput,
    UpdateIssueOutput,
)

API = "https://api.linear.app/graphql"
_API_KEY = "lin_api_fake"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _gql(body: dict[str, Any]) -> dict[str, Any]:
    return body


class TestManifest:
    def test_manifest_exposes_seven_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_get_teams(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "teams": {
                    "nodes": [
                        {"id": "T1", "name": "Backend", "key": "BE"},
                        {"id": "T2", "name": "Frontend", "key": "FE"},
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
    )

    result_dict = await get_teams.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetTeamsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 2
    assert result.teams[0]["key"] == "BE"


@pytest.mark.asyncio
async def test_get_teams_http_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="POST", url=API, status_code=401, text="unauthorized")
    result = GetTeamsOutput.model_validate(await get_teams.ainvoke(_args()))
    assert result.success is False
    assert result.error is not None and "401" in result.error


@pytest.mark.asyncio
async def test_get_teams_graphql_errors(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"errors": [{"message": "Authentication required"}]},
    )
    result = GetTeamsOutput.model_validate(await get_teams.ainvoke(_args()))
    assert result.success is False
    assert result.error is not None and "Authentication required" in result.error


@pytest.mark.asyncio
async def test_get_issue(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "issue": {
                    "id": "I1",
                    "identifier": "BE-1",
                    "title": "Fix bug",
                    "state": {"id": "S1", "name": "Todo", "type": "unstarted"},
                }
            }
        },
    )
    result = GetIssueOutput.model_validate(
        await get_issue.ainvoke(_args(issue_id="I1"))
    )
    assert result.success is True
    assert result.issue is not None
    assert result.issue["identifier"] == "BE-1"


@pytest.mark.asyncio
async def test_get_issue_not_found(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=API, json={"data": {"issue": None}}
    )
    result = GetIssueOutput.model_validate(
        await get_issue.ainvoke(_args(issue_id="missing"))
    )
    assert result.success is False
    assert result.error is not None and "missing" in result.error


@pytest.mark.asyncio
async def test_search_issues_interpolates_filters(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(
            200,
            json={
                "data": {
                    "issues": {
                        "nodes": [{"id": "I1", "identifier": "BE-1", "title": "x"}],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            },
        )

    httpx_mock.add_callback(_capture, method="POST", url=API)
    result = SearchIssuesOutput.model_validate(
        await search_issues.ainvoke(
            _args(team_id="T1", query="bug", label_names=["urgent", "bug"], limit=10)
        )
    )
    assert result.success is True
    assert result.count == 1
    # The filter clause is interpolated in the GraphQL string.
    q = captured["query"]
    assert 'team: { id: { eq: "T1" } }' in q
    assert 'title: { containsIgnoreCase: "bug" }' in q
    assert 'labels: { name: { in: ["urgent", "bug"] } }' in q
    # Variables carry pagination + ordering.
    assert captured["variables"] == {
        "first": 10,
        "includeArchived": False,
        "orderBy": "updatedAt",
    }


@pytest.mark.asyncio
async def test_create_issue(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "I99",
                        "identifier": "BE-99",
                        "title": "New bug",
                    },
                }
            }
        },
    )
    result = CreateIssueOutput.model_validate(
        await create_issue.ainvoke(_args(team_id="T1", title="New bug", priority=2))
    )
    assert result.success is True
    assert result.issue is not None
    assert result.issue["identifier"] == "BE-99"


@pytest.mark.asyncio
async def test_create_issue_mutation_failure(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"issueCreate": {"success": False, "issue": None}}},
    )
    result = CreateIssueOutput.model_validate(
        await create_issue.ainvoke(_args(team_id="T1", title="x"))
    )
    assert result.success is False
    assert result.error is not None and "create" in result.error


@pytest.mark.asyncio
async def test_update_issue_requires_some_field() -> None:
    result = UpdateIssueOutput.model_validate(
        await update_issue.ainvoke(_args(issue_id="I1"))
    )
    assert result.success is False
    assert result.error is not None and "update fields" in result.error


@pytest.mark.asyncio
async def test_update_issue(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": {"id": "I1", "identifier": "BE-1", "title": "New title"},
                }
            }
        },
    )
    result = UpdateIssueOutput.model_validate(
        await update_issue.ainvoke(_args(issue_id="I1", title="New title"))
    )
    assert result.success is True
    assert result.issue is not None
    assert result.issue["title"] == "New title"


@pytest.mark.asyncio
async def test_list_projects(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "projects": {
                    "nodes": [{"id": "P1", "name": "Q3 roadmap", "state": "started"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
    )
    result = ListProjectsOutput.model_validate(
        await list_projects.ainvoke(_args(team_id="T1", limit=5))
    )
    assert result.success is True
    assert result.count == 1
    assert result.projects[0]["name"] == "Q3 roadmap"


@pytest.mark.asyncio
async def test_create_project(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "projectCreate": {
                    "success": True,
                    "project": {"id": "P99", "name": "New project"},
                }
            }
        },
    )
    result = CreateProjectOutput.model_validate(
        await create_project.ainvoke(_args(team_id="T1", name="New project"))
    )
    assert result.success is True
    assert result.project is not None
    assert result.project["id"] == "P99"


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = GetTeamsOutput.model_validate(await get_teams.ainvoke({"api_key": ""}))
    assert result.success is False
    assert result.error is not None and "API key" in result.error
