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
    return dict(auth_type="api_key", auth_data={"api_key": _API_KEY}, **extra)


def _gql(body: dict[str, Any]) -> dict[str, Any]:
    return body


class TestManifest:
    def test_manifest_exposes_seven_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2", "api_key"}


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
async def test_get_teams_after_cursor_is_a_variable_not_interpolated(
    httpx_mock: Any,
) -> None:
    """The pagination cursor must travel as a GraphQL variable, never be
    interpolated into the query string (injection-safe)."""
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json

        from httpx import Response

        captured.update(json.loads(request.content.decode()))
        return Response(
            200, json={"data": {"teams": {"nodes": [], "pageInfo": None}}}
        )

    httpx_mock.add_callback(_capture, method="POST", url=API)
    GetTeamsOutput.model_validate(await get_teams.ainvoke(_args(after='evil" x')))
    # Cursor is bound as a typed variable, not spliced into the query text.
    assert captured["variables"]["after"] == 'evil" x'
    assert "evil" not in captured["query"]
    assert "$after: String" in captured["query"]


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
async def test_create_issue_argument_validation_surfaces_reason(
    httpx_mock: Any,
) -> None:
    """A team KEY passed as team_id yields Linear's generic 'Argument
    Validation Error'; the real reason lives in extensions and must be
    surfaced so the failure is debuggable."""
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": None,
            "errors": [
                {
                    "message": "Argument Validation Error",
                    "path": ["issueCreate"],
                    "extensions": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "type": "invalid_input",
                        "userPresentableMessage": "teamId must be a UUID",
                        "userError": True,
                    },
                }
            ],
        },
    )
    result = CreateIssueOutput.model_validate(
        await create_issue.ainvoke(_args(team_id="ENG", title="x"))
    )
    assert result.success is False
    assert result.error is not None
    # Generic wrapper preserved, actionable reason appended.
    assert "Argument Validation Error" in result.error
    assert "teamId must be a UUID" in result.error


@pytest.mark.asyncio
async def test_graphql_error_falls_back_to_validation_constraints(
    httpx_mock: Any,
) -> None:
    """When Linear omits userPresentableMessage, per-field class-validator
    constraints are surfaced instead."""
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "errors": [
                {
                    "message": "Argument Validation Error",
                    "extensions": {
                        "type": "invalid_input",
                        "exception": {
                            "validationErrors": [
                                {
                                    "property": "priority",
                                    "constraints": {
                                        "max": "priority must not be greater than 4"
                                    },
                                }
                            ]
                        },
                    },
                }
            ]
        },
    )
    result = CreateIssueOutput.model_validate(
        await create_issue.ainvoke(_args(team_id="T1", title="x", priority=9))
    )
    assert result.success is False
    assert result.error is not None
    assert "priority must not be greater than 4" in result.error


@pytest.mark.asyncio
async def test_graphql_error_without_extensions_is_unchanged(
    httpx_mock: Any,
) -> None:
    """Errors carrying only a message (no extensions) keep their plain
    message — backwards compatible with non-validation failures."""
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"errors": [{"message": "Authentication required"}]},
    )
    result = CreateIssueOutput.model_validate(
        await create_issue.ainvoke(_args(team_id="T1", title="x"))
    )
    assert result.success is False
    assert result.error == "GraphQL errors: Authentication required"


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
async def test_empty_api_key_short_circuits() -> None:
    result = GetTeamsOutput.model_validate(
        await get_teams.ainvoke(
            {"auth_type": "api_key", "auth_data": {"api_key": ""}}
        )
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error


@pytest.mark.asyncio
async def test_empty_oauth_token_short_circuits() -> None:
    result = GetTeamsOutput.model_validate(
        await get_teams.ainvoke(
            {"auth_type": "oauth2", "auth_data": {"access_token": ""}}
        )
    )
    assert result.success is False
    assert result.error is not None and "access_token" in result.error


@pytest.mark.asyncio
async def test_unsupported_auth_type_short_circuits() -> None:
    result = GetTeamsOutput.model_validate(
        await get_teams.ainvoke(
            {"auth_type": "bearer_token", "auth_data": {"token": "x"}}
        )
    )
    assert result.success is False
    assert result.error is not None and "Unsupported auth_type" in result.error


def _capture_auth(captured: dict[str, Any]) -> Any:
    """httpx_mock callback that records the Authorization header and returns
    an empty teams page."""
    from httpx import Response

    def _cb(request: Any) -> Any:
        captured["auth"] = request.headers.get("Authorization")
        return Response(
            200, json={"data": {"teams": {"nodes": [], "pageInfo": None}}}
        )

    return _cb


@pytest.mark.asyncio
async def test_oauth2_sends_bearer_authorization(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}
    httpx_mock.add_callback(_capture_auth(captured), method="POST", url=API)
    result = GetTeamsOutput.model_validate(
        await get_teams.ainvoke(
            {"auth_type": "oauth2", "auth_data": {"access_token": "tok_123"}}
        )
    )
    assert result.success is True
    assert captured["auth"] == "Bearer tok_123"


@pytest.mark.asyncio
async def test_api_key_sends_raw_authorization(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}
    httpx_mock.add_callback(_capture_auth(captured), method="POST", url=API)
    GetTeamsOutput.model_validate(await get_teams.ainvoke(_args()))
    # Linear personal API keys go in Authorization WITHOUT a Bearer prefix.
    assert captured["auth"] == _API_KEY
