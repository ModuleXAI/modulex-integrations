"""Microsoft Power BI integration manifest."""
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
    name="microsoft_power_bi",
    display_name="Microsoft Power BI",
    description="Business intelligence and analytics platform for interactive visualizations, reports, and dashboards",
    version="1.0.0",
    author="ModuleX",
    logo="logos:microsoft-power-bi",
    app_url="https://powerbi.microsoft.com",
    categories=["Business Intelligence", "Analytics", "Productivity"],
    actions=[
        ActionDefinition(
            name="add_rows_to_push_dataset",
            description="Append rows to a table in a Power BI Push Dataset",
            parameters={
                "dataset_id": ParameterDef(
                    type="string",
                    description="ID of the Push Dataset (use list_datasets to find IDs)",
                    required=True,
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Exact case-sensitive name of the table within the dataset",
                    required=True,
                ),
                "rows": ParameterDef(
                    type="string",
                    description="JSON array of row objects matching the table column schema",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the workspace (omit for My workspace)",
                ),
            },
        ),
        ActionDefinition(
            name="execute_dax_query",
            description="Execute a DAX query against a Power BI dataset",
            parameters={
                "dataset_id": ParameterDef(
                    type="string",
                    description="ID of the dataset to query (use list_datasets to find IDs)",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="DAX expression starting with EVALUATE",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the workspace (omit for My workspace)",
                ),
                "include_nulls": ParameterDef(
                    type="boolean",
                    description="Whether to include null values in the response",
                    default=True,
                ),
                "impersonated_user_name": ParameterDef(
                    type="string",
                    description="UPN of an effective identity for Row-Level Security",
                ),
            },
        ),
        ActionDefinition(
            name="export_report",
            description="Export a Power BI report to PDF, PPTX, PNG, or other file format (Premium only)",
            parameters={
                "report_id": ParameterDef(
                    type="string",
                    description="ID of the report to export (use list_reports to find IDs)",
                    required=True,
                ),
                "format": ParameterDef(
                    type="string",
                    description="Output format: PDF, PPTX, PNG, CSV, XLSX, DOCX, XML, MHTML",
                    default="PDF",
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the workspace (omit for My workspace)",
                ),
                "poll_interval_seconds": ParameterDef(
                    type="integer",
                    description="Seconds between export status polls",
                    default=5,
                ),
                "poll_timeout_seconds": ParameterDef(
                    type="integer",
                    description="Maximum seconds to wait for export completion",
                    default=300,
                ),
            },
        ),
        ActionDefinition(
            name="get_refresh_history",
            description="Get the refresh history for a Power BI dataset",
            parameters={
                "dataset_id": ParameterDef(
                    type="string",
                    description="ID of the dataset (use list_datasets to find IDs)",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the workspace (omit for My workspace)",
                ),
                "top": ParameterDef(
                    type="integer",
                    description="Number of most recent refresh entries to return (max 200)",
                ),
            },
        ),
        ActionDefinition(
            name="get_reports_by_id",
            description="Retrieve metadata for a single Power BI report by ID",
            parameters={
                "report_id": ParameterDef(
                    type="string",
                    description="Power BI report ID (GUID)",
                    required=True,
                ),
                "group_id": ParameterDef(
                    type="string",
                    description="Workspace group ID (omit for My workspace)",
                ),
            },
        ),
        ActionDefinition(
            name="list_dashboards",
            description="List Power BI dashboards in a workspace",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the workspace (omit for My workspace)",
                ),
            },
        ),
        ActionDefinition(
            name="list_datasets",
            description="List Power BI datasets (semantic models) in a workspace",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the workspace (omit for My workspace)",
                ),
            },
        ),
        ActionDefinition(
            name="list_reports",
            description="List Power BI reports in a workspace",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the workspace (omit for My workspace)",
                ),
            },
        ),
        ActionDefinition(
            name="list_workspaces",
            description="List Power BI workspaces accessible to the authenticated user",
            parameters={},
        ),
        ActionDefinition(
            name="refresh_dataset",
            description="Trigger a refresh of a Power BI dataset",
            parameters={
                "dataset_id": ParameterDef(
                    type="string",
                    description="ID of the dataset to refresh (use list_datasets to find IDs)",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the workspace (omit for My workspace)",
                ),
                "notify_option": ParameterDef(
                    type="string",
                    description="Email notification behavior: NoNotification, MailOnCompletion, MailOnFailure",
                    default="NoNotification",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 (Microsoft Entra ID)",
            description="Connect using Microsoft OAuth2 (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="MICROSOFT_POWER_BI_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Microsoft Entra ID App Registration Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
                EnvVar(
                    name="MICROSOFT_POWER_BI_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Microsoft Entra ID App Registration Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=["https://analysis.windows.net/powerbi/api/.default", "offline_access"],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.powerbi.com/v1.0/myorg/groups",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["value"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing workspaces",
            ),
        ),
    ],
)
