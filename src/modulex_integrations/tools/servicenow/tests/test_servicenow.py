"""Tests for the ServiceNow integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.servicenow import (
    TOOLS,
    create_case,
    create_incident,
    create_table_record,
    delete_table_record,
    get_table_record,
    get_table_records,
    manifest,
    update_table_record,
)
from modulex_integrations.tools.servicenow.outputs import (
    CreateCaseOutput,
    CreateIncidentOutput,
    CreateTableRecordOutput,
    DeleteTableRecordOutput,
    GetTableRecordOutput,
    GetTableRecordsOutput,
    UpdateTableRecordOutput,
)

_INSTANCE = "dev12345"
BASE = f"https://{_INSTANCE}.service-now.com"

_OAUTH_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "sn-oauth-token", "instance_name": _INSTANCE},
}
_PAT_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "sn-pat-token", "instance_name": _INSTANCE},
}


def _args(auth: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return dict(auth, **extra)


class TestManifest:
    def test_manifest_exposes_seven_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_paired_oauth_and_bearer_token_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}

    def test_oauth_url_carries_instance_placeholder(self) -> None:
        oauth = next(a for a in manifest.auth_schemas if a.auth_type == "oauth2")
        assert "{instance_name}" in oauth.oauth_config.auth_url
        assert "{instance_name}" in oauth.oauth_config.token_url


@pytest.mark.asyncio
async def test_create_case_oauth(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/sn_ind_tsm_sdwan/ticket/troubleTicket",
        status_code=201,
        json={"result": {"sys_id": "C1", "number": "CS0001", "priority": "2"}},
    )
    result_dict = await create_case.ainvoke(
        _args(
            _OAUTH_AUTH,
            description="Email outage",
            severity="2",
            name="Email down",
            channel_name="web",
            work_note="Acknowledged",
        )
    )
    assert isinstance(result_dict, dict)
    result = CreateCaseOutput.model_validate(result_dict)
    assert result.success is True
    assert result.result is not None
    assert result.result["result"]["number"] == "CS0001"


@pytest.mark.asyncio
async def test_create_case_bearer(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/sn_ind_tsm_sdwan/ticket/troubleTicket",
        status_code=201,
        json={"result": {"sys_id": "C2"}},
    )
    result = CreateCaseOutput.model_validate(
        await create_case.ainvoke(
            _args(_PAT_AUTH, description="Issue", severity="3")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_case_validates_missing_token() -> None:
    bad_auth = {
        "auth_type": "oauth2",
        "auth_data": {"instance_name": _INSTANCE},  # token missing
    }
    result = CreateCaseOutput.model_validate(
        await create_case.ainvoke(
            dict(bad_auth, description="x", severity="3")
        )
    )
    assert result.success is False
    assert result.error is not None and "access token" in result.error


@pytest.mark.asyncio
async def test_create_case_validates_missing_instance() -> None:
    bad_auth = {
        "auth_type": "oauth2",
        "auth_data": {"access_token": "tok"},  # instance_name missing
    }
    result = CreateCaseOutput.model_validate(
        await create_case.ainvoke(
            dict(bad_auth, description="x", severity="3")
        )
    )
    assert result.success is False
    assert result.error is not None and "instance_name" in result.error


@pytest.mark.asyncio
async def test_create_incident(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/sn_ind_tsm_sdwan/ticket/troubleTicket",
        status_code=201,
        json={"result": {"sys_id": "I1", "number": "INC0001"}},
    )
    result = CreateIncidentOutput.model_validate(
        await create_incident.ainvoke(
            _args(
                _OAUTH_AUTH,
                description="Server down",
                severity="1",
                name="Server outage",
                contact_method="phone",
            )
        )
    )
    assert result.success is True
    assert result.result is not None
    assert result.result["result"]["number"] == "INC0001"


@pytest.mark.asyncio
async def test_create_table_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/now/table/incident?sysparm_display_value=false",
        status_code=201,
        json={"result": {"sys_id": "R1", "number": "INC9999"}},
    )
    result = CreateTableRecordOutput.model_validate(
        await create_table_record.ainvoke(
            _args(
                _OAUTH_AUTH,
                table_name="incident",
                table_record={"short_description": "Disk full"},
            )
        )
    )
    assert result.success is True
    assert result.table == "incident"
    assert result.record == {"sys_id": "R1", "number": "INC9999"}


@pytest.mark.asyncio
async def test_get_table_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/now/table/incident/R1?sysparm_display_value=true",
        json={"result": {"sys_id": "R1", "state": "New"}},
    )
    result = GetTableRecordOutput.model_validate(
        await get_table_record.ainvoke(
            _args(
                _OAUTH_AUTH,
                table_name="incident",
                sys_id="R1",
                display_value="true",
            )
        )
    )
    assert result.success is True
    assert result.record is not None
    assert result.record["state"] == "New"


@pytest.mark.asyncio
async def test_get_table_record_404(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/now/table/incident/missing?sysparm_display_value=false",
        status_code=404,
        text="not found",
    )
    result = GetTableRecordOutput.model_validate(
        await get_table_record.ainvoke(
            _args(_OAUTH_AUTH, table_name="incident", sys_id="missing")
        )
    )
    assert result.success is False
    assert result.error is not None and "missing" in result.error


@pytest.mark.asyncio
async def test_get_table_records(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{BASE}/api/now/v2/table/incident"
            "?sysparm_display_value=false&sysparm_query=active%3Dtrue&sysparm_limit=25"
        ),
        json={
            "result": [
                {"sys_id": "R1", "state": "New"},
                {"sys_id": "R2", "state": "In Progress"},
            ]
        },
    )
    result = GetTableRecordsOutput.model_validate(
        await get_table_records.ainvoke(
            _args(
                _OAUTH_AUTH,
                table_name="incident",
                api_version="v2",
                query="active=true",
                limit=25,
            )
        )
    )
    assert result.success is True
    assert result.count == 2
    assert {r["sys_id"] for r in result.records} == {"R1", "R2"}


@pytest.mark.asyncio
async def test_update_table_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{BASE}/api/now/table/incident/R1?sysparm_display_value=false",
        json={"result": {"sys_id": "R1", "state": "Closed"}},
    )
    result = UpdateTableRecordOutput.model_validate(
        await update_table_record.ainvoke(
            _args(
                _OAUTH_AUTH,
                table_name="incident",
                sys_id="R1",
                update_fields={"state": "Closed"},
            )
        )
    )
    assert result.success is True
    assert result.record is not None
    assert result.record["state"] == "Closed"


@pytest.mark.asyncio
async def test_delete_table_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE}/api/now/table/incident/R1",
        status_code=204,
    )
    result = DeleteTableRecordOutput.model_validate(
        await delete_table_record.ainvoke(
            _args(_OAUTH_AUTH, table_name="incident", sys_id="R1")
        )
    )
    assert result.success is True
    assert result.sys_id == "R1"


@pytest.mark.asyncio
async def test_delete_table_record_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE}/api/now/table/incident/R1",
        status_code=403,
        text="forbidden",
    )
    result = DeleteTableRecordOutput.model_validate(
        await delete_table_record.ainvoke(
            _args(_OAUTH_AUTH, table_name="incident", sys_id="R1")
        )
    )
    assert result.success is False
    assert result.error is not None and "403" in result.error
