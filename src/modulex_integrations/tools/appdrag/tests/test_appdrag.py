"""Tests for the AppDrag integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.appdrag import (
    TOOLS,
    execute_api_function,
    insert_row,
    manifest,
    update_row,
)
from modulex_integrations.tools.appdrag.outputs import (
    ExecuteApiFunctionOutput,
    InsertRowOutput,
    UpdateRowOutput,
)

BACKEND = "https://api.appdrag.com/CloudBackend.aspx"
FUNCTION_HOST = "https://my-app.appdrag.site"

_API_KEY = "appdrag-fake-key"
_APP_ID = "my-app"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, app_id=_APP_ID, **extra)


class TestManifest:
    def test_manifest_exposes_three_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]

    def test_auth_has_two_env_vars(self) -> None:
        auth = manifest.auth_schemas[0]
        assert [e.name for e in auth.setup_environment_variables] == [
            "APPDRAG_API_KEY",
            "APPDRAG_APP_ID",
        ]


@pytest.mark.asyncio
async def test_execute_api_function_get(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{FUNCTION_HOST}/api/get-user?APIKey={_API_KEY}&appID={_APP_ID}&id=42",
        json={"status": "ok", "payload": {"id": 42, "name": "Ada"}},
    )

    result_dict = await execute_api_function.ainvoke(
        _args(path="/get-user", method="GET", data={"id": "42"})
    )
    assert isinstance(result_dict, dict)
    result = ExecuteApiFunctionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.path == "/get-user"
    assert result.method == "GET"
    assert isinstance(result.response, dict)
    assert result.response["payload"]["name"] == "Ada"


@pytest.mark.asyncio
async def test_execute_api_function_post(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{FUNCTION_HOST}/api/insert-user",
        json={"status": "ok", "lastInsertId": 99},
    )

    result_dict = await execute_api_function.ainvoke(
        _args(path="/insert-user", method="POST", data={"name": "Ada"})
    )
    result = ExecuteApiFunctionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.method == "POST"


@pytest.mark.asyncio
async def test_execute_api_function_rejects_bad_method() -> None:
    result_dict = await execute_api_function.ainvoke(
        _args(path="/x", method="OPTIONS")
    )
    result = ExecuteApiFunctionOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "Invalid HTTP method" in result.error


@pytest.mark.asyncio
async def test_execute_api_function_4xx(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{FUNCTION_HOST}/api/missing",
        status_code=404,
        text="not found",
    )
    result_dict = await execute_api_function.ainvoke(
        _args(path="/missing", method="POST")
    )
    result = ExecuteApiFunctionOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "404" in result.error


@pytest.mark.asyncio
async def test_insert_row(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=BACKEND,
        json={"affectedRows": 1, "lastInsertId": 7},
    )

    result_dict = await insert_row.ainvoke(
        _args(table="users", columns=["name", "email"], values=["Ada", "a@x.io"])
    )
    result = InsertRowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.affected_rows == 1
    assert result.columns == ["name", "email"]


@pytest.mark.asyncio
async def test_insert_row_zero_rows(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=BACKEND,
        json={"affectedRows": 0},
    )
    result_dict = await insert_row.ainvoke(
        _args(table="users", columns=["name"], values=["Ada"])
    )
    result = InsertRowOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "no rows affected" in result.error


@pytest.mark.asyncio
async def test_insert_row_validates_column_value_count() -> None:
    result_dict = await insert_row.ainvoke(
        _args(table="users", columns=["a", "b"], values=["1"])
    )
    result = InsertRowOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "must match" in result.error


@pytest.mark.asyncio
async def test_update_row(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=BACKEND,
        json={"affectedRows": 2},
    )

    result_dict = await update_row.ainvoke(
        _args(
            table="users",
            columns_to_update=["status"],
            values=["active"],
            where_condition="created_at < ?",
            where_values=["2026-01-01"],
        )
    )
    result = UpdateRowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.affected_rows == 2
    assert result.columns_updated == ["status"]


@pytest.mark.asyncio
async def test_update_row_placeholder_mismatch() -> None:
    result_dict = await update_row.ainvoke(
        _args(
            table="users",
            columns_to_update=["status"],
            values=["active"],
            where_condition="id = ? AND email = ?",
            where_values=["1"],
        )
    )
    result = UpdateRowOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "placeholders" in result.error


@pytest.mark.asyncio
async def test_update_row_requires_where() -> None:
    result_dict = await update_row.ainvoke(
        _args(
            table="users",
            columns_to_update=["status"],
            values=["active"],
            where_condition="   ",
            where_values=[],
        )
    )
    result = UpdateRowOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "WHERE" in result.error


@pytest.mark.asyncio
async def test_empty_credentials_short_circuit() -> None:
    no_key = await insert_row.ainvoke(
        {
            "api_key": "",
            "app_id": _APP_ID,
            "table": "users",
            "columns": ["a"],
            "values": ["1"],
        }
    )
    no_key_result = InsertRowOutput.model_validate(no_key)
    assert no_key_result.success is False
    assert no_key_result.error is not None and "API key" in no_key_result.error

    no_app = await insert_row.ainvoke(
        {
            "api_key": _API_KEY,
            "app_id": "",
            "table": "users",
            "columns": ["a"],
            "values": ["1"],
        }
    )
    no_app_result = InsertRowOutput.model_validate(no_app)
    assert no_app_result.success is False
    assert no_app_result.error is not None and "App ID" in no_app_result.error
