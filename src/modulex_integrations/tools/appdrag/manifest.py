"""AppDrag integration manifest."""
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
    name="appdrag",
    display_name="AppDrag",
    description=(
        "Cloud-based development platform for managing cloud functions, "
        "databases, and backend services. Build and deploy web applications "
        "with serverless architecture."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:appdrag",
    app_url="https://appdrag.com",
    categories=["Developer Tools & Infrastructure", "automation", "database"],
    actions=[
        ActionDefinition(
            name="execute_api_function",
            description=(
                "Execute an API function from an AppDrag cloud backend. "
                "Calls custom API functions deployed on your AppDrag "
                "application."
            ),
            parameters={
                "path": ParameterDef(
                    type="string",
                    description=(
                        "Function name path to execute "
                        "(e.g. '/insert-user', '/get-data')"
                    ),
                    required=True,
                ),
                "method": ParameterDef(
                    type="string",
                    description="HTTP method (GET, POST, PUT, PATCH, DELETE)",
                    default="GET",
                ),
                "data": ParameterDef(
                    type="object",
                    description="Data to pass to the function as key/value pairs",
                ),
            },
        ),
        ActionDefinition(
            name="insert_row",
            description=(
                "Insert a new row into an AppDrag cloud database table. "
                "Executes an INSERT query with the specified columns and "
                "values."
            ),
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the database table to insert into",
                    required=True,
                ),
                "columns": ParameterDef(
                    type="array",
                    description="Column names to insert values into",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description="Values corresponding to each column",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_row",
            description=(
                "Update rows in an AppDrag cloud database table. Executes "
                "an UPDATE query with a WHERE condition to target specific "
                "rows."
            ),
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the database table to update",
                    required=True,
                ),
                "columns_to_update": ParameterDef(
                    type="array",
                    description="Column names to update",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description="New values for each column to update",
                    required=True,
                ),
                "where_condition": ParameterDef(
                    type="string",
                    description=(
                        "SQL WHERE condition with ? placeholders "
                        "(e.g. 'id = ?' or 'email = ? AND status = ?')"
                    ),
                    required=True,
                ),
                "where_values": ParameterDef(
                    type="array",
                    description="Values to replace ? placeholders in where_condition",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using your AppDrag API key and Application "
                "ID. Find these in your AppDrag project settings."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="APPDRAG_API_KEY",
                    display_name="AppDrag API Key",
                    description="Your AppDrag API key for authentication",
                    required=True,
                    sensitive=True,
                    about_url="https://support.appdrag.com/doc/Get-your-API-Key",
                ),
                EnvVar(
                    name="APPDRAG_APP_ID",
                    display_name="AppDrag Application ID",
                    description="Your AppDrag Application ID (found in project settings)",
                    required=True,
                    sensitive=False,
                    about_url="https://support.appdrag.com/doc/Get-your-API-Key",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.appdrag.com/CloudBackend.aspx",
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body={
                    "APIKey": "{api_key}",
                    "appID": "{APPDRAG_APP_ID}",
                    "command": "CloudDBGetDataset",
                    "query": "show tables",
                },
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="minimal",
                description="Validates API key and App ID by listing database tables",
            ),
        ),
    ],
)
