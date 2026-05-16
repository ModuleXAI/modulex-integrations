"""PostgreSQL LangChain ``@tool`` functions.

Pure SDK integration over ``asyncpg``. Token-based runtime convention
(``auth_type, auth_data`` first args) — ``auth_type`` is informational
(modulex schema label ``custom``); the tool body pulls host/port/user/
password/database/ssl_mode out of ``auth_data``.

Every action opens a fresh asyncpg connection (no pool kept across
calls — matches legacy behavior) and closes it in a ``finally`` block.
Errors and connection failures all flow through a unified
``success=False`` envelope.

Note: ``asyncpg`` is imported lazily inside ``_connect`` so the
integration's manifest can still be inspected when ``asyncpg`` is not
installed (useful for the modulex-side package_loader cold-start).
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.postgresql.outputs import (
    CreateRowOutput,
    DeleteRowOutput,
    DescribeTableOutput,
    ExecuteQueryWithConditionOutput,
    ExecuteRawQueryOutput,
    FindRowOutput,
    ListSchemasOutput,
    ListTablesOutput,
    TableEntry,
    UpdateRowOutput,
    UpsertRowOutput,
)

__all__ = [
    "create_row",
    "delete_row",
    "describe_table",
    "execute_query_with_condition",
    "execute_raw_query",
    "find_row",
    "list_schemas",
    "list_tables",
    "update_row",
    "upsert_row",
]

_TIMEOUT = 60


async def _connect(auth_data: dict[str, Any]) -> Any:
    """Open an asyncpg connection from connection params in ``auth_data``."""
    import ssl as ssl_module

    import asyncpg  # type: ignore[import-untyped]

    ssl_config: Any = None
    ssl_mode = auth_data.get("ssl_mode")
    if ssl_mode and ssl_mode != "disabled":
        ctx = ssl_module.create_default_context()
        if ssl_mode == "skip_verification":
            ctx.check_hostname = False
            ctx.verify_mode = ssl_module.CERT_NONE
        ssl_config = ctx

    return await asyncpg.connect(
        host=auth_data.get("host", "localhost"),
        port=int(auth_data.get("port", 5432)),
        user=auth_data.get("user"),
        password=auth_data.get("password"),
        database=auth_data.get("database"),
        ssl=ssl_config,
        timeout=_TIMEOUT,
    )


def _convert_placeholders(sql: str) -> str:
    """Convert ``?`` placeholders to ``$1, $2, ...``."""
    out: list[str] = []
    n = 1
    for char in sql:
        if char == "?":
            out.append(f"${n}")
            n += 1
        else:
            out.append(char)
    return "".join(out)


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (custom)")
    auth_data: dict[str, Any] = Field(
        description="host/port/user/password/database/ssl_mode"
    )


class ExecuteRawQueryInput(_AuthFields):
    sql: str = Field(description="The SQL query to execute")
    values: list[Any] | None = Field(default=None, description="$N placeholder values")


class _TableMutationInput(_AuthFields):
    table: str = Field(description="Target table name")
    schema_name: str = Field(default="public")


class CreateRowInput(_TableMutationInput):
    data: dict[str, Any] = Field(description="Column-value pairs to insert")


class DeleteRowInput(_TableMutationInput):
    condition: str = Field(description="WHERE clause with '?' placeholders")
    values: list[Any] = Field(description="Values for '?' placeholders")


class UpdateRowInput(_TableMutationInput):
    data: dict[str, Any] = Field(description="Column-value pairs to update")
    condition: str = Field(description="WHERE clause with '?' placeholders")
    condition_values: list[Any] = Field(description="Values for '?' placeholders")


class UpsertRowInput(_TableMutationInput):
    data: dict[str, Any] = Field(description="Column-value pairs to upsert")
    conflict_target: str = Field(description="Conflict target column")


class FindRowInput(_TableMutationInput):
    column: str = Field(description="Column to filter on")
    operator: str = Field(default="=")
    value: Any = Field(default=None, description="Value to compare against")


class ExecuteQueryInput(_TableMutationInput):
    condition: str = Field(description="WHERE clause with '?' placeholders")
    values: list[Any] = Field(description="Values for '?' placeholders")


class ListSchemasInput(_AuthFields):
    pass


class ListTablesInput(_AuthFields):
    schema_name: str = Field(default="public")


class DescribeTableInput(_AuthFields):
    table: str = Field(description="Table to describe")
    schema_name: str = Field(default="public")


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
            sql_upper = sql.strip().upper()
            is_select = sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")
            if is_select:
                rows = (
                    await conn.fetch(sql, *values) if values else await conn.fetch(sql)
                )
                data = [dict(r) for r in rows]
                return ExecuteRawQueryOutput(
                    success=True, row_count=len(data), data=data
                )
            result = (
                await conn.execute(sql, *values) if values else await conn.execute(sql)
            )
            parts = str(result).split()
            affected = int(parts[-1]) if parts and parts[-1].isdigit() else 0
            return ExecuteRawQueryOutput(
                success=True, status=str(result), affected_rows=affected
            )
        finally:
            await conn.close()
    except Exception as exc:
        return ExecuteRawQueryOutput(success=False, error=str(exc))


@tool(args_schema=CreateRowInput)
@serialize_pydantic_return
async def create_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    data: dict[str, Any],
    schema_name: str = "public",
) -> CreateRowOutput:
    """INSERT one row and return the inserted record."""
    try:
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
        column_names = ", ".join(f'"{c}"' for c in columns)
        sql = (
            f'INSERT INTO "{schema_name}"."{table}" ({column_names}) '
            f"VALUES ({placeholders}) RETURNING *"
        )
        conn = await _connect(auth_data)
        try:
            rows = await conn.fetch(sql, *values)
        finally:
            await conn.close()
    except Exception as exc:
        return CreateRowOutput(success=False, error=str(exc))
    return CreateRowOutput.model_validate(
        {
            "success": True,
            "table": table,
            "schema_name": schema_name,
            "inserted_row": dict(rows[0]) if rows else None,
            "columns": columns,
        }
    )


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


@tool(args_schema=DeleteRowInput)
@serialize_pydantic_return
async def delete_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    condition: str,
    values: list[Any],
    schema_name: str = "public",
) -> DeleteRowOutput:
    """DELETE rows matching ``condition`` (returns deleted rows)."""
    err = _validate_placeholders(condition, values, "delete_row")
    if err:
        return DeleteRowOutput(success=False, error=err)
    try:
        pg_condition = _convert_placeholders(condition)
        sql = f'DELETE FROM "{schema_name}"."{table}" WHERE {pg_condition} RETURNING *'
        conn = await _connect(auth_data)
        try:
            rows = await conn.fetch(sql, *values)
        finally:
            await conn.close()
    except Exception as exc:
        return DeleteRowOutput(success=False, error=str(exc))
    deleted = [dict(r) for r in rows]
    return DeleteRowOutput.model_validate(
        {
            "success": True,
            "table": table,
            "schema_name": schema_name,
            "affected_rows": len(deleted),
            "deleted_rows": deleted,
        }
    )


@tool(args_schema=UpdateRowInput)
@serialize_pydantic_return
async def update_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    data: dict[str, Any],
    condition: str,
    condition_values: list[Any],
    schema_name: str = "public",
) -> UpdateRowOutput:
    """UPDATE rows matching ``condition`` (returns updated rows)."""
    err = _validate_placeholders(condition, condition_values, "update_row")
    if err:
        return UpdateRowOutput(success=False, error=err)
    try:
        columns = list(data.keys())
        update_values = list(data.values())
        set_clause = ", ".join(f'"{c}" = ${i + 1}' for i, c in enumerate(columns))
        # Renumber condition placeholders starting from len(columns)+1.
        offset = len(columns)
        pg_condition = condition
        for i in range(condition.count("?")):
            pg_condition = pg_condition.replace("?", f"${offset + i + 1}", 1)
        sql = (
            f'UPDATE "{schema_name}"."{table}" SET {set_clause} '
            f"WHERE {pg_condition} RETURNING *"
        )
        conn = await _connect(auth_data)
        try:
            rows = await conn.fetch(sql, *(update_values + condition_values))
        finally:
            await conn.close()
    except Exception as exc:
        return UpdateRowOutput(success=False, error=str(exc))
    updated = [dict(r) for r in rows]
    return UpdateRowOutput.model_validate(
        {
            "success": True,
            "table": table,
            "schema_name": schema_name,
            "affected_rows": len(updated),
            "updated_columns": columns,
            "updated_rows": updated,
        }
    )


@tool(args_schema=UpsertRowInput)
@serialize_pydantic_return
async def upsert_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    data: dict[str, Any],
    conflict_target: str,
    schema_name: str = "public",
) -> UpsertRowOutput:
    """INSERT … ON CONFLICT (conflict_target) DO UPDATE."""
    try:
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
        column_names = ", ".join(f'"{c}"' for c in columns)
        update_columns = [c for c in columns if c != conflict_target]
        update_clause = ", ".join(
            f'"{c}" = EXCLUDED."{c}"' for c in update_columns
        )
        sql = f"""
            INSERT INTO "{schema_name}"."{table}" ({column_names})
            VALUES ({placeholders})
            ON CONFLICT ("{conflict_target}")
            DO UPDATE SET {update_clause}
            RETURNING *
        """
        conn = await _connect(auth_data)
        try:
            rows = await conn.fetch(sql, *values)
        finally:
            await conn.close()
    except Exception as exc:
        return UpsertRowOutput(success=False, error=str(exc))
    return UpsertRowOutput.model_validate(
        {
            "success": True,
            "table": table,
            "schema_name": schema_name,
            "upserted_row": dict(rows[0]) if rows else None,
            "conflict_target": conflict_target,
        }
    )


_VALID_OPERATORS = {"=", ">", ">=", "<", "!=", "<=", "LIKE", "like", "ILIKE", "ilike"}


@tool(args_schema=FindRowInput)
@serialize_pydantic_return
async def find_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    column: str,
    operator: str = "=",
    value: Any = None,
    schema_name: str = "public",
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
        sql = (
            f'SELECT * FROM "{schema_name}"."{table}" '
            f'WHERE "{column}" {operator} $1'
        )
        conn = await _connect(auth_data)
        try:
            rows = await conn.fetch(sql, value)
        finally:
            await conn.close()
    except Exception as exc:
        return FindRowOutput(success=False, error=str(exc))
    data = [dict(r) for r in rows]
    return FindRowOutput.model_validate(
        {
            "success": True,
            "table": table,
            "schema_name": schema_name,
            "row_count": len(data),
            "data": data,
        }
    )


@tool(args_schema=ExecuteQueryInput)
@serialize_pydantic_return
async def execute_query_with_condition(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    condition: str,
    values: list[Any],
    schema_name: str = "public",
) -> ExecuteQueryWithConditionOutput:
    """SELECT * FROM table WHERE <condition>."""
    err = _validate_placeholders(condition, values, "execute_query_with_condition")
    if err:
        return ExecuteQueryWithConditionOutput(success=False, error=err)
    try:
        pg_condition = _convert_placeholders(condition)
        sql = f'SELECT * FROM "{schema_name}"."{table}" WHERE {pg_condition}'
        conn = await _connect(auth_data)
        try:
            rows = await conn.fetch(sql, *values)
        finally:
            await conn.close()
    except Exception as exc:
        return ExecuteQueryWithConditionOutput(success=False, error=str(exc))
    data = [dict(r) for r in rows]
    return ExecuteQueryWithConditionOutput.model_validate(
        {
            "success": True,
            "table": table,
            "schema_name": schema_name,
            "row_count": len(data),
            "data": data,
        }
    )


@tool(args_schema=ListSchemasInput)
@serialize_pydantic_return
async def list_schemas(
    auth_type: str, auth_data: dict[str, Any]
) -> ListSchemasOutput:
    """List all non-system schemas."""
    sql = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
          AND schema_name NOT LIKE 'pg_temp%'
          AND schema_name NOT LIKE 'pg_toast_temp%'
        ORDER BY schema_name
    """
    try:
        conn = await _connect(auth_data)
        try:
            rows = await conn.fetch(sql)
        finally:
            await conn.close()
    except Exception as exc:
        return ListSchemasOutput(success=False, error=str(exc))
    schemas = [r["schema_name"] for r in rows]
    return ListSchemasOutput(success=True, schemas=schemas, count=len(schemas))


