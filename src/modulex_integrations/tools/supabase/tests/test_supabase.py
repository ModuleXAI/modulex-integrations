"""Happy-path tests for every supabase @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.supabase import (
    TOOLS,
    batch_insert_rows,
    count_rows,
    delete_row,
    insert_row,
    manifest,
    remote_procedure_call,
    select_row,
    update_row,
    upsert_row,
)
from modulex_integrations.tools.supabase.outputs import (
    BatchInsertRowsOutput,
    CountRowsOutput,
    DeleteRowOutput,
    InsertRowOutput,
    RemoteProcedureCallOutput,
    SelectRowOutput,
    UpdateRowOutput,
    UpsertRowOutput,
)

_SUBDOMAIN = "fake-project"
_SERVICE_KEY = "fake-service-key"
API = f"https://{_SUBDOMAIN}.supabase.co/rest/v1"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(subdomain=_SUBDOMAIN, service_key=_SERVICE_KEY, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_8_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_select_row(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users?select=%2A&order=id.asc&limit=20",
        json=[
            # TODO: fill in a representative response shape from the Supabase REST API
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ],
    )

    result_dict = await select_row.ainvoke(_args(table="users", order_by="id"))

    assert isinstance(result_dict, dict)
    result = SelectRowOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_insert_row(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users",
        json=[{"id": 3, "name": "Charlie"}],
        status_code=201,
    )

    result_dict = await insert_row.ainvoke(_args(table="users", data={"name": "Charlie"}))

    assert isinstance(result_dict, dict)
    result = InsertRowOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_update_row(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/users?id=eq.1",
        json=[{"id": 1, "name": "Alice Updated"}],
    )

    result_dict = await update_row.ainvoke(
        _args(table="users", column="id", value="1", data={"name": "Alice Updated"})
    )

    assert isinstance(result_dict, dict)
    result = UpdateRowOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_upsert_row(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users",
        json=[{"id": 1, "name": "Alice Upserted"}],
        status_code=201,
    )

    result_dict = await upsert_row.ainvoke(_args(table="users", data={"id": 1, "name": "Alice Upserted"}))

    assert isinstance(result_dict, dict)
    result = UpsertRowOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_delete_row(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/users?id=eq.1",
        json=[{"id": 1, "name": "Alice"}],
    )

    result_dict = await delete_row.ainvoke(_args(table="users", column="id", value="1"))

    assert isinstance(result_dict, dict)
    result = DeleteRowOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_batch_insert_rows(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users",
        json=[
            {"id": 4, "name": "Dave"},
            {"id": 5, "name": "Eve"},
        ],
        status_code=201,
    )

    result_dict = await batch_insert_rows.ainvoke(
        _args(table="users", data=[{"name": "Dave"}, {"name": "Eve"}])
    )

    assert isinstance(result_dict, dict)
    result = BatchInsertRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_remote_procedure_call(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/rpc/get_total",
        json=42,
    )

    result_dict = await remote_procedure_call.ainvoke(
        _args(function_name="get_total", args={"category": "books"})
    )

    assert isinstance(result_dict, dict)
    result = RemoteProcedureCallOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data == 42


@pytest.mark.asyncio
async def test_count_rows(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="HEAD",
        url=f"{API}/users?select=count",
        headers={"content-range": "0-0/150"},
    )

    result_dict = await count_rows.ainvoke(_args(table="users"))

    assert isinstance(result_dict, dict)
    result = CountRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 150


# --- Failure-path tests -------------------------------------------------------


@pytest.mark.asyncio
async def test_select_row_empty_credentials() -> None:
    """Empty credentials should short-circuit without hitting the wire."""
    result_dict = await select_row.ainvoke(
        {"table": "users", "order_by": "id", "subdomain": "", "service_key": ""}
    )

    assert isinstance(result_dict, dict)
    result = SelectRowOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
