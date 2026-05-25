"""ServiceNow integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _table_query_params() -> dict[str, ParameterDef]:
    return {
        "api_version": ParameterDef(
            type="string",
            description="API version number ('v1', 'v2', or 'latest')",
        ),
        "display_value": ParameterDef(
            type="string",
            description="Return display values ('true'), actual values ('false'), or both ('all')",
            default="false",
        ),
        "exclude_reference_link": ParameterDef(
            type="boolean",
            description="Exclude Table API links for reference fields",
            default=False,
        ),
        "fields": ParameterDef(
            type="string",
            description="Comma-separated list of fields to return",
        ),
        "view": ParameterDef(
            type="string",
            description="Render the response according to the specified UI view",
        ),
    }


def _test_endpoint(placeholder: str, description: str) -> TestEndpoint:
    # {SERVICENOW_INSTANCE_NAME} uses the raw EnvVar name because the
    # modulex credential UI ships custom-field values keyed by EnvVar.name.
    return TestEndpoint(
        url="https://{SERVICENOW_INSTANCE_NAME}.service-now.com/api/now/table/sys_user?sysparm_limit=1",
        method="GET",
        headers={
            "Authorization": f"Bearer {{{placeholder}}}",
            "Content-Type": "application/json",
        },
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["result"]
        ),
        cost_level="minimal",
        description=description,
    )


manifest = IntegrationManifest(
    name="servicenow",
    display_name="ServiceNow",
    description=(
        "Enterprise IT Service Management (ITSM) platform for managing "
        "incidents, cases, and service requests. Create and manage "
        "incidents, cases, and perform CRUD operations on any ServiceNow "
        "table."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:servicenow",
    app_url="https://www.servicenow.com",
    categories=[
        "Developer Tools & Infrastructure",
        "automation",
        "development",
        "miscellaneous",
        "itsm",
        "servicenow",
    ],
    actions=[
        ActionDefinition(
            name="create_case",
            description=(
                "Create a new Case record in ServiceNow for customer service "
                "management"
            ),
            parameters={
                "description": ParameterDef(
                    type="string",
                    description="Detailed description of the issue",
                    required=True,
                ),
                "severity": ParameterDef(
                    type="string",
                    description=(
                        "Priority/severity: '1' Critical, '2' High, "
                        "'3' Moderate, '4' Low"
                    ),
                    required=True,
                ),
                "name": ParameterDef(
                    type="string", description="Short description of the case"
                ),
                "status": ParameterDef(
                    type="string",
                    description="Current status of the case",
                    default="New",
                ),
                "channel_name": ParameterDef(
                    type="string",
                    description="Channel (contact_type) the case came in through",
                ),
                "account_id": ParameterDef(
                    type="string",
                    description="Sys_id of the account related to the case",
                ),
                "contact_id": ParameterDef(
                    type="string",
                    description="Sys_id of the contact related to the case",
                ),
                "work_note": ParameterDef(
                    type="string", description="Internal work note for the case"
                ),
                "comment": ParameterDef(
                    type="string", description="Additional comment for the case"
                ),
            },
        ),
        ActionDefinition(
            name="create_incident",
            description="Create a new Incident record in ServiceNow for IT service management",
            parameters={
                "description": ParameterDef(
                    type="string",
                    description="Detailed description of the incident",
                    required=True,
                ),
                "severity": ParameterDef(
                    type="string",
                    description=(
                        "Priority/severity: '1' Critical, '2' High, "
                        "'3' Moderate, '4' Low, '5' Planning"
                    ),
                    required=True,
                ),
                "name": ParameterDef(
                    type="string", description="Short description of the incident"
                ),
                "status": ParameterDef(
                    type="string",
                    description="Current status of the incident",
                    default="New",
                ),
                "contact_method": ParameterDef(
                    type="string",
                    description="Name of the contact method (contact_type)",
                ),
                "company_id": ParameterDef(
                    type="string", description="Sys_id of the company"
                ),
                "user_id": ParameterDef(
                    type="string", description="Sys_id of the user"
                ),
                "work_note": ParameterDef(
                    type="string", description="Internal work note for the incident"
                ),
                "comment": ParameterDef(
                    type="string", description="Additional comment for the incident"
                ),
            },
        ),
        ActionDefinition(
            name="create_table_record",
            description="Insert a new record in any specified ServiceNow table",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Table to create the record in (e.g. 'incident', 'change_request')",
                    required=True,
                ),
                "table_record": ParameterDef(
                    type="object",
                    description="Record data — field name/value pairs",
                    required=True,
                ),
                **_table_query_params(),
                "input_display_value": ParameterDef(
                    type="boolean",
                    description="Treat input values as display values",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_table_record",
            description="Retrieve a specific record from a ServiceNow table by sys_id",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Table containing the record",
                    required=True,
                ),
                "sys_id": ParameterDef(
                    type="string",
                    description="Unique identifier (sys_id) of the record",
                    required=True,
                ),
                **_table_query_params(),
                "query_no_domain": ParameterDef(
                    type="boolean",
                    description="Access data across domains if authorized",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_table_records",
            description="Retrieve multiple records from a ServiceNow table with optional filtering",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Table containing the records",
                    required=True,
                ),
                **_table_query_params(),
                "query": ParameterDef(
                    type="string",
                    description="Encoded query string (e.g. 'active=true^priority=1')",
                ),
                "suppress_pagination_header": ParameterDef(
                    type="boolean", description="Suppress pagination header", default=False
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum results per page (default 10000)",
                ),
                "query_category": ParameterDef(
                    type="string",
                    description="Read-replica category for the query",
                ),
                "query_no_domain": ParameterDef(
                    type="boolean",
                    description="Access data across domains if authorized",
                    default=False,
                ),
                "no_count": ParameterDef(
                    type="boolean",
                    description="Skip select count(*) on the table",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="update_table_record",
            description="Update an existing record in a ServiceNow table",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Table containing the record",
                    required=True,
                ),
                "sys_id": ParameterDef(
                    type="string",
                    description="Sys_id of the record to update",
                    required=True,
                ),
                "update_fields": ParameterDef(
                    type="object",
                    description="Field name/value pairs to update",
                    required=True,
                ),
                **_table_query_params(),
                "input_display_value": ParameterDef(
                    type="boolean",
                    description="Treat input values as display values",
                    default=False,
                ),
                "query_no_domain": ParameterDef(
                    type="boolean",
                    description="Access data across domains if authorized",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_table_record",
            description="Delete a record from a ServiceNow table",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Table containing the record",
                    required=True,
                ),
                "sys_id": ParameterDef(
                    type="string",
                    description="Sys_id of the record to delete",
                    required=True,
                ),
                "api_version": ParameterDef(
                    type="string",
                    description="API version number ('v1', 'v2', or 'latest')",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth 2.0 (Connected App)",
            description=(
                "Authenticate using ServiceNow OAuth 2.0. Requires creating "
                "an OAuth API endpoint for external clients in your "
                "ServiceNow instance."
            ),
            oauth_config=OAuthConfig(
                auth_url="https://{instance_name}.service-now.com/oauth_auth.do",
                token_url="https://{instance_name}.service-now.com/oauth_token.do",
                scopes=["useraccount"],
                token_auth_method="body",
            ),
            setup_environment_variables=[
                EnvVar(
                    name="SERVICENOW_CLIENT_ID",
                    display_name="Client ID",
                    description="The Client ID from your ServiceNow OAuth application",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="SERVICENOW_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="The Client Secret from your ServiceNow OAuth application",
                    required=True,
                    sensitive=True,
                ),
                EnvVar(
                    name="SERVICENOW_INSTANCE_NAME",
                    display_name="Instance Name",
                    description=(
                        "Your ServiceNow instance name (e.g. 'dev12345' "
                        "from https://dev12345.service-now.com)"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="dev12345",
                ),
            ],
            # No test_endpoint for OAuth2: the test URL would need to
            # interpolate {SERVICENOW_INSTANCE_NAME} (tenant-specific),
            # but the modulex OAuth callback only stores OAuth tokens
            # in auth_data. The bearer_token schema below still gets a
            # working test because UI custom-fields ship the instance
            # name with the bearer_token credential. tools.py reads the
            # instance_name from auth_data at action call time for
            # both schemas.
            test_endpoint=None,
        ),
        BearerTokenAuthSchema(
            display_name="Access Token",
            description=(
                "Authenticate using a manually obtained ServiceNow access "
                "token. Useful for development and testing."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="SERVICENOW_ACCESS_TOKEN",
                    display_name="Access Token",
                    description="Your ServiceNow OAuth access token",
                    required=True,
                    sensitive=True,
                ),
                EnvVar(
                    name="SERVICENOW_INSTANCE_NAME",
                    display_name="Instance Name",
                    description="Your ServiceNow instance name",
                    required=True,
                    sensitive=False,
                    sample_format="dev12345",
                ),
            ],
            test_endpoint=_test_endpoint(
                "bearer_token",
                "Validates access token by retrieving a single user record",
            ),
        ),
    ],
)
