"""ClickUp LangChain ``@tool`` functions.

Pure HTTP integration against the ClickUp v2 REST API. Key-based
runtime convention (``api_key: str`` first arg). 23 actions across
teams/spaces/folders/lists/tasks/comments/tags/members.

Notable quirks (preserved from legacy):

- **`Authorization` header is just the raw key** — no `Bearer ` prefix.
- **`custom_task_ids=true&team_id=…` query string** lets you address
  tasks by their workspace-prefixed display ID (e.g. "ABC-123")
  instead of the API ID. Most task actions accept this.
- **`add_tag_to_task` / `remove_tag_from_task`** use path-style tag
  attachment: `POST /task/{id}/tag/{name}` (no body).
- **`search_tasks`** filters by `query` client-side (substring match
  on name + description) because ClickUp has no full-text search API.
- **`get_team_members`** is `GET /team` + a client-side filter; the
  team list endpoint already includes the member roster per team.
- All actions wrap in try/except → unified ``success=False`` envelope.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "add_tag_to_task",
    "create_folder",
    "create_list",
    "create_space",
    "create_task",
    "create_task_comment",
    "delete_folder",
    "delete_task",
    "get_folder",
    "get_folders",
    "get_list",
    "get_lists",
    "get_space",
    "get_space_tags",
    "get_spaces",
    "get_task",
    "get_task_comments",
    "get_tasks",
    "get_team_members",
    "get_teams",
    "remove_tag_from_task",
    "search_tasks",
    "update_task",
]

_API = "https://api.clickup.com/api/v2"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": api_key, "Content-Type": "application/json"}


def _validate(api_key: str, action: str) -> str | None:
    if not api_key or not api_key.strip():
        return f"ClickUp API key is empty for {action}"
    return None


def _api_err(status: int, body: str) -> str:
    return f"ClickUp API error: {status} - {body}"


async def _call(
    method: str,
    api_key: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    success_codes: tuple[int, ...] = (200,),
) -> tuple[bool, str | None, dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method,
                f"{_API}{path}",
                headers=_headers(api_key),
                json=json_body,
                params=params,
            )
        if response.status_code not in success_codes:
            return False, _api_err(response.status_code, response.text), {}
        if response.status_code == 204 or not response.content:
            return True, None, {}
        return True, None, response.json() or {}
    except httpx.TimeoutException:
        return False, "Request timed out", {}
    except Exception as exc:
        return False, str(exc), {}


def _custom_task_params(
    custom_task_ids: bool, team_id: str | None
) -> dict[str, Any] | None:
    if not custom_task_ids:
        return None
    return {"custom_task_ids": "true", "team_id": team_id or ""}


# --- Input schemas ---------------------------------------------------------


class _KeyField(BaseModel):
    api_key: str = Field(description="ClickUp API key")


class GetTeamsInput(_KeyField):
    pass


class GetSpacesInput(_KeyField):
    team_id: str = Field(description="Team ID")
    archived: bool = False


class GetSpaceInput(_KeyField):
    space_id: str = Field(description="Space ID")


class CreateSpaceInput(_KeyField):
    team_id: str = Field(description="Team ID")
    name: str = Field(description="Space name")
    multiple_assignees: bool = True
    features: dict[str, Any] | None = None


class GetFoldersInput(_KeyField):
    space_id: str = Field(description="Space ID")
    archived: bool = False


class GetFolderInput(_KeyField):
    folder_id: str = Field(description="Folder ID")


class CreateFolderInput(_KeyField):
    space_id: str = Field(description="Space ID")
    name: str = Field(description="Folder name")


class DeleteFolderInput(_KeyField):
    folder_id: str = Field(description="Folder ID")


class GetListsInput(_KeyField):
    folder_id: str | None = None
    space_id: str | None = None
    archived: bool = False


class GetListInput(_KeyField):
    list_id: str = Field(description="List ID")


class CreateListInput(_KeyField):
    name: str = Field(description="List name")
    folder_id: str | None = None
    space_id: str | None = None
    content: str | None = None
    due_date: int | None = None
    priority: int | None = None
    assignee: int | None = None
    status: str | None = None


class GetTasksInput(_KeyField):
    list_id: str = Field(description="List ID")
    archived: bool = False
    include_closed: bool = False
    subtasks: bool = False
    page: int = 0
    order_by: str | None = None
    reverse: bool = False
    statuses: list[str] | None = None
    assignees: list[str] | None = None


class GetTaskInput(_KeyField):
    task_id: str = Field(description="Task ID")
    custom_task_ids: bool = False
    team_id: str | None = None
    include_subtasks: bool = False


class CreateTaskInput(_KeyField):
    list_id: str = Field(description="List ID")
    name: str = Field(description="Task name")
    description: str | None = None
    status: str | None = None
    priority: int | None = None
    due_date: int | None = None
    due_date_time: bool = False
    start_date: int | None = None
    start_date_time: bool = False
    assignees: list[int] | None = None
    tags: list[str] | None = None
    parent: str | None = None
    notify_all: bool = True
    time_estimate: int | None = None


class UpdateTaskInput(_KeyField):
    task_id: str = Field(description="Task ID")
    custom_task_ids: bool = False
    team_id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    priority: int | None = None
    due_date: int | None = None
    due_date_time: bool | None = None
    start_date: int | None = None
    start_date_time: bool | None = None
    assignees_add: list[int] | None = None
    assignees_remove: list[int] | None = None
    archived: bool | None = None
    time_estimate: int | None = None


class DeleteTaskInput(_KeyField):
    task_id: str = Field(description="Task ID")
    custom_task_ids: bool = False
    team_id: str | None = None


class GetTaskCommentsInput(_KeyField):
    task_id: str = Field(description="Task ID")
    custom_task_ids: bool = False
    team_id: str | None = None
    start: int | None = None
    start_id: str | None = None


class CreateTaskCommentInput(_KeyField):
    task_id: str = Field(description="Task ID")
    custom_task_ids: bool = False
    team_id: str | None = None
    comment_text: str = Field(description="Comment body")
    notify_all: bool = False
    assignee: int | None = None


class SearchTasksInput(_KeyField):
    team_id: str = Field(description="Team ID")
    query: str | None = None
    statuses: list[str] | None = None
    assignees: list[str] | None = None
    tags: list[str] | None = None
    list_ids: list[str] | None = None
    folder_ids: list[str] | None = None
    space_ids: list[str] | None = None
    include_closed: bool = False
    page: int = 0
    order_by: str | None = None


class GetSpaceTagsInput(_KeyField):
    space_id: str = Field(description="Space ID")


class _TaskTagInput(_KeyField):
    task_id: str = Field(description="Task ID")
    tag_name: str = Field(description="Tag name")
    custom_task_ids: bool = False
    team_id: str | None = None


class GetTeamMembersInput(_KeyField):
    team_id: str = Field(description="Team ID")


# --- Tools — teams / spaces ----------------------------------------------


@tool(args_schema=GetTeamsInput)
@serialize_pydantic_return
async def get_teams(api_key: str) -> GetTeamsOutput:
    """List all authorized teams (workspaces)."""
    err = _validate(api_key, "get_teams")
    if err:
        return GetTeamsOutput(success=False, error=err)
    ok, e, data = await _call("GET", api_key, "/team")
    if not ok:
        return GetTeamsOutput(success=False, error=e)
    teams = data.get("teams") or []
    return GetTeamsOutput(success=True, teams=teams, count=len(teams))


@tool(args_schema=GetSpacesInput)
@serialize_pydantic_return
async def get_spaces(
    api_key: str, team_id: str, archived: bool = False
) -> GetSpacesOutput:
    """List spaces in a team."""
    err = _validate(api_key, "get_spaces")
    if err:
        return GetSpacesOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET",
        api_key,
        f"/team/{team_id}/space",
        params={"archived": str(archived).lower()},
    )
    if not ok:
        return GetSpacesOutput(success=False, error=e)
    spaces = data.get("spaces") or []
    return GetSpacesOutput(
        success=True, spaces=spaces, count=len(spaces), team_id=team_id
    )


@tool(args_schema=GetSpaceInput)
@serialize_pydantic_return
async def get_space(api_key: str, space_id: str) -> GetSpaceOutput:
    """Get a specific space."""
    err = _validate(api_key, "get_space")
    if err:
        return GetSpaceOutput(success=False, error=err)
    ok, e, data = await _call("GET", api_key, f"/space/{space_id}")
    if not ok:
        return GetSpaceOutput(success=False, error=e)
    return GetSpaceOutput(success=True, result=data)


@tool(args_schema=CreateSpaceInput)
@serialize_pydantic_return
async def create_space(
    api_key: str,
    team_id: str,
    name: str,
    multiple_assignees: bool = True,
    features: dict[str, Any] | None = None,
) -> CreateSpaceOutput:
    """Create a space in a team."""
    err = _validate(api_key, "create_space")
    if err:
        return CreateSpaceOutput(success=False, error=err)
    body: dict[str, Any] = {"name": name, "multiple_assignees": multiple_assignees}
    if features:
        body["features"] = features
    ok, e, data = await _call(
        "POST",
        api_key,
        f"/team/{team_id}/space",
        json_body=body,
        success_codes=(200, 201),
    )
    if not ok:
        return CreateSpaceOutput(success=False, error=e)
    return CreateSpaceOutput(success=True, result=data)


# --- Tools — folders ------------------------------------------------------


@tool(args_schema=GetFoldersInput)
@serialize_pydantic_return
async def get_folders(
    api_key: str, space_id: str, archived: bool = False
) -> GetFoldersOutput:
    """List folders in a space."""
    err = _validate(api_key, "get_folders")
    if err:
        return GetFoldersOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET",
        api_key,
        f"/space/{space_id}/folder",
        params={"archived": str(archived).lower()},
    )
    if not ok:
        return GetFoldersOutput(success=False, error=e)
    folders = data.get("folders") or []
    return GetFoldersOutput(
        success=True, folders=folders, count=len(folders), space_id=space_id
    )


@tool(args_schema=GetFolderInput)
@serialize_pydantic_return
async def get_folder(api_key: str, folder_id: str) -> GetFolderOutput:
    """Get a specific folder."""
    err = _validate(api_key, "get_folder")
    if err:
        return GetFolderOutput(success=False, error=err)
    ok, e, data = await _call("GET", api_key, f"/folder/{folder_id}")
    if not ok:
        return GetFolderOutput(success=False, error=e)
    return GetFolderOutput(success=True, result=data)


@tool(args_schema=CreateFolderInput)
@serialize_pydantic_return
async def create_folder(
    api_key: str, space_id: str, name: str
) -> CreateFolderOutput:
    """Create a folder in a space."""
    err = _validate(api_key, "create_folder")
    if err:
        return CreateFolderOutput(success=False, error=err)
    ok, e, data = await _call(
        "POST",
        api_key,
        f"/space/{space_id}/folder",
        json_body={"name": name},
        success_codes=(200, 201),
    )
    if not ok:
        return CreateFolderOutput(success=False, error=e)
    return CreateFolderOutput(success=True, result=data)


@tool(args_schema=DeleteFolderInput)
@serialize_pydantic_return
async def delete_folder(api_key: str, folder_id: str) -> DeleteFolderOutput:
    """Delete a folder."""
    err = _validate(api_key, "delete_folder")
    if err:
        return DeleteFolderOutput(success=False, error=err)
    ok, e, _ = await _call(
        "DELETE", api_key, f"/folder/{folder_id}", success_codes=(200, 204)
    )
    if not ok:
        return DeleteFolderOutput(success=False, error=e)
    return DeleteFolderOutput(success=True, deleted=True, folder_id=folder_id)


# --- Tools — lists --------------------------------------------------------


@tool(args_schema=GetListsInput)
@serialize_pydantic_return
async def get_lists(
    api_key: str,
    folder_id: str | None = None,
    space_id: str | None = None,
    archived: bool = False,
) -> GetListsOutput:
    """List lists in a folder OR folderless lists in a space."""
    err = _validate(api_key, "get_lists")
    if err:
        return GetListsOutput(success=False, error=err)
    if not folder_id and not space_id:
        return GetListsOutput(
            success=False, error="Either folder_id or space_id must be provided."
        )
    path = (
        f"/folder/{folder_id}/list" if folder_id else f"/space/{space_id}/list"
    )
    ok, e, data = await _call(
        "GET", api_key, path, params={"archived": str(archived).lower()}
    )
    if not ok:
        return GetListsOutput(success=False, error=e)
    lists = data.get("lists") or []
    return GetListsOutput(
        success=True,
        lists=lists,
        count=len(lists),
        folder_id=folder_id,
        space_id=space_id,
    )


@tool(args_schema=GetListInput)
@serialize_pydantic_return
async def get_list(api_key: str, list_id: str) -> GetListOutput:
    """Get a specific list."""
    err = _validate(api_key, "get_list")
    if err:
        return GetListOutput(success=False, error=err)
    ok, e, data = await _call("GET", api_key, f"/list/{list_id}")
    if not ok:
        return GetListOutput(success=False, error=e)
    return GetListOutput(success=True, result=data)


@tool(args_schema=CreateListInput)
@serialize_pydantic_return
async def create_list(
    api_key: str,
    name: str,
    folder_id: str | None = None,
    space_id: str | None = None,
    content: str | None = None,
    due_date: int | None = None,
    priority: int | None = None,
    assignee: int | None = None,
    status: str | None = None,
) -> CreateListOutput:
    """Create a list in a folder OR folderless list in a space."""
    err = _validate(api_key, "create_list")
    if err:
        return CreateListOutput(success=False, error=err)
    if not folder_id and not space_id:
        return CreateListOutput(
            success=False, error="Either folder_id or space_id must be provided."
        )
    body: dict[str, Any] = {"name": name}
    if content:
        body["content"] = content
    if due_date:
        body["due_date"] = due_date
    if priority:
        body["priority"] = priority
    if assignee:
        body["assignee"] = assignee
    if status:
        body["status"] = status
    path = (
        f"/folder/{folder_id}/list" if folder_id else f"/space/{space_id}/list"
    )
    ok, e, data = await _call(
        "POST", api_key, path, json_body=body, success_codes=(200, 201)
    )
    if not ok:
        return CreateListOutput(success=False, error=e)
    return CreateListOutput(success=True, result=data)


# --- Tools — tasks --------------------------------------------------------


@tool(args_schema=GetTasksInput)
@serialize_pydantic_return
async def get_tasks(
    api_key: str,
    list_id: str,
    archived: bool = False,
    include_closed: bool = False,
    subtasks: bool = False,
    page: int = 0,
    order_by: str | None = None,
    reverse: bool = False,
    statuses: list[str] | None = None,
    assignees: list[str] | None = None,
) -> GetTasksOutput:
    """List tasks in a list with filters + pagination."""
    err = _validate(api_key, "get_tasks")
    if err:
        return GetTasksOutput(success=False, error=err)
    params: dict[str, Any] = {
        "archived": str(archived).lower(),
        "include_closed": str(include_closed).lower(),
        "subtasks": str(subtasks).lower(),
        "page": str(page),
    }
    if order_by:
        params["order_by"] = order_by
    if reverse:
        params["reverse"] = str(reverse).lower()
    # ClickUp uses array-style query params: ?statuses[]=open&statuses[]=closed.
    # httpx serializes list values as repeated keys when given a list.
    if statuses:
        params["statuses[]"] = statuses
    if assignees:
        params["assignees[]"] = assignees

    ok, e, data = await _call(
        "GET", api_key, f"/list/{list_id}/task", params=params
    )
    if not ok:
        return GetTasksOutput(success=False, error=e)
    tasks = data.get("tasks") or []
    return GetTasksOutput(
        success=True, tasks=tasks, count=len(tasks), list_id=list_id
    )


@tool(args_schema=GetTaskInput)
@serialize_pydantic_return
async def get_task(
    api_key: str,
    task_id: str,
    custom_task_ids: bool = False,
    team_id: str | None = None,
    include_subtasks: bool = False,
) -> GetTaskOutput:
    """Get a specific task."""
    err = _validate(api_key, "get_task")
    if err:
        return GetTaskOutput(success=False, error=err)
    params: dict[str, Any] = {}
    cti = _custom_task_params(custom_task_ids, team_id)
    if cti:
        params.update(cti)
    if include_subtasks:
        params["include_subtasks"] = "true"
    ok, e, data = await _call(
        "GET",
        api_key,
        f"/task/{task_id}",
        params=params or None,
    )
    if not ok:
        return GetTaskOutput(success=False, error=e)
    return GetTaskOutput(success=True, result=data)


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    api_key: str,
    list_id: str,
    name: str,
    description: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    due_date: int | None = None,
    due_date_time: bool = False,
    start_date: int | None = None,
    start_date_time: bool = False,
    assignees: list[int] | None = None,
    tags: list[str] | None = None,
    parent: str | None = None,
    notify_all: bool = True,
    time_estimate: int | None = None,
) -> CreateTaskOutput:
    """Create a task in a list."""
    err = _validate(api_key, "create_task")
    if err:
        return CreateTaskOutput(success=False, error=err)
    body: dict[str, Any] = {"name": name, "notify_all": notify_all}
    if description:
        body["description"] = description
    if status:
        body["status"] = status
    if priority is not None:
        body["priority"] = priority
    if due_date:
        body["due_date"] = due_date
        body["due_date_time"] = due_date_time
    if start_date:
        body["start_date"] = start_date
        body["start_date_time"] = start_date_time
    if assignees:
        body["assignees"] = assignees
    if tags:
        body["tags"] = tags
    if parent:
        body["parent"] = parent
    if time_estimate:
        body["time_estimate"] = time_estimate

    ok, e, data = await _call(
        "POST",
        api_key,
        f"/list/{list_id}/task",
        json_body=body,
        success_codes=(200, 201),
    )
    if not ok:
        return CreateTaskOutput(success=False, error=e)
    return CreateTaskOutput(success=True, result=data)


@tool(args_schema=UpdateTaskInput)
@serialize_pydantic_return
async def update_task(
    api_key: str,
    task_id: str,
    custom_task_ids: bool = False,
    team_id: str | None = None,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    due_date: int | None = None,
    due_date_time: bool | None = None,
    start_date: int | None = None,
    start_date_time: bool | None = None,
    assignees_add: list[int] | None = None,
    assignees_remove: list[int] | None = None,
    archived: bool | None = None,
    time_estimate: int | None = None,
) -> UpdateTaskOutput:
    """Update fields on an existing task."""
    err = _validate(api_key, "update_task")
    if err:
        return UpdateTaskOutput(success=False, error=err)
    if custom_task_ids and not team_id:
        return UpdateTaskOutput(
            success=False,
            error="team_id is required when using custom_task_ids=true",
        )
    body: dict[str, Any] = {}
    for field, value in (
        ("name", name),
        ("description", description),
        ("status", status),
        ("priority", priority),
        ("due_date", due_date),
        ("due_date_time", due_date_time),
        ("start_date", start_date),
        ("start_date_time", start_date_time),
        ("archived", archived),
        ("time_estimate", time_estimate),
    ):
        if value is not None:
            body[field] = value
    if assignees_add or assignees_remove:
        body["assignees"] = {
            "add": assignees_add or [],
            "rem": assignees_remove or [],
        }
    ok, e, data = await _call(
        "PUT",
        api_key,
        f"/task/{task_id}",
        json_body=body,
        params=_custom_task_params(custom_task_ids, team_id),
    )
    if not ok:
        return UpdateTaskOutput(success=False, error=e)
    return UpdateTaskOutput(success=True, result=data)


@tool(args_schema=DeleteTaskInput)
@serialize_pydantic_return
async def delete_task(
    api_key: str,
    task_id: str,
    custom_task_ids: bool = False,
    team_id: str | None = None,
) -> DeleteTaskOutput:
    """Delete a task permanently."""
    err = _validate(api_key, "delete_task")
    if err:
        return DeleteTaskOutput(success=False, error=err)
    if custom_task_ids and not team_id:
        return DeleteTaskOutput(
            success=False,
            error="team_id is required when using custom_task_ids=true",
        )
    ok, e, _ = await _call(
        "DELETE",
        api_key,
        f"/task/{task_id}",
        params=_custom_task_params(custom_task_ids, team_id),
        success_codes=(200, 204),
    )
    if not ok:
        return DeleteTaskOutput(success=False, error=e)
    return DeleteTaskOutput(success=True, deleted=True, task_id=task_id)


# --- Tools — comments ----------------------------------------------------


@tool(args_schema=GetTaskCommentsInput)
@serialize_pydantic_return
async def get_task_comments(
    api_key: str,
    task_id: str,
    custom_task_ids: bool = False,
    team_id: str | None = None,
    start: int | None = None,
    start_id: str | None = None,
) -> GetTaskCommentsOutput:
    """Get comments on a task."""
    err = _validate(api_key, "get_task_comments")
    if err:
        return GetTaskCommentsOutput(success=False, error=err)
    params: dict[str, Any] = {}
    cti = _custom_task_params(custom_task_ids, team_id)
    if cti:
        params.update(cti)
    if start is not None:
        params["start"] = str(start)
    if start_id:
        params["start_id"] = start_id
    ok, e, data = await _call(
        "GET",
        api_key,
        f"/task/{task_id}/comment",
        params=params or None,
    )
    if not ok:
        return GetTaskCommentsOutput(success=False, error=e)
    comments = data.get("comments") or []
    return GetTaskCommentsOutput(
        success=True,
        comments=comments,
        count=len(comments),
        task_id=task_id,
    )


@tool(args_schema=CreateTaskCommentInput)
@serialize_pydantic_return
async def create_task_comment(
    api_key: str,
    task_id: str,
    comment_text: str,
    custom_task_ids: bool = False,
    team_id: str | None = None,
    notify_all: bool = False,
    assignee: int | None = None,
) -> CreateTaskCommentOutput:
    """Add a comment to a task."""
    err = _validate(api_key, "create_task_comment")
    if err:
        return CreateTaskCommentOutput(success=False, error=err)
    body: dict[str, Any] = {
        "comment_text": comment_text,
        "notify_all": notify_all,
    }
    if assignee:
        body["assignee"] = assignee
    ok, e, data = await _call(
        "POST",
        api_key,
        f"/task/{task_id}/comment",
        json_body=body,
        params=_custom_task_params(custom_task_ids, team_id),
        success_codes=(200, 201),
    )
    if not ok:
        return CreateTaskCommentOutput(success=False, error=e)
    return CreateTaskCommentOutput(success=True, result=data)


# --- Tools — search / tags / members --------------------------------------


@tool(args_schema=SearchTasksInput)
@serialize_pydantic_return
async def search_tasks(
    api_key: str,
    team_id: str,
    query: str | None = None,
    statuses: list[str] | None = None,
    assignees: list[str] | None = None,
    tags: list[str] | None = None,
    list_ids: list[str] | None = None,
    folder_ids: list[str] | None = None,
    space_ids: list[str] | None = None,
    include_closed: bool = False,
    page: int = 0,
    order_by: str | None = None,
) -> SearchTasksOutput:
    """Search tasks across a team (substring `query` filter is client-side)."""
    err = _validate(api_key, "search_tasks")
    if err:
        return SearchTasksOutput(success=False, error=err)
    params: dict[str, Any] = {
        "page": str(page),
        "include_closed": str(include_closed).lower(),
    }
    for key, value in (
        ("statuses[]", statuses),
        ("assignees[]", assignees),
        ("tags[]", tags),
        ("list_ids[]", list_ids),
        ("folder_ids[]", folder_ids),
        ("space_ids[]", space_ids),
    ):
        if value:
            params[key] = value
    if order_by:
        params["order_by"] = order_by

    ok, e, data = await _call(
        "GET", api_key, f"/team/{team_id}/task", params=params
    )
    if not ok:
        return SearchTasksOutput(success=False, error=e)
    tasks = data.get("tasks") or []
    if query:
        q = query.lower()
        tasks = [
            t
            for t in tasks
            if q in (t.get("name") or "").lower()
            or q in (t.get("description") or "").lower()
        ]
    return SearchTasksOutput(
        success=True, tasks=tasks, count=len(tasks), team_id=team_id
    )


@tool(args_schema=GetSpaceTagsInput)
@serialize_pydantic_return
async def get_space_tags(api_key: str, space_id: str) -> GetSpaceTagsOutput:
    """List all tags in a space."""
    err = _validate(api_key, "get_space_tags")
    if err:
        return GetSpaceTagsOutput(success=False, error=err)
    ok, e, data = await _call("GET", api_key, f"/space/{space_id}/tag")
    if not ok:
        return GetSpaceTagsOutput(success=False, error=e)
    tags = data.get("tags") or []
    return GetSpaceTagsOutput(
        success=True, tags=tags, count=len(tags), space_id=space_id
    )


@tool(args_schema=_TaskTagInput)
@serialize_pydantic_return
async def add_tag_to_task(
    api_key: str,
    task_id: str,
    tag_name: str,
    custom_task_ids: bool = False,
    team_id: str | None = None,
) -> AddTagToTaskOutput:
    """Attach a tag to a task by name."""
    err = _validate(api_key, "add_tag_to_task")
    if err:
        return AddTagToTaskOutput(success=False, error=err)
    ok, e, _ = await _call(
        "POST",
        api_key,
        f"/task/{task_id}/tag/{tag_name}",
        params=_custom_task_params(custom_task_ids, team_id),
        success_codes=(200, 201),
    )
    if not ok:
        return AddTagToTaskOutput(success=False, error=e)
    return AddTagToTaskOutput(
        success=True, added=True, task_id=task_id, tag_name=tag_name
    )


@tool(args_schema=_TaskTagInput)
@serialize_pydantic_return
async def remove_tag_from_task(
    api_key: str,
    task_id: str,
    tag_name: str,
    custom_task_ids: bool = False,
    team_id: str | None = None,
) -> RemoveTagFromTaskOutput:
    """Detach a tag from a task by name."""
    err = _validate(api_key, "remove_tag_from_task")
    if err:
        return RemoveTagFromTaskOutput(success=False, error=err)
    ok, e, _ = await _call(
        "DELETE",
        api_key,
        f"/task/{task_id}/tag/{tag_name}",
        params=_custom_task_params(custom_task_ids, team_id),
        success_codes=(200, 204),
    )
    if not ok:
        return RemoveTagFromTaskOutput(success=False, error=e)
    return RemoveTagFromTaskOutput(
        success=True, removed=True, task_id=task_id, tag_name=tag_name
    )


@tool(args_schema=GetTeamMembersInput)
@serialize_pydantic_return
async def get_team_members(
    api_key: str, team_id: str
) -> GetTeamMembersOutput:
    """List members of a team (filters all teams client-side)."""
    err = _validate(api_key, "get_team_members")
    if err:
        return GetTeamMembersOutput(success=False, error=err)
    ok, e, data = await _call("GET", api_key, "/team")
    if not ok:
        return GetTeamMembersOutput(success=False, error=e)
    teams = data.get("teams") or []
    team = next((t for t in teams if t.get("id") == team_id), None)
    if not team:
        return GetTeamMembersOutput(
            success=False, error=f"Team {team_id} not found"
        )
    members = team.get("members") or []
    return GetTeamMembersOutput(
        success=True, members=members, count=len(members), team_id=team_id
    )
