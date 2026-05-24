"""Microsoft SQL Server integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="microsoft_sql_server",
    display_name="Microsoft SQL Server",
    description="Execute queries and manage data in Microsoft SQL Server databases",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:microsoft_sql_server-themed",
    app_url="https://www.microsoft.com/en-us/sql-server",
    categories=["Databases", "Data Infrastructure"],
    actions=[
        ActionDefinition(
            name="execute_raw_query",
            description="Execute a raw SQL query against the database and return results",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="The SQL query to execute",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="execute_query",
            description="Execute a parameterized SQL query with named inputs",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="The SQL query to execute, using @name placeholders for parameters",
                    required=True,
                ),
                "inputs": ParameterDef(
                    type="object",
                    description="Key-value mapping of parameter names to values for the query placeholders",
                    default=None,
                ),
            },
        ),
        ActionDefinition(
            name="insert_row",
            description="Insert a new row into a specified table",
            parameters={
                "table": ParameterDef(
                    type="string",
                    description="Name of the table to insert into",
                    required=True,
                ),
                "data": ParameterDef(
                    type="object",
                    description="JSON object mapping column names to values for the new row",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_table_options",
            description="List all available base tables in the database",
            parameters={},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="SQL Server Connection",
            description=(
                "Connect using SQL Server host, port, database, username, and password"
            ),
            setup_environment_variables=[
                EnvVar(
                    name="MSSQL_HOST",
                    display_name="Host",
                    description="SQL Server hostname or IP address",
                    required=True,
                    sensitive=False,
                    sample_format="myserver.database.windows.net",
                ),
                EnvVar(
                    name="MSSQL_PORT",
                    display_name="Port",
                    description="SQL Server port number",
                    required=True,
                    sensitive=False,
                    sample_format="1433",
                ),
                EnvVar(
                    name="MSSQL_USERNAME",
                    display_name="Username",
                    description="SQL Server login username",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="MSSQL_PASSWORD",
                    display_name="Password",
                    description="SQL Server login password",
                    required=True,
                    sensitive=True,
                ),
                EnvVar(
                    name="MSSQL_DATABASE",
                    display_name="Database",
                    description="Name of the database to connect to",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="MSSQL_ENCRYPT",
                    display_name="Encrypt",
                    description="Whether to encrypt the connection (true/false). Use true for Azure SQL.",
                    required=False,
                    sensitive=False,
                    sample_format="true",
                ),
                EnvVar(
                    name="MSSQL_TRUST_SERVER_CERTIFICATE",
                    display_name="Trust Server Certificate",
                    description="Whether to trust self-signed certificates (true/false). Use true for local dev.",
                    required=False,
                    sensitive=False,
                    sample_format="false",
                ),
            ],
        ),
    ],
)
