"""Grafana integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    ParameterType,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _org_id_param() -> ParameterDef:
    return ParameterDef(
        type="string",
        description=(
            "Organization ID for multi-org Grafana instances (e.g. 1, 2). "
            "Sent as the X-Grafana-Org-Id header when set."
        ),
    )


def _p(
    type_: ParameterType,
    description: str,
    *,
    required: bool = False,
    default: object = None,
) -> ParameterDef:
    return ParameterDef(
        type=type_, description=description, required=required, default=default
    )


manifest = IntegrationManifest(
    name="grafana",
    display_name="Grafana",
    description=(
        "Manage Grafana dashboards, alert rules, annotations, contact points, "
        "data sources, and folders, and monitor instance and data source health "
        "via the Grafana HTTP API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:grafana",
    app_url="https://grafana.com",
    categories=["Monitoring & Observability", "monitoring", "data-analytics"],
    actions=[
        ActionDefinition(
            name="list_dashboards",
            description="Search and list all dashboards.",
            parameters={
                "organization_id": _org_id_param(),
                "query": _p("string", "Search query to filter dashboards by title"),
                "tag": _p(
                    "string", "Filter by tag (comma-separated for multiple tags)"
                ),
                "folder_uids": _p(
                    "string", "Filter by folder UIDs (comma-separated)"
                ),
                "dashboard_uids": _p(
                    "string", "Filter by dashboard UIDs (comma-separated)"
                ),
                "starred": _p("boolean", "Only return starred dashboards"),
                "limit": _p("integer", "Maximum number of dashboards to return"),
                "page": _p("integer", "Page number for pagination (1-based)"),
            },
        ),
        ActionDefinition(
            name="get_dashboard",
            description="Get a dashboard by its UID.",
            parameters={
                "dashboard_uid": _p(
                    "string", "The UID of the dashboard to retrieve", required=True
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="create_dashboard",
            description="Create a new dashboard.",
            parameters={
                "title": _p("string", "The title of the new dashboard", required=True),
                "folder_uid": _p(
                    "string", "UID of the folder to create the dashboard in"
                ),
                "tags": _p("string", "Comma-separated list of tags"),
                "timezone": _p("string", "Dashboard timezone (e.g. browser, utc)"),
                "refresh": _p("string", "Auto-refresh interval (e.g. 5s, 1m, 5m)"),
                "panels": _p("string", "JSON array of panel configurations"),
                "overwrite": _p(
                    "boolean", "Overwrite an existing dashboard with the same title"
                ),
                "message": _p("string", "Commit message for the dashboard version"),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="update_dashboard",
            description=(
                "Update an existing dashboard. Fetches the current dashboard "
                "and merges your changes."
            ),
            parameters={
                "dashboard_uid": _p(
                    "string", "The UID of the dashboard to update", required=True
                ),
                "title": _p("string", "New title for the dashboard"),
                "folder_uid": _p(
                    "string", "New folder UID to move the dashboard to"
                ),
                "tags": _p("string", "Comma-separated list of new tags"),
                "timezone": _p("string", "Dashboard timezone (e.g. browser, utc)"),
                "refresh": _p("string", "Auto-refresh interval (e.g. 5s, 1m, 5m)"),
                "panels": _p("string", "JSON array of panel configurations"),
                "overwrite": _p("boolean", "Overwrite even on a version conflict"),
                "message": _p("string", "Commit message for this version"),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="delete_dashboard",
            description="Delete a dashboard by its UID.",
            parameters={
                "dashboard_uid": _p(
                    "string", "The UID of the dashboard to delete", required=True
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="list_alert_rules",
            description="List all alert rules in the Grafana instance.",
            parameters={"organization_id": _org_id_param()},
        ),
        ActionDefinition(
            name="get_alert_rule",
            description="Get a specific alert rule by its UID.",
            parameters={
                "alert_rule_uid": _p(
                    "string", "The UID of the alert rule to retrieve", required=True
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="create_alert_rule",
            description="Create a new alert rule.",
            parameters={
                "title": _p("string", "The title of the alert rule", required=True),
                "folder_uid": _p(
                    "string",
                    "UID of the folder to create the alert in",
                    required=True,
                ),
                "rule_group": _p(
                    "string", "The name of the rule group", required=True
                ),
                "data": _p(
                    "string",
                    "JSON array of query/expression data objects",
                    required=True,
                ),
                "condition": _p(
                    "string",
                    "RefId of the query/expression used as the alert condition "
                    "(omit for recording rules)",
                ),
                "for_duration": _p(
                    "string", "Duration to wait before firing (e.g. 5m, 1h)"
                ),
                "no_data_state": _p(
                    "string", "State when no data is returned (NoData, Alerting, OK)"
                ),
                "exec_err_state": _p(
                    "string", "State on execution error (Error, Alerting, OK)"
                ),
                "annotations": _p("string", "JSON object of annotations"),
                "labels": _p("string", "JSON object of labels"),
                "uid": _p("string", "Optional custom UID for the alert rule"),
                "is_paused": _p("boolean", "Whether the rule is paused on creation"),
                "keep_firing_for": _p(
                    "string", "Duration to keep firing after the condition stops"
                ),
                "missing_series_evals_to_resolve": _p(
                    "integer", "Missing series evaluations before resolving"
                ),
                "notification_settings": _p(
                    "string", "JSON object of per-rule notification settings"
                ),
                "record": _p(
                    "string",
                    "JSON object configuring this as a recording rule",
                ),
                "disable_provenance": _p(
                    "boolean",
                    "Set the X-Disable-Provenance header so the rule stays UI-editable",
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="update_alert_rule",
            description=(
                "Update an existing alert rule. Fetches the current rule and "
                "merges your changes."
            ),
            parameters={
                "alert_rule_uid": _p(
                    "string", "The UID of the alert rule to update", required=True
                ),
                "title": _p("string", "New title for the alert rule"),
                "folder_uid": _p("string", "New folder UID for the rule"),
                "rule_group": _p("string", "New rule group name"),
                "condition": _p("string", "New condition refId"),
                "data": _p(
                    "string", "New JSON array of query/expression data objects"
                ),
                "for_duration": _p(
                    "string", "Duration to wait before firing (e.g. 5m, 1h)"
                ),
                "no_data_state": _p(
                    "string", "State when no data is returned (NoData, Alerting, OK)"
                ),
                "exec_err_state": _p(
                    "string", "State on execution error (Error, Alerting, OK)"
                ),
                "annotations": _p("string", "JSON object of annotations"),
                "labels": _p("string", "JSON object of labels"),
                "is_paused": _p("boolean", "Whether the rule is paused"),
                "keep_firing_for": _p(
                    "string", "Duration to keep firing after the condition stops"
                ),
                "missing_series_evals_to_resolve": _p(
                    "integer", "Missing series evaluations before resolving"
                ),
                "notification_settings": _p(
                    "string", "JSON object of per-rule notification settings"
                ),
                "record": _p(
                    "string", "JSON object configuring this as a recording rule"
                ),
                "disable_provenance": _p(
                    "boolean",
                    "Set the X-Disable-Provenance header so the rule stays UI-editable",
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="delete_alert_rule",
            description="Delete an alert rule by its UID.",
            parameters={
                "alert_rule_uid": _p(
                    "string", "The UID of the alert rule to delete", required=True
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="list_contact_points",
            description="List all alert notification contact points.",
            parameters={
                "name": _p(
                    "string", "Filter contact points by exact name match"
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="create_contact_point",
            description=(
                "Create a notification contact point (e.g. Slack, email, PagerDuty)."
            ),
            parameters={
                "name": _p("string", "Name of the contact point", required=True),
                "type": _p(
                    "string",
                    "Receiver type (e.g. slack, email, pagerduty, webhook, teams, "
                    "opsgenie, discord)",
                    required=True,
                ),
                "settings": _p(
                    "string",
                    "JSON object of type-specific receiver settings",
                    required=True,
                ),
                "disable_resolve_message": _p(
                    "boolean", "Do not send a notification when the alert resolves"
                ),
                "disable_provenance": _p(
                    "boolean",
                    "Set the X-Disable-Provenance header so the contact point stays "
                    "UI-editable",
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="create_annotation",
            description="Create an annotation on a dashboard or as a global annotation.",
            parameters={
                "text": _p(
                    "string", "The text content of the annotation", required=True
                ),
                "tags": _p("string", "Comma-separated list of tags"),
                "dashboard_uid": _p(
                    "string",
                    "UID of the dashboard to annotate; omit for a global annotation",
                ),
                "panel_id": _p(
                    "integer", "ID of the panel to attach the annotation to"
                ),
                "time": _p(
                    "integer", "Start time in epoch milliseconds (defaults to now)"
                ),
                "time_end": _p(
                    "integer", "End time in epoch milliseconds for range annotations"
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="list_annotations",
            description="Query annotations by time range, dashboard, or tags.",
            parameters={
                "from_": _p("integer", "Start time in epoch milliseconds"),
                "to": _p("integer", "End time in epoch milliseconds"),
                "dashboard_uid": _p(
                    "string", "Dashboard UID to query annotations from"
                ),
                "dashboard_id": _p(
                    "integer", "Legacy numeric dashboard ID filter"
                ),
                "panel_id": _p("integer", "Filter by panel ID"),
                "alert_id": _p("integer", "Filter by alert ID"),
                "user_id": _p("integer", "Filter by ID of the creating user"),
                "tags": _p(
                    "string", "Comma-separated list of tags to filter by"
                ),
                "type": _p("string", "Filter by type (alert or annotation)"),
                "limit": _p("integer", "Maximum number of annotations to return"),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="update_annotation",
            description="Update an existing annotation.",
            parameters={
                "annotation_id": _p(
                    "integer", "The ID of the annotation to update", required=True
                ),
                "text": _p("string", "New text content for the annotation"),
                "tags": _p("string", "Comma-separated list of new tags"),
                "time": _p("integer", "New start time in epoch milliseconds"),
                "time_end": _p("integer", "New end time in epoch milliseconds"),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="delete_annotation",
            description="Delete an annotation by its ID.",
            parameters={
                "annotation_id": _p(
                    "integer", "The ID of the annotation to delete", required=True
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="list_data_sources",
            description="List all data sources configured in Grafana.",
            parameters={"organization_id": _org_id_param()},
        ),
        ActionDefinition(
            name="get_data_source",
            description="Get a data source by its ID or UID.",
            parameters={
                "data_source_id": _p(
                    "string",
                    "The ID or UID of the data source to retrieve",
                    required=True,
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="check_data_source_health",
            description="Test connectivity to a data source by its UID.",
            parameters={
                "data_source_uid": _p(
                    "string",
                    "The UID of the data source to health-check",
                    required=True,
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="list_folders",
            description="List all folders in Grafana.",
            parameters={
                "limit": _p("integer", "Maximum number of folders to return"),
                "page": _p("integer", "Page number for pagination"),
                "parent_uid": _p(
                    "string", "List children of this folder UID"
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="create_folder",
            description="Create a new folder in Grafana.",
            parameters={
                "title": _p("string", "The title of the new folder", required=True),
                "uid": _p("string", "Optional UID for the folder"),
                "parent_uid": _p(
                    "string", "Parent folder UID for nested folders"
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="get_folder",
            description="Get a folder by its UID.",
            parameters={
                "folder_uid": _p(
                    "string", "The UID of the folder to retrieve", required=True
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="update_folder",
            description=(
                "Update (rename) a folder. Fetches the current folder and merges "
                "your changes."
            ),
            parameters={
                "folder_uid": _p(
                    "string", "The UID of the folder to update", required=True
                ),
                "title": _p("string", "New title for the folder", required=True),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="delete_folder",
            description="Delete a folder by its UID.",
            parameters={
                "folder_uid": _p(
                    "string", "The UID of the folder to delete", required=True
                ),
                "force_delete_rules": _p(
                    "boolean",
                    "Delete any alert rules stored in the folder along with it",
                ),
                "organization_id": _org_id_param(),
            },
        ),
        ActionDefinition(
            name="get_health",
            description=(
                "Check the health of the Grafana instance (version, database status)."
            ),
            parameters={"organization_id": _org_id_param()},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Service Account Token",
            description=(
                "Authenticate with a Grafana service account token against your "
                "instance"
            ),
            setup_instructions=[
                "In Grafana, open Administration -> Users and access -> "
                "Service accounts",
                "Create a service account with the roles your workflow needs "
                "(e.g. Editor or Admin)",
                "Add a service account token and copy the generated 'glsa_...' value",
                "Paste the token below and set your Grafana instance URL "
                "(e.g. https://your-grafana.com)",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GRAFANA_API_KEY",
                    display_name="Service Account Token",
                    description="Your Grafana service account token (starts with glsa_)",
                    required=True,
                    sensitive=True,
                    sample_format="glsa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx_xxxxxxxx",
                ),
                EnvVar(
                    name="GRAFANA_BASE_URL",
                    display_name="Grafana URL",
                    description=(
                        "Your Grafana instance base URL, e.g. https://your-grafana.com"
                    ),
                    required=True,
                    sensitive=False,
                    only_for_custom=False,
                    inject_into_auth_data=True,
                    sample_format="https://your-grafana.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="{base_url}/api/health",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["database"],
                ),
                cost_level="free",
                description=(
                    "Validates the token and instance URL via GET /api/health."
                ),
            ),
        ),
    ],
)
