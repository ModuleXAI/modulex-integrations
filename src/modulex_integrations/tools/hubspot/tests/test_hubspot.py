"""Tests for the HubSpot integration.

26 actions all share the same SDK pattern, so coverage is shape-
representative rather than exhaustive: one happy-path per shape
(recent/get_by_id/create/update/search/engagement/property/activity)
plus the manifest sanity trio and one auth-validation test.

``_client`` is mocked via ``unittest.mock.patch`` to bypass the real
HubSpot SDK; the returned MagicMock satisfies the chained
``client.crm.<obj>.basic_api.*`` attribute access used by the tools.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from modulex_integrations.tools.hubspot import (
    TOOLS,
    create_company,
    create_contact,
    create_deal,
    create_meeting,
    create_note,
    create_task,
    create_ticket,
    get_company_activity,
    get_company_by_id,
    get_contact_by_id,
    get_deal_by_id,
    get_property,
    get_recent_companies,
    get_recent_contacts,
    get_recent_deals,
    get_recent_tickets,
    get_ticket_by_id,
    list_properties,
    manifest,
    search_companies,
    search_contacts,
    search_deals,
    search_tickets,
    update_company,
    update_contact,
    update_deal,
    update_ticket,
)
from modulex_integrations.tools.hubspot.outputs import (
    CreateCompanyOutput,
    CreateContactOutput,
    CreateDealOutput,
    CreateMeetingOutput,
    CreateNoteOutput,
    CreateTaskOutput,
    CreateTicketOutput,
    GetCompanyActivityOutput,
    GetCompanyByIdOutput,
    GetContactByIdOutput,
    GetDealByIdOutput,
    GetPropertyOutput,
    GetRecentCompaniesOutput,
    GetRecentContactsOutput,
    GetRecentDealsOutput,
    GetRecentTicketsOutput,
    GetTicketByIdOutput,
    ListPropertiesOutput,
    SearchCompaniesOutput,
    SearchContactsOutput,
    SearchDealsOutput,
    SearchTicketsOutput,
    UpdateCompanyOutput,
    UpdateContactOutput,
    UpdateDealOutput,
    UpdateTicketOutput,
)

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "tok-123"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


def _sdk_obj(payload: dict[str, Any]) -> MagicMock:
    """Build a fake SDK response object with ``.to_dict()``."""
    obj = MagicMock()
    obj.to_dict = MagicMock(return_value=payload)
    return obj


def _sdk_paged(items: list[dict[str, Any]], total: int | None = None) -> MagicMock:
    response = MagicMock()
    response.results = [_sdk_obj(it) for it in items]
    response.total = total if total is not None else len(items)
    return response


def _patch_client(client: MagicMock) -> Any:
    return patch(
        "modulex_integrations.tools.hubspot.tools._client",
        return_value=client,
    )


# Patch the input-builder imports so tests don't depend on the SDK
# being installed: they accept any kwargs and just return a sentinel.
def _patch_inputs() -> Any:
    sentinel = MagicMock()
    return patch.multiple(
        "modulex_integrations.tools.hubspot.tools",
        _public_object_search_request=MagicMock(return_value=sentinel),
        _simple_create_input=MagicMock(return_value=sentinel),
        _simple_update_input=MagicMock(return_value=sentinel),
        _engagement_create_input=MagicMock(return_value=sentinel),
    )


class TestManifest:
    def test_manifest_exposes_26_actions(self) -> None:
        assert len(manifest.actions) == 26

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_bearer_token_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}


@pytest.mark.asyncio
async def test_get_recent_contacts() -> None:
    client = MagicMock()
    client.crm.contacts.search_api.do_search.return_value = _sdk_paged(
        [{"id": "c1", "properties": {"email": "x@y.io"}}]
    )
    with _patch_client(client), _patch_inputs():
        result = GetRecentContactsOutput.model_validate(
            await get_recent_contacts.ainvoke(_args())
        )
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_get_recent_contacts_missing_token() -> None:
    bad = {"auth_type": "oauth2", "auth_data": {}}
    result = GetRecentContactsOutput.model_validate(
        await get_recent_contacts.ainvoke(bad)
    )
    assert result.success is False
    assert result.error is not None and "token" in result.error


@pytest.mark.asyncio
async def test_get_contact_by_id() -> None:
    client = MagicMock()
    client.crm.contacts.basic_api.get_by_id.return_value = _sdk_obj(
        {"id": "c1", "properties": {"firstname": "A"}}
    )
    with _patch_client(client):
        result = GetContactByIdOutput.model_validate(
            await get_contact_by_id.ainvoke(_args(contact_id="c1"))
        )
    assert result.success is True
    assert result.result is not None and result.result["id"] == "c1"


@pytest.mark.asyncio
async def test_create_contact() -> None:
    client = MagicMock()
    client.crm.contacts.basic_api.create.return_value = _sdk_obj({"id": "new"})
    with _patch_client(client), _patch_inputs():
        result = CreateContactOutput.model_validate(
            await create_contact.ainvoke(
                _args(email="a@b.io", firstname="A", phone="123")
            )
        )
    assert result.success is True
    assert result.result is not None and result.result["id"] == "new"


@pytest.mark.asyncio
async def test_update_contact() -> None:
    client = MagicMock()
    client.crm.contacts.basic_api.update.return_value = _sdk_obj({"id": "c1"})
    with _patch_client(client), _patch_inputs():
        result = UpdateContactOutput.model_validate(
            await update_contact.ainvoke(
                _args(contact_id="c1", properties={"firstname": "Updated"})
            )
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_search_contacts() -> None:
    client = MagicMock()
    client.crm.contacts.search_api.do_search.return_value = _sdk_paged(
        [{"id": "c1"}, {"id": "c2"}], total=42
    )
    with _patch_client(client), _patch_inputs():
        result = SearchContactsOutput.model_validate(
            await search_contacts.ainvoke(_args(query="alice"))
        )
    assert result.success is True
    assert result.total == 42  # total is reported from API, not row count


@pytest.mark.asyncio
async def test_get_recent_companies() -> None:
    client = MagicMock()
    client.crm.companies.search_api.do_search.return_value = _sdk_paged(
        [{"id": "co1"}]
    )
    with _patch_client(client), _patch_inputs():
        result = GetRecentCompaniesOutput.model_validate(
            await get_recent_companies.ainvoke(_args())
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_company_by_id() -> None:
    client = MagicMock()
    client.crm.companies.basic_api.get_by_id.return_value = _sdk_obj({"id": "co1"})
    with _patch_client(client):
        result = GetCompanyByIdOutput.model_validate(
            await get_company_by_id.ainvoke(_args(company_id="co1"))
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_company() -> None:
    client = MagicMock()
    client.crm.companies.basic_api.create.return_value = _sdk_obj({"id": "new"})
    with _patch_client(client), _patch_inputs():
        result = CreateCompanyOutput.model_validate(
            await create_company.ainvoke(_args(name="Acme"))
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_company() -> None:
    client = MagicMock()
    client.crm.companies.basic_api.update.return_value = _sdk_obj({"id": "co1"})
    with _patch_client(client), _patch_inputs():
        result = UpdateCompanyOutput.model_validate(
            await update_company.ainvoke(
                _args(company_id="co1", properties={"name": "Acme2"})
            )
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_company_activity_n_plus_one() -> None:
    client = MagicMock()
    associations = MagicMock()
    assoc_row = MagicMock()
    assoc_row.to_object_id = "eng1"
    associations.results = [assoc_row]
    client.crm.associations.v4.basic_api.get_page.return_value = associations
    api_request_resp = MagicMock()
    api_request_resp.json.return_value = {
        "engagement": {"id": "eng1", "type": "NOTE", "createdAt": 0},
        "metadata": {"body": "hi"},
    }
    client.api_request.return_value = api_request_resp
    with _patch_client(client):
        result = GetCompanyActivityOutput.model_validate(
            await get_company_activity.ainvoke(_args(company_id="co1"))
        )
    assert result.success is True
    assert result.total == 1
    assert result.activities[0]["id"] == "eng1"


@pytest.mark.asyncio
async def test_search_companies() -> None:
    client = MagicMock()
    client.crm.companies.search_api.do_search.return_value = _sdk_paged([{"id": "co1"}])
    with _patch_client(client), _patch_inputs():
        result = SearchCompaniesOutput.model_validate(
            await search_companies.ainvoke(_args(query="acme"))
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_deal_lifecycle() -> None:
    client = MagicMock()
    client.crm.deals.search_api.do_search.return_value = _sdk_paged([{"id": "d1"}])
    client.crm.deals.basic_api.get_by_id.return_value = _sdk_obj({"id": "d1"})
    client.crm.deals.basic_api.create.return_value = _sdk_obj({"id": "new"})
    client.crm.deals.basic_api.update.return_value = _sdk_obj({"id": "d1"})
    with _patch_client(client), _patch_inputs():
        assert GetRecentDealsOutput.model_validate(
            await get_recent_deals.ainvoke(_args())
        ).success
        assert GetDealByIdOutput.model_validate(
            await get_deal_by_id.ainvoke(_args(deal_id="d1"))
        ).success
        assert CreateDealOutput.model_validate(
            await create_deal.ainvoke(_args(dealname="Big Deal", amount=10000))
        ).success
        assert UpdateDealOutput.model_validate(
            await update_deal.ainvoke(
                _args(deal_id="d1", properties={"amount": "20000"})
            )
        ).success
        assert SearchDealsOutput.model_validate(
            await search_deals.ainvoke(_args(query="big"))
        ).success


@pytest.mark.asyncio
async def test_ticket_lifecycle() -> None:
    client = MagicMock()
    client.crm.tickets.search_api.do_search.return_value = _sdk_paged([{"id": "t1"}])
    client.crm.tickets.basic_api.get_by_id.return_value = _sdk_obj({"id": "t1"})
    client.crm.tickets.basic_api.create.return_value = _sdk_obj({"id": "new"})
    client.crm.tickets.basic_api.update.return_value = _sdk_obj({"id": "t1"})
    with _patch_client(client), _patch_inputs():
        assert GetRecentTicketsOutput.model_validate(
            await get_recent_tickets.ainvoke(_args())
        ).success
        assert GetTicketByIdOutput.model_validate(
            await get_ticket_by_id.ainvoke(_args(ticket_id="t1"))
        ).success
        assert CreateTicketOutput.model_validate(
            await create_ticket.ainvoke(
                _args(subject="Help", hs_ticket_priority="HIGH")
            )
        ).success
        assert UpdateTicketOutput.model_validate(
            await update_ticket.ainvoke(
                _args(ticket_id="t1", properties={"hs_ticket_priority": "LOW"})
            )
        ).success
        assert SearchTicketsOutput.model_validate(
            await search_tickets.ainvoke(_args(query="urgent"))
        ).success


@pytest.mark.asyncio
async def test_create_note_with_associations() -> None:
    client = MagicMock()
    client.crm.objects.notes.basic_api.create.return_value = _sdk_obj({"id": "n1"})
    with _patch_client(client), _patch_inputs():
        result = CreateNoteOutput.model_validate(
            await create_note.ainvoke(
                _args(body="Test note", contact_ids=["c1"], deal_ids=["d1"])
            )
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_task() -> None:
    client = MagicMock()
    client.crm.objects.tasks.basic_api.create.return_value = _sdk_obj({"id": "tk1"})
    with _patch_client(client), _patch_inputs():
        result = CreateTaskOutput.model_validate(
            await create_task.ainvoke(
                _args(subject="Call back", priority="HIGH", company_ids=["co1"])
            )
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_meeting() -> None:
    client = MagicMock()
    client.crm.objects.meetings.basic_api.create.return_value = _sdk_obj({"id": "m1"})
    with _patch_client(client), _patch_inputs():
        result = CreateMeetingOutput.model_validate(
            await create_meeting.ainvoke(
                _args(title="Sync", start_time="0", end_time="3600000")
            )
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_property() -> None:
    client = MagicMock()
    client.crm.properties.core_api.get_by_name.return_value = _sdk_obj(
        {"name": "email", "type": "string"}
    )
    with _patch_client(client):
        result = GetPropertyOutput.model_validate(
            await get_property.ainvoke(
                _args(object_type="contacts", property_name="email")
            )
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_properties() -> None:
    client = MagicMock()
    client.crm.properties.core_api.get_all.return_value = _sdk_paged(
        [{"name": "email"}, {"name": "firstname"}]
    )
    with _patch_client(client):
        result = ListPropertiesOutput.model_validate(
            await list_properties.ainvoke(_args(object_type="contacts"))
        )
    assert result.success is True
    assert result.total == 2


@pytest.mark.asyncio
async def test_sdk_exception_flows_into_success_false_envelope() -> None:
    client = MagicMock()
    client.crm.contacts.basic_api.get_by_id.side_effect = RuntimeError("not found")
    with _patch_client(client):
        result = GetContactByIdOutput.model_validate(
            await get_contact_by_id.ainvoke(_args(contact_id="missing"))
        )
    assert result.success is False
    assert result.error == "not found"
