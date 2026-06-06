"""Motion integration manifest."""
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


manifest = IntegrationManifest(
    name="motion",
    display_name="Motion",
    description="AI-powered task and project management platform for automatic scheduling",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:motion-themed",
    app_url="https://www.usemotion.com",
    categories=["Project & Task Management", "Productivity & Collaboration", "project-management"],
    actions=[
        ActionDefinition(
            name="create_task",
            description="Create a new task in a Motion workspace",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="The ID of the workspace",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name / title of the task",
                    required=True,
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="The ID of the project to assign the task to",
                ),
                "due_date": ParameterDef(
                    type="string",
                    description="ISO 8601 due date. Required for scheduled tasks. Example: 2023-06-28T10:11:14.320-06:00",
                ),
                "duration": ParameterDef(
                    type="string",
                    description="Duration: NONE, REMINDER, or an integer greater than 0",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Task description in GitHub Flavored Markdown",
                ),
                "priority": ParameterDef(
                    type="string",
                    description="Priority level: ASAP, HIGH, MEDIUM, LOW",
                    default="MEDIUM",
                ),
                "assignee_id": ParameterDef(
                    type="string",
                    description="The user ID to assign the task to",
                ),
                "labels": ParameterDef(
                    type="array",
                    description="List of label names to add to the task",
                ),
                "status": ParameterDef(
                    type="string",
                    description="The name of the task status",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="ISO 8601 date for auto-scheduled tasks. Example: 2023-06-28",
                ),
                "deadline_type": ParameterDef(
                    type="string",
                    description="Deadline type for auto-scheduled tasks: HARD, SOFT, NONE",
                ),
                "schedule": ParameterDef(
                    type="string",
                    description="Schedule the task must adhere to. Must be 'Work Hours' if scheduling for another user",
                    default="Work Hours",
                ),
            },
        ),
        ActionDefinition(
            name="delete_task",
            description="Delete a specific task by ID",
            parameters={
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the task to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_schedules",
            description="Get a list of schedules for the authenticated user",
            parameters={},
        ),
        ActionDefinition(
            name="get_task",
            description="Retrieve a specific task by ID",
            parameters={
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the task to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="move_workspace",
            description="Move a task to another workspace. Resets the task's project, status, labels, and assignee",
            parameters={
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the task to move",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The ID of the target workspace",
                    required=True,
                ),
                "assignee_id": ParameterDef(
                    type="string",
                    description="The user ID to assign the task to in the target workspace",
                ),
            },
        ),
        ActionDefinition(
            name="update_task",
            description="Update a specific task's properties",
            parameters={
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the task to update",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="New name / title for the task",
                ),
                "due_date": ParameterDef(
                    type="string",
                    description="ISO 8601 due date. Example: 2023-06-28T10:11:14.320-06:00",
                ),
                "duration": ParameterDef(
                    type="string",
                    description="Duration: NONE, REMINDER, or an integer greater than 0",
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="The ID of the project to assign the task to",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Task description in GitHub Flavored Markdown",
                ),
                "priority": ParameterDef(
                    type="string",
                    description="Priority level: ASAP, HIGH, MEDIUM, LOW",
                    default="MEDIUM",
                ),
                "assignee_id": ParameterDef(
                    type="string",
                    description="The user ID to assign the task to",
                ),
                "labels": ParameterDef(
                    type="array",
                    description="List of label names to add to the task",
                ),
                "status": ParameterDef(
                    type="string",
                    description="The name of the task status",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="ISO 8601 date for auto-scheduled tasks. Example: 2023-06-28",
                ),
                "deadline_type": ParameterDef(
                    type="string",
                    description="Deadline type for auto-scheduled tasks: HARD, SOFT, NONE",
                ),
                "schedule": ParameterDef(
                    type="string",
                    description="Schedule the task must adhere to. Must be 'Work Hours' if scheduling for another user",
                    default="Work Hours",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Motion API key",
            setup_instructions=[
                "Go to https://app.usemotion.com and sign in",
                "Navigate to Settings > API",
                "Generate a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MOTION_API_KEY",
                    display_name="Motion API Key",
                    description="Your Motion API key from the Settings > API page",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.usemotion.com/settings",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.usemotion.com/v1/users/me",
                method="GET",
                headers={"X-API-Key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates the API key by fetching the current user",
            ),
        ),
    ],
)
