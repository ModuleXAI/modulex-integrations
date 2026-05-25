"""Supabase integration manifest."""
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
    name="supabase",
    display_name="Supabase",
    description="Open-source Firebase alternative providing a Postgres database, authentication, instant APIs, and realtime subscriptions",
    version="1.0.0",
    author="ModuleX",
    logo="logos:supabase-icon",
    app_url="https://supabase.com",
    categories=["Database", "Backend", "Developer Tools & Infrastructure"],
    actions=[
        ActionDefinition(
            name="select_row",
            description="Select row(s) from a Supabase database table with optional filtering and ordering",
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the table to query",
                    required=True,
                ),
                "column": ParameterDef(
                    type="string",
                    description="Column name to filter by (required if filter and value are provided)",
                ),
                "filter": ParameterDef(
                    type="string",
                    description="Filter operator: eq, neq, gt, gte, lt, lte, like, ilike",
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value to filter the column by",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Column name to order results by",
                    required=True,
                ),
                "sort_order": ParameterDef(
                    type="string",
                    description="Sort direction: ascending or descending",
                    default="ascending",
                ),
                "max": ParameterDef(
                    type="integer",
                    description="Maximum number of rows to return",
                    default=20,
                ),
            },
        ),
        ActionDefinition(
            name="insert_row",
            description="Insert a new row into a Supabase database table",
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the table to insert into",
                    required=True,
                ),
                "data": ParameterDef(
                    type="object",
                    description="Column names and values as key/value pairs for the new row",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_row",
            description="Update row(s) in a Supabase database table matching a column value",
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the table to update",
                    required=True,
                ),
                "column": ParameterDef(
                    type="string",
                    description="Column name to match rows for update",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value to match in the specified column",
                    required=True,
                ),
                "data": ParameterDef(
                    type="object",
                    description="Column names and new values as key/value pairs",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="upsert_row",
            description="Insert a row or update it if it already exists in a Supabase database table",
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the table to upsert into",
                    required=True,
                ),
                "data": ParameterDef(
                    type="object",
                    description="Column names and values as key/value pairs",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_row",
            description="Delete row(s) from a Supabase database table matching a column value",
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the table to delete from",
                    required=True,
                ),
                "column": ParameterDef(
                    type="string",
                    description="Column name to match rows for deletion",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value to match in the specified column",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="batch_insert_rows",
            description="Insert multiple rows into a Supabase database table at once",
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the table to insert rows into",
                    required=True,
                ),
                "data": ParameterDef(
                    type="array",
                    description="Array of objects, each representing a row with column names and values as key/value pairs",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="remote_procedure_call",
            description="Call a Postgres function (RPC) in a Supabase database",
            parameters={
                "function_name": ParameterDef(
                    type="string",
                    description="Name of the Postgres function to call",
                    required=True,
                ),
                "args": ParameterDef(
                    type="object",
                    description="Arguments to pass to the function as key/value pairs",
                ),
            },
        ),
        ActionDefinition(
            name="count_rows",
            description="Count rows in a Supabase database table with optional filtering",
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the table to count rows from",
                    required=True,
                ),
                "column": ParameterDef(
                    type="string",
                    description="Column name to filter by (optional)",
                ),
                "filter": ParameterDef(
                    type="string",
                    description="Filter operator: eq, neq, gt, gte, lt, lte, like, ilike",
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value to filter the column by",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Supabase Service Key",
            description="Authenticate using your Supabase project subdomain and service role key",
            setup_instructions=[
                "Go to https://app.supabase.com and open your project",
                "Navigate to Project Settings > API",
                "Copy your Project URL subdomain (the part before .supabase.co)",
                "Copy the service_role key (NOT the anon key)",
                "Paste both values below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SUPABASE_SUBDOMAIN",
                    display_name="Project Subdomain",
                    description="Your Supabase project subdomain (the part before .supabase.co in your project URL)",
                    required=True,
                    sensitive=False,
                    sample_format="abcdefghijklmnopqrst",
                    about_url="https://app.supabase.com/project/_/settings/api",
                ),
                EnvVar(
                    name="SUPABASE_SERVICE_KEY",
                    display_name="Service Role Key",
                    description="Your Supabase service_role key from Project Settings > API",
                    required=True,
                    sensitive=True,
                    sample_format="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    about_url="https://app.supabase.com/project/_/settings/api",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://{SUPABASE_SUBDOMAIN}.supabase.co/rest/v1/",
                method="GET",
                headers={
                    "apikey": "{SUPABASE_SERVICE_KEY}",
                    "Authorization": "Bearer {SUPABASE_SERVICE_KEY}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates credentials by listing available tables via the PostgREST root endpoint",
            ),
        ),
    ],
)
