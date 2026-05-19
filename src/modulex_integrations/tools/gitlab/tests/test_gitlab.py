"""Happy-path tests for every gitlab @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.gitlab import (
    TOOLS,
    create_branch,
    create_epic,
    create_issue,
    get_issue,
    get_repo_branch,
    list_commits,
    list_groups,
    list_project_members,
    list_repo_branches,
    manifest,
    search_issues,
    update_epic,
    update_issue,
)
from modulex_integrations.tools.gitlab.outputs import (
    CreateBranchOutput,
    CreateEpicOutput,
    CreateIssueOutput,
    GetIssueOutput,
    GetRepoBranchOutput,
    ListCommitsOutput,
    ListGroupsOutput,
    ListProjectMembersOutput,
    ListRepoBranchesOutput,
    SearchIssuesOutput,
    UpdateEpicOutput,
    UpdateIssueOutput,
)

API = "https://gitlab.com/api/v4"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_12_actions(self) -> None:
        assert len(manifest.actions) == 12

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_branch(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/projects/123/repository/branches?branch=feature-x&ref=main",
        json={
            # TODO: fill in a representative response shape from the GitLab API docs
            "name": "feature-x",
            "commit": {"id": "abc123", "short_id": "abc", "title": "init", "author_name": "dev", "author_email": "dev@example.com", "created_at": "2026-01-01T00:00:00Z", "message": "init"},
            "merged": False,
            "protected": False,
            "developers_can_push": False,
            "developers_can_merge": False,
            "can_push": True,
            "web_url": "https://gitlab.com/owner/repo/-/tree/feature-x",
        },
    )

    result_dict = await create_branch.ainvoke(_args(project_id=123, ref="main", branch_name="feature-x"))

    assert isinstance(result_dict, dict)
    result = CreateBranchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.branch is not None
    assert result.branch.name == "feature-x"


@pytest.mark.asyncio
async def test_create_epic(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/groups/42/epics",
        json={
            # TODO: fill in a representative response shape from the GitLab API docs
            "id": 1,
            "iid": 1,
            "group_id": 42,
            "title": "New Epic",
            "description": None,
            "state": "opened",
            "confidential": False,
            "web_url": "https://gitlab.com/groups/mygroup/-/epics/1",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "labels": [],
        },
    )

    result_dict = await create_epic.ainvoke(_args(group_id="42", title="New Epic"))

    assert isinstance(result_dict, dict)
    result = CreateEpicOutput.model_validate(result_dict)
    assert result.success is True
    assert result.epic is not None
    assert result.epic.title == "New Epic"


@pytest.mark.asyncio
async def test_create_issue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/projects/123/issues",
        json={
            # TODO: fill in a representative response shape from the GitLab API docs
            "id": 10,
            "iid": 5,
            "project_id": 123,
            "title": "Bug report",
            "description": "Something is broken",
            "state": "opened",
            "web_url": "https://gitlab.com/owner/repo/-/issues/5",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "closed_at": None,
            "labels": ["bug"],
            "assignees": [],
        },
    )

    result_dict = await create_issue.ainvoke(_args(project_id=123, title="Bug report", description="Something is broken"))

    assert isinstance(result_dict, dict)
    result = CreateIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.issue is not None
    assert result.issue.title == "Bug report"


@pytest.mark.asyncio
async def test_get_issue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects/123/issues/5",
        json={
            # TODO: fill in a representative response shape from the GitLab API docs
            "id": 10,
            "iid": 5,
            "project_id": 123,
            "title": "Bug report",
            "description": "Something is broken",
            "state": "opened",
            "web_url": "https://gitlab.com/owner/repo/-/issues/5",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "closed_at": None,
            "labels": [],
            "assignees": [],
        },
    )

    result_dict = await get_issue.ainvoke(_args(project_id=123, issue_iid="5"))

    assert isinstance(result_dict, dict)
    result = GetIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.issue is not None
    assert result.issue.iid == 5


@pytest.mark.asyncio
async def test_get_repo_branch(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects/123/repository/branches/main",
        json={
            # TODO: fill in a representative response shape from the GitLab API docs
            "name": "main",
            "commit": {"id": "abc123", "short_id": "abc", "title": "init", "author_name": "dev", "author_email": "dev@example.com", "created_at": "2026-01-01T00:00:00Z", "message": "init"},
            "merged": False,
            "protected": True,
            "developers_can_push": False,
            "developers_can_merge": False,
            "can_push": True,
            "web_url": "https://gitlab.com/owner/repo/-/tree/main",
        },
    )

    result_dict = await get_repo_branch.ainvoke(_args(project_id=123, branch="main"))

    assert isinstance(result_dict, dict)
    result = GetRepoBranchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.branch is not None
    assert result.branch.name == "main"


@pytest.mark.asyncio
async def test_list_commits(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects/123/repository/commits?per_page=100",
        json=[
            # TODO: fill in a representative response shape from the GitLab API docs
            {
                "id": "abc123",
                "short_id": "abc",
                "title": "Initial commit",
                "author_name": "dev",
                "author_email": "dev@example.com",
                "authored_date": "2026-01-01T00:00:00Z",
                "committed_date": "2026-01-01T00:00:00Z",
                "message": "Initial commit",
                "web_url": "https://gitlab.com/owner/repo/-/commit/abc123",
            },
        ],
    )

    result_dict = await list_commits.ainvoke(_args(project_id=123))

    assert isinstance(result_dict, dict)
    result = ListCommitsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.commits) == 1
    assert result.commits[0].title == "Initial commit"


@pytest.mark.asyncio
async def test_list_groups(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/groups?sort=asc",
        json=[
            # TODO: fill in a representative response shape from the GitLab API docs
            {
                "id": 42,
                "name": "My Group",
                "path": "my-group",
                "description": "A test group",
                "visibility": "private",
                "web_url": "https://gitlab.com/groups/my-group",
                "full_name": "My Group",
                "full_path": "my-group",
            },
        ],
    )

    result_dict = await list_groups.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListGroupsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.groups) == 1
    assert result.groups[0].name == "My Group"


@pytest.mark.asyncio
async def test_list_project_members(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects/123/members",
        json=[
            # TODO: fill in a representative response shape from the GitLab API docs
            {
                "id": 1,
                "username": "dev1",
                "name": "Developer One",
                "state": "active",
                "access_level": 30,
                "web_url": "https://gitlab.com/dev1",
            },
        ],
    )

    result_dict = await list_project_members.ainvoke(_args(project_id=123))

    assert isinstance(result_dict, dict)
    result = ListProjectMembersOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.members) == 1
    assert result.members[0].username == "dev1"


@pytest.mark.asyncio
async def test_list_repo_branches(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects/123/repository/branches",
        json=[
            # TODO: fill in a representative response shape from the GitLab API docs
            {
                "name": "main",
                "commit": {"id": "abc123", "short_id": "abc", "title": "init", "author_name": "dev", "author_email": "dev@example.com", "created_at": "2026-01-01T00:00:00Z", "message": "init"},
                "merged": False,
                "protected": True,
                "developers_can_push": False,
                "developers_can_merge": False,
                "can_push": True,
                "web_url": "https://gitlab.com/owner/repo/-/tree/main",
            },
        ],
    )

    result_dict = await list_repo_branches.ainvoke(_args(project_id=123))

    assert isinstance(result_dict, dict)
    result = ListRepoBranchesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.branches) == 1
    assert result.branches[0].name == "main"


@pytest.mark.asyncio
async def test_search_issues(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects/123/issues?scope=all&state=all&per_page=100",
        json=[
            # TODO: fill in a representative response shape from the GitLab API docs
            {
                "id": 10,
                "iid": 5,
                "project_id": 123,
                "title": "Bug report",
                "description": "Something is broken",
                "state": "opened",
                "web_url": "https://gitlab.com/owner/repo/-/issues/5",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "closed_at": None,
                "labels": [],
                "assignees": [],
            },
        ],
    )

    result_dict = await search_issues.ainvoke(_args(project_id=123))

    assert isinstance(result_dict, dict)
    result = SearchIssuesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.issues) == 1


@pytest.mark.asyncio
async def test_update_epic(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/groups/42/epics/1",
        json={
            # TODO: fill in a representative response shape from the GitLab API docs
            "id": 1,
            "iid": 1,
            "group_id": 42,
            "title": "Updated Epic",
            "description": None,
            "state": "opened",
            "confidential": False,
            "web_url": "https://gitlab.com/groups/mygroup/-/epics/1",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-02T00:00:00Z",
            "labels": [],
        },
    )

    result_dict = await update_epic.ainvoke(_args(group_id="42", epic_iid="1", title="Updated Epic"))

    assert isinstance(result_dict, dict)
    result = UpdateEpicOutput.model_validate(result_dict)
    assert result.success is True
    assert result.epic is not None
    assert result.epic.title == "Updated Epic"


@pytest.mark.asyncio
async def test_update_issue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/projects/123/issues/5",
        json={
            # TODO: fill in a representative response shape from the GitLab API docs
            "id": 10,
            "iid": 5,
            "project_id": 123,
            "title": "Updated Bug",
            "description": "Something is broken",
            "state": "opened",
            "web_url": "https://gitlab.com/owner/repo/-/issues/5",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-02T00:00:00Z",
            "closed_at": None,
            "labels": [],
            "assignees": [],
        },
    )

    result_dict = await update_issue.ainvoke(_args(project_id=123, issue_iid="5", title="Updated Bug"))

    assert isinstance(result_dict, dict)
    result = UpdateIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.issue is not None
    assert result.issue.title == "Updated Bug"
