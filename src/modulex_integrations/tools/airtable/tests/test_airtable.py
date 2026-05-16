"""Tests for the Airtable integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.airtable import (
    TOOLS,
    create_records,
    delete_records,
    get_record,
    list_bases,
    list_records,
    list_tables,
    manifest,
    update_records,
)
from modulex_integrations.tools.airtable.outputs import (
    CreateRecordsOutput,
    DeleteRecordsOutput,
    GetRecordOutput,
    ListBasesOutput,
    ListRecordsOutput,
    ListTablesOutput,
    UpdateRecordsOutput,
)

API = "https://api.airtable.com/v0"
_API_KEY = "patFAKE.token"
_BASE = "appXYZ123"
_TABLE = "Tasks"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_seven_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_list_bases(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meta/bases",
        json={
            "bases": [
                {"id": _BASE, "name": "My Base", "permissionLevel": "create"},
            ]
        },
    )
    result_dict = await list_bases.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListBasesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.bases[0]["id"] == _BASE


@pytest.mark.asyncio
async def test_list_tables(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meta/bases/{_BASE}/tables",
        json={
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Tasks",
                    "primaryFieldId": "fld0",
                    "description": "Task tracker",
                    "fields": [
                        {"id": "fld0", "name": "Title", "type": "singleLineText"}
                    ],
                    "views": [{"id": "vw1", "name": "Grid", "type": "grid"}],
                }
            ]
        },
    )
    result = ListTablesOutput.model_validate(
        await list_tables.ainvoke(_args(base_id=_BASE))
    )
    assert result.success is True
    assert result.tables[0]["name"] == "Tasks"
    assert result.tables[0]["fields"][0]["name"] == "Title"


@pytest.mark.asyncio
async def test_list_records(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/{_BASE}/{_TABLE}?maxRecords=10&filterByFormula=%7BStatus%7D%3D%27Active%27",
        json={
            "records": [
                {
                    "id": "rec1",
                    "fields": {"Status": "Active"},
                    "createdTime": "2026-01-01T00:00:00Z",
                },
                {
                    "id": "rec2",
                    "fields": {"Status": "Active"},
                    "createdTime": "2026-02-01T00:00:00Z",
                },
            ]
        },
    )
    result = ListRecordsOutput.model_validate(
        await list_records.ainvoke(
            _args(
                base_id=_BASE,
                table_name=_TABLE,
                max_records=10,
                filter_formula="{Status}='Active'",
            )
        )
    )
    assert result.success is True
    assert result.count == 2
    assert result.records[0].id == "rec1"


@pytest.mark.asyncio
async def test_get_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/{_BASE}/{_TABLE}/rec1",
        json={
            "id": "rec1",
            "fields": {"Title": "Buy milk"},
            "createdTime": "2026-01-01T00:00:00Z",
        },
    )
    result = GetRecordOutput.model_validate(
        await get_record.ainvoke(_args(base_id=_BASE, table_name=_TABLE, record_id="rec1"))
    )
    assert result.success is True
    assert result.record is not None
    assert result.record.fields["Title"] == "Buy milk"


@pytest.mark.asyncio
async def test_get_record_404(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/{_BASE}/{_TABLE}/missing",
        status_code=404,
        text="not found",
    )
    result = GetRecordOutput.model_validate(
        await get_record.ainvoke(
            _args(base_id=_BASE, table_name=_TABLE, record_id="missing")
        )
    )
    assert result.success is False
    assert result.error is not None and "missing" in result.error


@pytest.mark.asyncio
async def test_create_records_batches(httpx_mock: Any) -> None:
    # 12 records → 2 batches (10 then 2).
    inputs = [{"Title": f"Task {i}"} for i in range(12)]
    captured_bodies: list[dict[str, Any]] = []

    def _capture(request: Any) -> Any:
        import json
        captured_bodies.append(json.loads(request.content.decode()))
        # echo back records with synthetic IDs
        batch_size = len(captured_bodies[-1]["records"])
        idx = sum(len(b["records"]) for b in captured_bodies[:-1])
        from httpx import Response
        return Response(
            201,
            json={
                "records": [
                    {
                        "id": f"rec{idx + j}",
                        "fields": captured_bodies[-1]["records"][j]["fields"],
                        "createdTime": "2026-05-16T00:00:00Z",
                    }
                    for j in range(batch_size)
                ]
            },
        )

    # 2 batches → register the same callback twice (pytest_httpx
    # matches one request per registration).
    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/{_BASE}/{_TABLE}")
    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/{_BASE}/{_TABLE}")
    result = CreateRecordsOutput.model_validate(
        await create_records.ainvoke(
            _args(base_id=_BASE, table_name=_TABLE, records=inputs)
        )
    )
    assert result.success is True
    assert result.count == 12
    # Confirm batching: first request had 10 records, second had 2.
    assert len(captured_bodies) == 2
    assert len(captured_bodies[0]["records"]) == 10
    assert len(captured_bodies[1]["records"]) == 2


@pytest.mark.asyncio
async def test_update_records_normalizes_flat_shape(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(
            200,
            json={
                "records": [
                    {
                        "id": "rec1",
                        "fields": {"Status": "Done"},
                        "createdTime": "2026-01-01T00:00:00Z",
                    }
                ]
            },
        )

    httpx_mock.add_callback(_capture, method="PATCH", url=f"{API}/{_BASE}/{_TABLE}")
    result = UpdateRecordsOutput.model_validate(
        await update_records.ainvoke(
            _args(
                base_id=_BASE,
                table_name=_TABLE,
                # Flat-top-level shape, no explicit "fields" wrapper.
                records=[{"id": "rec1", "Status": "Done"}],
            )
        )
    )
    assert result.success is True
    # The flat shape should have been normalized to the canonical form.
    assert captured["records"][0]["fields"] == {"Status": "Done"}
    assert "Status" not in captured["records"][0]


@pytest.mark.asyncio
async def test_update_records_requires_id() -> None:
    result = UpdateRecordsOutput.model_validate(
        await update_records.ainvoke(
            _args(
                base_id=_BASE,
                table_name=_TABLE,
                records=[{"Status": "Done"}],  # missing 'id'
            )
        )
    )
    assert result.success is False
    assert result.error is not None and "'id'" in result.error


@pytest.mark.asyncio
async def test_delete_records(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/{_BASE}/{_TABLE}?records%5B%5D=rec1&records%5B%5D=rec2",
        json={
            "records": [
                {"id": "rec1", "deleted": True},
                {"id": "rec2", "deleted": True},
            ]
        },
    )
    result = DeleteRecordsOutput.model_validate(
        await delete_records.ainvoke(
            _args(base_id=_BASE, table_name=_TABLE, record_ids=["rec1", "rec2"])
        )
    )
    assert result.success is True
    assert result.deleted_ids == ["rec1", "rec2"]


@pytest.mark.asyncio
async def test_delete_records_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/{_BASE}/{_TABLE}?records%5B%5D=rec1",
        status_code=403,
        text="forbidden",
    )
    result = DeleteRecordsOutput.model_validate(
        await delete_records.ainvoke(
            _args(base_id=_BASE, table_name=_TABLE, record_ids=["rec1"])
        )
    )
    assert result.success is False
    assert result.error is not None and "403" in result.error


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = ListBasesOutput.model_validate(
        await list_bases.ainvoke({"api_key": ""})
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
