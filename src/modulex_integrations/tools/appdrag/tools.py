"""AppDrag LangChain ``@tool`` functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.appdrag.outputs import (
    ExecuteApiFunctionOutput,
    InsertRowOutput,
    UpdateRowOutput,
)

__all__ = ["execute_api_function", "insert_row", "update_row"]

_BACKEND_URL = "https://api.appdrag.com/CloudBackend.aspx"
_FUNCTION_URL_TEMPLATE = "https://{app_id}.appdrag.site/api{path}"
_TIMEOUT = 30.0
_HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
_FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


def _function_url(app_id: str, path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    return _FUNCTION_URL_TEMPLATE.format(app_id=app_id, path=path)


def _auth_form(api_key: str, app_id: str) -> dict[str, str]:
    return {"APIKey": api_key, "appID": app_id}


def _escape_sql_values(values: list[str]) -> str:
    parts: list[str] = []
    for v in values:
        if v is None:
            parts.append("NULL")
        else:
            parts.append(f"'{str(v).replace(chr(39), chr(39) * 2)}'")
    return ", ".join(parts)


def _build_insert_query(table: str, columns: list[str], values: list[str]) -> str:
    return (
        f"INSERT INTO {table} ({', '.join(columns)}) "
        f"VALUES ({_escape_sql_values(values)})"
    )


def _build_update_query(
    table: str,
    columns: list[str],
    values: list[str],
    where_condition: str,
    where_values: list[str],
) -> str:
    set_parts: list[str] = []
    for col, val in zip(columns, values, strict=False):
        if val is None:
            set_parts.append(f"{col} = NULL")
        else:
            escaped = str(val).replace("'", "''")
            set_parts.append(f"{col} = '{escaped}'")

    where_clause = where_condition
    for val in where_values:
        if val is None:
            where_clause = where_clause.replace("?", "NULL", 1)
        else:
            escaped = str(val).replace("'", "''")
            where_clause = where_clause.replace("?", f"'{escaped}'", 1)

    return f"UPDATE {table} SET {', '.join(set_parts)} WHERE {where_clause}"


class ExecuteApiFunctionInput(BaseModel):
    api_key: str = Field(description="AppDrag API key (provided by credential system)")
    app_id: str = Field(description="AppDrag Application ID")
    path: str = Field(description="Function name path (e.g. '/insert-user')")
    method: str = Field(default="GET", description="HTTP method")
    data: dict[str, Any] | None = Field(default=None, description="Function payload")


class InsertRowInput(BaseModel):
    api_key: str = Field(description="AppDrag API key (provided by credential system)")
    app_id: str = Field(description="AppDrag Application ID")
    table: str = Field(description="Database table name")
    columns: list[str] = Field(description="Column names to insert into")
    values: list[str] = Field(description="Values corresponding to each column")


class UpdateRowInput(BaseModel):
    api_key: str = Field(description="AppDrag API key (provided by credential system)")
    app_id: str = Field(description="AppDrag Application ID")
    table: str = Field(description="Database table name")
    columns_to_update: list[str] = Field(description="Column names to update")
    values: list[str] = Field(description="New values for each column")
    where_condition: str = Field(description="SQL WHERE condition with ? placeholders")
    where_values: list[str] = Field(description="Values to replace ? placeholders")


def _credential_error(name: str, field: str) -> str:
    return (
        f"AppDrag {field} is empty for {name}. "
        "Please configure a valid credential."
    )


@tool(args_schema=ExecuteApiFunctionInput)
@serialize_pydantic_return
async def execute_api_function(
    api_key: str,
    app_id: str,
    path: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
) -> ExecuteApiFunctionOutput:
    """Execute an API function from an AppDrag cloud backend."""
    if not api_key or not api_key.strip():
        return ExecuteApiFunctionOutput(
            success=False, error=_credential_error("execute_api_function", "API key")
        )
    if not app_id or not app_id.strip():
        return ExecuteApiFunctionOutput(
            success=False, error=_credential_error("execute_api_function", "App ID")
        )
    if not path or not path.strip():
        return ExecuteApiFunctionOutput(
            success=False, error="Function path is required."
        )

    method_upper = method.upper()
    if method_upper not in _HTTP_METHODS:
        return ExecuteApiFunctionOutput(
            success=False,
            error=(
                f"Invalid HTTP method: {method}. "
                f"Must be one of: {', '.join(_HTTP_METHODS)}"
            ),
        )

    url = _function_url(app_id, path)
    auth = _auth_form(api_key, app_id)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            if method_upper == "GET":
                params: dict[str, Any] = {**auth, **(data or {})}
                response = await client.get(url, params=params, headers=_FORM_HEADERS)
            else:
                form: dict[str, Any] = {**auth, **(data or {})}
                response = await client.request(
                    method=method_upper, url=url, data=form, headers=_FORM_HEADERS
                )

        try:
            parsed: Any = response.json()
        except Exception:
            parsed = response.text

        if response.status_code >= 400:
            return ExecuteApiFunctionOutput(
                success=False,
                error=f"API error: {response.status_code} - {parsed}",
            )
    except Exception as exc:
        return ExecuteApiFunctionOutput(
            success=False, error=f"Failed to execute API function: {exc}"
        )

    return ExecuteApiFunctionOutput(
        success=True, path=path, method=method_upper, response=parsed
    )


@tool(args_schema=InsertRowInput)
@serialize_pydantic_return
async def insert_row(
    api_key: str,
    app_id: str,
    table: str,
    columns: list[str],
    values: list[str],
) -> InsertRowOutput:
    """Insert a new row into an AppDrag cloud database table."""
    if not api_key or not api_key.strip():
        return InsertRowOutput(
            success=False, error=_credential_error("insert_row", "API key")
        )
    if not app_id or not app_id.strip():
        return InsertRowOutput(
            success=False, error=_credential_error("insert_row", "App ID")
        )
    if not table or not table.strip():
        return InsertRowOutput(success=False, error="Table name is required.")
    if not columns:
        return InsertRowOutput(success=False, error="At least one column is required.")
    if not values:
        return InsertRowOutput(success=False, error="At least one value is required.")
    if len(columns) != len(values):
        return InsertRowOutput(
            success=False,
            error=(
                f"Number of columns ({len(columns)}) must match number of "
                f"values ({len(values)})."
            ),
        )

    query = _build_insert_query(table, columns, values)
    form = {
        **_auth_form(api_key, app_id),
        "command": "CloudDBExecuteRawQuery",
        "query": query,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _BACKEND_URL, data=form, headers=_FORM_HEADERS
            )

        try:
            parsed = response.json()
        except Exception:
            parsed = {"raw_response": response.text}

        if response.status_code >= 400:
            return InsertRowOutput(
                success=False,
                error=f"API error: {response.status_code} - {parsed}",
            )
        if isinstance(parsed, dict) and parsed.get("error"):
            return InsertRowOutput(success=False, error=str(parsed.get("error")))
    except Exception as exc:
        return InsertRowOutput(success=False, error=f"Failed to insert row: {exc}")

    affected = parsed.get("affectedRows", 0) if isinstance(parsed, dict) else 0
    if isinstance(parsed, dict) and affected == 0:
        return InsertRowOutput(
            success=False, error="Insert operation failed - no rows affected"
        )

    return InsertRowOutput(
        success=True,
        table=table,
        columns=columns,
        affected_rows=affected,
        response=parsed if isinstance(parsed, dict) else None,
    )


@tool(args_schema=UpdateRowInput)
@serialize_pydantic_return
async def update_row(
    api_key: str,
    app_id: str,
    table: str,
    columns_to_update: list[str],
    values: list[str],
    where_condition: str,
    where_values: list[str],
) -> UpdateRowOutput:
    """Update rows in an AppDrag cloud database table."""
    if not api_key or not api_key.strip():
        return UpdateRowOutput(
            success=False, error=_credential_error("update_row", "API key")
        )
    if not app_id or not app_id.strip():
        return UpdateRowOutput(
            success=False, error=_credential_error("update_row", "App ID")
        )
    if not table or not table.strip():
        return UpdateRowOutput(success=False, error="Table name is required.")
    if not columns_to_update:
        return UpdateRowOutput(
            success=False, error="At least one column to update is required."
        )
    if not values:
        return UpdateRowOutput(success=False, error="At least one value is required.")
    if len(columns_to_update) != len(values):
        return UpdateRowOutput(
            success=False,
            error=(
                f"Number of columns ({len(columns_to_update)}) must match "
                f"number of values ({len(values)})."
            ),
        )
    if not where_condition or not where_condition.strip():
        return UpdateRowOutput(
            success=False,
            error="WHERE condition is required to prevent accidental full table updates.",
        )

    placeholders = where_condition.count("?")
    if placeholders != len(where_values):
        return UpdateRowOutput(
            success=False,
            error=(
                f"Number of ? placeholders ({placeholders}) must match number "
                f"of where_values ({len(where_values)})."
            ),
        )

    query = _build_update_query(
        table, columns_to_update, values, where_condition, where_values
    )
    form = {
        **_auth_form(api_key, app_id),
        "command": "CloudDBExecuteRawQuery",
        "query": query,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _BACKEND_URL, data=form, headers=_FORM_HEADERS
            )

        try:
            parsed = response.json()
        except Exception:
            parsed = {"raw_response": response.text}

        if response.status_code >= 400:
            return UpdateRowOutput(
                success=False,
                error=f"API error: {response.status_code} - {parsed}",
            )
        if isinstance(parsed, dict) and parsed.get("error"):
            return UpdateRowOutput(success=False, error=str(parsed.get("error")))
    except Exception as exc:
        return UpdateRowOutput(success=False, error=f"Failed to update row: {exc}")

    affected = parsed.get("affectedRows", 0) if isinstance(parsed, dict) else 0
    if isinstance(parsed, dict) and affected == 0:
        return UpdateRowOutput(
            success=False,
            error="Update operation failed - no rows matched the WHERE condition",
        )

    return UpdateRowOutput(
        success=True,
        table=table,
        columns_updated=columns_to_update,
        affected_rows=affected,
        response=parsed if isinstance(parsed, dict) else None,
    )
