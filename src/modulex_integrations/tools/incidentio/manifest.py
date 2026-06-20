"""incident.io integration manifest.

Pydantic manifest for the incident.io REST API (``https://api.incident.io``).
Authentication is a single bring-your-own API key sent as
``Authorization: Bearer {api_key}``.
"""
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


_PAGE_SIZE = ParameterDef(
    type="integer",
    description="Number of results to return per page (e.g., 10, 25, 50)",
)
_AFTER = ParameterDef(
    type="string",
    description="Pagination cursor to fetch the next page of results",
)


manifest = IntegrationManifest(
    name="incidentio",
    display_name="incident.io",
    description=(
        "Manage incidents, actions, follow-ups, workflows, schedules, escalations, "
        "custom fields, and more with incident.io — the incident management and "
        "on-call response platform."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:incidentio-themed",
    app_url="https://incident.io",
    categories=["Monitoring & Observability", "incident-management", "on-call"],
    actions=[
        # --- Incidents ---------------------------------------------------
        ActionDefinition(
            name="incidents_list",
            description=(
                "List incidents from incident.io. Returns a list of incidents with "
                "their details including severity, status, and timestamps."
            ),
            parameters={
                "page_size": _PAGE_SIZE,
                "after": _AFTER,
                "sort_by": ParameterDef(
                    type="string",
                    description=(
                        "Sort order: 'created_at_newest_first' or "
                        "'created_at_oldest_first'"
                    ),
                ),
                "filter_mode": ParameterDef(
                    type="string",
                    description="How to combine filters: 'all' or 'any'",
                ),
            },
        ),
        ActionDefinition(
            name="incidents_create",
            description=(
                "Create a new incident in incident.io. Requires idempotency_key, "
                "severity_id, and visibility. Optionally accepts name, summary, type, "
                "and status."
            ),
            parameters={
                "idempotency_key": ParameterDef(
                    type="string",
                    description="Unique identifier to prevent duplicate creation (e.g., a UUID)",
                    required=True,
                ),
                "severity_id": ParameterDef(
                    type="string",
                    description="ID of the severity level",
                    required=True,
                ),
                "visibility": ParameterDef(
                    type="string",
                    description="Visibility of the incident: 'public' or 'private'",
                    required=True,
                ),
                "name": ParameterDef(type="string", description="Name of the incident"),
                "summary": ParameterDef(
                    type="string", description="Brief summary of the incident"
                ),
                "incident_type_id": ParameterDef(
                    type="string", description="ID of the incident type"
                ),
                "incident_status_id": ParameterDef(
                    type="string", description="ID of the initial incident status"
                ),
            },
        ),
        ActionDefinition(
            name="incidents_show",
            description=(
                "Retrieve detailed information about a specific incident by its ID, "
                "including custom fields and role assignments."
            ),
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="ID of the incident to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="incidents_update",
            description=(
                "Update an existing incident in incident.io. Can update name, summary, "
                "severity, status, or type."
            ),
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="ID of the incident to update",
                    required=True,
                ),
                "notify_incident_channel": ParameterDef(
                    type="boolean",
                    description="Whether to notify the incident channel about this update",
                    required=True,
                ),
                "name": ParameterDef(type="string", description="Updated name of the incident"),
                "summary": ParameterDef(
                    type="string", description="Updated summary of the incident"
                ),
                "severity_id": ParameterDef(type="string", description="Updated severity ID"),
                "incident_status_id": ParameterDef(
                    type="string", description="Updated status ID"
                ),
                "incident_type_id": ParameterDef(
                    type="string", description="Updated incident type ID"
                ),
            },
        ),
        # --- Actions -----------------------------------------------------
        ActionDefinition(
            name="actions_list",
            description="List actions from incident.io. Optionally filter by incident ID.",
            parameters={
                "incident_id": ParameterDef(
                    type="string", description="Filter actions by incident ID"
                ),
                "incident_mode": ParameterDef(
                    type="string",
                    description=(
                        "Filter by incident mode: standard, retrospective, test, "
                        "tutorial, or stream"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="actions_show",
            description="Get detailed information about a specific action from incident.io.",
            parameters={
                "id": ParameterDef(type="string", description="Action ID", required=True),
            },
        ),
        # --- Follow-ups --------------------------------------------------
        ActionDefinition(
            name="follow_ups_list",
            description="List follow-ups from incident.io. Optionally filter by incident ID.",
            parameters={
                "incident_id": ParameterDef(
                    type="string", description="Filter follow-ups by incident ID"
                ),
                "incident_mode": ParameterDef(
                    type="string",
                    description=(
                        "Filter by incident mode: standard, retrospective, test, "
                        "tutorial, or stream"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="follow_ups_show",
            description="Get detailed information about a specific follow-up from incident.io.",
            parameters={
                "id": ParameterDef(type="string", description="Follow-up ID", required=True),
            },
        ),
        # --- Users -------------------------------------------------------
        ActionDefinition(
            name="users_list",
            description=(
                "List all users in the incident.io workspace. Returns user details "
                "including id, name, email, and role."
            ),
            parameters={
                "page_size": _PAGE_SIZE,
                "after": _AFTER,
                "email": ParameterDef(
                    type="string", description="Filter users by email address"
                ),
                "slack_user_id": ParameterDef(
                    type="string", description="Filter users by Slack user ID"
                ),
            },
        ),
        ActionDefinition(
            name="users_show",
            description="Get detailed information about a specific user by their ID.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The unique identifier of the user to retrieve",
                    required=True,
                ),
            },
        ),
        # --- Workflows ---------------------------------------------------
        ActionDefinition(
            name="workflows_list",
            description="List all workflows in the incident.io workspace.",
            parameters={},
        ),
        ActionDefinition(
            name="workflows_create",
            description="Create a new workflow in incident.io.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Name of the workflow", required=True
                ),
                "folder": ParameterDef(
                    type="string", description="Folder to organize the workflow in"
                ),
                "state": ParameterDef(
                    type="string",
                    description="State of the workflow: active, draft, or disabled",
                    default="draft",
                ),
                "trigger": ParameterDef(
                    type="string",
                    description="Trigger type for the workflow",
                    default="incident.updated",
                ),
                "steps": ParameterDef(
                    type="array", description="Array of workflow steps (defaults to [])"
                ),
                "condition_groups": ParameterDef(
                    type="array",
                    description="Array of condition groups controlling when the workflow runs",
                ),
                "runs_on_incidents": ParameterDef(
                    type="string",
                    description=(
                        "When to run: newly_created, newly_created_and_active, active, or all"
                    ),
                    default="newly_created",
                ),
                "runs_on_incident_modes": ParameterDef(
                    type="array",
                    description="Array of incident modes to run on (defaults to ['standard'])",
                ),
                "include_private_incidents": ParameterDef(
                    type="boolean",
                    description="Whether to include private incidents",
                    default=True,
                ),
                "continue_on_step_error": ParameterDef(
                    type="boolean",
                    description="Whether to continue executing subsequent steps if one fails",
                    default=False,
                ),
                "once_for": ParameterDef(
                    type="array",
                    description="Array of fields making the workflow run once per combination",
                ),
                "expressions": ParameterDef(
                    type="array", description="Array of workflow expressions for advanced logic"
                ),
                "delay": ParameterDef(
                    type="object", description="Delay configuration object"
                ),
            },
        ),
        ActionDefinition(
            name="workflows_show",
            description="Get details of a specific workflow in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the workflow to retrieve",
                    required=True,
                ),
                "skip_step_upgrades": ParameterDef(
                    type="boolean",
                    description="Skip workflow step upgrades when existing step parameters changed",
                ),
            },
        ),
        ActionDefinition(
            name="workflows_update",
            description="Update an existing workflow in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the workflow to update",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string", description="New name for the workflow", required=True
                ),
                "steps": ParameterDef(
                    type="array", description="Complete array of workflow steps", required=True
                ),
                "condition_groups": ParameterDef(
                    type="array",
                    description="Complete array of workflow condition groups",
                    required=True,
                ),
                "runs_on_incidents": ParameterDef(
                    type="string",
                    description=(
                        "When to run: newly_created, newly_created_and_active, active, or all"
                    ),
                    required=True,
                ),
                "runs_on_incident_modes": ParameterDef(
                    type="array",
                    description="Complete array of incident modes to run on",
                    required=True,
                ),
                "include_private_incidents": ParameterDef(
                    type="boolean",
                    description="Whether to include private incidents",
                    required=True,
                ),
                "continue_on_step_error": ParameterDef(
                    type="boolean",
                    description="Whether to continue executing subsequent steps if one fails",
                    required=True,
                ),
                "once_for": ParameterDef(
                    type="array",
                    description="Complete array of fields that make the workflow run once",
                    required=True,
                ),
                "expressions": ParameterDef(
                    type="array",
                    description="Complete array of workflow expressions",
                    required=True,
                ),
                "state": ParameterDef(
                    type="string", description="New state: active, draft, or disabled"
                ),
                "folder": ParameterDef(
                    type="string", description="New folder for the workflow"
                ),
                "delay": ParameterDef(
                    type="object", description="Delay configuration object"
                ),
            },
        ),
        ActionDefinition(
            name="workflows_delete",
            description="Delete a workflow in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the workflow to delete",
                    required=True,
                ),
            },
        ),
        # --- Schedules ---------------------------------------------------
        ActionDefinition(
            name="schedules_list",
            description="List all schedules in incident.io.",
            parameters={"page_size": _PAGE_SIZE, "after": _AFTER},
        ),
        ActionDefinition(
            name="schedules_create",
            description="Create a new schedule in incident.io.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Name of the schedule", required=True
                ),
                "timezone": ParameterDef(
                    type="string",
                    description="Timezone for the schedule (e.g., America/New_York)",
                    required=True,
                ),
                "rotations_config": ParameterDef(
                    type="object",
                    description="Schedule configuration object with rotations",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="schedules_show",
            description="Get details of a specific schedule in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string", description="The ID of the schedule", required=True
                ),
            },
        ),
        ActionDefinition(
            name="schedules_update",
            description="Update an existing schedule in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the schedule to update",
                    required=True,
                ),
                "name": ParameterDef(type="string", description="New name for the schedule"),
                "timezone": ParameterDef(
                    type="string", description="New timezone for the schedule"
                ),
                "rotations_config": ParameterDef(
                    type="object",
                    description="Schedule configuration object with rotations",
                ),
            },
        ),
        ActionDefinition(
            name="schedules_delete",
            description="Delete a schedule in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the schedule to delete",
                    required=True,
                ),
            },
        ),
        # --- Escalations -------------------------------------------------
        ActionDefinition(
            name="escalations_list",
            description="List all escalations in incident.io.",
            parameters={"page_size": _PAGE_SIZE, "after": _AFTER},
        ),
        ActionDefinition(
            name="escalations_create",
            description="Create a new escalation in incident.io.",
            parameters={
                "idempotency_key": ParameterDef(
                    type="string",
                    description="Unique identifier to prevent duplicate escalation creation",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string", description="Title of the escalation", required=True
                ),
                "escalation_path_id": ParameterDef(
                    type="string",
                    description="ID of the escalation path (required if user_ids not provided)",
                ),
                "user_ids": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated user IDs to notify (required if no escalation_path_id)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="escalations_show",
            description="Get details of a specific escalation in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string", description="The ID of the escalation policy", required=True
                ),
            },
        ),
        # --- Custom Fields -----------------------------------------------
        ActionDefinition(
            name="custom_fields_list",
            description="List all custom fields from incident.io.",
            parameters={},
        ),
        ActionDefinition(
            name="custom_fields_create",
            description="Create a new custom field in incident.io.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Name of the custom field", required=True
                ),
                "description": ParameterDef(
                    type="string", description="Description of the custom field", required=True
                ),
                "field_type": ParameterDef(
                    type="string",
                    description=(
                        "Field type: text, single_select, multi_select, numeric, link, etc."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="custom_fields_show",
            description="Get detailed information about a specific custom field from incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string", description="Custom field ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="custom_fields_update",
            description="Update an existing custom field in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string", description="Custom field ID", required=True
                ),
                "name": ParameterDef(
                    type="string", description="New name for the custom field", required=True
                ),
                "description": ParameterDef(
                    type="string",
                    description="New description for the custom field",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="custom_fields_delete",
            description="Delete a custom field from incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string", description="Custom field ID", required=True
                ),
            },
        ),
        # --- Reference data ----------------------------------------------
        ActionDefinition(
            name="severities_list",
            description=(
                "List all severity levels configured in the incident.io workspace."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="incident_statuses_list",
            description=(
                "List all incident statuses configured in the incident.io workspace."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="incident_types_list",
            description=(
                "List all incident types configured in the incident.io workspace."
            ),
            parameters={},
        ),
        # --- Incident Roles ----------------------------------------------
        ActionDefinition(
            name="incident_roles_list",
            description="List all incident roles in incident.io.",
            parameters={},
        ),
        ActionDefinition(
            name="incident_roles_create",
            description="Create a new incident role in incident.io.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Name of the incident role", required=True
                ),
                "description": ParameterDef(
                    type="string", description="Description of the incident role", required=True
                ),
                "instructions": ParameterDef(
                    type="string",
                    description="Instructions for the incident role",
                    required=True,
                ),
                "shortform": ParameterDef(
                    type="string",
                    description="Short form abbreviation for the role",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="incident_roles_show",
            description="Get details of a specific incident role in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string", description="The ID of the incident role", required=True
                ),
            },
        ),
        ActionDefinition(
            name="incident_roles_update",
            description="Update an existing incident role in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the incident role to update",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string", description="Name of the incident role", required=True
                ),
                "description": ParameterDef(
                    type="string", description="Description of the incident role", required=True
                ),
                "instructions": ParameterDef(
                    type="string",
                    description="Instructions for the incident role",
                    required=True,
                ),
                "shortform": ParameterDef(
                    type="string",
                    description="Short form abbreviation for the role",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="incident_roles_delete",
            description="Delete an incident role in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the incident role to delete",
                    required=True,
                ),
            },
        ),
        # --- Incident Timestamps -----------------------------------------
        ActionDefinition(
            name="incident_timestamps_list",
            description="List all incident timestamp definitions in incident.io.",
            parameters={},
        ),
        ActionDefinition(
            name="incident_timestamps_show",
            description="Get details of a specific incident timestamp definition in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string", description="The ID of the incident timestamp", required=True
                ),
            },
        ),
        # --- Incident Updates --------------------------------------------
        ActionDefinition(
            name="incident_updates_list",
            description="List incident updates in incident.io. Optionally filter by incident ID.",
            parameters={
                "incident_id": ParameterDef(
                    type="string", description="The ID of the incident to get updates for"
                ),
                "page_size": _PAGE_SIZE,
                "after": _AFTER,
            },
        ),
        # --- Schedule Entries --------------------------------------------
        ActionDefinition(
            name="schedule_entries_list",
            description="List all entries for a specific schedule in incident.io.",
            parameters={
                "schedule_id": ParameterDef(
                    type="string",
                    description="The ID of the schedule to get entries for",
                    required=True,
                ),
                "entry_window_start": ParameterDef(
                    type="string",
                    description="Start of the filter window in ISO 8601 format",
                ),
                "entry_window_end": ParameterDef(
                    type="string",
                    description="End of the filter window in ISO 8601 format",
                ),
            },
        ),
        # --- Schedule Overrides ------------------------------------------
        ActionDefinition(
            name="schedule_overrides_create",
            description="Create a new schedule override in incident.io.",
            parameters={
                "rotation_id": ParameterDef(
                    type="string",
                    description="The ID of the rotation to override",
                    required=True,
                ),
                "layer_id": ParameterDef(
                    type="string",
                    description="The ID of the layer this override applies to",
                    required=True,
                ),
                "schedule_id": ParameterDef(
                    type="string", description="The ID of the schedule", required=True
                ),
                "start_at": ParameterDef(
                    type="string",
                    description="When the override starts in ISO 8601 format",
                    required=True,
                ),
                "end_at": ParameterDef(
                    type="string",
                    description="When the override ends in ISO 8601 format",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string", description="The ID of the user to assign"
                ),
                "user_email": ParameterDef(
                    type="string", description="The email of the user to assign"
                ),
                "user_slack_id": ParameterDef(
                    type="string", description="The Slack ID of the user to assign"
                ),
            },
        ),
        # --- Escalation Paths --------------------------------------------
        ActionDefinition(
            name="escalation_paths_list",
            description="List escalation paths in incident.io.",
            parameters={"page_size": _PAGE_SIZE, "after": _AFTER},
        ),
        ActionDefinition(
            name="escalation_paths_create",
            description="Create a new escalation path in incident.io.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Name of the escalation path", required=True
                ),
                "path": ParameterDef(
                    type="array",
                    description=(
                        "Array of escalation levels. Each level has targets "
                        "(array of {id, type, schedule_id?, user_id?, urgency}) and "
                        "time_to_ack_seconds"
                    ),
                    required=True,
                ),
                "working_hours": ParameterDef(
                    type="array",
                    description=(
                        "Optional working hours config: array of "
                        "{weekday, start_time, end_time}"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="escalation_paths_show",
            description="Get details of a specific escalation path in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string", description="The ID of the escalation path", required=True
                ),
            },
        ),
        ActionDefinition(
            name="escalation_paths_update",
            description="Update an existing escalation path in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the escalation path to update",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="New name for the escalation path",
                    required=True,
                ),
                "path": ParameterDef(
                    type="array",
                    description=(
                        "New escalation path: array of levels with targets and "
                        "time_to_ack_seconds"
                    ),
                    required=True,
                ),
                "working_hours": ParameterDef(
                    type="array",
                    description=(
                        "New working hours config: array of {weekday, start_time, end_time}"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="escalation_paths_delete",
            description="Delete an escalation path in incident.io.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="The ID of the escalation path to delete",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your incident.io API key",
            setup_instructions=[
                "Log in to your incident.io dashboard",
                "Go to Settings -> API keys",
                "Create a new API key and select the permissions it should have",
                "Copy the key (it is shown only once) and paste it below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="INCIDENTIO_API_KEY",
                    display_name="incident.io API Key",
                    description="Your incident.io API key from Settings -> API keys",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.incident.io/integrations/api-create-incident",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.incident.io/v1/severities",
                method="GET",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {api_key}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["severities"],
                ),
                cost_level="free",
                description="Validates the API key by listing configured severities",
            ),
        ),
    ],
)
