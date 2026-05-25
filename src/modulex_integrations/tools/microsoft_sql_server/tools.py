"""Microsoft SQL Server LangChain @tool functions."""
from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_sql_server.outputs import (
    ExecuteQueryOutput,
    ExecuteRawQueryOutput,
    InsertRowOutput,
    ListTableOptionsOutput,
)

__all__ = [
    "execute_query",
    "execute_raw_query",
    "insert_row",
    "list_table_options",
]


def _get_connection_config(auth_data: dict[str, Any]) -> dict[str, Any]:
    """Build pymssql connection kwargs from auth_data fields."""
    encrypt = str(auth_data.get("encrypt", "false")).lower() == "true"
    tls_validate = not (
        str(auth_data.get("trust_server_certificate", "false")).lower() == "true"
    )
    config: dict[str, Any] = {
        "server": auth_data.get("host", ""),
        "port": str(auth_data.get("port", "1433")),
        "user": auth_data.get("username", ""),
        "password": auth_data.get("password", ""),
        "database": auth_data.get("database", ""),
        "tds_version": "7.3",
    }
    if encrypt:
        config["conn_properties"] = ""
        config["tds_version"] = "7.3"
    if not tls_validate:
        config["conn_properties"] = ""
    return config


def _run_query(
    config: dict[str, Any], query: str, inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a query synchronously via pymssql and return results."""
    import pymssql

    conn = pymssql.connect(**config)
    try:
        cursor = conn.cursor(as_dict=True)
        if inputs:
            cursor.execute(query, inputs)
        else:
            cursor.execute(query)
        try:
            rows = cursor.fetchall()
        except pymssql.OperationalError:
            rows = []
        rows_affected = [cursor.rowcount] if cursor.rowcount >= 0 else []
        conn.commit()
        return {"recordset": rows, "rows_affected": rows_affected}
    finally:
        conn.close()


# --- Input schemas --------------------------------------------------------


class ExecuteRawQueryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(description="The SQL query to execute")


class ExecuteQueryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(
        description="The SQL query to execute, using %(name)s placeholders for parameters",
    )
    inputs: dict[str, Any] | None = Field(
        default=None,
        description="Key-value mapping of parameter names to values for the query placeholders",
    )


class InsertRowInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    table: str = Field(description="Name of the table to insert into")
    data: dict[str, Any] = Field(
        description="JSON object mapping column names to values for the new row",
    )


class ListTableOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ExecuteRawQueryInput)
@serialize_pydantic_return
async def execute_raw_query(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
) -> ExecuteRawQueryOutput:
    """Execute a raw SQL query against the database and return results."""
    config = _get_connection_config(auth_data)
    if not config["server"] or not config["user"] or not config["password"]:
        return ExecuteRawQueryOutput(
            success=False,
            error="Missing required connection fields (host, username, or password).",
        )
    try:
        result = await asyncio.to_thread(_run_query, config, query)
    except Exception as exc:
        return ExecuteRawQueryOutput(success=False, error=f"Query failed: {exc}")
    return ExecuteRawQueryOutput(
        success=True,
        recordset=result["recordset"],
        rows_affected=result["rows_affected"],
    )


@tool(args_schema=ExecuteQueryInput)
@serialize_pydantic_return
async def execute_query(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    inputs: dict[str, Any] | None = None,
) -> ExecuteQueryOutput:
    """Execute a parameterized SQL query with named inputs."""
    config = _get_connection_config(auth_data)
    if not config["server"] or not config["user"] or not config["password"]:
        return ExecuteQueryOutput(
            success=False,
            error="Missing required connection fields (host, username, or password).",
        )
    try:
        result = await asyncio.to_thread(_run_query, config, query, inputs)
    except Exception as exc:
        return ExecuteQueryOutput(success=False, error=f"Query failed: {exc}")
    return ExecuteQueryOutput(
        success=True,
        recordset=result["recordset"],
        rows_affected=result["rows_affected"],
    )


@tool(args_schema=InsertRowInput)
@serialize_pydantic_return
async def insert_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    data: dict[str, Any],
) -> InsertRowOutput:
    """Insert a new row into a specified table."""
    config = _get_connection_config(auth_data)
    if not config["server"] or not config["user"] or not config["password"]:
        return InsertRowOutput(
            success=False,
            error="Missing required connection fields (host, username, or password).",
        )
    if not table or not data:
        return InsertRowOutput(
            success=False,
            error="Both table name and data object are required.",
        )
    columns = list(data.keys())
    safe_table = table.replace("]", "]]")
    safe_columns = [col.replace("]", "]]") for col in columns]
    placeholders = ", ".join(f"%({col})s" for col in columns)
    col_list = ", ".join(f"[{col}]" for col in safe_columns)
    insert_query = f"INSERT INTO [{safe_table}] ({col_list}) VALUES ({placeholders})"
    try:
        result = await asyncio.to_thread(_run_query, config, insert_query, data)
    except Exception as exc:
        return InsertRowOutput(success=False, error=f"Insert failed: {exc}")
    return InsertRowOutput(
        success=True,
        rows_affected=result["rows_affected"],
    )


@tool(args_schema=ListTableOptionsInput)
@serialize_pydantic_return
async def list_table_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListTableOptionsOutput:
    """List all available base tables in the database."""
    config = _get_connection_config(auth_data)
    if not config["server"] or not config["user"] or not config["password"]:
        return ListTableOptionsOutput(
            success=False,
            error="Missing required connection fields (host, username, or password).",
        )
    query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
    try:
        result = await asyncio.to_thread(_run_query, config, query)
    except Exception as exc:
        return ListTableOptionsOutput(success=False, error=f"Query failed: {exc}")
    tables = [row.get("TABLE_NAME", "") for row in result["recordset"] if row.get("TABLE_NAME")]
    return ListTableOptionsOutput(
        success=True,
        tables=tables,
    )
