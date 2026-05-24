"""Happy-path tests for every microsoft_sql_server @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from modulex_integrations.tools.microsoft_sql_server import (
    TOOLS,
    execute_query,
    execute_raw_query,
    insert_row,
    list_table_options,
    manifest,
)
from modulex_integrations.tools.microsoft_sql_server.outputs import (
    ExecuteQueryOutput,
    ExecuteRawQueryOutput,
    InsertRowOutput,
    ListTableOptionsOutput,
)

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "host": "localhost",
        "port": "1433",
        "username": "sa",
        "password": "fake_password",
        "database": "testdb",
        "encrypt": "false",
        "trust_server_certificate": "true",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_execute_raw_query() -> None:
    mock_result = {
        "recordset": [{"id": 1, "name": "test"}],
        "rows_affected": [1],
    }
    with patch(
        "modulex_integrations.tools.microsoft_sql_server.tools._run_query",
        return_value=mock_result,
    ):
        result_dict = await execute_raw_query.ainvoke(
            _args(query="SELECT * FROM users"),
        )

    assert isinstance(result_dict, dict)
    result = ExecuteRawQueryOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.recordset) == 1
    assert result.recordset[0]["name"] == "test"


@pytest.mark.asyncio
async def test_execute_query() -> None:
    mock_result = {
        "recordset": [{"id": 1, "name": "test"}],
        "rows_affected": [1],
    }
    with patch(
        "modulex_integrations.tools.microsoft_sql_server.tools._run_query",
        return_value=mock_result,
    ):
        result_dict = await execute_query.ainvoke(
            _args(query="SELECT * FROM users WHERE id = %(id)s", inputs={"id": 1}),
        )

    assert isinstance(result_dict, dict)
    result = ExecuteQueryOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.recordset) == 1


@pytest.mark.asyncio
async def test_insert_row() -> None:
    mock_result = {
        "recordset": [],
        "rows_affected": [1],
    }
    with patch(
        "modulex_integrations.tools.microsoft_sql_server.tools._run_query",
        return_value=mock_result,
    ):
        result_dict = await insert_row.ainvoke(
            _args(table="users", data={"name": "Alice", "email": "alice@example.com"}),
        )

    assert isinstance(result_dict, dict)
    result = InsertRowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.rows_affected == [1]


@pytest.mark.asyncio
async def test_list_table_options() -> None:
    mock_result = {
        "recordset": [
            {"TABLE_NAME": "users"},
            {"TABLE_NAME": "orders"},
            {"TABLE_NAME": "products"},
        ],
        "rows_affected": [-1],
    }
    with patch(
        "modulex_integrations.tools.microsoft_sql_server.tools._run_query",
        return_value=mock_result,
    ):
        result_dict = await list_table_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTableOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.tables == ["users", "orders", "products"]


@pytest.mark.asyncio
async def test_execute_raw_query_missing_credentials() -> None:
    bad_auth: dict[str, Any] = {
        "auth_type": "custom",
        "auth_data": {"host": "", "port": "1433", "username": "", "password": "", "database": ""},
    }
    result_dict = await execute_raw_query.ainvoke(dict(bad_auth, query="SELECT 1"))
    result = ExecuteRawQueryOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Missing" in result.error
