"""Happy-path tests for every motion @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.motion import (
    TOOLS,
    create_task,
    delete_task,
    get_schedules,
    get_task,
    manifest,
    move_workspace,
    update_task,
)
from modulex_integrations.tools.motion.outputs import (
    CreateTaskOutput,
    DeleteTaskOutput,
    GetSchedulesOutput,
    GetTaskOutput,
    MoveWorkspaceOutput,
    UpdateTaskOutput,
)

API = "https://api.usemotion.com/v1"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tasks",
        json={
            # TODO: fill in a representative response shape from the Motion API docs
            "id": "task_123",
            "name": "Test Task",
            "description": None,
            "status": {"name": "To Do", "isDefaultStatus": True, "isResolvedStatus": False},
            "workspaceId": "ws_1",
            "projectId": None,
            "priority": "MEDIUM",
            "assigneeId": None,
            "labels": [],
            "dueDate": None,
            "duration": None,
            "createdAt": "2023-06-28T10:00:00Z",
        },
    )

    result_dict = await create_task.ainvoke(
        _args(workspace_id="ws_1", name="Test Task")
    )

    assert isinstance(result_dict, dict)
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task is not None
    assert result.task.id == "task_123"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-API-Key"] == _API_KEY


@pytest.mark.asyncio
async def test_delete_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/tasks/task_456",
        status_code=204,
    )

    result_dict = await delete_task.ainvoke(_args(task_id="task_456"))

    assert isinstance(result_dict, dict)
    result = DeleteTaskOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_schedules(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/schedules",
        json=[
            # TODO: fill in a representative response shape from the Motion API docs
            {"id": "sched_1", "name": "Work Hours", "timezone": "America/New_York", "isDefault": True},
        ],
    )

    result_dict = await get_schedules.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetSchedulesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.schedules) == 1
    assert result.schedules[0].name == "Work Hours"


@pytest.mark.asyncio
async def test_get_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tasks/task_789",
        json={
            # TODO: fill in a representative response shape from the Motion API docs
            "id": "task_789",
            "name": "My Task",
            "description": "A description",
            "status": {"name": "In Progress", "isDefaultStatus": False, "isResolvedStatus": False},
            "workspaceId": "ws_1",
            "projectId": "proj_1",
            "priority": "HIGH",
            "assigneeId": "user_1",
            "labels": ["urgent"],
            "dueDate": "2023-07-01T00:00:00Z",
            "duration": "60",
            "createdAt": "2023-06-20T08:00:00Z",
        },
    )

    result_dict = await get_task.ainvoke(_args(task_id="task_789"))

    assert isinstance(result_dict, dict)
    result = GetTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task is not None
    assert result.task.name == "My Task"


@pytest.mark.asyncio
async def test_move_workspace(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/tasks/task_100/move",
        json={
            # TODO: fill in a representative response shape from the Motion API docs
            "id": "task_100",
            "name": "Moved Task",
            "description": None,
            "status": {"name": "To Do", "isDefaultStatus": True, "isResolvedStatus": False},
            "workspaceId": "ws_2",
            "projectId": None,
            "priority": "LOW",
            "assigneeId": None,
            "labels": [],
            "dueDate": None,
            "duration": None,
            "createdAt": "2023-06-15T12:00:00Z",
        },
    )

    result_dict = await move_workspace.ainvoke(
        _args(task_id="task_100", workspace_id="ws_2")
    )

    assert isinstance(result_dict, dict)
    result = MoveWorkspaceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task is not None
    assert result.task.workspace_id == "ws_2"


@pytest.mark.asyncio
async def test_update_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/tasks/task_200",
        json={
            # TODO: fill in a representative response shape from the Motion API docs
            "id": "task_200",
            "name": "Updated Task",
            "description": "New description",
            "status": {"name": "In Progress", "isDefaultStatus": False, "isResolvedStatus": False},
            "workspaceId": "ws_1",
            "projectId": "proj_2",
            "priority": "HIGH",
            "assigneeId": "user_2",
            "labels": ["review"],
            "dueDate": "2023-08-01T00:00:00Z",
            "duration": "30",
            "createdAt": "2023-06-10T09:00:00Z",
        },
    )

    result_dict = await update_task.ainvoke(
        _args(task_id="task_200", name="Updated Task", priority="HIGH")
    )

    assert isinstance(result_dict, dict)
    result = UpdateTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task is not None
    assert result.task.name == "Updated Task"


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_create_task_validates_empty_api_key() -> None:
    result_dict = await create_task.ainvoke(
        {"workspace_id": "ws_1", "name": "Test", "api_key": ""}
    )
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
