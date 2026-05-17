"""Tests for the Salesforce integration."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.salesforce import (
    TOOLS,
    add_contact_to_campaign,
    add_lead_to_campaign,
    create_account,
    create_case,
    create_contact,
    create_lead,
    create_opportunity,
    create_record,
    create_task,
    delete_record,
    describe_object,
    get_record,
    list_objects,
    manifest,
    soql_query,
    sosl_search,
    update_record,
)
from modulex_integrations.tools.salesforce.outputs import (
    AddContactToCampaignOutput,
    AddLeadToCampaignOutput,
    CreateAccountOutput,
    CreateCaseOutput,
    CreateContactOutput,
    CreateLeadOutput,
    CreateOpportunityOutput,
    CreateRecordOutput,
    CreateTaskOutput,
    DeleteRecordOutput,
    DescribeObjectOutput,
    GetRecordOutput,
    ListObjectsOutput,
    SoqlQueryOutput,
    SoslSearchOutput,
    UpdateRecordOutput,
)

API = "https://acme.my.salesforce.com/services/data/v62.0"
_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {
        "access_token": "tok",
        "instance_url": "https://acme.my.salesforce.com",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


class TestManifest:
    def test_manifest_exposes_16_actions(self) -> None:
        assert len(manifest.actions) == 16

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_paired_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}


@pytest.mark.asyncio
async def test_soql_query_missing_instance_url() -> None:
    bad = {"auth_type": "oauth2", "auth_data": {"access_token": "tok"}}
    result = SoqlQueryOutput.model_validate(
        await soql_query.ainvoke(dict(bad, query="SELECT Id FROM Account"))
    )
    assert result.success is False
    assert result.error is not None and "instance_url" in result.error


@pytest.mark.asyncio
async def test_soql_query(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/query\?.*"),
        json={
            "totalSize": 2,
            "done": True,
            "records": [{"Id": "001"}, {"Id": "002"}],
        },
    )
    result = SoqlQueryOutput.model_validate(
        await soql_query.ainvoke(_args(query="SELECT Id FROM Account"))
    )
    assert result.success is True
    assert result.total_size == 2
    assert len(result.records) == 2


@pytest.mark.asyncio
async def test_sosl_search(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/search\?.*"),
        json={"searchRecords": [{"Id": "001", "Name": "Acme"}]},
    )
    result = SoslSearchOutput.model_validate(
        await sosl_search.ainvoke(_args(search="FIND {acme} IN ALL FIELDS"))
    )
    assert result.success is True
    assert isinstance(result.search_records, list)


@pytest.mark.asyncio
async def test_get_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sobjects/Account/001",
        json={"Id": "001", "Name": "Acme"},
    )
    result = GetRecordOutput.model_validate(
        await get_record.ainvoke(_args(object_type="Account", record_id="001"))
    )
    assert result.success is True
    assert result.result is not None and result.result["Id"] == "001"


@pytest.mark.asyncio
async def test_get_record_with_fields_filter(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/sobjects/Account/001\?fields=.*"),
        json={"Id": "001", "Name": "Acme"},
    )
    result = GetRecordOutput.model_validate(
        await get_record.ainvoke(
            _args(object_type="Account", record_id="001", fields=["Id", "Name"])
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sobjects/Account",
        status_code=201,
        json={"id": "001AB", "success": True},
    )
    result = CreateRecordOutput.model_validate(
        await create_record.ainvoke(
            _args(object_type="Account", data={"Name": "Acme"})
        )
    )
    assert result.success is True
    assert result.id == "001AB"


@pytest.mark.asyncio
async def test_update_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/sobjects/Account/001",
        status_code=204,
    )
    result = UpdateRecordOutput.model_validate(
        await update_record.ainvoke(
            _args(object_type="Account", record_id="001", data={"Name": "X"})
        )
    )
    assert result.success is True
    assert result.updated is True


@pytest.mark.asyncio
async def test_delete_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/sobjects/Account/001",
        status_code=204,
    )
    result = DeleteRecordOutput.model_validate(
        await delete_record.ainvoke(_args(object_type="Account", record_id="001"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_account_maps_snake_to_pascal(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured.update(_json.loads(request.content.decode()))
        return Response(201, json={"id": "001", "success": True})

    httpx_mock.add_callback(
        _capture, method="POST", url=f"{API}/sobjects/Account"
    )
    result = CreateAccountOutput.model_validate(
        await create_account.ainvoke(
            _args(
                name="Acme",
                industry="Tech",
                annual_revenue=1_000_000,
                billing_city="SF",
            )
        )
    )
    assert result.success is True
    assert captured["Name"] == "Acme"
    assert captured["Industry"] == "Tech"
    assert captured["AnnualRevenue"] == 1_000_000
    assert captured["BillingCity"] == "SF"


@pytest.mark.asyncio
async def test_create_contact(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sobjects/Contact",
        status_code=201,
        json={"id": "003", "success": True},
    )
    result = CreateContactOutput.model_validate(
        await create_contact.ainvoke(
            _args(last_name="Doe", first_name="John", email="j@x.io")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_lead(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sobjects/Lead",
        status_code=201,
        json={"id": "00Q", "success": True},
    )
    result = CreateLeadOutput.model_validate(
        await create_lead.ainvoke(_args(last_name="Doe", company="Acme"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_opportunity(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sobjects/Opportunity",
        status_code=201,
        json={"id": "006", "success": True},
    )
    result = CreateOpportunityOutput.model_validate(
        await create_opportunity.ainvoke(
            _args(
                name="Big Deal",
                stage_name="Prospecting",
                close_date="2026-12-31",
            )
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_task(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sobjects/Task",
        status_code=201,
        json={"id": "00T", "success": True},
    )
    result = CreateTaskOutput.model_validate(
        await create_task.ainvoke(_args(subject="Follow up"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_case(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sobjects/Case",
        status_code=201,
        json={"id": "500", "success": True},
    )
    result = CreateCaseOutput.model_validate(
        await create_case.ainvoke(_args(subject="Bug"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_add_contact_to_campaign(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sobjects/CampaignMember",
        status_code=201,
        json={"id": "00v", "success": True},
    )
    result = AddContactToCampaignOutput.model_validate(
        await add_contact_to_campaign.ainvoke(
            _args(campaign_id="701", contact_id="003")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_add_lead_to_campaign(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sobjects/CampaignMember",
        status_code=201,
        json={"id": "00v", "success": True},
    )
    result = AddLeadToCampaignOutput.model_validate(
        await add_lead_to_campaign.ainvoke(
            _args(campaign_id="701", lead_id="00Q")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_describe_object(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sobjects/Account/describe",
        json={
            "name": "Account",
            "label": "Account",
            "keyPrefix": "001",
            "createable": True,
            "fields": [
                {
                    "name": "Name",
                    "label": "Name",
                    "type": "string",
                    "nillable": False,
                    "createable": True,
                    "updateable": True,
                }
            ],
        },
    )
    result = DescribeObjectOutput.model_validate(
        await describe_object.ainvoke(_args(object_type="Account"))
    )
    assert result.success is True
    assert result.field_count == 1
    assert result.fields[0]["required"] is True


@pytest.mark.asyncio
async def test_list_objects(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sobjects",
        json={
            "sobjects": [
                {"name": "Account", "label": "Account", "queryable": True},
                {"name": "Internal", "label": "Internal", "queryable": False},
            ]
        },
    )
    result = ListObjectsOutput.model_validate(
        await list_objects.ainvoke(_args())
    )
    assert result.success is True
    assert result.total_count == 1  # Only the queryable one
