"""Happy-path tests for every google_tasks @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_tasks import (
    TOOLS,
    create_task,
    create_task_list,
    delete_task,
    delete_task_list,
    list_task_lists,
    list_tasks,
    manifest,
    update_task,
    update_task_list,
)
from modulex_integrations.tools.google_tasks.outputs import (
    CreateTaskListOutput,
    CreateTaskOutput,
    DeleteTaskListOutput,
    DeleteTaskOutput,
    ListTaskListsOutput,
    ListTasksOutput,
    UpdateTaskListOutput,
    UpdateTaskOutput,
)

API = "https://tasks.googleapis.com/tasks/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_8_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lists/list1/tasks",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "kind": "tasks#task",
            "id": "task123",
            "etag": "\"etag\"",
            "title": "Buy groceries",
            "updated": "2026-05-22T00:00:00.000Z",
            "selfLink": "https://tasks.googleapis.com/tasks/v1/lists/list1/tasks/task123",
            "status": "needsAction",
        },
    )

    result_dict = await create_task.ainvoke(
        _args(task_list_id="list1", title="Buy groceries", completed=False)
    )

    assert isinstance(result_dict, dict)
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task is not None
    assert result.task.id == "task123"


@pytest.mark.asyncio
async def test_create_task_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/@me/lists",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "kind": "tasks#taskList",
            "id": "list456",
            "etag": "\"etag\"",
            "title": "Shopping",
            "updated": "2026-05-22T00:00:00.000Z",
            "selfLink": "https://tasks.googleapis.com/tasks/v1/users/@me/lists/list456",
        },
    )

    result_dict = await create_task_list.ainvoke(_args(title="Shopping"))

    assert isinstance(result_dict, dict)
    result = CreateTaskListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task_list is not None
    assert result.task_list.id == "list456"


@pytest.mark.asyncio
async def test_delete_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/lists/list1/tasks/task123",
        status_code=204,
    )

    result_dict = await delete_task.ainvoke(
        _args(task_list_id="list1", task_id="task123")
    )

    assert isinstance(result_dict, dict)
    result = DeleteTaskOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_task_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/users/@me/lists/list1",
        status_code=204,
    )

    result_dict = await delete_task_list.ainvoke(_args(task_list_id="list1"))

    assert isinstance(result_dict, dict)
    result = DeleteTaskListOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_tasks(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lists/list1/tasks?maxResults=20",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "kind": "tasks#tasks",
            "items": [
                {
                    "kind": "tasks#task",
                    "id": "task1",
                    "title": "Task one",
                    "status": "needsAction",
                    "updated": "2026-05-22T00:00:00.000Z",
                },
                {
                    "kind": "tasks#task",
                    "id": "task2",
                    "title": "Task two",
                    "status": "completed",
                    "updated": "2026-05-22T00:00:00.000Z",
                },
            ],
        },
    )

    result_dict = await list_tasks.ainvoke(_args(task_list_id="list1"))

    assert isinstance(result_dict, dict)
    result = ListTasksOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.tasks) == 2


@pytest.mark.asyncio
async def test_list_task_lists(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/@me/lists?maxResults=20",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "kind": "tasks#taskLists",
            "items": [
                {
                    "kind": "tasks#taskList",
                    "id": "list1",
                    "title": "My Tasks",
                    "updated": "2026-05-22T00:00:00.000Z",
                },
            ],
        },
    )

    result_dict = await list_task_lists.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTaskListsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.task_lists) == 1


@pytest.mark.asyncio
async def test_update_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/lists/list1/tasks/task123",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "kind": "tasks#task",
            "id": "task123",
            "etag": "\"etag\"",
            "title": "Updated title",
            "updated": "2026-05-22T00:00:00.000Z",
            "selfLink": "https://tasks.googleapis.com/tasks/v1/lists/list1/tasks/task123",
            "status": "needsAction",
        },
    )

    result_dict = await update_task.ainvoke(
        _args(task_list_id="list1", task_id="task123", title="Updated title")
    )

    assert isinstance(result_dict, dict)
    result = UpdateTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task is not None
    assert result.task.title == "Updated title"


@pytest.mark.asyncio
async def test_create_task_api_error(httpx_mock):  # type: ignore[no-untyped-def]
    """Failure-path: non-2xx response returns success=False with error message."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lists/list1/tasks",
        status_code=403,
        text="Forbidden",
    )

    result_dict = await create_task.ainvoke(
        _args(task_list_id="list1", title="Denied task", completed=False)
    )

    assert isinstance(result_dict, dict)
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "403" in result.error


@pytest.mark.asyncio
async def test_update_task_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/users/@me/lists/list1",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "kind": "tasks#taskList",
            "id": "list1",
            "etag": "\"etag\"",
            "title": "Renamed list",
            "updated": "2026-05-22T00:00:00.000Z",
            "selfLink": "https://tasks.googleapis.com/tasks/v1/users/@me/lists/list1",
        },
    )

    result_dict = await update_task_list.ainvoke(
        _args(task_list_id="list1", title="Renamed list")
    )

    assert isinstance(result_dict, dict)
    result = UpdateTaskListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task_list is not None
    assert result.task_list.title == "Renamed list"
