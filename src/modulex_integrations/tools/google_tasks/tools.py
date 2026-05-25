"""Google Tasks LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_tasks.outputs import (
    CreateTaskListOutput,
    CreateTaskOutput,
    DeleteTaskListOutput,
    DeleteTaskOutput,
    ListTaskListsOutput,
    ListTasksOutput,
    TaskItem,
    TaskListItem,
    UpdateTaskListOutput,
    UpdateTaskOutput,
)

__all__ = [
    "create_task",
    "create_task_list",
    "delete_task",
    "delete_task_list",
    "list_task_lists",
    "list_tasks",
    "update_task",
    "update_task_list",
]

_BASE_URL = "https://tasks.googleapis.com/tasks/v1"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google Tasks API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _parse_task(data: dict[str, Any]) -> TaskItem:
    return TaskItem(
        id=data.get("id"),
        title=data.get("title"),
        notes=data.get("notes"),
        status=data.get("status"),
        due=data.get("due"),
        updated=data.get("updated"),
        self_link=data.get("selfLink"),
        etag=data.get("etag"),
        kind=data.get("kind"),
    )


def _parse_task_list(data: dict[str, Any]) -> TaskListItem:
    return TaskListItem(
        id=data.get("id"),
        title=data.get("title"),
        updated=data.get("updated"),
        self_link=data.get("selfLink"),
        etag=data.get("etag"),
        kind=data.get("kind"),
    )


# --- Input schemas --------------------------------------------------------


class CreateTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    task_list_id: str = Field(description="The ID of the task list")
    title: str = Field(description="The title of the task")
    notes: str | None = Field(default=None, description="The description of the task")
    completed: bool = Field(description="Mark as true if your task is already completed")
    due: str | None = Field(default=None, description="Due date of the task as an RFC 3339 timestamp (date portion only)")


class CreateTaskListInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="The title of the task list")


class DeleteTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    task_list_id: str = Field(description="The ID of the task list")
    task_id: str = Field(description="The ID of the task")


class DeleteTaskListInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    task_list_id: str = Field(description="The ID of the task list")


class ListTasksInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    task_list_id: str = Field(description="The ID of the task list")
    max_results: int = Field(default=20, description="Maximum number of tasks to be fetched")
    show_completed: bool | None = Field(default=None, description="Whether completed tasks are returned in the result")
    show_deleted: bool | None = Field(default=None, description="Whether deleted tasks are returned in the result")


class ListTaskListsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_results: int = Field(default=20, description="Maximum number of task lists to be fetched")


class UpdateTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    task_list_id: str = Field(description="The ID of the task list")
    task_id: str = Field(description="The ID of the task")
    title: str = Field(description="The title of the task")
    notes: str | None = Field(default=None, description="The description of the task")
    completed: bool | None = Field(default=None, description="Mark as true if your task is already completed")
    due: str | None = Field(default=None, description="Due date of the task as an RFC 3339 timestamp (date portion only)")


class UpdateTaskListInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    task_list_id: str = Field(description="The ID of the task list")
    title: str = Field(description="The title of the task list")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    auth_type: str,
    auth_data: dict[str, Any],
    task_list_id: str,
    title: str,
    completed: bool,
    notes: str | None = None,
    due: str | None = None,
) -> CreateTaskOutput:
    """Creates a new task and adds it to the authenticated user's task lists"""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {
        "title": title,
        "status": "completed" if completed else "needsAction",
    }
    if notes is not None:
        body["notes"] = notes
    if due is not None:
        body["due"] = due
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/lists/{task_list_id}/tasks",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateTaskOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTaskOutput(success=False, error=f"Call failed: {exc}")
    return CreateTaskOutput(success=True, task=_parse_task(data))


@tool(args_schema=CreateTaskListInput)
@serialize_pydantic_return
async def create_task_list(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
) -> CreateTaskListOutput:
    """Creates a new task list and adds it to the authenticated user's task lists"""
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/users/@me/lists",
                headers=headers,
                json={"title": title},
            )
        if response.status_code not in (200, 201):
            return CreateTaskListOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateTaskListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTaskListOutput(success=False, error=f"Call failed: {exc}")
    return CreateTaskListOutput(success=True, task_list=_parse_task_list(data))


@tool(args_schema=DeleteTaskInput)
@serialize_pydantic_return
async def delete_task(
    auth_type: str,
    auth_data: dict[str, Any],
    task_list_id: str,
    task_id: str,
) -> DeleteTaskOutput:
    """Deletes the authenticated user's specified task"""
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/lists/{task_list_id}/tasks/{task_id}",
                headers=headers,
            )
        if response.status_code not in (200, 204):
            return DeleteTaskOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteTaskOutput(success=False, error=f"Call failed: {exc}")
    return DeleteTaskOutput(success=True)


