"""Tests for the MySQL integration.

``_connect`` and ``_dict_cursor`` / ``_plain_cursor`` are mocked via
``unittest.mock.patch`` to avoid a real MySQL server. The cursor mock
is a MagicMock configured as an async context manager.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modulex_integrations.tools.mysql import (
    TOOLS,
    create_row,
    delete_row,
    describe_table,
    execute_query_with_condition,
    execute_raw_query,
    execute_stored_procedure,
    find_row,
    list_tables,
    manifest,
    update_row,
)
from modulex_integrations.tools.mysql.outputs import (
    CreateRowOutput,
    DeleteRowOutput,
    DescribeTableOutput,
    ExecuteQueryWithConditionOutput,
    ExecuteRawQueryOutput,
    ExecuteStoredProcedureOutput,
    FindRowOutput,
    ListTablesOutput,
    UpdateRowOutput,
)

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "host": "h",
        "port": 3306,
        "user": "u",
        "password": "p",
        "database": "testdb",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


def _make_cursor(
    description: Any = (("id",),),
    fetchall_return: list[Any] | None = None,
    rowcount: int = 0,
    lastrowid: int | None = None,
    nextset_returns: list[bool] | None = None,
) -> AsyncMock:
    cursor = AsyncMock()
    cursor.description = description
    cursor.rowcount = rowcount
    cursor.lastrowid = lastrowid
    cursor.execute = AsyncMock()
    cursor.fetchall = AsyncMock(return_value=fetchall_return or [])
    cursor.nextset = AsyncMock(
        side_effect=(nextset_returns or [False])
    )
    return cursor


def _cursor_ctx(cursor: AsyncMock) -> MagicMock:
    """Build an async-context-manager mock that yields ``cursor``."""
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=cursor)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


def _patch_layer(cursor: AsyncMock) -> Any:
    """Patch both the connect and cursor factory layers in one go."""
    conn = MagicMock()
    conn.close = MagicMock()
    ctx = _cursor_ctx(cursor)
    return patch.multiple(
        "modulex_integrations.tools.mysql.tools",
        _connect=AsyncMock(return_value=conn),
        _dict_cursor=MagicMock(return_value=ctx),
        _plain_cursor=MagicMock(return_value=ctx),
    )


class TestManifest:
    def test_manifest_exposes_nine_actions(self) -> None:
        assert len(manifest.actions) == 9

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["custom"]


@pytest.mark.asyncio
async def test_execute_raw_query_select() -> None:
    cursor = _make_cursor(fetchall_return=[{"id": 1}, {"id": 2}])
    with _patch_layer(cursor):
        result = ExecuteRawQueryOutput.model_validate(
            await execute_raw_query.ainvoke(_args(sql="SELECT * FROM t"))
        )
    assert result.success is True
    assert result.row_count == 2


@pytest.mark.asyncio
async def test_execute_raw_query_dml() -> None:
    cursor = _make_cursor(description=None, rowcount=3, lastrowid=42)
    with _patch_layer(cursor):
        result = ExecuteRawQueryOutput.model_validate(
            await execute_raw_query.ainvoke(_args(sql="UPDATE t SET x=1"))
        )
    assert result.success is True
    assert result.data[0]["affected_rows"] == 3
    assert result.data[0]["last_insert_id"] == 42


@pytest.mark.asyncio
async def test_execute_raw_query_connection_failure() -> None:
    with patch(
        "modulex_integrations.tools.mysql.tools._connect",
        new=AsyncMock(side_effect=RuntimeError("connection refused")),
    ):
        result = ExecuteRawQueryOutput.model_validate(
            await execute_raw_query.ainvoke(_args(sql="SELECT 1"))
        )
    assert result.success is False
    assert result.error == "connection refused"


@pytest.mark.asyncio
async def test_create_row() -> None:
    cursor = _make_cursor(rowcount=1, lastrowid=10)
    with _patch_layer(cursor):
        result = CreateRowOutput.model_validate(
            await create_row.ainvoke(
                _args(table="users", data={"name": "X"})
            )
        )
    assert result.success is True
    assert result.last_insert_id == 10


@pytest.mark.asyncio
async def test_delete_row_validates_placeholders() -> None:
    result = DeleteRowOutput.model_validate(
        await delete_row.ainvoke(
            _args(table="users", condition="id = 1", values=[])
        )
    )
    assert result.success is False
    assert result.error is not None and "?" in result.error


@pytest.mark.asyncio
async def test_delete_row_happy_path() -> None:
    cursor = _make_cursor(rowcount=2)
    with _patch_layer(cursor):
        result = DeleteRowOutput.model_validate(
            await delete_row.ainvoke(
                _args(table="users", condition="id = ?", values=[1])
            )
        )
    assert result.success is True
    assert result.affected_rows == 2


@pytest.mark.asyncio
async def test_update_row_combines_value_lists() -> None:
    cursor = _make_cursor(rowcount=1)
    with _patch_layer(cursor):
        result = UpdateRowOutput.model_validate(
            await update_row.ainvoke(
                _args(
                    table="users",
                    data={"name": "Y", "age": 30},
                    condition="id = ?",
                    condition_values=[1],
                )
            )
        )
    # Verify the cursor saw the right SQL + value list.
    call_args = cursor.execute.call_args
    sql = call_args.args[0]
    bound = call_args.args[1]
    assert "`name` = %s" in sql and "`age` = %s" in sql
    assert "WHERE id = %s" in sql
    assert bound == ["Y", 30, 1]
    assert result.success is True


@pytest.mark.asyncio
async def test_find_row_rejects_unknown_operator() -> None:
    result = FindRowOutput.model_validate(
        await find_row.ainvoke(
            _args(table="users", column="x", operator="<>", value=1)
        )
    )
    assert result.success is False
    assert result.error is not None and "Invalid operator" in result.error


@pytest.mark.asyncio
async def test_find_row_happy_path() -> None:
    cursor = _make_cursor(fetchall_return=[{"id": 1}])
    with _patch_layer(cursor):
        result = FindRowOutput.model_validate(
            await find_row.ainvoke(
                _args(table="users", column="status", value="active")
            )
        )
    assert result.success is True
    assert result.row_count == 1


@pytest.mark.asyncio
async def test_execute_query_with_condition() -> None:
    cursor = _make_cursor(fetchall_return=[{"id": 1}])
    with _patch_layer(cursor):
        result = ExecuteQueryWithConditionOutput.model_validate(
            await execute_query_with_condition.ainvoke(
                _args(
                    table="orders",
                    condition="status = ?",
                    values=["pending"],
                )
            )
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_execute_stored_procedure_with_no_results() -> None:
    cursor = _make_cursor(description=None)
    with _patch_layer(cursor):
        result = ExecuteStoredProcedureOutput.model_validate(
            await execute_stored_procedure.ainvoke(
                _args(stored_procedure="recalc", values=[2026])
            )
        )
    assert result.success is True
    assert result.data == {"executed": True}


@pytest.mark.asyncio
async def test_execute_stored_procedure_collects_multi_result_sets() -> None:
    cursor = _make_cursor(
        fetchall_return=[{"x": 1}],
        nextset_returns=[True, False],
    )
    # When nextset returns True, the same description is reused and fetchall
    # called again. fetchall_return is the *initial* value; we capture the
    # second call separately via side_effect.
    cursor.fetchall = AsyncMock(side_effect=[[{"x": 1}], [{"x": 2}]])
    with _patch_layer(cursor):
        result = ExecuteStoredProcedureOutput.model_validate(
            await execute_stored_procedure.ainvoke(
                _args(stored_procedure="multi", values=None)
            )
        )
    assert result.success is True
    assert result.row_count == 2


@pytest.mark.asyncio
async def test_list_tables() -> None:
    cursor = _make_cursor(
        fetchall_return=[
            {"Tables_in_testdb": "users", "Table_type": "BASE TABLE"},
            {"Tables_in_testdb": "active_users", "Table_type": "VIEW"},
        ]
    )
    with _patch_layer(cursor):
        result = ListTablesOutput.model_validate(
            await list_tables.ainvoke(_AUTH)
        )
    assert result.success is True
    assert result.count == 2
    assert result.tables[0].name == "users"


@pytest.mark.asyncio
async def test_describe_table() -> None:
    cursor = _make_cursor(
        fetchall_return=[
            {
                "Field": "id",
                "Type": "int(11)",
                "Null": "NO",
                "Key": "PRI",
                "Default": None,
                "Extra": "auto_increment",
            }
        ]
    )
    with _patch_layer(cursor):
        result = DescribeTableOutput.model_validate(
            await describe_table.ainvoke(_args(table="users"))
        )
    assert result.success is True
    assert result.column_count == 1
    assert result.columns[0]["name"] == "id"
