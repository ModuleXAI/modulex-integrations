"""Tests for the Apollo.io integration.

27 actions all share one ``_call`` helper, so test coverage is
representative-not-exhaustive: one happy-path per HTTP method/path
shape (POST enrichment, GET enrichment, POST search, PATCH update,
PUT update, GET view, GET stage list) plus the manifest sanity trio
and one HTTP-error case.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.apollo_io import (
    TOOLS,
    add_contacts_to_sequence,
    bulk_organization_enrichment,
    bulk_people_enrichment,
    create_account,
    create_contact,
    create_deal,
    create_task,
    get_api_usage,
    list_account_stages,
    list_contact_stages,
    list_deal_stages,
    list_deals,
    list_users,
    manifest,
    organization_enrichment,
    organization_job_postings,
    organization_search,
    people_enrichment,
    people_search,
    search_accounts,
    search_contacts,
    search_sequences,
    search_tasks,
    update_account,
    update_contact,
    update_deal,
    view_account,
    view_contact,
    view_deal,
)
from modulex_integrations.tools.apollo_io.outputs import (
    AddContactsToSequenceOutput,
    BulkOrganizationEnrichmentOutput,
    BulkPeopleEnrichmentOutput,
    CreateAccountOutput,
    CreateContactOutput,
    CreateDealOutput,
    CreateTaskOutput,
    GetApiUsageOutput,
    ListAccountStagesOutput,
    ListContactStagesOutput,
    ListDealsOutput,
    ListDealStagesOutput,
    ListUsersOutput,
    OrganizationEnrichmentOutput,
    OrganizationJobPostingsOutput,
    OrganizationSearchOutput,
    PeopleEnrichmentOutput,
    PeopleSearchOutput,
    SearchAccountsOutput,
    SearchContactsOutput,
    SearchSequencesOutput,
    SearchTasksOutput,
    UpdateAccountOutput,
    UpdateContactOutput,
    UpdateDealOutput,
    ViewAccountOutput,
    ViewContactOutput,
    ViewDealOutput,
)

API = "https://api.apollo.io/api/v1"
_API_KEY = "apollo-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_twenty_eight_actions(self) -> None:
        assert len(manifest.actions) == 28

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_people_enrichment_post(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/people/match",
        json={"person": {"id": "p1", "name": "Ada"}},
    )
    result_dict = await people_enrichment.ainvoke(_args(email="ada@example.com"))
    assert isinstance(result_dict, dict)
    result = PeopleEnrichmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.result is not None
    assert result.result["person"]["name"] == "Ada"


@pytest.mark.asyncio
async def test_bulk_people_enrichment_clamps_to_10(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(200, json={"matches": []})

    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/people/bulk_match")
    too_many = [{"email": f"u{i}@x.io"} for i in range(15)]
    result = BulkPeopleEnrichmentOutput.model_validate(
        await bulk_people_enrichment.ainvoke(_args(details=too_many))
    )
    assert result.success is True
    assert len(captured["details"]) == 10


@pytest.mark.asyncio
async def test_organization_enrichment_get(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/organizations/enrich?domain=apollo.io",
        json={"organization": {"id": "o1", "name": "Apollo"}},
    )
    result = OrganizationEnrichmentOutput.model_validate(
        await organization_enrichment.ainvoke(_args(domain="https://www.apollo.io/about"))
    )
    assert result.success is True
    assert result.result is not None
    assert result.result["organization"]["name"] == "Apollo"


@pytest.mark.asyncio
async def test_bulk_organization_enrichment(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/organizations/bulk_enrich",
        json={"organizations": [], "status": "ok"},
    )
    result = BulkOrganizationEnrichmentOutput.model_validate(
        await bulk_organization_enrichment.ainvoke(
            _args(domains=["apollo.io", "https://example.com"])
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_people_search(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/mixed_people/search",
        json={"people": [{"id": "p1"}], "pagination": {"total_entries": 1}},
    )
    result = PeopleSearchOutput.model_validate(
        await people_search.ainvoke(
            _args(person_titles=["CEO"], per_page=10, q_keywords="founder")
        )
    )
    assert result.success is True
    assert result.result is not None
    assert len(result.result["people"]) == 1


@pytest.mark.asyncio
async def test_organization_search_revenue_range(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(200, json={"organizations": [], "pagination": {}})

    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/mixed_companies/search")
    result = OrganizationSearchOutput.model_validate(
        await organization_search.ainvoke(
            _args(revenue_range_min=1_000_000, revenue_range_max=10_000_000)
        )
    )
    assert result.success is True
    assert captured["revenue_range"] == {"min": 1_000_000, "max": 10_000_000}


@pytest.mark.asyncio
async def test_organization_job_postings(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/organizations/O1/job_postings",
        json={"organization_job_postings": [{"id": "j1", "title": "SWE"}]},
    )
    result = OrganizationJobPostingsOutput.model_validate(
        await organization_job_postings.ainvoke(_args(organization_id="O1"))
    )
    assert result.success is True
    assert result.result is not None
    assert result.result["organization_job_postings"][0]["title"] == "SWE"


@pytest.mark.asyncio
async def test_create_contact(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts",
        json={"contact": {"id": "c1", "email": "x@y.io"}},
    )
    result = CreateContactOutput.model_validate(
        await create_contact.ainvoke(_args(email="x@y.io", first_name="X"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_contact_patch(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/contacts/C1",
        json={"contact": {"id": "C1", "email": "new@x.io"}},
    )
    result = UpdateContactOutput.model_validate(
        await update_contact.ainvoke(_args(contact_id="C1", email="new@x.io"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_search_contacts(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/search",
        json={"contacts": [{"id": "c1"}], "pagination": {}},
    )
    result = SearchContactsOutput.model_validate(
        await search_contacts.ainvoke(_args(q_keywords="acme"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_view_contact_get(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/C1",
        json={"contact": {"id": "C1"}},
    )
    result = ViewContactOutput.model_validate(
        await view_contact.ainvoke(_args(contact_id="C1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_account(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/accounts",
        json={"account": {"id": "A1", "name": "Acme"}},
    )
    result = CreateAccountOutput.model_validate(
        await create_account.ainvoke(_args(name="Acme", domain="acme.io"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_account_patch(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/accounts/A1",
        json={"account": {"id": "A1", "name": "Acme2"}},
    )
    result = UpdateAccountOutput.model_validate(
        await update_account.ainvoke(_args(account_id="A1", name="Acme2"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_search_accounts(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/accounts/search",
        json={"accounts": [{"id": "A1"}], "pagination": {}},
    )
    result = SearchAccountsOutput.model_validate(
        await search_accounts.ainvoke(_args(q_organization_name="Acme"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_view_account_get(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/accounts/A1", json={"account": {"id": "A1"}}
    )
    result = ViewAccountOutput.model_validate(
        await view_account.ainvoke(_args(account_id="A1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_deal(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/opportunities",
        json={"deal": {"id": "D1", "name": "Acme deal", "amount": 10000.0}},
    )
    result = CreateDealOutput.model_validate(
        await create_deal.ainvoke(_args(name="Acme deal", deal_stage_id="S1", amount=10000.0))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_deal_put(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/opportunities/D1",
        json={"deal": {"id": "D1", "amount": 20000.0}},
    )
    result = UpdateDealOutput.model_validate(
        await update_deal.ainvoke(_args(deal_id="D1", amount=20000.0))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_deals(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/opportunities/search",
        json={"opportunities": [{"id": "D1"}], "pagination": {}},
    )
    result = ListDealsOutput.model_validate(await list_deals.ainvoke(_args()))
    assert result.success is True


@pytest.mark.asyncio
async def test_view_deal_get(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/opportunities/D1", json={"deal": {"id": "D1"}}
    )
    result = ViewDealOutput.model_validate(
        await view_deal.ainvoke(_args(deal_id="D1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_search_sequences(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/emailer_campaigns/search",
        json={"emailer_campaigns": [], "pagination": {}},
    )
    result = SearchSequencesOutput.model_validate(
        await search_sequences.ainvoke(_args(q_name="welcome"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_add_contacts_to_sequence(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/emailer_campaigns/SEQ1/add_contact_ids",
        json={"contacts": [{"id": "C1"}]},
    )
    result = AddContactsToSequenceOutput.model_validate(
        await add_contacts_to_sequence.ainvoke(
            _args(sequence_id="SEQ1", contact_ids=["C1"])
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_task(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tasks",
        json={"task": {"id": "T1", "name": "Follow up"}},
    )
    result = CreateTaskOutput.model_validate(
        await create_task.ainvoke(_args(name="Follow up", due_date="2026-06-01"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_search_tasks(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tasks/search",
        json={"tasks": [], "pagination": {}},
    )
    result = SearchTasksOutput.model_validate(
        await search_tasks.ainvoke(_args(status="open"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_api_usage(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/account/stats",
        json={"rate_limit_remaining": 100, "credits_remaining": 1000},
    )
    result = GetApiUsageOutput.model_validate(await get_api_usage.ainvoke(_args()))
    assert result.success is True


@pytest.mark.asyncio
async def test_list_users(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/search",
        json={"users": [{"id": "U1"}], "pagination": {}},
    )
    result = ListUsersOutput.model_validate(await list_users.ainvoke(_args()))
    assert result.success is True


@pytest.mark.asyncio
async def test_list_contact_stages(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contact_stages",
        json={"contact_stages": [{"id": "CS1", "name": "Cold"}]},
    )
    result = ListContactStagesOutput.model_validate(
        await list_contact_stages.ainvoke(_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_account_stages(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/account_stages",
        json={"account_stages": [{"id": "AS1", "name": "Lead"}]},
    )
    result = ListAccountStagesOutput.model_validate(
        await list_account_stages.ainvoke(_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_deal_stages(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/opportunity_stages",
        json={"deal_stages": [{"id": "DS1", "name": "Discovery"}]},
    )
    result = ListDealStagesOutput.model_validate(
        await list_deal_stages.ainvoke(_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_http_error_surfaces(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/people/match",
        status_code=429,
        text="rate limit exceeded",
    )
    result = PeopleEnrichmentOutput.model_validate(
        await people_enrichment.ainvoke(_args(email="x@y.io"))
    )
    assert result.success is False
    assert result.error is not None and "429" in result.error


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = PeopleEnrichmentOutput.model_validate(
        await people_enrichment.ainvoke({"api_key": ""})
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
