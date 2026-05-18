"""Happy-path tests for every jira @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.jira import (
    TOOLS,
    add_attachment_to_issue,
    add_comment_to_issue,
    add_multiple_attachments_to_issue,
    add_watcher_to_issue,
    assign_issue,
    check_issues_against_jql,
    count_issues_using_jql,
    create_custom_field_options_context,
    create_future_sprint,
    create_issue,
    create_version,
    delete_project,
    get_all_projects,
    get_board,
    get_cloud_id,
    get_current_user,
    get_issue,
    get_issue_picker_suggestions,
    get_issue_types,
    get_sprint,
    get_task,
    get_transitions,
    get_user,
    get_users,
    list_board_issues,
    list_boards,
    list_epic_issues,
    list_epics,
    list_issue_comments,
    list_labels_options,
    list_sprint_issues,
    list_sprints,
    manifest,
    move_issues_to_sprint,
    search_issues_with_jql,
    search_issues_with_jql_post,
    transition_issue,
    update_comment,
    update_issue,
)
from modulex_integrations.tools.jira.outputs import (
    AddAttachmentToIssueOutput,
    AddCommentToIssueOutput,
    AddMultipleAttachmentsToIssueOutput,
    AddWatcherToIssueOutput,
    AssignIssueOutput,
    CheckIssuesAgainstJqlOutput,
    CountIssuesUsingJqlOutput,
    CreateCustomFieldOptionsContextOutput,
    CreateFutureSprintOutput,
    CreateIssueOutput,
    CreateVersionOutput,
    DeleteProjectOutput,
    GetAllProjectsOutput,
    GetBoardOutput,
    GetCloudIdOutput,
    GetCurrentUserOutput,
    GetIssueOutput,
    GetIssuePickerSuggestionsOutput,
    GetIssueTypesOutput,
    GetSprintOutput,
    GetTaskOutput,
    GetTransitionsOutput,
    GetUserOutput,
    GetUsersOutput,
    ListBoardIssuesOutput,
    ListBoardsOutput,
    ListEpicIssuesOutput,
    ListEpicsOutput,
    ListIssueCommentsOutput,
    ListLabelsOptionsOutput,
    ListSprintIssuesOutput,
    ListSprintsOutput,
    MoveIssuesToSprintOutput,
    SearchIssuesWithJqlOutput,
    SearchIssuesWithJqlPostOutput,
    TransitionIssueOutput,
    UpdateCommentOutput,
    UpdateIssueOutput,
)

_CLOUD_API = "https://api.atlassian.com"
_CLOUD_ID = "fake-cloud-id"
_REST = f"{_CLOUD_API}/ex/jira/{_CLOUD_ID}/rest/api/3"
_AGILE = f"{_CLOUD_API}/ex/jira/{_CLOUD_ID}/rest/agile/1.0"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_38_actions(self) -> None:
        assert len(manifest.actions) == 38

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_get_cloud_id(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_CLOUD_API}/oauth/token/accessible-resources",
        json=[
            # TODO: fill in a representative response shape from the upstream API docs
            {"id": "abc-123", "url": "https://mysite.atlassian.net", "name": "My Site", "scopes": [], "avatarUrl": "https://example.com/avatar.png"}
        ],
    )

    result_dict = await get_cloud_id.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetCloudIdOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.sites) == 1
    assert result.sites[0].id == "abc-123"


@pytest.mark.asyncio
async def test_get_current_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/myself",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "accountId": "5b10ac8d82e05b22cc7d4ef5",
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "active": True,
            "avatarUrls": {"48x48": "https://example.com/avatar.png"},
            "accountType": "atlassian",
        },
    )

    result_dict = await get_current_user.ainvoke(_args(cloud_id=_CLOUD_ID))

    assert isinstance(result_dict, dict)
    result = GetCurrentUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.account_id == "5b10ac8d82e05b22cc7d4ef5"


@pytest.mark.asyncio
async def test_get_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/issue/TEST-1",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "10001",
            "key": "TEST-1",
            "self": "https://mysite.atlassian.net/rest/api/3/issue/10001",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "To Do"},
                "issuetype": {"name": "Task"},
                "priority": {"name": "Medium"},
                "assignee": {"displayName": "Test User"},
                "reporter": {"displayName": "Reporter"},
                "created": "2024-01-01T00:00:00.000+0000",
                "updated": "2024-01-02T00:00:00.000+0000",
            },
        },
    )

    result_dict = await get_issue.ainvoke(_args(cloud_id=_CLOUD_ID, issue_id_or_key="TEST-1"))

    assert isinstance(result_dict, dict)
    result = GetIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.issue is not None
    assert result.issue.key == "TEST-1"


@pytest.mark.asyncio
async def test_create_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/issue",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "10002",
            "key": "TEST-2",
            "self": "https://mysite.atlassian.net/rest/api/3/issue/10002",
        },
    )

    result_dict = await create_issue.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        project_id="10000",
        issue_type_id="10001",
        additional_properties={"summary": "New issue"},
    ))

    assert isinstance(result_dict, dict)
    result = CreateIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.key == "TEST-2"


@pytest.mark.asyncio
async def test_search_issues_with_jql(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/search/jql?jql=project+%3D+TEST&maxResults=10",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "issues": [
                {
                    "id": "10001",
                    "key": "TEST-1",
                    "self": "https://mysite.atlassian.net/rest/api/3/issue/10001",
                    "fields": {"summary": "Test", "status": {"name": "Done"}, "issuetype": {"name": "Task"}, "priority": {"name": "High"}, "assignee": None, "reporter": None, "created": None, "updated": None},
                }
            ],
            "total": 1,
            "startAt": 0,
            "maxResults": 10,
        },
    )

    result_dict = await search_issues_with_jql.ainvoke(_args(cloud_id=_CLOUD_ID, jql="project = TEST", max_results=10))

    assert isinstance(result_dict, dict)
    result = SearchIssuesWithJqlOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.issues) == 1


@pytest.mark.asyncio
async def test_list_boards(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_AGILE}/board",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "values": [{"id": 1, "name": "Board 1", "type": "scrum", "self": "https://example.com/board/1"}],
            "total": 1,
            "startAt": 0,
            "maxResults": 50,
        },
    )

    result_dict = await list_boards.ainvoke(_args(cloud_id=_CLOUD_ID))

    assert isinstance(result_dict, dict)
    result = ListBoardsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.boards) == 1
    assert result.boards[0].name == "Board 1"


@pytest.mark.asyncio
async def test_add_comment_to_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/issue/TEST-1/comment",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "10000",
            "self": "https://mysite.atlassian.net/rest/api/3/issue/TEST-1/comment/10000",
            "body": {"type": "doc", "version": 1, "content": []},
            "author": {"displayName": "Test User"},
            "created": "2024-01-01T00:00:00.000+0000",
            "updated": "2024-01-01T00:00:00.000+0000",
        },
    )

    result_dict = await add_comment_to_issue.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_id_or_key="TEST-1",
        comment="Hello world",
    ))

    assert isinstance(result_dict, dict)
    result = AddCommentToIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.comment is not None
    assert result.comment.id == "10000"


@pytest.mark.asyncio
async def test_transition_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/issue/TEST-1/transitions",
        status_code=204,
    )

    result_dict = await transition_issue.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_id_or_key="TEST-1",
        transition="31",
    ))

    assert isinstance(result_dict, dict)
    result = TransitionIssueOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_assign_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{_REST}/issue/TEST-1/assignee",
        status_code=204,
    )

    result_dict = await assign_issue.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_id_or_key="TEST-1",
        account_id="5b10ac8d82e05b22cc7d4ef5",
    ))

    assert isinstance(result_dict, dict)
    result = AssignIssueOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_transitions(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/issue/TEST-1/transitions",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "transitions": [
                {"id": "11", "name": "To Do", "to": {"name": "To Do"}, "hasScreen": False},
                {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}, "hasScreen": False},
            ]
        },
    )

    result_dict = await get_transitions.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_id_or_key="TEST-1",
    ))

    assert isinstance(result_dict, dict)
    result = GetTransitionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.transitions) == 2


@pytest.mark.asyncio
async def test_add_attachment_to_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/file.pdf",
        content=b"fake file content",
        headers={"content-type": "application/pdf"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/issue/TEST-1/attachments",
        json=[
            # TODO: fill in a representative response shape from the upstream API docs
            {"id": "10001", "filename": "file.pdf", "mimeType": "application/pdf", "size": 1234, "self": "https://mysite.atlassian.net/rest/api/3/attachment/10001"}
        ],
    )

    result_dict = await add_attachment_to_issue.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_id_or_key="TEST-1",
        file="https://example.com/file.pdf",
    ))

    assert isinstance(result_dict, dict)
    result = AddAttachmentToIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.filename == "file.pdf"


@pytest.mark.asyncio
async def test_add_multiple_attachments_to_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/a.txt",
        content=b"content a",
        headers={"content-type": "text/plain"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/issue/TEST-1/attachments",
        json=[{"id": "10002", "filename": "a.txt", "mimeType": "text/plain", "size": 9}],
    )

    result_dict = await add_multiple_attachments_to_issue.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_id_or_key="TEST-1",
        files=["https://example.com/a.txt"],
    ))

    assert isinstance(result_dict, dict)
    result = AddMultipleAttachmentsToIssueOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.attachments) == 1


@pytest.mark.asyncio
async def test_add_watcher_to_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/issue/TEST-1/watchers",
        status_code=204,
    )

    result_dict = await add_watcher_to_issue.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_id_or_key="TEST-1",
        account_id="5b10ac8d82e05b22cc7d4ef5",
    ))

    assert isinstance(result_dict, dict)
    result = AddWatcherToIssueOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_check_issues_against_jql(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/jql/match",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "matches": [{"issueId": 10001, "matchedJqls": ["project = TEST"]}]
        },
    )

    result_dict = await check_issues_against_jql.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_ids=[10001],
        jqls=["project = TEST"],
    ))

    assert isinstance(result_dict, dict)
    result = CheckIssuesAgainstJqlOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.matches) == 1


@pytest.mark.asyncio
async def test_count_issues_using_jql(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/search/approximate-count",
        json={"count": 42},
    )

    result_dict = await count_issues_using_jql.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        jql="project = TEST",
    ))

    assert isinstance(result_dict, dict)
    result = CountIssuesUsingJqlOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 42


@pytest.mark.asyncio
async def test_create_custom_field_options_context(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/field/customfield_10001/context/10100/option",
        json={"options": []},
    )

    result_dict = await create_custom_field_options_context.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        field_id="customfield_10001",
        context_id="10100",
    ))

    assert isinstance(result_dict, dict)
    result = CreateCustomFieldOptionsContextOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_future_sprint(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_AGILE}/sprint",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": 100, "name": "Sprint 1", "state": "future", "self": "https://example.com/sprint/100"
        },
    )

    result_dict = await create_future_sprint.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        board_id="1",
        name="Sprint 1",
    ))

    assert isinstance(result_dict, dict)
    result = CreateFutureSprintOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sprint is not None
    assert result.sprint.name == "Sprint 1"


@pytest.mark.asyncio
async def test_create_version(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/version",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "10001", "name": "v1.0", "self": "https://example.com/version/10001"
        },
    )

    result_dict = await create_version.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        project_id="10000",
        name="v1.0",
    ))

    assert isinstance(result_dict, dict)
    result = CreateVersionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.version is not None
    assert result.version.name == "v1.0"


@pytest.mark.asyncio
async def test_delete_project(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{_REST}/project/10000?enableUndo=true",
        status_code=204,
    )

    result_dict = await delete_project.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        project_id="10000",
        enable_undo=True,
    ))

    assert isinstance(result_dict, dict)
    result = DeleteProjectOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_all_projects(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/project/search",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "values": [{"id": "10000", "key": "TEST", "name": "Test Project", "projectTypeKey": "software", "self": "https://example.com/project/10000"}],
            "total": 1,
        },
    )

    result_dict = await get_all_projects.ainvoke(_args(cloud_id=_CLOUD_ID))

    assert isinstance(result_dict, dict)
    result = GetAllProjectsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.projects) == 1


@pytest.mark.asyncio
async def test_get_board(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_AGILE}/board/1",
        json={"id": 1, "name": "Board 1", "type": "scrum", "self": "https://example.com/board/1"},
    )

    result_dict = await get_board.ainvoke(_args(cloud_id=_CLOUD_ID, board_id="1"))

    assert isinstance(result_dict, dict)
    result = GetBoardOutput.model_validate(result_dict)
    assert result.success is True
    assert result.board is not None
    assert result.board.name == "Board 1"


@pytest.mark.asyncio
async def test_get_issue_picker_suggestions(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/issue/picker?query=test",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "sections": [{"label": "Recent", "issues": [{"id": 10001, "key": "TEST-1", "summaryText": "Test"}]}]
        },
    )

    result_dict = await get_issue_picker_suggestions.ainvoke(_args(cloud_id=_CLOUD_ID, query="test"))

    assert isinstance(result_dict, dict)
    result = GetIssuePickerSuggestionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.sections) == 1


@pytest.mark.asyncio
async def test_get_issue_types(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/issuetype",
        json=[
            # TODO: fill in a representative response shape from the upstream API docs
            {"id": "10001", "name": "Task", "description": "A task", "subtask": False, "self": "https://example.com/issuetype/10001"}
        ],
    )

    result_dict = await get_issue_types.ainvoke(_args(cloud_id=_CLOUD_ID))

    assert isinstance(result_dict, dict)
    result = GetIssueTypesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.issue_types) == 1


@pytest.mark.asyncio
async def test_get_sprint(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_AGILE}/sprint/100",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": 100, "name": "Sprint 1", "state": "active", "self": "https://example.com/sprint/100"
        },
    )

    result_dict = await get_sprint.ainvoke(_args(cloud_id=_CLOUD_ID, sprint_id="100"))

    assert isinstance(result_dict, dict)
    result = GetSprintOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sprint is not None
    assert result.sprint.name == "Sprint 1"


@pytest.mark.asyncio
async def test_get_task(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/task/task-001",
        json={"status": "COMPLETE", "progress": 100, "result": "done", "taskId": "task-001"},
    )

    result_dict = await get_task.ainvoke(_args(cloud_id=_CLOUD_ID, task_id="task-001"))

    assert isinstance(result_dict, dict)
    result = GetTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "COMPLETE"


@pytest.mark.asyncio
async def test_get_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/user?accountId=5b10ac8d82e05b22cc7d4ef5",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "accountId": "5b10ac8d82e05b22cc7d4ef5",
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "active": True,
            "avatarUrls": {"48x48": "https://example.com/avatar.png"},
            "accountType": "atlassian",
        },
    )

    result_dict = await get_user.ainvoke(_args(cloud_id=_CLOUD_ID, account_id="5b10ac8d82e05b22cc7d4ef5"))

    assert isinstance(result_dict, dict)
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.display_name == "Test User"


@pytest.mark.asyncio
async def test_get_users(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/user/search?query=User",
        json=[
            # TODO: fill in a representative response shape from the upstream API docs
            {"accountId": "abc", "displayName": "User A", "active": True, "avatarUrls": {"48x48": "https://example.com/a.png"}, "accountType": "atlassian"}
        ],
    )

    result_dict = await get_users.ainvoke(_args(cloud_id=_CLOUD_ID, query="User"))

    assert isinstance(result_dict, dict)
    result = GetUsersOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.users) == 1


@pytest.mark.asyncio
async def test_list_board_issues(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_AGILE}/board/1/issue",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "issues": [{"id": "10001", "key": "TEST-1", "fields": {"summary": "Test", "status": {"name": "Done"}, "issuetype": {"name": "Task"}, "priority": None, "assignee": None, "reporter": None, "created": None, "updated": None}}],
            "total": 1, "startAt": 0, "maxResults": 50,
        },
    )

    result_dict = await list_board_issues.ainvoke(_args(cloud_id=_CLOUD_ID, board_id="1"))

    assert isinstance(result_dict, dict)
    result = ListBoardIssuesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.issues) == 1


@pytest.mark.asyncio
async def test_list_epic_issues(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_AGILE}/board/1/epic/100/issue",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "issues": [{"id": "10001", "key": "TEST-1", "fields": {"summary": "Epic issue", "status": {"name": "To Do"}, "issuetype": {"name": "Story"}, "priority": None, "assignee": None, "reporter": None, "created": None, "updated": None}}],
            "total": 1, "startAt": 0, "maxResults": 50,
        },
    )

    result_dict = await list_epic_issues.ainvoke(_args(cloud_id=_CLOUD_ID, board_id="1", epic_id="100"))

    assert isinstance(result_dict, dict)
    result = ListEpicIssuesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.issues) == 1


@pytest.mark.asyncio
async def test_list_epics(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_AGILE}/board/1/epic",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "values": [{"id": 100, "key": "TEST-100", "name": "Epic 1", "summary": "Epic", "done": False, "self": "https://example.com/epic/100"}],
            "total": 1, "startAt": 0, "maxResults": 50,
        },
    )

    result_dict = await list_epics.ainvoke(_args(cloud_id=_CLOUD_ID, board_id="1"))

    assert isinstance(result_dict, dict)
    result = ListEpicsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.epics) == 1


@pytest.mark.asyncio
async def test_list_issue_comments(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/issue/TEST-1/comment",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "comments": [{"id": "10000", "self": "https://example.com/comment/10000", "body": {}, "author": {"displayName": "User"}, "created": "2024-01-01", "updated": "2024-01-01"}],
            "total": 1, "startAt": 0, "maxResults": 50,
        },
    )

    result_dict = await list_issue_comments.ainvoke(_args(cloud_id=_CLOUD_ID, issue_id_or_key="TEST-1"))

    assert isinstance(result_dict, dict)
    result = ListIssueCommentsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.comments) == 1


@pytest.mark.asyncio
async def test_list_labels_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_REST}/label",
        json={"values": ["bug", "feature", "docs"], "total": 3},
    )

    result_dict = await list_labels_options.ainvoke(_args(cloud_id=_CLOUD_ID))

    assert isinstance(result_dict, dict)
    result = ListLabelsOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.labels) == 3


@pytest.mark.asyncio
async def test_list_sprint_issues(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_AGILE}/sprint/100/issue",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "issues": [{"id": "10001", "key": "TEST-1", "fields": {"summary": "Sprint issue", "status": {"name": "In Progress"}, "issuetype": {"name": "Task"}, "priority": None, "assignee": None, "reporter": None, "created": None, "updated": None}}],
            "total": 1, "startAt": 0, "maxResults": 50,
        },
    )

    result_dict = await list_sprint_issues.ainvoke(_args(cloud_id=_CLOUD_ID, sprint_id="100"))

    assert isinstance(result_dict, dict)
    result = ListSprintIssuesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.issues) == 1


@pytest.mark.asyncio
async def test_list_sprints(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_AGILE}/board/1/sprint",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "values": [{"id": 100, "name": "Sprint 1", "state": "active", "self": "https://example.com/sprint/100"}],
            "total": 1, "startAt": 0, "maxResults": 50,
        },
    )

    result_dict = await list_sprints.ainvoke(_args(cloud_id=_CLOUD_ID, board_id="1"))

    assert isinstance(result_dict, dict)
    result = ListSprintsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.sprints) == 1


@pytest.mark.asyncio
async def test_move_issues_to_sprint(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_AGILE}/sprint/100/issue",
        status_code=204,
    )

    result_dict = await move_issues_to_sprint.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        sprint_id="100",
        issues=["TEST-1", "TEST-2"],
    ))

    assert isinstance(result_dict, dict)
    result = MoveIssuesToSprintOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_issues_with_jql_post(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_REST}/search/jql",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "issues": [{"id": "10001", "key": "TEST-1", "fields": {"summary": "Test", "status": {"name": "Done"}, "issuetype": {"name": "Task"}, "priority": None, "assignee": None, "reporter": None, "created": None, "updated": None}}],
            "total": 1,
        },
    )

    result_dict = await search_issues_with_jql_post.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        jql="project = TEST",
    ))

    assert isinstance(result_dict, dict)
    result = SearchIssuesWithJqlPostOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.issues) == 1


@pytest.mark.asyncio
async def test_update_comment(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{_REST}/issue/TEST-1/comment/10000",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "10000",
            "self": "https://example.com/comment/10000",
            "body": {"type": "doc", "version": 1, "content": []},
            "author": {"displayName": "User"},
            "created": "2024-01-01",
            "updated": "2024-01-02",
        },
    )

    result_dict = await update_comment.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        issue_id_or_key="TEST-1",
        comment_id="10000",
        comment="Updated text",
    ))

    assert isinstance(result_dict, dict)
    result = UpdateCommentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.comment is not None


@pytest.mark.asyncio
async def test_update_issue(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{_REST}/issue/TEST-1",
        status_code=204,
    )

    result_dict = await update_issue.ainvoke(_args(
        cloud_id=_CLOUD_ID,
        project_id="10000",
        issue_id_or_key="TEST-1",
        additional_properties={"summary": "Updated summary"},
    ))

    assert isinstance(result_dict, dict)
    result = UpdateIssueOutput.model_validate(result_dict)
    assert result.success is True
