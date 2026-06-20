"""Amplitude integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BasicAuthSpec,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="amplitude",
    display_name="Amplitude",
    description=(
        "Track events, identify users and groups, search for users, query "
        "analytics, and retrieve revenue data from Amplitude"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:amplitude-themed",
    app_url="https://amplitude.com",
    categories=["Analytics & Data", "Product Analytics", "Marketing"],
    actions=[
        ActionDefinition(
            name="send_event",
            description="Track an event in Amplitude using the HTTP V2 API.",
            parameters={
                "event_type": ParameterDef(
                    type="string",
                    description='Name of the event (e.g., "page_view", "purchase").',
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="User ID (required if no device_id).",
                ),
                "device_id": ParameterDef(
                    type="string",
                    description="Device ID (required if no user_id).",
                ),
                "event_properties": ParameterDef(
                    type="object",
                    description="Custom event properties as a JSON object.",
                ),
                "user_properties": ParameterDef(
                    type="object",
                    description=(
                        "User properties to set (supports $set, $setOnce, $add, "
                        "$append, $unset)."
                    ),
                ),
                "time": ParameterDef(
                    type="integer",
                    description="Event timestamp in milliseconds since epoch.",
                ),
                "session_id": ParameterDef(
                    type="integer",
                    description=(
                        "Session start time in milliseconds since epoch "
                        "(-1 for no session)."
                    ),
                ),
                "insert_id": ParameterDef(
                    type="string",
                    description="Unique ID for deduplication (within a 7-day window).",
                ),
                "app_version": ParameterDef(
                    type="string",
                    description="Application version string.",
                ),
                "platform": ParameterDef(
                    type="string",
                    description='Platform (e.g., "Web", "iOS", "Android").',
                ),
                "country": ParameterDef(
                    type="string",
                    description="Two-letter country code.",
                ),
                "language": ParameterDef(
                    type="string",
                    description='Language code (e.g., "en").',
                ),
                "ip": ParameterDef(
                    type="string",
                    description='IP address for geo-location (use "$remote" for request IP).',
                ),
                "price": ParameterDef(
                    type="number",
                    description="Price of the item purchased.",
                ),
                "quantity": ParameterDef(
                    type="integer",
                    description="Quantity of items purchased.",
                ),
                "revenue": ParameterDef(
                    type="number",
                    description="Revenue amount.",
                ),
                "product_id": ParameterDef(
                    type="string",
                    description="Product identifier.",
                ),
                "revenue_type": ParameterDef(
                    type="string",
                    description='Revenue type (e.g., "purchase", "refund").',
                ),
            },
        ),
        ActionDefinition(
            name="identify_user",
            description=(
                "Set user properties in Amplitude using the Identify API. "
                "Supports $set, $setOnce, $add, $append, $unset operations."
            ),
            parameters={
                "user_properties": ParameterDef(
                    type="object",
                    description=(
                        "User properties to set. Use operations like $set, "
                        "$setOnce, $add, $append, $unset."
                    ),
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="User ID (required if no device_id).",
                ),
                "device_id": ParameterDef(
                    type="string",
                    description="Device ID (required if no user_id).",
                ),
            },
        ),
        ActionDefinition(
            name="group_identify",
            description=(
                "Set group-level properties in Amplitude. Supports $set, "
                "$setOnce, $add, $append, $unset operations."
            ),
            parameters={
                "group_type": ParameterDef(
                    type="string",
                    description='Group classification (e.g., "company", "org_id").',
                    required=True,
                ),
                "group_value": ParameterDef(
                    type="string",
                    description='Specific group identifier (e.g., "Acme Corp").',
                    required=True,
                ),
                "group_properties": ParameterDef(
                    type="object",
                    description=(
                        "Group properties as a JSON object. Use operations like "
                        "$set, $setOnce, $add, $append, $unset."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="user_search",
            description=(
                "Search for a user by User ID, Device ID, or Amplitude ID "
                "using the Dashboard REST API."
            ),
            parameters={
                "user": ParameterDef(
                    type="string",
                    description="User ID, Device ID, or Amplitude ID to search for.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="user_activity",
            description="Get the event stream for a specific user by their Amplitude ID.",
            parameters={
                "amplitude_id": ParameterDef(
                    type="string",
                    description="Amplitude internal user ID.",
                    required=True,
                ),
                "offset": ParameterDef(
                    type="integer",
                    description="Offset for pagination (default 0).",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of events to return (default 1000, max 1000).",
                ),
                "direction": ParameterDef(
                    type="string",
                    description='Sort direction: "latest" or "earliest" (default: latest).',
                ),
            },
        ),
        ActionDefinition(
            name="user_profile",
            description=(
                "Get a user profile including properties, cohort memberships, "
                "and computed properties."
            ),
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="External user ID (required if no device_id).",
                ),
                "device_id": ParameterDef(
                    type="string",
                    description="Device ID (required if no user_id).",
                ),
                "get_amp_props": ParameterDef(
                    type="boolean",
                    description="Include Amplitude user properties (default: false).",
                    default=False,
                ),
                "get_cohort_ids": ParameterDef(
                    type="boolean",
                    description="Include cohort IDs the user belongs to (default: false).",
                    default=False,
                ),
                "get_computations": ParameterDef(
                    type="boolean",
                    description="Include computed user properties (default: false).",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="event_segmentation",
            description=(
                "Query event analytics data with segmentation. Get event "
                "counts, uniques, averages, and more."
            ),
            parameters={
                "event_type": ParameterDef(
                    type="string",
                    description="Event type name to analyze.",
                    required=True,
                ),
                "start": ParameterDef(
                    type="string",
                    description="Start date in YYYYMMDD format.",
                    required=True,
                ),
                "end": ParameterDef(
                    type="string",
                    description="End date in YYYYMMDD format.",
                    required=True,
                ),
                "metric": ParameterDef(
                    type="string",
                    description=(
                        "Metric type: uniques, totals, pct_dau, average, "
                        "histogram, sums, value_avg, or formula (default: uniques)."
                    ),
                ),
                "interval": ParameterDef(
                    type="string",
                    description="Time interval: 1 (daily), 7 (weekly), or 30 (monthly).",
                ),
                "group_by": ParameterDef(
                    type="string",
                    description=(
                        "Property name to group by (prefix custom user "
                        'properties with "gp:").'
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of group-by values (max 1000).",
                ),
            },
        ),
        ActionDefinition(
            name="get_active_users",
            description=(
                "Get active or new user counts over a date range from the "
                "Dashboard REST API."
            ),
            parameters={
                "start": ParameterDef(
                    type="string",
                    description="Start date in YYYYMMDD format.",
                    required=True,
                ),
                "end": ParameterDef(
                    type="string",
                    description="End date in YYYYMMDD format.",
                    required=True,
                ),
                "metric": ParameterDef(
                    type="string",
                    description='Metric type: "active" or "new" (default: active).',
                ),
                "interval": ParameterDef(
                    type="string",
                    description="Time interval: 1 (daily), 7 (weekly), or 30 (monthly).",
                ),
            },
        ),
        ActionDefinition(
            name="realtime_active_users",
            description=(
                "Get real-time active user counts at 5-minute granularity for "
                "the last 2 days."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="list_events",
            description=(
                "List all event types in the project with their weekly totals "
                "and unique counts."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="get_revenue",
            description=(
                "Get revenue LTV data including ARPU, ARPPU, total revenue, "
                "and paying user counts."
            ),
            parameters={
                "start": ParameterDef(
                    type="string",
                    description="Start date in YYYYMMDD format.",
                    required=True,
                ),
                "end": ParameterDef(
                    type="string",
                    description="End date in YYYYMMDD format.",
                    required=True,
                ),
                "metric": ParameterDef(
                    type="string",
                    description="Metric: 0 (ARPU), 1 (ARPPU), 2 (Total Revenue), 3 (Paying Users).",
                ),
                "interval": ParameterDef(
                    type="string",
                    description="Time interval: 1 (daily), 7 (weekly), or 30 (monthly).",
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Amplitude API Key + Secret Key",
            description=(
                "Authenticate with your Amplitude project's API Key (used to send "
                "events and identify users) and Secret Key (required for the "
                "Dashboard REST API and User Profile analytics endpoints)."
            ),
            setup_instructions=[
                "Sign in to Amplitude and open the project you want to use.",
                "Go to Settings -> Projects -> (your project) -> General.",
                "Copy the 'API Key' and the 'Secret Key' shown for the project.",
                "Provide the API Key for event tracking; the Secret Key is also "
                "needed for analytics/dashboard queries.",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="AMPLITUDE_API_KEY",
                    display_name="API Key",
                    description=(
                        "Amplitude project API Key (used for event tracking and "
                        "Dashboard Basic auth)."
                    ),
                    required=True,
                    sensitive=False,
                    inject_into_auth_data=True,
                    about_url="https://amplitude.com/docs/apis/authentication",
                ),
                EnvVar(
                    name="AMPLITUDE_SECRET_KEY",
                    display_name="Secret Key",
                    description=(
                        "Amplitude project Secret Key (required for Dashboard "
                        "REST API and User Profile queries)."
                    ),
                    required=False,
                    sensitive=True,
                    inject_into_auth_data=True,
                    about_url="https://amplitude.com/docs/apis/authentication",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://amplitude.com/api/2/events/list",
                method="GET",
                # Amplitude Dashboard REST API uses HTTP Basic auth with the
                # project API Key as username and Secret Key as password. The
                # modulex runtime synthesises the
                # ``Authorization: Basic <base64(api_key:secret_key)>`` header
                # from these placeholders resolved against auth_data.
                auth=BasicAuthSpec(
                    username_placeholder="AMPLITUDE_API_KEY",
                    password_placeholder="AMPLITUDE_SECRET_KEY",
                ),
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description=(
                    "Validates the API Key + Secret Key by listing the "
                    "project's events via Basic Auth."
                ),
            ),
        ),
    ],
)
