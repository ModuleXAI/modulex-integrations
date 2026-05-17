"""Tests for the Snowflake integration.

The Snowflake driver is synchronous, so tests mock the local
``_connect`` helper to return a MagicMock with a sync ``cursor()``
factory. ``cursor.execute`` / ``.fetchall`` / ``.description`` /
``.rowcount`` / ``.close`` are all configured per test.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from modulex_integrations.tools.snowflake import (
    TOOLS,
    describe_table,
    execute_sql_query,
    get_table_sample,
    insert_multiple_rows,
    insert_row,
    list_databases,
    list_schemas,
    list_tables,
    list_warehouses,
    manifest,
)
from modulex_integrations.tools.snowflake.outputs import (
    DescribeTableOutput,
    ExecuteSqlQueryOutput,
    GetTableSampleOutput,
    InsertMultipleRowsOutput,
    InsertRowOutput,
    ListDatabasesOutput,
    ListSchemasOutput,
    ListTablesOutput,
    ListWarehousesOutput,
)

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "account": "xy12345.us-east-1",
        "user": "u",
        "password": "p",
        "warehouse": "WH",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


def _make_cursor(
    description: Any = None,
    fetchall_return: list[Any] | None = None,
    rowcount: int = 0,
) -> MagicMock:
    cursor = MagicMock()
    cursor.description = description if description is not None else [("ID",), ("NAME",)]
    cursor.rowcount = rowcount
    cursor.execute = MagicMock()
    cursor.fetchall = MagicMock(return_value=fetchall_return or [])
    cursor.close = MagicMock()
    return cursor


def _patch_connect(cursor: MagicMock) -> Any:
    conn = MagicMock()
    conn.cursor = MagicMock(return_value=cursor)
    conn.close = MagicMock()
    return patch(
        "modulex_integrations.tools.snowflake.tools._connect",
        return_value=conn,
    )


class TestManifest:
    def test_manifest_exposes_nine_actions(self) -> None:
        assert len(manifest.actions) == 9

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["custom"]


@pytest.mark.asyncio
async def test_execute_sql_query() -> None:
    cursor = _make_cursor(
        description=[("ID",), ("NAME",)],
        fetchall_return=[(1, "Alice"), (2, "Bob")],
    )
    with _patch_connect(cursor):
        result = ExecuteSqlQueryOutput.model_validate(
            await execute_sql_query.ainvoke(_args(query="SELECT * FROM users"))
        )
    assert result.success is True
    assert result.row_count == 2
    assert result.data == [
        {"ID": 1, "NAME": "Alice"},
        {"ID": 2, "NAME": "Bob"},
    ]


@pytest.mark.asyncio
async def test_execute_sql_query_failure() -> None:
    with patch(
        "modulex_integrations.tools.snowflake.tools._connect",
        side_effect=RuntimeError("connection refused"),
    ):
        result = ExecuteSqlQueryOutput.model_validate(
            await execute_sql_query.ainvoke(_args(query="SELECT 1"))
        )
    assert result.success is False
    assert result.error == "connection refused"


@pytest.mark.asyncio
async def test_insert_row() -> None:
    cursor = _make_cursor(rowcount=1)
    with _patch_connect(cursor):
        result = InsertRowOutput.model_validate(
            await insert_row.ainvoke(
                _args(table_name="DB.SCH.USERS", values={"NAME": "A"})
            )
        )
    assert result.success is True
    assert result.rows_inserted == 1
    sql = cursor.execute.call_args.args[0]
    assert "INSERT INTO DB.SCH.USERS (NAME) VALUES (%s)" in sql


@pytest.mark.asyncio
async def test_insert_multiple_rows_validates_empty() -> None:
    result = InsertMultipleRowsOutput.model_validate(
        await insert_multiple_rows.ainvoke(
            _args(table_name="t", columns=["c"], values=[])
        )
    )
    assert result.success is False
    assert result.error is not None and "No values" in result.error


@pytest.mark.asyncio
async def test_insert_multiple_rows_validates_row_widths() -> None:
    result = InsertMultipleRowsOutput.model_validate(
        await insert_multiple_rows.ainvoke(
            _args(
                table_name="t",
                columns=["a", "b"],
                values=[[1, 2], [3]],
            )
        )
    )
    assert result.success is False
    assert result.error is not None and "Row 2" in result.error


@pytest.mark.asyncio
async def test_insert_multiple_rows_batching() -> None:
    cursor = _make_cursor(rowcount=5)
    rows = [[i, f"n{i}"] for i in range(15)]
    with _patch_connect(cursor):
        result = InsertMultipleRowsOutput.model_validate(
            await insert_multiple_rows.ainvoke(
                _args(
                    table_name="t",
                    columns=["a", "b"],
                    values=rows,
                    batch_size=10,
                )
            )
        )
    assert result.success is True
    assert result.total_rows == 15
    assert result.total_batches == 2
    assert result.batch_size == 10


@pytest.mark.asyncio
async def test_list_databases() -> None:
    cursor = _make_cursor(
        description=[("name",), ("owner",), ("created_on",), ("comment",)],
        fetchall_return=[("DB1", "OWN", None, "main")],
    )
    with _patch_connect(cursor):
        result = ListDatabasesOutput.model_validate(
            await list_databases.ainvoke(_AUTH)
        )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_list_schemas() -> None:
    cursor = _make_cursor(
        description=[("name",), ("database_name",), ("owner",), ("created_on",), ("comment",)],
        fetchall_return=[("PUBLIC", "DB1", "OWN", None, None)],
    )
    with _patch_connect(cursor):
        result = ListSchemasOutput.model_validate(
            await list_schemas.ainvoke(_args(database="DB1"))
        )
    assert result.success is True
    assert result.count == 1
    assert result.database == "DB1"


@pytest.mark.asyncio
async def test_list_tables() -> None:
    cursor = _make_cursor(
        description=[
            ("name",), ("database_name",), ("schema_name",), ("kind",),
            ("owner",), ("rows",), ("created_on",), ("comment",),
        ],
        fetchall_return=[("USERS", "DB1", "PUBLIC", "TABLE", "OWN", 100, None, None)],
    )
    with _patch_connect(cursor):
        result = ListTablesOutput.model_validate(
            await list_tables.ainvoke(
                _args(database="DB1", schema_name="PUBLIC")
            )
        )
    assert result.success is True
    assert result.count == 1
    assert result.tables[0].rows == 100


@pytest.mark.asyncio
async def test_list_warehouses() -> None:
    cursor = _make_cursor(
        description=[
            ("name",), ("state",), ("size",), ("type",),
            ("owner",), ("auto_suspend",), ("auto_resume",),
            ("created_on",), ("comment",),
        ],
        fetchall_return=[("WH", "STARTED", "X-Small", "STANDARD", "OWN", 600, "true", None, None)],
    )
    with _patch_connect(cursor):
        result = ListWarehousesOutput.model_validate(
            await list_warehouses.ainvoke(_AUTH)
        )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_describe_table() -> None:
    cursor = _make_cursor(
        description=[
            ("name",), ("type",), ("kind",), ("null?",),
            ("default",), ("primary key",), ("unique key",), ("comment",),
        ],
        fetchall_return=[
            ("ID", "NUMBER(38,0)", "COLUMN", "N", None, "Y", "N", None),
        ],
    )
    with _patch_connect(cursor):
        result = DescribeTableOutput.model_validate(
            await describe_table.ainvoke(_args(table_name="DB.SCH.USERS"))
        )
    assert result.success is True
    assert result.column_count == 1
    assert result.columns[0]["primary_key"] == "Y"


@pytest.mark.asyncio
async def test_get_table_sample_clamps_limit() -> None:
    cursor = _make_cursor(
        description=[("ID",)], fetchall_return=[(1,), (2,)]
    )
    with _patch_connect(cursor):
        result = GetTableSampleOutput.model_validate(
            await get_table_sample.ainvoke(
                _args(table_name="t", limit=5000)
            )
        )
    assert result.success is True
    # 5000 should be clamped to 1000
    sql = cursor.execute.call_args.args[0]
    assert "LIMIT 1000" in sql
