"""Tests for the ClickUp integration."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.clickup import (
    TOOLS,
    add_tag_to_task,
    create_folder,
    create_list,
    create_space,
    create_task,
    create_task_comment,
    delete_folder,
    delete_task,
    get_folder,
    get_folders,
    get_list,
    get_lists,
    get_space,
    get_space_tags,
    get_spaces,
    get_task,
    get_task_comments,
    get_tasks,
    get_team_members,
    get_teams,
    manifest,
    remove_tag_from_task,
    search_tasks,
    update_task,
)
from modulex_integrations.tools.clickup.outputs import (
    AddTagToTaskOutput,
    CreateFolderOutput,
    CreateListOutput,
    CreateSpaceOutput,
    CreateTaskCommentOutput,
    CreateTaskOutput,
    DeleteFolderOutput,
    DeleteTaskOutput,
    GetFolderOutput,
    GetFoldersOutput,
    GetListOutput,
    GetListsOutput,
    GetSpaceOutput,
    GetSpacesOutput,
    GetSpaceTagsOutput,
    GetTaskCommentsOutput,
    GetTaskOutput,
    GetTasksOutput,
    GetTeamMembersOutput,
    GetTeamsOutput,
    RemoveTagFromTaskOutput,
    SearchTasksOutput,
    UpdateTaskOutput,
)

API = "https://api.clickup.com/api/v2"
KEY = "pk_test_xxxx"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=KEY, **extra)


class TestManifest:
    def test_manifest_exposes_23_actions(self) -> None:
        assert len(manifest.actions) == 23

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_get_teams_missing_key() -> None:
    result = GetTeamsOutput.model_validate(
        await get_teams.ainvoke({"api_key": ""})
    )
    assert result.success is False
    assert result.error is not None and "empty" in result.error


@pytest.mark.asyncio
async def test_get_teams(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/team",
        json={"teams": [{"id": "t1", "name": "Workspace"}]},
    )
    result = GetTeamsOutput.model_validate(await get_teams.ainvoke(_args()))
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_get_spaces(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/team/t1/space?archived=false",
        json={"spaces": [{"id": "s1", "name": "Engineering"}]},
    )
    result = GetSpacesOutput.model_validate(
        await get_spaces.ainvoke(_args(team_id="t1"))
    )
    assert result.success is True
    assert result.team_id == "t1"


@pytest.mark.asyncio
async def test_get_space(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/space/s1", json={"id": "s1", "name": "Eng"}
    )
    result = GetSpaceOutput.model_validate(
        await get_space.ainvoke(_args(space_id="s1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_space(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/team/t1/space",
        status_code=201,
        json={"id": "s_new", "name": "New"},
    )
    result = CreateSpaceOutput.model_validate(
        await create_space.ainvoke(_args(team_id="t1", name="New"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_folders(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/space/s1/folder?archived=false",
        json={"folders": [{"id": "f1"}]},
    )
    result = GetFoldersOutput.model_validate(
        await get_folders.ainvoke(_args(space_id="s1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_folder(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/folder/f1", json={"id": "f1"}
    )
    result = GetFolderOutput.model_validate(
        await get_folder.ainvoke(_args(folder_id="f1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_folder(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/space/s1/folder",
        status_code=201,
        json={"id": "f_new"},
    )
    result = CreateFolderOutput.model_validate(
        await create_folder.ainvoke(_args(space_id="s1", name="X"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_folder(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/folder/f1", status_code=204
    )
    result = DeleteFolderOutput.model_validate(
        await delete_folder.ainvoke(_args(folder_id="f1"))
    )
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_get_lists_validates_xor() -> None:
    result = GetListsOutput.model_validate(
        await get_lists.ainvoke(_args())
    )
    assert result.success is False
    assert result.error is not None and "folder_id" in result.error


@pytest.mark.asyncio
async def test_get_lists_by_folder(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/folder/f1/list?archived=false",
        json={"lists": [{"id": "l1"}]},
    )
    result = GetListsOutput.model_validate(
        await get_lists.ainvoke(_args(folder_id="f1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_lists_by_space(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/space/s1/list?archived=false",
        json={"lists": []},
    )
    result = GetListsOutput.model_validate(
        await get_lists.ainvoke(_args(space_id="s1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/list/l1", json={"id": "l1"}
    )
    result = GetListOutput.model_validate(
        await get_list.ainvoke(_args(list_id="l1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/folder/f1/list",
        status_code=201,
        json={"id": "l_new"},
    )
    result = CreateListOutput.model_validate(
        await create_list.ainvoke(_args(folder_id="f1", name="X"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_tasks(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/list/l1/task\?.*"),
        json={"tasks": [{"id": "t1"}, {"id": "t2"}]},
    )
    result = GetTasksOutput.model_validate(
        await get_tasks.ainvoke(_args(list_id="l1", statuses=["open"]))
    )
    assert result.success is True
    assert result.count == 2


@pytest.mark.asyncio
async def test_get_task(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/task/t1", json={"id": "t1"}
    )
    result = GetTaskOutput.model_validate(
        await get_task.ainvoke(_args(task_id="t1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_task(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/list/l1/task",
        status_code=201,
        json={"id": "t_new"},
    )
    result = CreateTaskOutput.model_validate(
        await create_task.ainvoke(
            _args(list_id="l1", name="X", priority=2, assignees=[42])
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_task_requires_team_id_for_custom_ids() -> None:
    result = UpdateTaskOutput.model_validate(
        await update_task.ainvoke(
            _args(task_id="ABC-1", custom_task_ids=True, name="X")
        )
    )
    assert result.success is False
    assert result.error is not None and "team_id" in result.error


@pytest.mark.asyncio
async def test_update_task_assignees_diff_payload(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured.update(_json.loads(request.content.decode()))
        return Response(200, json={"id": "t1"})

    httpx_mock.add_callback(_capture, method="PUT", url=f"{API}/task/t1")
    result = UpdateTaskOutput.model_validate(
        await update_task.ainvoke(
            _args(
                task_id="t1",
                name="Renamed",
                assignees_add=[1, 2],
                assignees_remove=[3],
            )
        )
    )
    assert result.success is True
    assert captured["name"] == "Renamed"
    assert captured["assignees"] == {"add": [1, 2], "rem": [3]}


@pytest.mark.asyncio
async def test_delete_task(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/task/t1", status_code=204
    )
    result = DeleteTaskOutput.model_validate(
        await delete_task.ainvoke(_args(task_id="t1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_task_comments(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/task/t1/comment",
        json={"comments": [{"id": "c1"}]},
    )
    result = GetTaskCommentsOutput.model_validate(
        await get_task_comments.ainvoke(_args(task_id="t1"))
    )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_create_task_comment(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/task/t1/comment",
        status_code=201,
        json={"id": "c_new"},
    )
    result = CreateTaskCommentOutput.model_validate(
        await create_task_comment.ainvoke(
            _args(task_id="t1", comment_text="hi")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_search_tasks_client_side_query_filter(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/team/t1/task\?.*"),
        json={
            "tasks": [
                {"id": "1", "name": "Alpha task", "description": ""},
                {"id": "2", "name": "Beta task", "description": ""},
            ]
        },
    )
    result = SearchTasksOutput.model_validate(
        await search_tasks.ainvoke(
            _args(team_id="t1", query="alpha", include_closed=True)
        )
    )
    assert result.success is True
    assert result.count == 1
    assert result.tasks[0]["id"] == "1"


@pytest.mark.asyncio
async def test_get_space_tags(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/space/s1/tag",
        json={"tags": [{"name": "urgent"}]},
    )
    result = GetSpaceTagsOutput.model_validate(
        await get_space_tags.ainvoke(_args(space_id="s1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_add_tag_to_task(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{API}/task/t1/tag/urgent", status_code=200
    )
    result = AddTagToTaskOutput.model_validate(
        await add_tag_to_task.ainvoke(_args(task_id="t1", tag_name="urgent"))
    )
    assert result.success is True
    assert result.added is True


@pytest.mark.asyncio
async def test_remove_tag_from_task(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/task/t1/tag/urgent", status_code=204
    )
    result = RemoveTagFromTaskOutput.model_validate(
        await remove_tag_from_task.ainvoke(
            _args(task_id="t1", tag_name="urgent")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_team_members_filters_by_team_id(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/team",
        json={
            "teams": [
                {"id": "t1", "members": [{"user": {"id": 1}}]},
                {"id": "t2", "members": [{"user": {"id": 2}}]},
            ]
        },
    )
    result = GetTeamMembersOutput.model_validate(
        await get_team_members.ainvoke(_args(team_id="t1"))
    )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_get_team_members_not_found(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/team", json={"teams": []}
    )
    result = GetTeamMembersOutput.model_validate(
        await get_team_members.ainvoke(_args(team_id="missing"))
    )
    assert result.success is False
    assert result.error is not None and "not found" in result.error