@tool(args_schema=ListTablesInput)
@serialize_pydantic_return
async def list_tables(
    auth_type: str,
    auth_data: dict[str, Any],
    schema_name: str = "public",
) -> ListTablesOutput:
    """List all tables and views in ``schema_name``."""
    sql = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = $1
        ORDER BY table_name
    """
    try:
        conn = await _connect(auth_data)
        try:
            rows = await conn.fetch(sql, schema_name)
        finally:
            await conn.close()
    except Exception as exc:
        return ListTablesOutput(success=False, error=str(exc))
    tables = [TableEntry(name=r["table_name"], type=r["table_type"]) for r in rows]
    return ListTablesOutput.model_validate(
        {
            "success": True,
            "schema_name": schema_name,
            "tables": tables,
            "count": len(tables),
        }
    )


@tool(args_schema=DescribeTableInput)
@serialize_pydantic_return
async def describe_table(
    auth_type: str,
    auth_data: dict[str, Any],
    table: str,
    schema_name: str = "public",
) -> DescribeTableOutput:
    """Return column metadata + primary keys for ``schema_name.table``."""
    cols_sql = """
        SELECT
            column_name, data_type, character_maximum_length,
            numeric_precision, numeric_scale,
            is_nullable, column_default, udt_name
        FROM information_schema.columns
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position
    """
    pk_sql = """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = ($1 || '.' || $2)::regclass
          AND i.indisprimary
    """
    try:
        conn = await _connect(auth_data)
        try:
            col_rows = await conn.fetch(cols_sql, schema_name, table)
            try:
                pk_rows = await conn.fetch(pk_sql, schema_name, table)
            except Exception:
                pk_rows = []
        finally:
            await conn.close()
    except Exception as exc:
        return DescribeTableOutput(success=False, error=str(exc))

    columns: list[dict[str, Any]] = []
    for r in col_rows:
        col: dict[str, Any] = {
            "name": r["column_name"],
            "type": r["data_type"],
            "nullable": r["is_nullable"] == "YES",
            "default": r["column_default"],
        }
        if r["character_maximum_length"]:
            col["max_length"] = r["character_maximum_length"]
        if r["numeric_precision"]:
            col["precision"] = r["numeric_precision"]
            if r["numeric_scale"]:
                col["scale"] = r["numeric_scale"]
        if r["udt_name"] and r["udt_name"] != r["data_type"]:
            col["udt_name"] = r["udt_name"]
        columns.append(col)

    primary_keys = [r["attname"] for r in pk_rows]
    return DescribeTableOutput.model_validate(
        {
            "success": True,
            "table": table,
            "schema_name": schema_name,
            "columns": columns,
            "column_count": len(columns),
            "primary_keys": primary_keys,
        }
    )
