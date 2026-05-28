"""Datadog integration manifest."""
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
    name="datadog",
    display_name="Datadog",
    description="Infrastructure monitoring, log management, and application performance platform",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:datadog-themed",
    app_url="https://www.datadoghq.com",
    categories=["Monitoring & Observability", "Developer Tools & Infrastructure"],
    actions=[
        ActionDefinition(
            name="get_account_info",
            description="Detect the Datadog region for the connected account by validating the API key across all regions",
            parameters={},
        ),
        ActionDefinition(
            name="get_metric_data",
            description="Query time-series metric data for analyzing trends and system performance",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Metric query string (e.g. avg:system.cpu.user{*} or sum:my.metric{env:prod} by {host})",
                    required=True,
                ),
                "from_ts": ParameterDef(
                    type="integer",
                    description="Start of the query window as POSIX timestamp in seconds",
                    required=True,
                ),
                "to_ts": ParameterDef(
                    type="integer",
                    description="End of the query window as POSIX timestamp in seconds",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="post_metric_data",
            description="Post custom time-series metric data points to Datadog",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "metric": ParameterDef(
                    type="string",
                    description="The name of the timeseries metric",
                    required=True,
                ),
                "points": ParameterDef(
                    type="object",
                    description="Points as a JSON object where keys are Unix timestamps (seconds) and values are numeric (e.g. {\"1640995200\": 1.0})",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_dashboards",
            description="List and search Datadog dashboards with their IDs, titles, and URLs",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "filter_shared": ParameterDef(
                    type="boolean",
                    description="If true, only return dashboards that are shared",
                ),
                "count": ParameterDef(
                    type="integer",
                    description="Maximum number of dashboards to return",
                ),
                "start": ParameterDef(
                    type="integer",
                    description="Offset for pagination",
                ),
            },
        ),
        ActionDefinition(
            name="search_events",
            description="Search Datadog events including monitor state changes, deployment markers, and error spikes",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "start": ParameterDef(
                    type="integer",
                    description="POSIX timestamp (seconds) for the start of the query window; defaults to 24 hours ago",
                ),
                "end": ParameterDef(
                    type="integer",
                    description="POSIX timestamp (seconds) for the end of the query window; defaults to now",
                ),
                "priority": ParameterDef(
                    type="string",
                    description="Filter by event priority: normal or low",
                ),
                "sources": ParameterDef(
                    type="string",
                    description="Comma-separated list of sources to filter events (e.g. nagios,hudson)",
                ),
                "tags": ParameterDef(
                    type="string",
                    description="Comma-separated list of tags to filter events (e.g. env:prod,role:db)",
                ),
            },
        ),
        ActionDefinition(
            name="search_hosts",
            description="Search monitored infrastructure hosts with filtering by tag, name, or partial match",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "filter": ParameterDef(
                    type="string",
                    description="Filter hosts by name, alias, or tag (e.g. env:production or host:web-01)",
                ),
                "sort_field": ParameterDef(
                    type="string",
                    description="Field to sort hosts by: status, apps, cpu, iowait, or load",
                ),
                "sort_dir": ParameterDef(
                    type="string",
                    description="Direction of sort: asc or desc",
                ),
                "count": ParameterDef(
                    type="integer",
                    description="Number of hosts to return (max 1000)",
                ),
            },
        ),
        ActionDefinition(
            name="search_incidents",
            description="Search Datadog incidents by state, severity, and metadata",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Search query to filter incidents using field:value syntax (e.g. state:active or severity:SEV-1)",
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of incidents per page (default 10)",
                ),
                "page_offset": ParameterDef(
                    type="integer",
                    description="Offset for pagination",
                ),
            },
        ),
        ActionDefinition(
            name="search_logs",
            description="Search Datadog logs matching a query with support for facets and time ranges",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Search query following log search syntax (e.g. service:web-app status:error)",
                    required=True,
                    default="*",
                ),
                "from_time": ParameterDef(
                    type="string",
                    description="Minimum timestamp for logs; supports date math (now-15m), ISO-8601, or epoch ms; defaults to 15 minutes ago",
                ),
                "to_time": ParameterDef(
                    type="string",
                    description="Maximum timestamp for logs; supports date math (now), ISO-8601, or epoch ms; defaults to now",
                ),
                "indexes": ParameterDef(
                    type="array",
                    description="List of log index names to search (defaults to all indexes); element type: string",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of logs to return per page (default 10, max 1000)",
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Sort order for results: -timestamp (newest first) or timestamp (oldest first)",
                ),
            },
        ),
        ActionDefinition(
            name="search_metrics",
            description="List available Datadog metric names, optionally filtered by host",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "host": ParameterDef(
                    type="string",
                    description="Filter metrics by host name",
                ),
            },
        ),
        ActionDefinition(
            name="search_monitors",
            description="Search Datadog monitors (alerting rules) including status, thresholds, and conditions",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Filter monitors by name, tag, or other attributes (e.g. tag:env:production or type:metric)",
                ),
                "tags": ParameterDef(
                    type="string",
                    description="Comma-separated list of tags to filter monitors (e.g. env:prod,team:backend)",
                ),
                "page": ParameterDef(
                    type="integer",
                    description="Page number to return (0-indexed)",
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of monitors per page (default 100)",
                ),
            },
        ),
        ActionDefinition(
            name="search_services",
            description="List services from Datadog Service Catalog with ownership, metadata, and team info",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="The regional site for the Datadog account (e.g. datadoghq.com, us3.datadoghq.com, us5.datadoghq.com, datadoghq.eu, ddog-gov.com)",
                    required=True,
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of services per page (default 10)",
                ),
                "page_number": ParameterDef(
                    type="integer",
                    description="Page number (0-indexed)",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Datadog API Keys",
            description="Authenticate using your Datadog API key and Application key",
            setup_instructions=[
                "Go to https://app.datadoghq.com/organization-settings/api-keys and sign in",
                "Copy or create a new API key",
                "Go to https://app.datadoghq.com/organization-settings/application-keys",
                "Copy or create a new Application key",
                "Paste both keys below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="DATADOG_API_KEY",
                    display_name="API Key",
                    description="Your Datadog API key from Organization Settings > API Keys",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.datadoghq.com/organization-settings/api-keys",
                ),
                EnvVar(
                    name="DATADOG_APPLICATION_KEY",
                    display_name="Application Key",
                    description="Your Datadog Application key from Organization Settings > Application Keys",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.datadoghq.com/organization-settings/application-keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.datadoghq.com/api/v1/validate",
                method="GET",
                headers={"DD-API-KEY": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["valid"],
                ),
                cost_level="free",
                description="Validates the API key against the US1 region",
            ),
        ),
    ],
)