@tool(args_schema=DeleteTaskListInput)
@serialize_pydantic_return
async def delete_task_list(
    auth_type: str,
    auth_data: dict[str, Any],
    task_list_id: str,
) -> DeleteTaskListOutput:
    """Deletes the authenticated user's specified task list"""
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/users/@me/lists/{task_list_id}",
                headers=headers,
            )
        if response.status_code not in (200, 204):
            return DeleteTaskListOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteTaskListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteTaskListOutput(success=False, error=f"Call failed: {exc}")
    return DeleteTaskListOutput(success=True)


@tool(args_schema=ListTasksInput)
@serialize_pydantic_return
async def list_tasks(
    auth_type: str,
    auth_data: dict[str, Any],
    task_list_id: str,
    max_results: int = 20,
    show_completed: bool | None = None,
    show_deleted: bool | None = None,
) -> ListTasksOutput:
    """Returns all tasks in the specified task list"""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"maxResults": min(max_results, 100)}
    if show_completed is not None:
        params["showCompleted"] = str(show_completed).lower()
    if show_deleted is not None:
        params["showDeleted"] = str(show_deleted).lower()
    all_tasks: list[TaskItem] = []
    page_token: str | None = None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while True:
                if page_token:
                    params["pageToken"] = page_token
                response = await client.get(
                    f"{_BASE_URL}/lists/{task_list_id}/tasks",
                    headers=headers,
                    params=params,
                )
                if response.status_code != 200:
                    return ListTasksOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                for item in data.get("items", []):
                    all_tasks.append(_parse_task(item))
                    if len(all_tasks) >= max_results:
                        break
                if len(all_tasks) >= max_results:
                    break
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
    except httpx.TimeoutException:
        return ListTasksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTasksOutput(success=False, error=f"Call failed: {exc}")
    return ListTasksOutput(success=True, tasks=all_tasks)


@tool(args_schema=ListTaskListsInput)
@serialize_pydantic_return
async def list_task_lists(
    auth_type: str,
    auth_data: dict[str, Any],
    max_results: int = 20,
) -> ListTaskListsOutput:
    """Lists the authenticated user's task lists"""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"maxResults": min(max_results, 100)}
    all_lists: list[TaskListItem] = []
    page_token: str | None = None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while True:
                if page_token:
                    params["pageToken"] = page_token
                response = await client.get(
                    f"{_BASE_URL}/users/@me/lists",
                    headers=headers,
                    params=params,
                )
                if response.status_code != 200:
                    return ListTaskListsOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                for item in data.get("items", []):
                    all_lists.append(_parse_task_list(item))
                    if len(all_lists) >= max_results:
                        break
                if len(all_lists) >= max_results:
                    break
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
    except httpx.TimeoutException:
        return ListTaskListsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTaskListsOutput(success=False, error=f"Call failed: {exc}")
    return ListTaskListsOutput(success=True, task_lists=all_lists)


@tool(args_schema=UpdateTaskInput)
@serialize_pydantic_return
async def update_task(
    auth_type: str,
    auth_data: dict[str, Any],
    task_list_id: str,
    task_id: str,
    title: str,
    notes: str | None = None,
    completed: bool | None = None,
    due: str | None = None,
) -> UpdateTaskOutput:
    """Updates the authenticated user's specified task"""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"id": task_id, "title": title}
    if notes is not None:
        body["notes"] = notes
    if completed is not None:
        body["status"] = "completed" if completed else "needsAction"
    if due is not None:
        body["due"] = due
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/lists/{task_list_id}/tasks/{task_id}",
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return UpdateTaskOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateTaskOutput(success=False, error=f"Call failed: {exc}")
    return UpdateTaskOutput(success=True, task=_parse_task(data))


@tool(args_schema=UpdateTaskListInput)
@serialize_pydantic_return
async def update_task_list(
    auth_type: str,
    auth_data: dict[str, Any],
    task_list_id: str,
    title: str,
) -> UpdateTaskListOutput:
    """Updates the authenticated user's specified task list"""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"id": task_list_id, "title": title}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/users/@me/lists/{task_list_id}",
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return UpdateTaskListOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateTaskListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateTaskListOutput(success=False, error=f"Call failed: {exc}")
    return UpdateTaskListOutput(success=True, task_list=_parse_task_list(data))
