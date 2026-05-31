"""Motion LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.motion.outputs import (
    CreateTaskOutput,
    DeleteTaskOutput,
    GetSchedulesOutput,
    GetTaskOutput,
    MoveWorkspaceOutput,
    ScheduleItem,
    TaskObject,
    TaskStatus,
    UpdateTaskOutput,
)

__all__ = [
    "create_task",
    "delete_task",
    "get_schedules",
    "get_task",
    "move_workspace",
    "update_task",
]

_BASE_URL = "https://api.usemotion.com/v1"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _parse_task(data: dict[str, Any]) -> TaskObject:
    status_raw = data.get("status")
    status = None
    if isinstance(status_raw, dict):
        status = TaskStatus(
            name=status_raw.get("name"),
            is_default_status=status_raw.get("isDefaultStatus"),
            is_resolved_status=status_raw.get("isResolvedStatus"),
        )
    return TaskObject(
        id=data.get("id"),
        name=data.get("name"),
        description=data.get("description"),
        status=status,
        workspace_id=data.get("workspaceId"),
        project_id=data.get("projectId"),
        priority=data.get("priority"),
        assignee_id=data.get("assigneeId"),
        labels=data.get("labels") or [],
        due_date=data.get("dueDate"),
        duration=str(data["duration"]) if data.get("duration") is not None else None,
        created_at=data.get("createdAt"),
    )


# --- Input schemas --------------------------------------------------------


class CreateTaskInput(BaseModel):
    workspace_id: str = Field(description="The ID of the workspace")
    name: str = Field(description="Name / title of the task")
    api_key: str = Field(description="Motion API key")
    project_id: str | None = Field(default=None, description="The ID of the project to assign the task to")
    due_date: str | None = Field(default=None, description="ISO 8601 due date. Required for scheduled tasks")
    duration: str | None = Field(default=None, description="Duration: NONE, REMINDER, or an integer greater than 0")
    description: str | None = Field(default=None, description="Task description in GitHub Flavored Markdown")
    priority: str = Field(default="MEDIUM", description="Priority level: ASAP, HIGH, MEDIUM, LOW")
    assignee_id: str | None = Field(default=None, description="The user ID to assign the task to")
    labels: list[str] | None = Field(default=None, description="List of label names to add to the task")
    status: str | None = Field(default=None, description="The name of the task status")
    start_date: str | None = Field(default=None, description="ISO 8601 date for auto-scheduled tasks")
    deadline_type: str | None = Field(default=None, description="Deadline type for auto-scheduled tasks: HARD, SOFT, NONE")
    schedule: str | None = Field(default=None, description="Schedule the task must adhere to")


class DeleteTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to delete")
    api_key: str = Field(description="Motion API key")


class GetSchedulesInput(BaseModel):
    api_key: str = Field(description="Motion API key")


class GetTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to retrieve")
    api_key: str = Field(description="Motion API key")


class MoveWorkspaceInput(BaseModel):
    task_id: str = Field(description="The ID of the task to move")
    workspace_id: str = Field(description="The ID of the target workspace")
    api_key: str = Field(description="Motion API key")
    assignee_id: str | None = Field(default=None, description="The user ID to assign the task to in the target workspace")


class UpdateTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to update")
    api_key: str = Field(description="Motion API key")
    name: str | None = Field(default=None, description="New name / title for the task")
    due_date: str | None = Field(default=None, description="ISO 8601 due date")
    duration: str | None = Field(default=None, description="Duration: NONE, REMINDER, or an integer greater than 0")
    project_id: str | None = Field(default=None, description="The ID of the project to assign the task to")
    description: str | None = Field(default=None, description="Task description in GitHub Flavored Markdown")
    priority: str | None = Field(default=None, description="Priority level: ASAP, HIGH, MEDIUM, LOW")
    assignee_id: str | None = Field(default=None, description="The user ID to assign the task to")
    labels: list[str] | None = Field(default=None, description="List of label names to add to the task")
    status: str | None = Field(default=None, description="The name of the task status")
    start_date: str | None = Field(default=None, description="ISO 8601 date for auto-scheduled tasks")
    deadline_type: str | None = Field(default=None, description="Deadline type for auto-scheduled tasks: HARD, SOFT, NONE")
    schedule: str | None = Field(default=None, description="Schedule the task must adhere to")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    workspace_id: str,
    name: str,
    api_key: str,
    project_id: str | None = None,
    due_date: str | None = None,
    duration: str | None = None,
    description: str | None = None,
    priority: str = "MEDIUM",
    assignee_id: str | None = None,
    labels: list[str] | None = None,
    status: str | None = None,
    start_date: str | None = None,
    deadline_type: str | None = None,
    schedule: str | None = None,
) -> CreateTaskOutput:
    """Create a new task in a Motion workspace."""
    if not api_key or not api_key.strip():
        return CreateTaskOutput(success=False, error="API key is empty. Please configure a valid credential.")
    body: dict[str, Any] = {
        "workspaceId": workspace_id,
        "name": name,
        "priority": priority,
    }
    if project_id is not None:
        body["projectId"] = project_id
    if due_date is not None:
        body["dueDate"] = due_date
    if duration is not None:
        body["duration"] = duration
    if description is not None:
        body["description"] = description
    if assignee_id is not None:
        body["assigneeId"] = assignee_id
    if labels is not None:
        body["labels"] = labels
    if status is not None:
        body["status"] = status
    if start_date is not None:
        body["startDate"] = start_date
    if deadline_type is not None:
        body["deadlineType"] = deadline_type
    if schedule is not None:
        body["schedule"] = schedule
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/tasks",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateTaskOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTaskOutput(success=False, error=f"Call failed: {exc}")
    return CreateTaskOutput(success=True, task=_parse_task(data))


@tool(args_schema=DeleteTaskInput)
@serialize_pydantic_return
async def delete_task(
    task_id: str,
    api_key: str,
) -> DeleteTaskOutput:
    """Delete a specific task by ID."""
    if not api_key or not api_key.strip():
        return DeleteTaskOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/tasks/{task_id}",
                headers=_headers(api_key),
            )
        if response.status_code not in (200, 204):
            return DeleteTaskOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteTaskOutput(success=False, error=f"Call failed: {exc}")
    return DeleteTaskOutput(success=True)


@tool(args_schema=GetSchedulesInput)
@serialize_pydantic_return
async def get_schedules(
    api_key: str,
) -> GetSchedulesOutput:
    """Get a list of schedules for the authenticated user."""
    if not api_key or not api_key.strip():
        return GetSchedulesOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/schedules",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetSchedulesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetSchedulesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSchedulesOutput(success=False, error=f"Call failed: {exc}")
    items = data if isinstance(data, list) else data.get("schedules", [])
    schedules = [
        ScheduleItem(
            id=s.get("id"),
            name=s.get("name"),
            timezone=s.get("timezone"),
            is_default=s.get("isDefault"),
        )
        for s in items
    ]
    return GetSchedulesOutput(success=True, schedules=schedules)


@tool(args_schema=GetTaskInput)
@serialize_pydantic_return
async def get_task(
    task_id: str,
    api_key: str,
) -> GetTaskOutput:
    """Retrieve a specific task by ID."""
    if not api_key or not api_key.strip():
        return GetTaskOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/tasks/{task_id}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetTaskOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTaskOutput(success=False, error=f"Call failed: {exc}")
    return GetTaskOutput(success=True, task=_parse_task(data))


@tool(args_schema=MoveWorkspaceInput)
@serialize_pydantic_return
async def move_workspace(
    task_id: str,
    workspace_id: str,
    api_key: str,
    assignee_id: str | None = None,
) -> MoveWorkspaceOutput:
    """Move a task to another workspace. Resets the task's project, status, labels, and assignee."""
    if not api_key or not api_key.strip():
        return MoveWorkspaceOutput(success=False, error="API key is empty. Please configure a valid credential.")
    body: dict[str, Any] = {"workspaceId": workspace_id}
    if assignee_id is not None:
        body["assigneeId"] = assignee_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/tasks/{task_id}/move",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return MoveWorkspaceOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return MoveWorkspaceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return MoveWorkspaceOutput(success=False, error=f"Call failed: {exc}")
    return MoveWorkspaceOutput(success=True, task=_parse_task(data))


