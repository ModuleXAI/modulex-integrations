"""Tests for the PostgreSQL integration.

Database integration: ``asyncpg.connect`` is mocked via
``unittest.mock.patch`` on the local ``_connect`` helper. The mock
returns an AsyncMock with ``.fetch`` / ``.execute`` / ``.close``
configured per test.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from modulex_integrations.tools.postgresql import (
    TOOLS,
    create_row,
    delete_row,
    describe_table,
    execute_query_with_condition,
    execute_raw_query,
    find_row,
    list_schemas,
    list_tables,
    manifest,
    update_row,
    upsert_row,
)
from modulex_integrations.tools.postgresql.outputs import (
    CreateRowOutput,
    DeleteRowOutput,
    DescribeTableOutput,
    ExecuteQueryWithConditionOutput,
    ExecuteRawQueryOutput,
    FindRowOutput,
    ListSchemasOutput,
    ListTablesOutput,
    UpdateRowOutput,
    UpsertRowOutput,
)
from modulex_integrations.tools.postgresql.tools import _convert_placeholders

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "host": "h",
        "port": 5432,
        "user": "u",
        "password": "p",
        "database": "d",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


def _patched(conn: AsyncMock) -> Any:
    return patch(
        "modulex_integrations.tools.postgresql.tools._connect",
        new=AsyncMock(return_value=conn),
    )


def _mock_conn(
    fetch_return: Any = None, execute_return: Any = None
) -> AsyncMock:
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=fetch_return or [])
    conn.execute = AsyncMock(return_value=execute_return or "")
    conn.close = AsyncMock()
    return conn


class TestManifest:
    def test_manifest_exposes_ten_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["custom"]


def test_convert_placeholders_renumbers_sequentially() -> None:
    assert _convert_placeholders("a = ? AND b = ?") == "a = $1 AND b = $2"


@pytest.mark.asyncio
async def test_execute_raw_query_select() -> None:
    conn = _mock_conn(fetch_return=[{"x": 1}, {"x": 2}])
    with _patched(conn):
        result = ExecuteRawQueryOutput.model_validate(
            await execute_raw_query.ainvoke(_args(sql="SELECT * FROM t"))
        )
    assert result.success is True
    assert result.row_count == 2
    assert result.data == [{"x": 1}, {"x": 2}]


@pytest.mark.asyncio
async def test_execute_raw_query_update_command() -> None:
    conn = _mock_conn(execute_return="UPDATE 3")
    with _patched(conn):
        result = ExecuteRawQueryOutput.model_validate(
            await execute_raw_query.ainvoke(
                _args(sql="UPDATE t SET x=1", values=[])
            )
        )
    assert result.success is True
    assert result.affected_rows == 3
    assert result.status == "UPDATE 3"


@pytest.mark.asyncio
async def test_execute_raw_query_failure_surfaces() -> None:
    with patch(
        "modulex_integrations.tools.postgresql.tools._connect",
        new=AsyncMock(side_effect=RuntimeError("connection refused")),
    ):
        result = ExecuteRawQueryOutput.model_validate(
            await execute_raw_query.ainvoke(_args(sql="SELECT 1"))
        )
    assert result.success is False
    assert result.error == "connection refused"


@pytest.mark.asyncio
async def test_create_row() -> None:
    conn = _mock_conn(fetch_return=[{"id": 1, "name": "X"}])
    with _patched(conn):
        result = CreateRowOutput.model_validate(
            await create_row.ainvoke(
                _args(table="users", data={"name": "X"})
            )
        )
    assert result.success is True
    assert result.inserted_row == {"id": 1, "name": "X"}


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
    conn = _mock_conn(fetch_return=[{"id": 1}])
    with _patched(conn):
        result = DeleteRowOutput.model_validate(
            await delete_row.ainvoke(
                _args(table="users", condition="id = ?", values=[1])
            )
        )
    assert result.success is True
    assert result.affected_rows == 1


@pytest.mark.asyncio
async def test_update_row_renumbers_condition_placeholders() -> None:
    conn = _mock_conn(fetch_return=[{"id": 1, "name": "Y"}])
    with _patched(conn):
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
    # First fetch call captures the SQL; placeholders should be $1, $2 for SET
    # values and $3 for the condition.
    call_args = conn.fetch.call_args
    sql = call_args.args[0]
    assert '"name" = $1' in sql and '"age" = $2' in sql
    assert "WHERE id = $3" in sql
    assert call_args.args[1:] == ("Y", 30, 1)
    assert result.success is True
    assert result.affected_rows == 1


@pytest.mark.asyncio
async def test_upsert_row_excludes_conflict_target_from_update_set() -> None:
    conn = _mock_conn(fetch_return=[{"id": 1, "name": "X"}])
    with _patched(conn):
        result = UpsertRowOutput.model_validate(
            await upsert_row.ainvoke(
                _args(
                    table="users",
                    data={"id": 1, "name": "X"},
                    conflict_target="id",
                )
            )
        )
    sql = conn.fetch.call_args.args[0]
    assert 'ON CONFLICT ("id")' in sql
    # The conflict_target "id" must NOT appear in the DO UPDATE SET clause.
    assert '"id" = EXCLUDED."id"' not in sql
    assert '"name" = EXCLUDED."name"' in sql
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
    conn = _mock_conn(fetch_return=[{"id": 1}])
    with _patched(conn):
        result = FindRowOutput.model_validate(
            await find_row.ainvoke(
                _args(table="users", column="status", value="active")
            )
        )
    assert result.success is True
    assert result.row_count == 1


@pytest.mark.asyncio
async def test_execute_query_with_condition() -> None:
    conn = _mock_conn(fetch_return=[{"id": 1}, {"id": 2}])
    with _patched(conn):
        result = ExecuteQueryWithConditionOutput.model_validate(
            await execute_query_with_condition.ainvoke(
                _args(
                    table="orders",
                    condition="status = ? AND total > ?",
                    values=["pending", 100],
                )
            )
        )
    assert result.success is True
    assert result.row_count == 2


@pytest.mark.asyncio
async def test_list_schemas() -> None:
    conn = _mock_conn(
        fetch_return=[{"schema_name": "public"}, {"schema_name": "analytics"}]
    )
    with _patched(conn):
        result = ListSchemasOutput.model_validate(
            await list_schemas.ainvoke(_AUTH)
        )
    assert result.success is True
    assert result.count == 2


@pytest.mark.asyncio
async def test_list_tables() -> None:
    conn = _mock_conn(
        fetch_return=[
            {"table_name": "users", "table_type": "BASE TABLE"},
            {"table_name": "active_users", "table_type": "VIEW"},
        ]
    )
    with _patched(conn):
        result = ListTablesOutput.model_validate(
            await list_tables.ainvoke(_AUTH)
        )
    assert result.success is True
    assert result.count == 2


@pytest.mark.asyncio
async def test_describe_table() -> None:
    conn = AsyncMock()
    conn.close = AsyncMock()
    conn.fetch = AsyncMock(
        side_effect=[
            # columns
            [
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "character_maximum_length": None,
                    "numeric_precision": 32,
                    "numeric_scale": None,
                    "is_nullable": "NO",
                    "column_default": None,
                    "udt_name": "int4",
                },
                {
                    "column_name": "name",
                    "data_type": "character varying",
                    "character_maximum_length": 255,
                    "numeric_precision": None,
                    "numeric_scale": None,
                    "is_nullable": "YES",
                    "column_default": None,
                    "udt_name": "varchar",
                },
            ],
            # primary keys
            [{"attname": "id"}],
        ]
    )
    with _patched(conn):
        result = DescribeTableOutput.model_validate(
            await describe_table.ainvoke(_args(table="users"))
        )
    assert result.success is True
    assert result.column_count == 2
    assert result.primary_keys == ["id"]
    # Confirm character_varying column got max_length annotation.
    name_col = next(c for c in result.columns if c["name"] == "name")
    assert name_col["max_length"] == 255
