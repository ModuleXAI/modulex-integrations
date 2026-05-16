"""PostHog integration manifest.

PostHog auth in legacy is `custom` with three credential fields
(``api_key`` personal token, ``project_id``, ``base_url``). We model
that here as ``CustomAuthSchema`` with three ``EnvVar`` entries — the
modulex runtime injects all three into each tool function as
positional args (same pattern as the zendesk triple-credential setup).
"""
from __future__ import annotations

from typing import Literal, cast

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

ParameterType = Literal["string", "integer", "number", "boolean", "array", "object"]

__all__ = ["manifest"]


# --- Parameter shorthands -------------------------------------------------


def _project_id() -> ParameterDef:
    return ParameterDef(
        type="integer", description="PostHog project ID", required=True
    )


def _base_url() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="PostHog instance URL (default: https://app.posthog.com)",
    )


def _ingest_url() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="PostHog ingest URL (default: https://us.i.posthog.com)",
    )


def _project_api_key() -> ParameterDef:
    return ParameterDef(
        type="string", description="PostHog project API key", required=True
    )


def _required_int(label: str) -> ParameterDef:
    return ParameterDef(type="integer", description=label, required=True)


def _required_str(label: str) -> ParameterDef:
    return ParameterDef(type="string", description=label, required=True)


def _opt_str(label: str) -> ParameterDef:
    return ParameterDef(type="string", description=label)


def _opt_int(label: str) -> ParameterDef:
    return ParameterDef(type="integer", description=label)


def _opt_bool(label: str) -> ParameterDef:
    return ParameterDef(type="boolean", description=label)


def _limit() -> ParameterDef:
    return ParameterDef(type="integer", description="Max results", default=100)


def _offset() -> ParameterDef:
    return ParameterDef(type="integer", description="Results to skip", default=0)


# --- Action definitions ---------------------------------------------------


def _crud_get_all(
    name: str, description: str, extra: dict[str, ParameterDef] | None = None
) -> ActionDefinition:
    params: dict[str, ParameterDef] = {
        "project_id": _project_id(),
        "base_url": _base_url(),
        "limit": _limit(),
        "offset": _offset(),
    }
    if extra:
        params.update(extra)
    return ActionDefinition(name=name, description=description, parameters=params)


def _crud_get_one(
    name: str, description: str, id_field: str, id_type: str = "integer"
) -> ActionDefinition:
    return ActionDefinition(
        name=name,
        description=description,
        parameters={
            "project_id": _project_id(),
            id_field: ParameterDef(
                type=cast(ParameterType, id_type),
                description=f"{id_field} to retrieve",
                required=True,
            ),
            "base_url": _base_url(),
        },
    )


def _crud_delete(
    name: str, description: str, id_field: str, id_type: str = "integer"
) -> ActionDefinition:
    return ActionDefinition(
        name=name,
        description=description,
        parameters={
            "project_id": _project_id(),
            id_field: ParameterDef(
                type=cast(ParameterType, id_type),
                description=f"{id_field} to delete",
                required=True,
            ),
            "base_url": _base_url(),
        },
    )


