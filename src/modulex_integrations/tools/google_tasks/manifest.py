"""Google Tasks integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="google_tasks",
    display_name="Google Tasks",
    description="Manage tasks and task lists using the Google Tasks API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_tasks",
    app_url="https://tasks.google.com",
    categories=["Productivity & Collaboration", "task-management"],
    actions=[
        ActionDefinition(
            name="create_task",
            description="Creates a new task and adds it to the authenticated user's task lists",
            parameters={
                "task_list_id": ParameterDef(
                    type="string",
                    description="The ID of the task list",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the task",
                    required=True,
                ),
                "notes": ParameterDef(
                    type="string",
                    description="The description of the task",
                ),
                "completed": ParameterDef(
                    type="boolean",
                    description="Mark as true if your task is already completed",
                    required=True,
                ),
                "due": ParameterDef(
                    type="string",
                    description="Due date of the task as an RFC 3339 timestamp (date portion only)",
                ),
            },
        ),
        ActionDefinition(
            name="create_task_list",
            description="Creates a new task list and adds it to the authenticated user's task lists",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The title of the task list",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_task",
            description="Deletes the authenticated user's specified task",
            parameters={
                "task_list_id": ParameterDef(
                    type="string",
                    description="The ID of the task list",
                    required=True,
                ),
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the task",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_task_list",
            description="Deletes the authenticated user's specified task list",
            parameters={
                "task_list_id": ParameterDef(
                    type="string",
                    description="The ID of the task list",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_tasks",
            description="Returns all tasks in the specified task list",
            parameters={
                "task_list_id": ParameterDef(
                    type="string",
                    description="The ID of the task list",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of tasks to be fetched",
                    default=20,
                ),
                "show_completed": ParameterDef(
                    type="boolean",
                    description="Whether completed tasks are returned in the result",
                ),
                "show_deleted": ParameterDef(
                    type="boolean",
                    description="Whether deleted tasks are returned in the result",
                ),
            },
        ),
        ActionDefinition(
            name="list_task_lists",
            description="Lists the authenticated user's task lists",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of task lists to be fetched",
                    default=20,
                ),
            },
        ),
        ActionDefinition(
            name="update_task",
            description="Updates the authenticated user's specified task",
            parameters={
                "task_list_id": ParameterDef(
                    type="string",
                    description="The ID of the task list",
                    required=True,
                ),
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the task",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the task",
                    required=True,
                ),
                "notes": ParameterDef(
                    type="string",
                    description="The description of the task",
                ),
                "completed": ParameterDef(
                    type="boolean",
                    description="Mark as true if your task is already completed",
                ),
                "due": ParameterDef(
                    type="string",
                    description="Due date of the task as an RFC 3339 timestamp (date portion only)",
                ),
            },
        ),
        ActionDefinition(
            name="update_task_list",
            description="Updates the authenticated user's specified task list",
            parameters={
                "task_list_id": ParameterDef(
                    type="string",
                    description="The ID of the task list",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the task list",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_TASKS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_TASKS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-" + "x" * 28,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                access_type="offline",
                prompt="consent",
                scopes=["https://www.googleapis.com/auth/tasks"],
            ),
            test_endpoint=TestEndpoint(
                url="https://tasks.googleapis.com/tasks/v1/users/@me/lists",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["items"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing the user's task lists",
            ),
        ),
    ],
)
