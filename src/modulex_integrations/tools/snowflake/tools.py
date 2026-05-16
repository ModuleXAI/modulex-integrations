"""Snowflake LangChain ``@tool`` functions.

Wraps the **synchronous** ``snowflake.connector`` SDK inside async
tool functions. The driver itself is sync — calls block the event
loop, which matches legacy behavior. We preserve rather than improve.

Connection helper is imported lazily so the manifest can be inspected
without the `snowflake-connector-python` package installed.

Token-based runtime convention (``auth_type, auth_data`` first args).
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.snowflake.outputs import (
    BatchResult,
    DatabaseEntry,
    DescribeTableOutput,
    ExecuteSqlQueryOutput,
    GetTableSampleOutput,
    InsertMultipleRowsOutput,
    InsertRowOutput,
    ListDatabasesOutput,
    ListSchemasOutput,
    ListTablesOutput,
    ListWarehousesOutput,
    SchemaEntry,
    TableEntry,
    WarehouseEntry,
)

__all__ = [
    "describe_table",
    "execute_sql_query",
    "get_table_sample",
    "insert_multiple_rows",
    "insert_row",
    "list_databases",
    "list_schemas",
    "list_tables",
    "list_warehouses",
]


def _connect(auth_data: dict[str, Any]) -> Any:
    """Open a Snowflake connection (synchronous driver)."""
    import snowflake.connector

    params: dict[str, Any] = {
        "account": auth_data.get("account"),
        "user": auth_data.get("user"),
        "password": auth_data.get("password"),
        "warehouse": auth_data.get("warehouse"),
        "application": "MODULEX_INTEGRATION",
    }
    for key in ("database", "schema", "role"):
        value = auth_data.get(key)
        if value:
            params[key] = value
    return snowflake.connector.connect(**params)


def _exec_query(
    conn: Any, sql: str, binds: list[Any] | None = None
) -> list[dict[str, Any]]:
    cursor = conn.cursor()
    try:
        if binds:
            cursor.execute(sql, binds)
        else:
            cursor.execute(sql)
        columns = (
            [desc[0] for desc in cursor.description] if cursor.description else []
        )
        rows = cursor.fetchall()
        return [dict(zip(columns, row, strict=False)) for row in rows]
    finally:
        cursor.close()


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (custom)")
    auth_data: dict[str, Any] = Field(
        description="account/user/password/warehouse[/database/schema/role]"
    )


class ExecuteSqlQueryInput(_AuthFields):
    query: str = Field(description="The SQL query to execute")
    binds: list[Any] | None = Field(default=None, description="Bind parameters")


class InsertRowInput(_AuthFields):
    table_name: str = Field(description="Target table (qualified or bare)")
    values: dict[str, Any] = Field(description="Column-value pairs to insert")


class InsertMultipleRowsInput(_AuthFields):
    table_name: str = Field(description="Target table")
    columns: list[str] = Field(description="Column names")
    values: list[list[Any]] = Field(description="Rows of values matching columns")
    batch_size: int = Field(default=100, description="Rows per batch (10-1000)")


class ListDatabasesInput(_AuthFields):
    pass


class ListSchemasInput(_AuthFields):
    database: str = Field(description="Database name")


class ListTablesInput(_AuthFields):
    database: str = Field(description="Database name")
    schema_name: str = Field(description="Schema name")


class ListWarehousesInput(_AuthFields):
    pass


class DescribeTableInput(_AuthFields):
    table_name: str = Field(description="Table to describe")


class GetTableSampleInput(_AuthFields):
    table_name: str = Field(description="Table to sample")
    limit: int = Field(default=10, description="Rows to return (1-1000)")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=ExecuteSqlQueryInput)
@serialize_pydantic_return
async def execute_sql_query(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    binds: list[Any] | None = None,
) -> ExecuteSqlQueryOutput:
    """Execute any SQL statement."""
    try:
        conn = _connect(auth_data)
        try:
            rows = _exec_query(conn, query, binds)
        finally:
            conn.close()
    except Exception as exc:
        return ExecuteSqlQueryOutput(success=False, error=str(exc))
    return ExecuteSqlQueryOutput(success=True, row_count=len(rows), data=rows)


@tool(args_schema=InsertRowInput)
@serialize_pydantic_return
async def insert_row(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    values: dict[str, Any],
) -> InsertRowOutput:
    """INSERT a single row from a column→value mapping."""
    try:
        columns = list(values.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        binds = list(values.values())

        conn = _connect(auth_data)
        try:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, binds)
                affected = cursor.rowcount
            finally:
                cursor.close()
        finally:
            conn.close()
    except Exception as exc:
        return InsertRowOutput(success=False, error=str(exc))
    return InsertRowOutput(
        success=True, table=table_name, rows_inserted=affected, columns=columns
    )


@tool(args_schema=InsertMultipleRowsInput)
@serialize_pydantic_return
async def insert_multiple_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    columns: list[str],
    values: list[list[Any]],
    batch_size: int = 100,
) -> InsertMultipleRowsOutput:
    """Batched INSERT for multiple rows."""
    if not values:
        return InsertMultipleRowsOutput(
            success=False, error="No values provided to insert"
        )
    for i, row in enumerate(values):
        if len(row) != len(columns):
            return InsertMultipleRowsOutput(
                success=False,
                error=(
                    f"Row {i + 1} has {len(row)} values but "
                    f"{len(columns)} columns specified"
                ),
            )

    batch_size = max(10, min(batch_size, 1000))
    batches = [values[i : i + batch_size] for i in range(0, len(values), batch_size)]

    total_inserted = 0
    batch_results: list[BatchResult] = []
    failed_batches = 0

    try:
        conn = _connect(auth_data)
        try:
            for idx, batch in enumerate(batches):
                row_ph = f"({', '.join(['%s'] * len(columns))})"
                all_ph = ", ".join([row_ph] * len(batch))
                sql = (
                    f"INSERT INTO {table_name} "
                    f"({', '.join(columns)}) VALUES {all_ph}"
                )
                flat = [val for row in batch for val in row]
                try:
                    cursor = conn.cursor()
                    try:
                        cursor.execute(sql, flat)
                        total_inserted += cursor.rowcount
                        batch_results.append(
                            BatchResult(
                                batch_index=idx + 1,
                                rows_processed=len(batch),
                                success=True,
                            )
                        )
                    finally:
                        cursor.close()
                except Exception as batch_exc:
                    failed_batches += 1
                    batch_results.append(
                        BatchResult(
                            batch_index=idx + 1,
                            rows_processed=0,
                            success=False,
                            error=str(batch_exc),
                        )
                    )
        finally:
            conn.close()
    except Exception as exc:
        return InsertMultipleRowsOutput(success=False, error=str(exc))

    if failed_batches == len(batches):
        return InsertMultipleRowsOutput(
            success=False,
            error=f"All {len(batches)} batches failed",
            batch_results=batch_results,
        )
    return InsertMultipleRowsOutput(
        success=True,
        table=table_name,
        total_rows=len(values),
        rows_inserted=total_inserted,
        total_batches=len(batches),
        successful_batches=len(batches) - failed_batches,
        failed_batches=failed_batches,
        batch_size=batch_size,
        batch_results=batch_results,
    )


def _opt_str(value: Any) -> str | None:
    return str(value) if value is not None else None


@tool(args_schema=ListDatabasesInput)
@serialize_pydantic_return
async def list_databases(
    auth_type: str, auth_data: dict[str, Any]
) -> ListDatabasesOutput:
    """SHOW DATABASES — all accessible databases."""
    try:
        conn = _connect(auth_data)
        try:
            rows = _exec_query(conn, "SHOW DATABASES")
        finally:
            conn.close()
    except Exception as exc:
        return ListDatabasesOutput(success=False, error=str(exc))
    databases = [
        DatabaseEntry(
            name=r.get("name"),
            owner=r.get("owner"),
            created_on=_opt_str(r.get("created_on")),
            comment=r.get("comment"),
        )
        for r in rows
    ]
    return ListDatabasesOutput(success=True, databases=databases, count=len(databases))


@tool(args_schema=ListSchemasInput)
@serialize_pydantic_return
async def list_schemas(
    auth_type: str, auth_data: dict[str, Any], database: str
) -> ListSchemasOutput:
    """SHOW SCHEMAS IN DATABASE <database>."""
    try:
        conn = _connect(auth_data)
        try:
            rows = _exec_query(conn, f"SHOW SCHEMAS IN DATABASE {database}")
        finally:
            conn.close()
    except Exception as exc:
        return ListSchemasOutput(success=False, error=str(exc))
    schemas = [
        SchemaEntry(
            name=r.get("name"),
            database_name=r.get("database_name"),
            owner=r.get("owner"),
            created_on=_opt_str(r.get("created_on")),
            comment=r.get("comment"),
        )
        for r in rows
    ]
    return ListSchemasOutput(
        success=True, database=database, schemas=schemas, count=len(schemas)
    )


@tool(args_schema=ListTablesInput)
@serialize_pydantic_return
async def list_tables(
    auth_type: str,
    auth_data: dict[str, Any],
    database: str,
    schema_name: str,
) -> ListTablesOutput:
    """SHOW TABLES IN SCHEMA <database>.<schema>."""
    try:
        conn = _connect(auth_data)
        try:
            rows = _exec_query(
                conn, f"SHOW TABLES IN SCHEMA {database}.{schema_name}"
            )
        finally:
            conn.close()
    except Exception as exc:
        return ListTablesOutput(success=False, error=str(exc))
    tables = [
        TableEntry(
            name=r.get("name"),
            database_name=r.get("database_name"),
            schema_name=r.get("schema_name"),
            kind=r.get("kind"),
            owner=r.get("owner"),
            rows=r.get("rows"),
            created_on=_opt_str(r.get("created_on")),
            comment=r.get("comment"),
        )
        for r in rows
    ]
    return ListTablesOutput(
        success=True,
        database=database,
        schema_name=schema_name,
        tables=tables,
        count=len(tables),
    )


@tool(args_schema=ListWarehousesInput)
@serialize_pydantic_return
async def list_warehouses(
    auth_type: str, auth_data: dict[str, Any]
) -> ListWarehousesOutput:
    """SHOW WAREHOUSES — compute resources."""
    try:
        conn = _connect(auth_data)
        try:
            rows = _exec_query(conn, "SHOW WAREHOUSES")
        finally:
            conn.close()
    except Exception as exc:
        return ListWarehousesOutput(success=False, error=str(exc))
    warehouses = [
        WarehouseEntry(
            name=r.get("name"),
            state=r.get("state"),
            size=r.get("size"),
            type=r.get("type"),
            owner=r.get("owner"),
            auto_suspend=r.get("auto_suspend"),
            auto_resume=r.get("auto_resume"),
            created_on=_opt_str(r.get("created_on")),
            comment=r.get("comment"),
        )
        for r in rows
    ]
    return ListWarehousesOutput(
        success=True, warehouses=warehouses, count=len(warehouses)
    )


@tool(args_schema=DescribeTableInput)
@serialize_pydantic_return
async def describe_table(
    auth_type: str, auth_data: dict[str, Any], table_name: str
) -> DescribeTableOutput:
    """DESCRIBE TABLE — column metadata."""
    try:
        conn = _connect(auth_data)
        try:
            rows = _exec_query(conn, f"DESCRIBE TABLE {table_name}")
        finally:
            conn.close()
    except Exception as exc:
        return DescribeTableOutput(success=False, error=str(exc))
    columns = [
        {
            "name": r.get("name"),
            "type": r.get("type"),
            "kind": r.get("kind"),
            "null": r.get("null?"),
            "default": r.get("default"),
            "primary_key": r.get("primary key"),
            "unique_key": r.get("unique key"),
            "comment": r.get("comment"),
        }
        for r in rows
    ]
    return DescribeTableOutput(
        success=True, table=table_name, columns=columns, column_count=len(columns)
    )


@tool(args_schema=GetTableSampleInput)
@serialize_pydantic_return
async def get_table_sample(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    limit: int = 10,
) -> GetTableSampleOutput:
    """SELECT * FROM table LIMIT N — preview data."""
    limit = max(1, min(limit, 1000))
    try:
        conn = _connect(auth_data)
        try:
            rows = _exec_query(conn, f"SELECT * FROM {table_name} LIMIT {limit}")
        finally:
            conn.close()
    except Exception as exc:
        return GetTableSampleOutput(success=False, error=str(exc))
    return GetTableSampleOutput(
        success=True, table=table_name, row_count=len(rows), data=rows
    )
