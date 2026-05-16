"""MySQL LangChain ``@tool`` functions.

Pure SDK integration over ``aiomysql`` (DB-API style with ``%s``
placeholders). Token-based runtime convention (``auth_type, auth_data``
first args).

Like the postgresql sibling, every action opens a fresh connection
and closes it in a ``finally`` block; ``aiomysql`` connection objects
expose a synchronous ``close()``. ``aiomysql`` is imported lazily
inside ``_connect``/``_dict_cursor`` so the manifest can be inspected
without the driver installed.

Tests stub ``_connect`` and ``_dict_cursor`` so that integration
behavior can be exercised without a running MySQL server.
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.mysql.outputs import (
    CreateRowOutput,
    DeleteRowOutput,
    DescribeTableOutput,
    ExecuteQueryWithConditionOutput,
    ExecuteRawQueryOutput,
    ExecuteStoredProcedureOutput,
    FindRowOutput,
    ListTablesOutput,
    TableEntry,
    UpdateRowOutput,
)

__all__ = [
    "create_row",
    "delete_row",
    "describe_table",
    "execute_query_with_condition",
    "execute_raw_query",
    "execute_stored_procedure",
    "find_row",
    "list_tables",
    "update_row",
]

_TIMEOUT = 60


async def _connect(auth_data: dict[str, Any]) -> Any:
    """Open an aiomysql connection from connection params in ``auth_data``."""
    import aiomysql  # type: ignore[import-untyped]

    ssl_config: Any = None
    ssl_mode = auth_data.get("ssl_mode")
    if ssl_mode and ssl_mode != "disabled":
        import ssl as ssl_module

        ctx = ssl_module.create_default_context()
        if ssl_mode == "skip_verification":
            ctx.check_hostname = False
            ctx.verify_mode = ssl_module.CERT_NONE
        ssl_config = ctx

    return await aiomysql.connect(
        host=auth_data.get("host", "localhost"),
        port=int(auth_data.get("port", 3306)),
        user=auth_data.get("user"),
        password=auth_data.get("password"),
        db=auth_data.get("database"),
        ssl=ssl_config,
        autocommit=True,
        connect_timeout=_TIMEOUT,
    )


def _dict_cursor(conn: Any) -> Any:
    """Return a DictCursor context manager (lazy aiomysql import)."""
    import aiomysql

    return conn.cursor(aiomysql.DictCursor)


def _plain_cursor(conn: Any) -> Any:
    """Return a plain cursor context manager."""
    return conn.cursor()


def _to_mysql_placeholders(condition: str) -> str:
    return condition.replace("?", "%s")


def _validate_placeholders(
    condition: str, values: list[Any], action: str
) -> str | None:
    count = condition.count("?")
    if count == 0:
        return f"No valid condition provided for {action}: at least one '?' placeholder required"
    if len(values) != count:
        return (
            f"{action}: number of values ({len(values)}) does not match "
            f"placeholders ({count})"
        )
    return None


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (custom)")
    auth_data: dict[str, Any] = Field(
        description="host/port/user/password/database/ssl_mode"
    )


class ExecuteRawQueryInput(_AuthFields):
    sql: str = Field(description="The SQL query to execute")
    values: list[Any] | None = Field(default=None)


class _TableInput(_AuthFields):
    table: str = Field(description="Target table name")


class CreateRowInput(_TableInput):
    data: dict[str, Any] = Field(description="Column-value pairs to insert")


class DeleteRowInput(_TableInput):
    condition: str = Field(description="WHERE clause with '?' placeholders")
    values: list[Any] = Field(description="Values for '?' placeholders")


class UpdateRowInput(_TableInput):
    data: dict[str, Any] = Field(description="Column-value pairs to update")
    condition: str = Field(description="WHERE clause with '?' placeholders")
    condition_values: list[Any] = Field(description="Values for '?' placeholders")


class FindRowInput(_TableInput):
    column: str = Field(description="Column to filter on")
    operator: str = Field(default="=")
    value: Any = Field(default=None)


class ExecuteQueryInput(_TableInput):
    condition: str = Field(description="WHERE clause with '?' placeholders")
    values: list[Any] = Field(description="Values for '?' placeholders")


class ExecuteStoredProcedureInput(_AuthFields):
    stored_procedure: str = Field(description="Procedure name")
    values: list[Any] | None = Field(default=None)


class ListTablesInput(_AuthFields):
    pass


class DescribeTableInput(_AuthFields):
    table: str = Field(description="Table to describe")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=ExecuteRawQueryInput)
@serialize_pydantic_return
async def execute_raw_query(
    auth_type: str,
    auth_data: dict[str, Any],
    sql: str,
    values: list[Any] | None = None,
) -> ExecuteRawQueryOutput:
    """Execute any SQL statement (SELECT/INSERT/UPDATE/DELETE/DDL)."""
    try:
        conn = await _connect(auth_data)
        try:
            async with _dict_cursor(conn) as cursor:
                if values:
                    await cursor.execute(sql, values)
                else:
                    await cursor.execute(sql)
                if cursor.description:
                    rows = await cursor.fetchall()
                    data = [dict(r) for r in rows]
                    return ExecuteRawQueryOutput(
                        success=True, row_count=len(data), data=data
                    )
                # DML statement — report affected rows like the legacy impl.
                data = [
                    {
                        "affected_rows": cursor.rowcount,
                        "last_insert_id": cursor.lastrowid,
                    }
                ]
                return ExecuteRawQueryOutput(
                    success=True, row_count=len(data), data=data
                )
        finally:
            conn.close()
    except Exception as exc:
        return ExecuteRawQueryOutput(success=False, error=str(exc))


@tool(args_schema=CreateRowInput)
@serialize_pydantic_return
async def create_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    data: dict[str, Any],
) -> CreateRowOutput:
    """INSERT a single row."""
    try:
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["%s"] * len(columns))
        column_names = ", ".join(f"`{c}`" for c in columns)
        sql = f"INSERT INTO `{table}` ({column_names}) VALUES ({placeholders})"

        conn = await _connect(auth_data)
        try:
            async with _plain_cursor(conn) as cursor:
                await cursor.execute(sql, values)
                affected = cursor.rowcount
                last_id = cursor.lastrowid
        finally:
            conn.close()
    except Exception as exc:
        return CreateRowOutput(success=False, error=str(exc))
    return CreateRowOutput(
        success=True,
        table=table,
        affected_rows=affected,
        last_insert_id=last_id,
        columns=columns,
    )


@tool(args_schema=DeleteRowInput)
@serialize_pydantic_return
async def delete_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    condition: str,
    values: list[Any],
) -> DeleteRowOutput:
    """DELETE rows matching ``condition``."""
    err = _validate_placeholders(condition, values, "delete_row")
    if err:
        return DeleteRowOutput(success=False, error=err)
    try:
        sql = f"DELETE FROM `{table}` WHERE {_to_mysql_placeholders(condition)}"
        conn = await _connect(auth_data)
        try:
            async with _plain_cursor(conn) as cursor:
                await cursor.execute(sql, values)
                affected = cursor.rowcount
        finally:
            conn.close()
    except Exception as exc:
        return DeleteRowOutput(success=False, error=str(exc))
    return DeleteRowOutput(success=True, table=table, affected_rows=affected)


@tool(args_schema=UpdateRowInput)
@serialize_pydantic_return
async def update_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    data: dict[str, Any],
    condition: str,
    condition_values: list[Any],
) -> UpdateRowOutput:
    """UPDATE rows matching ``condition``."""
    err = _validate_placeholders(condition, condition_values, "update_row")
    if err:
        return UpdateRowOutput(success=False, error=err)
    try:
        columns = list(data.keys())
        update_values = list(data.values())
        set_clause = ", ".join(f"`{c}` = %s" for c in columns)
        sql = (
            f"UPDATE `{table}` SET {set_clause} "
            f"WHERE {_to_mysql_placeholders(condition)}"
        )
        conn = await _connect(auth_data)
        try:
            async with _plain_cursor(conn) as cursor:
                await cursor.execute(sql, update_values + condition_values)
                affected = cursor.rowcount
        finally:
            conn.close()
    except Exception as exc:
        return UpdateRowOutput(success=False, error=str(exc))
    return UpdateRowOutput(
        success=True,
        table=table,
        affected_rows=affected,
        updated_columns=columns,
    )


_VALID_OPERATORS = {"=", ">", ">=", "<", "!=", "<=", "LIKE", "like"}


@tool(args_schema=FindRowInput)
@serialize_pydantic_return
async def find_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    column: str,
    operator: str = "=",
    value: Any = None,
) -> FindRowOutput:
    """SELECT * FROM table WHERE column <op> value."""
    if operator not in _VALID_OPERATORS:
        return FindRowOutput(
            success=False,
            error=(
                f"Invalid operator '{operator}'. Supported: "
                f"{', '.join(sorted(_VALID_OPERATORS))}"
            ),
        )
    try:
        sql = f"SELECT * FROM `{table}` WHERE `{column}` {operator} %s"
        conn = await _connect(auth_data)
        try:
            async with _dict_cursor(conn) as cursor:
                await cursor.execute(sql, [value])
                rows = await cursor.fetchall()
        finally:
            conn.close()
    except Exception as exc:
        return FindRowOutput(success=False, error=str(exc))
    data = list(rows)
    return FindRowOutput(success=True, table=table, row_count=len(data), data=data)


@tool(args_schema=ExecuteQueryInput)
@serialize_pydantic_return
async def execute_query_with_condition(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    condition: str,
    values: list[Any],
) -> ExecuteQueryWithConditionOutput:
    """SELECT * FROM table WHERE <condition>."""
    err = _validate_placeholders(condition, values, "execute_query_with_condition")
    if err:
        return ExecuteQueryWithConditionOutput(success=False, error=err)
    try:
        sql = f"SELECT * FROM `{table}` WHERE {_to_mysql_placeholders(condition)}"
        conn = await _connect(auth_data)
        try:
            async with _dict_cursor(conn) as cursor:
                await cursor.execute(sql, values)
                rows = await cursor.fetchall()
        finally:
            conn.close()
    except Exception as exc:
        return ExecuteQueryWithConditionOutput(success=False, error=str(exc))
    data = list(rows)
    return ExecuteQueryWithConditionOutput(
        success=True, table=table, row_count=len(data), data=data
    )


@tool(args_schema=ExecuteStoredProcedureInput)
@serialize_pydantic_return
async def execute_stored_procedure(
    auth_type: str,
    auth_data: dict[str, Any],
    stored_procedure: str,
    values: list[Any] | None = None,
) -> ExecuteStoredProcedureOutput:
    """CALL <stored_procedure>(...)."""
    try:
        if values:
            placeholders = ", ".join(["%s"] * len(values))
            sql = f"CALL {stored_procedure}({placeholders})"
        else:
            sql = f"CALL {stored_procedure}()"
            values = []

        conn = await _connect(auth_data)
        try:
            async with _dict_cursor(conn) as cursor:
                await cursor.execute(sql, values)
                results: list[dict[str, Any]] = []
                if cursor.description:
                    rows = await cursor.fetchall()
                    results = list(rows)
                while await cursor.nextset():
                    if cursor.description:
                        rows = await cursor.fetchall()
                        results.extend(list(rows))
        finally:
            conn.close()
    except Exception as exc:
        return ExecuteStoredProcedureOutput(success=False, error=str(exc))
    return ExecuteStoredProcedureOutput(
        success=True,
        procedure=stored_procedure,
        row_count=len(results),
        data=results if results else {"executed": True},
    )


@tool(args_schema=ListTablesInput)
@serialize_pydantic_return
async def list_tables(
    auth_type: str, auth_data: dict[str, Any]
) -> ListTablesOutput:
    """List all tables and views in the current database (SHOW FULL TABLES)."""
    try:
        conn = await _connect(auth_data)
        try:
            async with _dict_cursor(conn) as cursor:
                await cursor.execute("SHOW FULL TABLES")
                rows = await cursor.fetchall()
        finally:
            conn.close()
    except Exception as exc:
        return ListTablesOutput(success=False, error=str(exc))

    database = auth_data.get("database")
    tables: list[TableEntry] = []
    for row in rows:
        name_key = f"Tables_in_{database}"
        name = row.get(name_key) if isinstance(row, dict) else None
        if name is None and isinstance(row, dict):
            name = next(iter(row.values()), None)
        tables.append(
            TableEntry(name=name, type=row.get("Table_type", "UNKNOWN"))
        )
    return ListTablesOutput(
        success=True, database=database, tables=tables, count=len(tables)
    )


@tool(args_schema=DescribeTableInput)
@serialize_pydantic_return
async def describe_table(
    auth_type: str, auth_data: dict[str, Any], table: str
) -> DescribeTableOutput:
    """SHOW COLUMNS FROM `table` — column metadata."""
    try:
        conn = await _connect(auth_data)
        try:
            async with _dict_cursor(conn) as cursor:
                await cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                rows = await cursor.fetchall()
        finally:
            conn.close()
    except Exception as exc:
        return DescribeTableOutput(success=False, error=str(exc))
    columns = [
        {
            "name": r.get("Field"),
            "type": r.get("Type"),
            "null": r.get("Null"),
            "key": r.get("Key"),
            "default": r.get("Default"),
            "extra": r.get("Extra"),
        }
        for r in rows
    ]
    return DescribeTableOutput(
        success=True, table=table, columns=columns, column_count=len(columns)
    )