manifest = IntegrationManifest(
    name="posthog",
    display_name="PostHog",
    description=(
        "Product analytics platform: events, persons, groups, cohorts, "
        "dashboards, insights, experiments, feature flags, surveys, "
        "session recordings, error tracking, and more (78 actions)."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:posthog-icon",
    app_url="https://posthog.com",
    categories=["Data & Analytics", "data", "development"],
    actions=[
        # --- Dashboards ----------------------------------------------------
        _crud_get_all(
            "get_dashboards",
            "List dashboards with optional search / pinned filter",
            {
                "search": _opt_str("Search query"),
                "pinned": _opt_bool("Filter by pinned status"),
            },
        ),
        _crud_get_one("get_dashboard", "Get a specific dashboard", "dashboard_id"),
        ActionDefinition(
            name="create_dashboard",
            description="Create a new dashboard",
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Dashboard name"),
                "base_url": _base_url(),
                "description": _opt_str("Dashboard description"),
                "pinned": _opt_bool("Pin the dashboard"),
                "tags": ParameterDef(type="array", description="Tag list"),
            },
        ),
        ActionDefinition(
            name="update_dashboard",
            description="Update a dashboard's name, description, pin, or tags",
            parameters={
                "project_id": _project_id(),
                "dashboard_id": _required_int("Dashboard ID"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "description": _opt_str("New description"),
                "pinned": _opt_bool("Pin status"),
                "tags": ParameterDef(type="array", description="Tag list"),
            },
        ),
        _crud_delete("delete_dashboard", "Delete a dashboard", "dashboard_id"),
        # --- Experiments ---------------------------------------------------
        ActionDefinition(
            name="get_experiments",
            description="List experiments",
            parameters={"project_id": _project_id(), "base_url": _base_url()},
        ),
        _crud_get_one("get_experiment", "Get an experiment", "experiment_id"),
        ActionDefinition(
            name="create_experiment",
            description="Create an A/B test experiment",
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Experiment name"),
                "feature_flag_key": _required_str(
                    "Feature flag key linked to the experiment"
                ),
                "base_url": _base_url(),
                "description": _opt_str("Experiment description"),
                "experiment_type": ParameterDef(
                    type="string",
                    description="'product' or 'web'",
                    default="product",
                ),
                "primary_metrics": ParameterDef(
                    type="array", description="Primary metric definitions"
                ),
                "secondary_metrics": ParameterDef(
                    type="array", description="Secondary metric definitions"
                ),
                "variants": ParameterDef(
                    type="array", description="Experiment variants"
                ),
                "minimum_detectable_effect": ParameterDef(
                    type="number",
                    description="Minimum detectable effect %",
                    default=30,
                ),
                "filter_test_accounts": ParameterDef(
                    type="boolean",
                    description="Filter out internal/test accounts",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_experiment",
            description=(
                "Update an experiment (rename, change metrics, launch, "
                "conclude, or archive)"
            ),
            parameters={
                "project_id": _project_id(),
                "experiment_id": _required_int("Experiment ID"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "description": _opt_str("New description"),
                "primary_metrics": ParameterDef(
                    type="array", description="Primary metrics"
                ),
                "secondary_metrics": ParameterDef(
                    type="array", description="Secondary metrics"
                ),
                "launch": _opt_bool("Launch the experiment"),
                "conclude": _opt_str("'won' / 'lost' / 'inconclusive'"),
                "archive": _opt_bool("Archive the experiment"),
            },
        ),
        _crud_delete("delete_experiment", "Delete an experiment", "experiment_id"),
        ActionDefinition(
            name="get_experiment_results",
            description="Get experiment results (optionally force refresh)",
            parameters={
                "project_id": _project_id(),
                "experiment_id": _required_int("Experiment ID"),
                "base_url": _base_url(),
                "refresh": ParameterDef(
                    type="boolean",
                    description="Force refresh",
                    default=False,
                ),
            },
        ),
        # --- Feature flags -------------------------------------------------
        ActionDefinition(
            name="get_feature_flags",
            description="List feature flags",
            parameters={"project_id": _project_id(), "base_url": _base_url()},
        ),
        ActionDefinition(
            name="get_feature_flag",
            description="Get a flag definition (by id OR key)",
            parameters={
                "project_id": _project_id(),
                "flag_id": _opt_int("Feature flag ID"),
                "flag_key": _opt_str("Feature flag key"),
                "base_url": _base_url(),
            },
        ),
        ActionDefinition(
            name="create_feature_flag",
            description="Create a feature flag",
            parameters={
                "project_id": _project_id(),
                "key": _required_str("Flag key"),
                "name": _required_str("Flag name"),
                "base_url": _base_url(),
                "description": _opt_str("Description"),
                "filters": ParameterDef(type="object", description="Flag filters"),
                "active": ParameterDef(
                    type="boolean", description="Active", default=True
                ),
                "tags": ParameterDef(type="array", description="Tag list"),
            },
        ),
        ActionDefinition(
            name="update_feature_flag",
            description="Update a feature flag (addressed by key)",
            parameters={
                "project_id": _project_id(),
                "flag_key": _required_str("Flag key to update"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "description": _opt_str("New description"),
                "filters": ParameterDef(
                    type="object", description="Updated filters"
                ),
                "active": _opt_bool("Active state"),
                "tags": ParameterDef(type="array", description="Tag list"),
            },
        ),
        _crud_delete("delete_feature_flag", "Delete a feature flag", "flag_id"),
        # --- Insights ------------------------------------------------------
        _crud_get_all(
            "get_insights",
            "List insights",
            {"search": _opt_str("Search query")},
        ),
        _crud_get_one("get_insight", "Get an insight", "insight_id"),
        ActionDefinition(
            name="create_insight",
            description="Create an insight",
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Insight name"),
                "base_url": _base_url(),
                "description": _opt_str("Description"),
                "filters": ParameterDef(
                    type="object", description="Insight filter config"
                ),
                "query": ParameterDef(
                    type="object", description="HogQL/JSON query"
                ),
                "dashboards": ParameterDef(
                    type="array", description="Dashboard IDs to attach"
                ),
                "tags": ParameterDef(type="array", description="Tag list"),
            },
        ),
        ActionDefinition(
            name="update_insight",
            description="Update an insight",
            parameters={
                "project_id": _project_id(),
                "insight_id": _required_int("Insight ID"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "description": _opt_str("New description"),
                "filters": ParameterDef(type="object", description="Filter config"),
                "query": ParameterDef(type="object", description="Query"),
                "tags": ParameterDef(type="array", description="Tag list"),
            },
        ),
        _crud_delete("delete_insight", "Delete an insight", "insight_id"),
        # --- Query ---------------------------------------------------------
        ActionDefinition(
            name="run_query",
            description="Run an ad-hoc HogQL/JSON query",
            parameters={
                "project_id": _project_id(),
                "query": ParameterDef(
                    type="object", description="Query body", required=True
                ),
                "base_url": _base_url(),
            },
        ),
        # --- Error tracking ------------------------------------------------
        _crud_get_all(
            "list_error_tracking_issues",
            "List error tracking issues",
            {
                "search": _opt_str("Search query"),
                "status": _opt_str("Filter by status"),
            },
        ),
        _crud_get_one(
            "get_error_tracking_issue",
            "Get an error tracking issue",
            "issue_id",
            "string",
        ),
        # --- Surveys -------------------------------------------------------
        _crud_get_all(
            "get_surveys",
            "List surveys",
            {"search": _opt_str("Search query")},
        ),
        _crud_get_one("get_survey", "Get a survey", "survey_id", "string"),
        ActionDefinition(
            name="create_survey",
            description="Create a survey",
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Survey name"),
                "type": ParameterDef(
                    type="string",
                    description="'popover' / 'widget' / 'api'",
                    default="popover",
                ),
                "base_url": _base_url(),
                "description": _opt_str("Description"),
                "questions": ParameterDef(
                    type="array", description="Survey questions"
                ),
                "conditions": ParameterDef(
                    type="object", description="Trigger conditions"
                ),
                "linked_flag_id": _opt_int("Linked feature flag ID"),
                "targeting_flag_filters": ParameterDef(
                    type="object", description="Targeting filters"
                ),
                "appearance": ParameterDef(
                    type="object", description="Survey appearance config"
                ),
                "start_date": _opt_str("Start date"),
                "end_date": _opt_str("End date"),
            },
        ),
        ActionDefinition(
            name="update_survey",
            description="Update a survey",
            parameters={
                "project_id": _project_id(),
                "survey_id": _required_str("Survey ID"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "description": _opt_str("New description"),
                "questions": ParameterDef(
                    type="array", description="Questions"
                ),
                "conditions": ParameterDef(
                    type="object", description="Trigger conditions"
                ),
                "archived": _opt_bool("Archive the survey"),
                "start_date": _opt_str("Start date"),
                "end_date": _opt_str("End date"),
            },
        ),
        _crud_delete("delete_survey", "Delete a survey", "survey_id", "string"),
        # --- Org + projects ------------------------------------------------
        ActionDefinition(
            name="get_organizations",
            description="List organizations the user belongs to",
            parameters={"base_url": _base_url()},
        ),
        ActionDefinition(
            name="get_projects",
            description="List projects in an organization",
            parameters={
                "organization_id": _opt_str("Organization ID"),
                "base_url": _base_url(),
            },
        ),
        # --- Definitions ---------------------------------------------------
        _crud_get_all(
            "get_event_definitions",
            "List event definitions",
            {"search": _opt_str("Search query")},
        ),
        _crud_get_all(
            "get_property_definitions",
            "List property definitions",
            {
                "search": _opt_str("Search query"),
                "event_names": ParameterDef(
                    type="array", description="Filter by event names"
                ),
                "type": _opt_str("Filter by property type"),
            },
        ),
        # --- Capture / identify (ingest API) -------------------------------
        ActionDefinition(
            name="capture_event",
            description="Capture a single event (ingest API)",
            parameters={
                "project_api_key": _project_api_key(),
                "distinct_id": _required_str("Distinct user ID"),
                "event": _required_str("Event name"),
                "properties": ParameterDef(
                    type="object", description="Event properties"
                ),
                "timestamp": _opt_str("ISO 8601 timestamp"),
                "ingest_url": _ingest_url(),
            },
        ),
        ActionDefinition(
            name="batch_capture_events",
            description="Capture multiple events in one batch request",
            parameters={
                "project_api_key": _project_api_key(),
                "events": ParameterDef(
                    type="array",
                    description="List of event objects",
                    required=True,
                ),
                "historical_migration": ParameterDef(
                    type="boolean",
                    description="Flag historical imports",
                    default=False,
                ),
                "ingest_url": _ingest_url(),
            },
        ),
        ActionDefinition(
            name="identify_user",
            description="Set / update properties on a person via $identify event",
            parameters={
                "project_api_key": _project_api_key(),
                "distinct_id": _required_str("Distinct user ID"),
                "properties": ParameterDef(
                    type="object",
                    description="Properties to set",
                    required=True,
                ),
                "ingest_url": _ingest_url(),
            },
        ),
        ActionDefinition(
            name="alias_user",
            description="Create an alias between two distinct IDs (merge users)",
            parameters={
                "project_api_key": _project_api_key(),
                "distinct_id": _required_str("Canonical distinct ID"),
                "alias": _required_str("Alias distinct ID to merge in"),
                "ingest_url": _ingest_url(),
            },
        ),
        ActionDefinition(
            name="evaluate_feature_flags",
            description=(
                "Evaluate all feature flags for a user (server-side flag "
                "evaluation via /flags?v=2)"
            ),
            parameters={
                "project_api_key": _project_api_key(),
                "distinct_id": _required_str("Distinct user ID"),
                "groups": ParameterDef(
                    type="object", description="Group memberships"
                ),
                "person_properties": ParameterDef(
                    type="object", description="Person properties"
                ),
                "group_properties": ParameterDef(
                    type="object", description="Group properties"
                ),
                "ingest_url": _ingest_url(),
            },
        ),
        ActionDefinition(
            name="group_identify",
            description="Identify a group (B2B analytics — org/company/etc.)",
            parameters={
                "project_api_key": _project_api_key(),
                "group_type": _required_str("Group type (e.g. 'company')"),
                "group_key": _required_str("Group key (the unique ID)"),
                "properties": ParameterDef(
                    type="object",
                    description="Properties to set on the group",
                    required=True,
                ),
                "ingest_url": _ingest_url(),
            },
        ),
        # --- Persons -------------------------------------------------------
        _crud_get_all(
            "get_persons",
            "List persons",
            {
                "search": _opt_str("Search query"),
                "distinct_id": _opt_str("Filter by distinct ID"),
                "email": _opt_str("Filter by email"),
            },
        ),
        _crud_get_one("get_person", "Get a person by ID", "person_id", "string"),
        ActionDefinition(
            name="update_person",
            description="Update person properties (PATCH)",
            parameters={
                "project_id": _project_id(),
                "person_id": _required_int("Person ID"),
                "properties": ParameterDef(
                    type="object",
                    description="Properties to set",
                    required=True,
                ),
                "base_url": _base_url(),
            },
        ),
        ActionDefinition(
            name="delete_person",
            description="Delete a person (optionally with associated events)",
            parameters={
                "project_id": _project_id(),
                "person_id": _required_int("Person ID"),
                "delete_events": ParameterDef(
                    type="boolean",
                    description="Also delete events (GDPR)",
                    default=False,
                ),
                "base_url": _base_url(),
            },
        ),
        ActionDefinition(
            name="bulk_delete_persons",
            description="Delete multiple persons in one call",
            parameters={
                "project_id": _project_id(),
                "person_ids": ParameterDef(
                    type="array",
                    description="Person IDs to delete",
                    required=True,
                ),
                "delete_events": ParameterDef(
                    type="boolean", description="Also delete events", default=False
                ),
                "base_url": _base_url(),
            },
        ),
        # --- Groups --------------------------------------------------------
        ActionDefinition(
            name="get_groups",
            description="List groups of a specific group type",
            parameters={
                "project_id": _project_id(),
                "group_type_index": _required_int("Group type index (0-4)"),
                "base_url": _base_url(),
                "search": _opt_str("Search query"),
            },
        ),
        ActionDefinition(
            name="find_group",
            description="Find a specific group by type + key",
            parameters={
                "project_id": _project_id(),
                "group_type_index": _required_int("Group type index"),
                "group_key": _required_str("Group key"),
                "base_url": _base_url(),
            },
        ),
        ActionDefinition(
            name="get_group_types",
            description="List configured group types for the project",
            parameters={
                "project_id": _project_id(),
                "base_url": _base_url(),
            },
        ),
        # --- Cohorts -------------------------------------------------------
        ActionDefinition(
            name="get_cohorts",
            description="List cohorts",
            parameters={"project_id": _project_id(), "base_url": _base_url()},
        ),
        _crud_get_one("get_cohort", "Get a cohort", "cohort_id"),
        ActionDefinition(
            name="create_cohort",
            description="Create a static or dynamic cohort",
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Cohort name"),
                "base_url": _base_url(),
                "description": _opt_str("Description"),
                "is_static": ParameterDef(
                    type="boolean", description="Static cohort", default=False
                ),
                "filters": ParameterDef(type="object", description="Filter config"),
                "groups": ParameterDef(type="array", description="Group filters"),
            },
        ),
        ActionDefinition(
            name="update_cohort",
            description="Update a cohort",
            parameters={
                "project_id": _project_id(),
                "cohort_id": _required_int("Cohort ID"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "description": _opt_str("New description"),
                "filters": ParameterDef(type="object", description="Filters"),
                "groups": ParameterDef(type="array", description="Groups"),
            },
        ),
        _crud_delete("delete_cohort", "Soft-delete a cohort", "cohort_id"),
        ActionDefinition(
            name="get_cohort_persons",
            description="List persons in a cohort",
            parameters={
                "project_id": _project_id(),
                "cohort_id": _required_int("Cohort ID"),
                "base_url": _base_url(),
                "limit": _limit(),
            },
        ),
        # --- Session recordings --------------------------------------------
        _crud_get_all(
            "get_session_recordings",
            "List session recordings (metadata only)",
        ),
        _crud_get_one(
            "get_session_recording",
            "Get one session recording",
            "recording_id",
            "string",
        ),
        _crud_delete(
            "delete_session_recording",
            "Delete a session recording",
            "recording_id",
            "string",
        ),
        # --- Actions -------------------------------------------------------
        _crud_get_all(
            "get_actions",
            "List actions",
            {"search": _opt_str("Search query")},
        ),
        _crud_get_one("get_action", "Get an action", "action_id"),
        ActionDefinition(
            name="create_action",
            description="Create an action (composite event)",
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Action name"),
                "base_url": _base_url(),
                "description": _opt_str("Description"),
                "steps": ParameterDef(
                    type="array", description="Action steps (conditions)"
                ),
                "tags": ParameterDef(type="array", description="Tag list"),
            },
        ),
        ActionDefinition(
            name="update_action",
            description="Update an action",
            parameters={
                "project_id": _project_id(),
                "action_id": _required_int("Action ID"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "description": _opt_str("New description"),
                "steps": ParameterDef(type="array", description="Steps"),
                "tags": ParameterDef(type="array", description="Tag list"),
            },
        ),
        ActionDefinition(
            name="delete_action",
            description=(
                "Delete an action (tries soft-delete, falls back to rename "
                "if PostHog's soft-delete fails — legacy bug workaround)"
            ),
            parameters={
                "project_id": _project_id(),
                "action_id": _required_int("Action ID"),
                "base_url": _base_url(),
            },
        ),
        ActionDefinition(
            name="delete_action_by_name",
            description=(
                "Search + delete an action by name (DELETE → soft-delete "
                "→ rename fallback chain)"
            ),
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Action name to find + delete"),
                "base_url": _base_url(),
            },
        ),
        # --- Annotations ---------------------------------------------------
        _crud_get_all(
            "get_annotations",
            "List annotations",
            {"search": _opt_str("Search query")},
        ),
        _crud_get_one("get_annotation", "Get an annotation", "annotation_id"),
        ActionDefinition(
            name="create_annotation",
            description="Create an annotation (a note at a point in time)",
            parameters={
                "project_id": _project_id(),
                "content": _required_str("Annotation text"),
                "date_marker": _required_str("Date marker (ISO 8601)"),
                "base_url": _base_url(),
                "dashboard_item": _opt_int("Linked insight (dashboard item)"),
                "scope": ParameterDef(
                    type="string",
                    description="'dashboard_item' / 'project' / 'organization'",
                    default="organization",
                ),
            },
        ),
        ActionDefinition(
            name="update_annotation",
            description="Update an annotation",
            parameters={
                "project_id": _project_id(),
                "annotation_id": _required_int("Annotation ID"),
                "base_url": _base_url(),
                "content": _opt_str("New content"),
                "date_marker": _opt_str("New date marker"),
                "scope": _opt_str("New scope"),
            },
        ),
        _crud_delete("delete_annotation", "Delete an annotation", "annotation_id"),
        # --- Alerts --------------------------------------------------------
        _crud_get_all(
            "get_alerts",
            "List alerts",
            {"insight_id": _opt_int("Filter by insight ID")},
        ),
        _crud_get_one("get_alert", "Get an alert", "alert_id", "string"),
        ActionDefinition(
            name="create_alert",
            description="Create an alert on an insight",
            parameters={
                "project_id": _project_id(),
                "insight_id": _required_int("Insight ID"),
                "name": _required_str("Alert name"),
                "base_url": _base_url(),
                "threshold": ParameterDef(
                    type="object", description="Threshold config"
                ),
                "subscribed_users": ParameterDef(
                    type="array", description="User IDs to notify"
                ),
                "enabled": ParameterDef(
                    type="boolean", description="Enabled", default=True
                ),
                "notification_targets": ParameterDef(
                    type="object", description="Notification target config"
                ),
            },
        ),
        ActionDefinition(
            name="update_alert",
            description="Update an alert",
            parameters={
                "project_id": _project_id(),
                "alert_id": _required_str("Alert ID"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "threshold": ParameterDef(
                    type="object", description="Threshold config"
                ),
                "subscribed_users": ParameterDef(
                    type="array", description="User IDs"
                ),
                "enabled": _opt_bool("Enabled state"),
                "notification_targets": ParameterDef(
                    type="object", description="Notification targets"
                ),
            },
        ),
        _crud_delete("delete_alert", "Delete an alert", "alert_id", "string"),
        # --- Early access features ----------------------------------------
        _crud_get_all(
            "get_early_access_features",
            "List early-access features",
        ),
        _crud_get_one(
            "get_early_access_feature",
            "Get an early-access feature",
            "feature_id",
            "string",
        ),
        ActionDefinition(
            name="create_early_access_feature",
            description="Create an early-access feature",
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Feature name"),
                "base_url": _base_url(),
                "description": _opt_str("Description"),
                "stage": ParameterDef(
                    type="string",
                    description="draft / beta / general-availability / archived",
                    default="beta",
                ),
                "documentation_url": _opt_str("Documentation URL"),
                "feature_flag_id": _opt_int("Linked feature flag ID"),
            },
        ),
        ActionDefinition(
            name="update_early_access_feature",
            description="Update an early-access feature",
            parameters={
                "project_id": _project_id(),
                "feature_id": _required_str("Feature ID"),
                "base_url": _base_url(),
                "name": _opt_str("New name"),
                "description": _opt_str("New description"),
                "stage": _opt_str("Updated stage"),
                "documentation_url": _opt_str("Updated documentation URL"),
            },
        ),
        _crud_delete(
            "delete_early_access_feature",
            "Delete an early-access feature",
            "feature_id",
            "string",
        ),
        ActionDefinition(
            name="delete_early_access_feature_by_name",
            description="Search + delete an early-access feature by name",
            parameters={
                "project_id": _project_id(),
                "name": _required_str("Feature name to find + delete"),
                "base_url": _base_url(),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="PostHog API Key Authentication",
            description=(
                "Connect to PostHog using your personal API key, project "
                "ID, and instance URL."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="POSTHOG_API_KEY",
                    display_name="Personal API Key",
                    description="Your PostHog personal API key",
                    required=True,
                    sensitive=True,
                    sample_format="phx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url=(
                        "https://posthog.com/docs/api/overview#personal-api-keys"
                    ),
                ),
                EnvVar(
                    name="POSTHOG_PROJECT_ID",
                    display_name="Project ID",
                    description="PostHog project ID (found in project settings)",
                    required=True,
                    sensitive=False,
                    sample_format="12345",
                ),
                EnvVar(
                    name="POSTHOG_BASE_URL",
                    display_name="Instance URL",
                    description=(
                        "PostHog instance URL (https://app.posthog.com for "
                        "cloud, or your self-hosted URL)"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="https://app.posthog.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://app.posthog.com/api/projects/",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Accept": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["results"]
                ),
                cost_level="free",
                description="Validates API key by listing projects",
            ),
        ),
    ],
)
