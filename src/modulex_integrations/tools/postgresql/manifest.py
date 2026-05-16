"""PostgreSQL integration manifest.

Database-connection auth: host/port/user/password/database. None of
our standard auth_types fit (this isn't a single API key or an OAuth
flow), so the integration uses ``CustomAuthSchema``. The tool body
reads connection parameters straight out of ``auth_data``.

Port defaults to 5432 at the tool layer (the manifest doesn't carry
defaults for ``EnvVar`` — that field doesn't exist in the schema).
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


def _table_param() -> ParameterDef:
    return ParameterDef(type="string", description="The table name", required=True)


def _schema_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="The schema name (default 'public')", default="public"
    )


def _condition_param() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="WHERE condition with '?' placeholders",
        required=True,
    )


def _values_param() -> ParameterDef:
    return ParameterDef(
        type="array",
        description="Values matching the '?' placeholders in the condition",
        required=True,
    )


manifest = IntegrationManifest(
    name="postgresql",
    display_name="PostgreSQL",
    description=(
        "PostgreSQL database integration for executing SQL queries, "
        "managing tables, and performing CRUD operations. Uses the "
        "asyncpg driver."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:postgresql",
    app_url="https://www.postgresql.org/",
    categories=["Database", "Data Management", "storage"],
    actions=[
        ActionDefinition(
            name="execute_raw_query",
            description=(
                "Execute a raw SQL statement (SELECT/INSERT/UPDATE/DELETE/DDL). "
                "Use $1, $2, ... placeholders for parameterized queries."
            ),
            parameters={
                "sql": ParameterDef(
                    type="string", description="The SQL to execute", required=True
                ),
                "values": ParameterDef(
                    type="array",
                    description="Values for $1, $2, ... placeholders",
                ),
            },
        ),
        ActionDefinition(
            name="create_row",
            description="INSERT a new row, returning the inserted record",
            parameters={
                "table": _table_param(),
                "data": ParameterDef(
                    type="object",
                    description="Column-value pairs to insert",
                    required=True,
                ),
                "schema_name": _schema_param(),
            },
        ),
        ActionDefinition(
            name="delete_row",
            description="DELETE rows matching a WHERE condition (returns deleted rows)",
            parameters={
                "table": _table_param(),
                "condition": _condition_param(),
                "values": _values_param(),
                "schema_name": _schema_param(),
            },
        ),
        ActionDefinition(
            name="update_row",
            description="UPDATE rows matching a WHERE condition (returns updated rows)",
            parameters={
                "table": _table_param(),
                "data": ParameterDef(
                    type="object",
                    description="Column-value pairs to update",
                    required=True,
                ),
                "condition": _condition_param(),
                "condition_values": ParameterDef(
                    type="array",
                    description="Values matching the '?' placeholders",
                    required=True,
                ),
                "schema_name": _schema_param(),
            },
        ),
        ActionDefinition(
            name="upsert_row",
            description="INSERT … ON CONFLICT (conflict_target) DO UPDATE …",
            parameters={
                "table": _table_param(),
                "data": ParameterDef(
                    type="object",
                    description="Column-value pairs to insert/update",
                    required=True,
                ),
                "conflict_target": ParameterDef(
                    type="string",
                    description="Column to use for conflict detection (usually PK)",
                    required=True,
                ),
                "schema_name": _schema_param(),
            },
        ),
        ActionDefinition(
            name="find_row",
            description="SELECT * FROM table WHERE column <op> value",
            parameters={
                "table": _table_param(),
                "column": ParameterDef(
                    type="string",
                    description="The column to filter by",
                    required=True,
                ),
                "operator": ParameterDef(
                    type="string",
                    description="Comparison operator (=, >, >=, <, !=, <=, LIKE, ILIKE)",
                    default="=",
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value to compare against (typed dynamically)",
                ),
                "schema_name": _schema_param(),
            },
        ),
        ActionDefinition(
            name="execute_query_with_condition",
            description="SELECT * FROM table WHERE <condition>",
            parameters={
                "table": _table_param(),
                "condition": _condition_param(),
                "values": _values_param(),
                "schema_name": _schema_param(),
            },
        ),
        ActionDefinition(
            name="list_schemas",
            description="List all user-visible schemas (excludes pg_catalog etc.)",
            parameters={},
        ),
        ActionDefinition(
            name="list_tables",
            description="List all tables and views in a schema",
            parameters={"schema_name": _schema_param()},
        ),
        ActionDefinition(
            name="describe_table",
            description="Return column metadata + primary keys for a table",
            parameters={
                "table": _table_param(),
                "schema_name": _schema_param(),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="PostgreSQL Database Credentials",
            description=(
                "Authenticate using PostgreSQL connection credentials "
                "(host/port/user/password/database)."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="POSTGRESQL_HOST",
                    display_name="Host",
                    description="PostgreSQL server hostname or IP",
                    required=True,
                    sensitive=False,
                    sample_format="localhost or postgres.example.com",
                ),
                EnvVar(
                    name="POSTGRESQL_PORT",
                    display_name="Port",
                    description="PostgreSQL server port (defaults to 5432 if omitted)",
                    required=False,
                    sensitive=False,
                    sample_format="5432",
                ),
                EnvVar(
                    name="POSTGRESQL_USER",
                    display_name="Username",
                    description="PostgreSQL username for authentication",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="POSTGRESQL_PASSWORD",
                    display_name="Password",
                    description="PostgreSQL password for authentication",
                    required=True,
                    sensitive=True,
                ),
                EnvVar(
                    name="POSTGRESQL_DATABASE",
                    display_name="Database",
                    description="The database name to connect to",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="POSTGRESQL_SSL_MODE",
                    display_name="SSL Mode",
                    description=(
                        "SSL mode: 'disabled', 'verify' (default — full verify), "
                        "or 'skip_verification' (encrypted but no cert check)"
                    ),
                    required=False,
                    sensitive=False,
                    sample_format="verify | skip_verification | disabled",
                ),
            ],
        ),
    ],
)
