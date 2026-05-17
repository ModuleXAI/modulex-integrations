"""Snowflake integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


def _table_name_param() -> ParameterDef:
    return ParameterDef(
        type="string",
        description=(
            "Fully qualified table (DATABASE.SCHEMA.TABLE) — or just TABLE "
            "if database/schema is set in auth_data"
        ),
        required=True,
    )


manifest = IntegrationManifest(
    name="snowflake",
    display_name="Snowflake",
    description=(
        "Snowflake data warehouse integration for executing SQL queries, "
        "managing tables, and performing data operations. Uses the "
        "snowflake-connector-python SDK."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:snowflake-icon",
    app_url="https://www.snowflake.com/",
    categories=["Database", "Data Warehouse", "analytics"],
    actions=[
        ActionDefinition(
            name="execute_sql_query",
            description=(
                "Execute any SQL statement. Use '%s' for parameterized "
                "queries (DB-API style)."
            ),
            parameters={
                "query": ParameterDef(
                    type="string", description="The SQL to execute", required=True
                ),
                "binds": ParameterDef(
                    type="array", description="Bind values for '%s' placeholders"
                ),
            },
        ),
        ActionDefinition(
            name="insert_row",
            description="INSERT a single row from a column→value mapping",
            parameters={
                "table_name": _table_name_param(),
                "values": ParameterDef(
                    type="object",
                    description="Column-value pairs to insert",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="insert_multiple_rows",
            description="Batched INSERT for multiple rows (configurable batch_size)",
            parameters={
                "table_name": _table_name_param(),
                "columns": ParameterDef(
                    type="array",
                    description="Column names",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description="List of rows, each a list of values matching columns",
                    required=True,
                ),
                "batch_size": ParameterDef(
                    type="integer",
                    description="Rows per batch (clamped to 10-1000)",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_databases",
            description="SHOW DATABASES — all accessible databases",
            parameters={},
        ),
        ActionDefinition(
            name="list_schemas",
            description="SHOW SCHEMAS IN DATABASE <database>",
            parameters={
                "database": ParameterDef(
                    type="string",
                    description="Database name",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_tables",
            description="SHOW TABLES IN SCHEMA <database>.<schema>",
            parameters={
                "database": ParameterDef(
                    type="string", description="Database name", required=True
                ),
                "schema_name": ParameterDef(
                    type="string", description="Schema name", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_warehouses",
            description="SHOW WAREHOUSES — compute resources",
            parameters={},
        ),
        ActionDefinition(
            name="describe_table",
            description="DESCRIBE TABLE — column metadata",
            parameters={"table_name": _table_name_param()},
        ),
        ActionDefinition(
            name="get_table_sample",
            description="SELECT * FROM table LIMIT N — preview data",
            parameters={
                "table_name": _table_name_param(),
                "limit": ParameterDef(
                    type="integer",
                    description="Rows to sample (clamped 1-1000)",
                    default=10,
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Snowflake Credentials",
            description=(
                "Authenticate with Snowflake account credentials "
                "(account/user/password/warehouse)."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="SNOWFLAKE_ACCOUNT",
                    display_name="Account",
                    description=(
                        "Snowflake account identifier "
                        "(e.g. xy12345.us-east-1)"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="xy12345.us-east-1",
                ),
                EnvVar(
                    name="SNOWFLAKE_USER",
                    display_name="Username",
                    description="Snowflake username",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="SNOWFLAKE_PASSWORD",
                    display_name="Password",
                    description="Snowflake password",
                    required=True,
                    sensitive=True,
                ),
                EnvVar(
                    name="SNOWFLAKE_WAREHOUSE",
                    display_name="Warehouse",
                    description="Compute warehouse to use for queries",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="SNOWFLAKE_DATABASE",
                    display_name="Database",
                    description="Default database (optional)",
                    required=False,
                    sensitive=False,
                ),
                EnvVar(
                    name="SNOWFLAKE_SCHEMA",
                    display_name="Schema",
                    description="Default schema (optional)",
                    required=False,
                    sensitive=False,
                ),
                EnvVar(
                    name="SNOWFLAKE_ROLE",
                    display_name="Role",
                    description="Optional Snowflake role to assume",
                    required=False,
                    sensitive=False,
                ),
            ],
        ),
    ],
)
