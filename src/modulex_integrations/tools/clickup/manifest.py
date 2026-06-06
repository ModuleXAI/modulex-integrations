"""ClickUp integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _team_id_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Team (workspace) ID", required=True
    )


def _space_id_param() -> ParameterDef:
    return ParameterDef(type="string", description="Space ID", required=True)


def _folder_id_param() -> ParameterDef:
    return ParameterDef(type="string", description="Folder ID", required=True)


def _list_id_param() -> ParameterDef:
    return ParameterDef(type="string", description="List ID", required=True)


def _task_id_param() -> ParameterDef:
    return ParameterDef(type="string", description="Task ID", required=True)


def _custom_task_params() -> dict[str, ParameterDef]:
    return {
        "custom_task_ids": ParameterDef(
            type="boolean",
            description="If true, task_id is a custom task ID (e.g. 'ABC-123')",
            default=False,
        ),
        "team_id": ParameterDef(
            type="string",
            description="Required when custom_task_ids=true",
        ),
    }


manifest = IntegrationManifest(
    name="clickup",
    display_name="ClickUp",
    description=(
        "ClickUp integration: workspaces, spaces, folders, lists, "
        "tasks, comments, tags, and team members."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:clickup",
    app_url="https://clickup.com",
    categories=[
        "Project & Task Management",
        "Project Management",
        "Productivity",
        "Communication & Collaboration",
    ],
    actions=[
        # --- Workspace / team ----------------------------------------------
        ActionDefinition(
            name="get_teams",
            description="List all authorized teams (workspaces)",
            parameters={},
        ),
        ActionDefinition(
            name="get_spaces",
            description="List spaces in a team",
            parameters={
                "team_id": _team_id_param(),
                "archived": ParameterDef(
                    type="boolean",
                    description="Include archived spaces",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_space",
            description="Get a specific space",
            parameters={"space_id": _space_id_param()},
        ),
        ActionDefinition(
            name="create_space",
            description="Create a new space in a team",
            parameters={
                "team_id": _team_id_param(),
                "name": ParameterDef(
                    type="string", description="Space name", required=True
                ),
                "multiple_assignees": ParameterDef(
                    type="boolean",
                    description="Allow multiple assignees",
                    default=True,
                ),
                "features": ParameterDef(
                    type="object",
                    description="Optional features (due_dates, time_tracking, …)",
                ),
            },
        ),
        # --- Folders -------------------------------------------------------
        ActionDefinition(
            name="get_folders",
            description="List folders in a space",
            parameters={
                "space_id": _space_id_param(),
                "archived": ParameterDef(
                    type="boolean",
                    description="Include archived folders",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_folder",
            description="Get a specific folder",
            parameters={"folder_id": _folder_id_param()},
        ),
        ActionDefinition(
            name="create_folder",
            description="Create a folder in a space",
            parameters={
                "space_id": _space_id_param(),
                "name": ParameterDef(
                    type="string", description="Folder name", required=True
                ),
            },
        ),
        ActionDefinition(
            name="delete_folder",
            description="Delete a folder",
            parameters={"folder_id": _folder_id_param()},
        ),
        # --- Lists ---------------------------------------------------------
        ActionDefinition(
            name="get_lists",
            description=(
                "List lists in a folder OR folderless lists in a space "
                "(exactly one of folder_id/space_id required)"
            ),
            parameters={
                "folder_id": ParameterDef(type="string", description="Folder ID"),
                "space_id": ParameterDef(type="string", description="Space ID"),
                "archived": ParameterDef(
                    type="boolean",
                    description="Include archived",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_list",
            description="Get a specific list",
            parameters={"list_id": _list_id_param()},
        ),
        ActionDefinition(
            name="create_list",
            description="Create a list in a folder OR folderless list in a space",
            parameters={
                "name": ParameterDef(
                    type="string", description="List name", required=True
                ),
                "folder_id": ParameterDef(type="string", description="Folder ID"),
                "space_id": ParameterDef(type="string", description="Space ID"),
                "content": ParameterDef(
                    type="string", description="List description"
                ),
                "due_date": ParameterDef(
                    type="integer", description="Due date (epoch ms)"
                ),
                "priority": ParameterDef(
                    type="integer",
                    description="Priority (1=Urgent..4=Low)",
                ),
                "assignee": ParameterDef(
                    type="integer", description="Assignee user ID"
                ),
                "status": ParameterDef(type="string", description="List status"),
            },
        ),
        # --- Tasks ---------------------------------------------------------
        ActionDefinition(
            name="get_tasks",
            description="List tasks in a list with filters + pagination",
            parameters={
                "list_id": _list_id_param(),
                "archived": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Whether to archive",
                ),
                "include_closed": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Include closed tasks",
                ),
                "subtasks": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Include subtasks",
                ),
                "page": ParameterDef(
                    type="integer",
                    description="Page number (0-indexed)",
                    default=0,
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="id / created / updated / due_date",
                ),
                "reverse": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Reverse sort order",
                ),
                "statuses": ParameterDef(
                    type="array", description="Filter by status names"
                ),
                "assignees": ParameterDef(
                    type="array", description="Filter by assignee IDs"
                ),
            },
        ),
        ActionDefinition(
            name="get_task",
            description="Get a specific task",
            parameters={
                "task_id": _task_id_param(),
                **_custom_task_params(),
                "include_subtasks": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Include subtasks in response",
                ),
            },
        ),
        ActionDefinition(
            name="create_task",
            description="Create a task in a list",
            parameters={
                "list_id": _list_id_param(),
                "name": ParameterDef(
                    type="string", description="Task name", required=True
                ),
                "description": ParameterDef(
                    type="string", description="Markdown description"
                ),
                "status": ParameterDef(type="string", description="Status name"),
                "priority": ParameterDef(
                    type="integer",
                    description="1=Urgent..4=Low",
                ),
                "due_date": ParameterDef(
                    type="integer", description="Due date (epoch ms)"
                ),
                "due_date_time": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Whether due_date includes time",
                ),
                "start_date": ParameterDef(
                    type="integer", description="Start date (epoch ms)"
                ),
                "start_date_time": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Whether start_date includes time",
                ),
                "assignees": ParameterDef(
                    type="array", description="Assignee user IDs"
                ),
                "tags": ParameterDef(type="array", description="Tag names"),
                "parent": ParameterDef(
                    type="string", description="Parent task ID (for subtasks)"
                ),
                "notify_all": ParameterDef(
                    type="boolean",
                    default=True,
                    description="Notify all assignees",
                ),
                "time_estimate": ParameterDef(
                    type="integer", description="Time estimate (ms)"
                ),
            },
        ),
        ActionDefinition(
            name="update_task",
            description="Update fields on an existing task",
            parameters={
                "task_id": _task_id_param(),
                **_custom_task_params(),
                "name": ParameterDef(type="string", description="Updated task name"),
                "description": ParameterDef(type="string", description="Updated task description"),
                "status": ParameterDef(type="string", description="Updated status"),
                "priority": ParameterDef(
                    type="integer",
                    description="Updated priority (1=Urgent..4=Low)",
                ),
                "due_date": ParameterDef(type="integer", description="Updated due date (epoch ms)"),
                "due_date_time": ParameterDef(
                    type="boolean",
                    description="Whether due_date includes time",
                ),
                "start_date": ParameterDef(
                    type="integer",
                    description="Updated start date (epoch ms)",
                ),
                "start_date_time": ParameterDef(
                    type="boolean",
                    description="Whether start_date includes time",
                ),
                "assignees_add": ParameterDef(
                    type="array", description="User IDs to add"
                ),
                "assignees_remove": ParameterDef(
                    type="array", description="User IDs to remove"
                ),
                "archived": ParameterDef(type="boolean", description="Whether to archive"),
                "time_estimate": ParameterDef(type="integer", description="Time estimate (ms)"),
            },
        ),
        ActionDefinition(
            name="delete_task",
            description="Delete a task permanently",
            parameters={
                "task_id": _task_id_param(),
                **_custom_task_params(),
            },
        ),
        # --- Comments ------------------------------------------------------
        ActionDefinition(
            name="get_task_comments",
            description="Get comments on a task",
            parameters={
                "task_id": _task_id_param(),
                **_custom_task_params(),
                "start": ParameterDef(
                    type="integer", description="Pagination start position"
                ),
                "start_id": ParameterDef(
                    type="string", description="Comment ID to start from"
                ),
            },
        ),
        ActionDefinition(
            name="create_task_comment",
            description="Add a comment to a task",
            parameters={
                "task_id": _task_id_param(),
                **_custom_task_params(),
                "comment_text": ParameterDef(
                    type="string", description="Comment body", required=True
                ),
                "notify_all": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Notify all assignees",
                ),
                "assignee": ParameterDef(
                    type="integer", description="Assigned user ID"
                ),
            },
        ),
        # --- Search --------------------------------------------------------
        ActionDefinition(
            name="search_tasks",
            description=(
                "Search tasks across a team with filters. ``query`` is "
                "applied as a client-side substring filter on name + "
                "description (ClickUp has no full-text search API)."
            ),
            parameters={
                "team_id": _team_id_param(),
                "query": ParameterDef(type="string", description="Search query"),
                "statuses": ParameterDef(type="array", description="Status filter"),
                "assignees": ParameterDef(
                    type="array", description="Assignee user IDs"
                ),
                "tags": ParameterDef(type="array", description="Tag names"),
                "list_ids": ParameterDef(type="array", description="List IDs"),
                "folder_ids": ParameterDef(type="array", description="Folder IDs"),
                "space_ids": ParameterDef(type="array", description="Space IDs"),
                "include_closed": ParameterDef(
                    type="boolean",
                    default=False,
                    description="Include closed tasks",
                ),
                "page": ParameterDef(
                    type="integer",
                    default=0,
                    description="Page number (0-indexed)",
                ),
                "order_by": ParameterDef(type="string", description="Order field"),
            },
        ),
        # --- Tags ----------------------------------------------------------
        ActionDefinition(
            name="get_space_tags",
            description="List all tags in a space",
            parameters={"space_id": _space_id_param()},
        ),
        ActionDefinition(
            name="add_tag_to_task",
            description="Attach a tag to a task by name",
            parameters={
                "task_id": _task_id_param(),
                "tag_name": ParameterDef(
                    type="string", description="Tag name", required=True
                ),
                **_custom_task_params(),
            },
        ),
        ActionDefinition(
            name="remove_tag_from_task",
            description="Detach a tag from a task by name",
            parameters={
                "task_id": _task_id_param(),
                "tag_name": ParameterDef(
                    type="string", description="Tag name", required=True
                ),
                **_custom_task_params(),
            },
        ),
        # --- Members -------------------------------------------------------
        ActionDefinition(
            name="get_team_members",
            description=(
                "List members of a team. Implementation N+1: fetches all "
                "teams via GET /team and filters client-side by team_id."
            ),
            parameters={"team_id": _team_id_param()},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your ClickUp Personal API Token",
            setup_environment_variables=[
                EnvVar(
                    name="CLICKUP_API_KEY",
                    display_name="ClickUp API Key",
                    description=(
                        "Your ClickUp Personal API Token from Settings > Apps"
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="pk_xxxxxxxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.clickup.com/settings/apps",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.clickup.com/api/v2/team",
                method="GET",
                headers={"Authorization": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["teams"]
                ),
                cost_level="free",
                description="Validates API key by listing teams",
            ),
        ),
    ],
)
