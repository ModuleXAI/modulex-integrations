"""MySQL integration manifest."""
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


def _condition_param() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="WHERE condition with '?' placeholders",
        required=True,
    )


def _values_param() -> ParameterDef:
    return ParameterDef(
        type="array",
        description="Values matching the '?' placeholders",
        required=True,
    )


manifest = IntegrationManifest(
    name="mysql",
    display_name="MySQL",
    description=(
        "MySQL database integration for executing SQL queries, "
        "managing tables, and performing CRUD operations. Uses the "
        "aiomysql driver."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:mysql-icon",
    app_url="https://www.mysql.com/",
    categories=["Database", "Data Management", "storage"],
    actions=[
        ActionDefinition(
            name="execute_raw_query",
            description=(
                "Execute any SQL statement. Use '%s' for parameterized "
                "queries (DB-API style)."
            ),
            parameters={
                "sql": ParameterDef(
                    type="string", description="The SQL to execute", required=True
                ),
                "values": ParameterDef(
                    type="array", description="Values for '%s' placeholders"
                ),
            },
        ),
        ActionDefinition(
            name="create_row",
            description="INSERT a new row (returns affected_rows + last_insert_id)",
            parameters={
                "table": _table_param(),
                "data": ParameterDef(
                    type="object",
                    description="Column-value pairs to insert",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_row",
            description="DELETE rows matching a WHERE condition",
            parameters={
                "table": _table_param(),
                "condition": _condition_param(),
                "values": _values_param(),
            },
        ),
        ActionDefinition(
            name="update_row",
            description="UPDATE rows matching a WHERE condition",
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
            },
        ),
        ActionDefinition(
            name="find_row",
            description="SELECT * FROM table WHERE column <op> value",
            parameters={
                "table": _table_param(),
                "column": ParameterDef(
                    type="string",
                    description="Column to filter by",
                    required=True,
                ),
                "operator": ParameterDef(
                    type="string",
                    description="=, >, >=, <, !=, <=, LIKE",
                    default="=",
                ),
                "value": ParameterDef(
                    type="string", description="Value to compare against"
                ),
            },
        ),
        ActionDefinition(
            name="execute_query_with_condition",
            description="SELECT * FROM table WHERE <condition>",
            parameters={
                "table": _table_param(),
                "condition": _condition_param(),
                "values": _values_param(),
            },
        ),
        ActionDefinition(
            name="execute_stored_procedure",
            description="CALL <stored_procedure>(...) with optional parameters",
            parameters={
                "stored_procedure": ParameterDef(
                    type="string",
                    description="Procedure name (may be qualified 'db.proc')",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array", description="Procedure parameters"
                ),
            },
        ),
        ActionDefinition(
            name="list_tables",
            description="List all tables and views in the current database",
            parameters={},
        ),
        ActionDefinition(
            name="describe_table",
            description="Return column metadata for a table (SHOW COLUMNS)",
            parameters={"table": _table_param()},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="MySQL Database Credentials",
            description=(
                "Authenticate using MySQL connection credentials "
                "(host/port/user/password/database)."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="MYSQL_HOST",
                    display_name="Host",
                    description="MySQL server hostname or IP",
                    required=True,
                    sensitive=False,
                    sample_format="localhost or mysql.example.com",
                ),
                EnvVar(
                    name="MYSQL_PORT",
                    display_name="Port",
                    description="MySQL server port (defaults to 3306 if omitted)",
                    required=False,
                    sensitive=False,
                    sample_format="3306",
                ),
                EnvVar(
                    name="MYSQL_USER",
                    display_name="Username",
                    description="MySQL username for authentication",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="MYSQL_PASSWORD",
                    display_name="Password",
                    description="MySQL password for authentication",
                    required=True,
                    sensitive=True,
                ),
                EnvVar(
                    name="MYSQL_DATABASE",
                    display_name="Database",
                    description="The database name to connect to",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="MYSQL_SSL_MODE",
                    display_name="SSL Mode",
                    description=(
                        "SSL mode: 'disabled', 'verify' (default), "
                        "or 'skip_verification'"
                    ),
                    required=False,
                    sensitive=False,
                    sample_format="verify | skip_verification | disabled",
                ),
            ],
        ),
    ],
)