@tool(args_schema=UpdateTaskInput)
@serialize_pydantic_return
async def update_task(
    task_id: str,
    api_key: str,
    name: str | None = None,
    due_date: str | None = None,
    duration: str | None = None,
    project_id: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    assignee_id: str | None = None,
    labels: list[str] | None = None,
    status: str | None = None,
    start_date: str | None = None,
    deadline_type: str | None = None,
    schedule: str | None = None,
) -> UpdateTaskOutput:
    """Update a specific task's properties."""
    if not api_key or not api_key.strip():
        return UpdateTaskOutput(success=False, error="API key is empty. Please configure a valid credential.")
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if due_date is not None:
        body["dueDate"] = due_date
    if duration is not None:
        body["duration"] = duration
    if project_id is not None:
        body["projectId"] = project_id
    if description is not None:
        body["description"] = description
    if priority is not None:
        body["priority"] = priority
    if assignee_id is not None:
        body["assigneeId"] = assignee_id
    if labels is not None:
        body["labels"] = labels
    if status is not None:
        body["status"] = status
    if start_date is not None:
        body["startDate"] = start_date
    if deadline_type is not None:
        body["deadlineType"] = deadline_type
    if schedule is not None:
        body["schedule"] = schedule
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/tasks/{task_id}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return UpdateTaskOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdateTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateTaskOutput(success=False, error=f"Call failed: {exc}")
    return UpdateTaskOutput(success=True, task=_parse_task(data))
