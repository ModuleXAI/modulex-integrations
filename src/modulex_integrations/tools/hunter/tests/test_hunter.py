"""Happy-path tests for every hunter @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.hunter import (
    TOOLS,
    account_information,
    combined_enrichment,
    create_lead,
    delete_lead,
    domain_search,
    email_count,
    email_finder,
    email_verifier,
    get_lead,
    get_leads_list,
    list_leads,
    list_leads_lists,
    manifest,
    update_lead,
)
from modulex_integrations.tools.hunter.outputs import (
    AccountInformationOutput,
    CombinedEnrichmentOutput,
    CreateLeadOutput,
    DeleteLeadOutput,
    DomainSearchOutput,
    EmailCountOutput,
    EmailFinderOutput,
    EmailVerifierOutput,
    GetLeadOutput,
    GetLeadsListOutput,
    ListLeadsListsOutput,
    ListLeadsOutput,
    UpdateLeadOutput,
)

API = "https://api.hunter.io/v2"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_13_actions(self) -> None:
        assert len(manifest.actions) == 13

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_account_information(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/account?api_key={_API_KEY}",
        json={
            "data": {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "plan_name": "Free",
                "plan_level": 0,
                "reset_date": "2026-06-01",
                "team_id": 1,
                "calls": {"used": 10, "available": 50},
            }
        },
    )

    result_dict = await account_information.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = AccountInformationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email == "user@example.com"
    assert result.calls_used == 10


@pytest.mark.asyncio
async def test_combined_enrichment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/combined/find?api_key={_API_KEY}&email=test%40example.com",
        json={
            "data": {
                "person": {"first_name": "John"},
                "company": {"name": "Example"},
            }
        },
    )

    result_dict = await combined_enrichment.ainvoke(_args(email="test@example.com"))

    assert isinstance(result_dict, dict)
    result = CombinedEnrichmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None


@pytest.mark.asyncio
async def test_create_lead(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/leads?api_key={_API_KEY}",
        json={
            "data": {
                "id": 123,
                "email": "lead@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
            }
        },
    )

    result_dict = await create_lead.ainvoke(_args(email="lead@example.com"))

    assert isinstance(result_dict, dict)
    result = CreateLeadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 123


@pytest.mark.asyncio
async def test_delete_lead(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/leads/456?api_key={_API_KEY}",
        status_code=204,
        content=b"",
    )

    result_dict = await delete_lead.ainvoke(_args(lead_id="456"))

    assert isinstance(result_dict, dict)
    result = DeleteLeadOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_domain_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/domain-search?api_key={_API_KEY}&domain=stripe.com&limit=10",
        json={
            "data": {
                "domain": "stripe.com",
                "disposable": False,
                "webmail": False,
                "accept_all": False,
                "pattern": "{first}",
                "organization": "Stripe",
                "emails": [{"value": "john@stripe.com", "type": "personal"}],
            },
            "meta": {"results": 1, "limit": 10, "offset": 0},
        },
    )

    result_dict = await domain_search.ainvoke(_args(domain="stripe.com", limit=10))

    assert isinstance(result_dict, dict)
    result = DomainSearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.domain == "stripe.com"
    assert len(result.emails) == 1


@pytest.mark.asyncio
async def test_email_count(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/email-count?api_key={_API_KEY}&domain=stripe.com",
        json={
            "data": {
                "total": 100,
                "personal_emails": 80,
                "generic_emails": 20,
                "department": {},
            }
        },
    )

    result_dict = await email_count.ainvoke(_args(domain="stripe.com"))

    assert isinstance(result_dict, dict)
    result = EmailCountOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 100


@pytest.mark.asyncio
async def test_email_finder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/email-finder?api_key={_API_KEY}&domain=stripe.com&first_name=John&last_name=Doe",
        json={
            "data": {
                "email": "john.doe@stripe.com",
                "first_name": "John",
                "last_name": "Doe",
                "score": 92,
                "domain": "stripe.com",
                "accept_all": False,
                "position": "Engineer",
                "twitter": None,
                "linkedin_url": None,
                "phone_number": None,
                "company": "Stripe",
                "sources": [],
            }
        },
    )

    result_dict = await email_finder.ainvoke(
        _args(first_name="John", last_name="Doe", domain="stripe.com")
    )

    assert isinstance(result_dict, dict)
    result = EmailFinderOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email == "john.doe@stripe.com"
    assert result.score == 92


@pytest.mark.asyncio
async def test_email_verifier(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/email-verifier?api_key={_API_KEY}&email=test%40example.com",
        json={
            "data": {
                "status": "valid",
                "result": "deliverable",
                "score": 95,
                "email": "test@example.com",
                "regexp": True,
                "gibberish": False,
                "disposable": False,
                "webmail": False,
                "mx_records": True,
                "smtp_server": True,
                "smtp_check": True,
                "accept_all": False,
                "block": False,
                "sources": [],
            }
        },
    )

    result_dict = await email_verifier.ainvoke(_args(email="test@example.com"))

    assert isinstance(result_dict, dict)
    result = EmailVerifierOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "valid"
    assert result.score == 95


@pytest.mark.asyncio
async def test_get_lead(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/leads/789?api_key={_API_KEY}",
        json={
            "data": {
                "id": 789,
                "email": "lead@example.com",
                "first_name": "Alice",
                "last_name": "Johnson",
                "position": "CTO",
                "company": "Acme",
            }
        },
    )

    result_dict = await get_lead.ainvoke(_args(lead_id="789"))

    assert isinstance(result_dict, dict)
    result = GetLeadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 789


@pytest.mark.asyncio
async def test_get_leads_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/leads_lists/10?api_key={_API_KEY}&limit=20",
        json={
            "data": {
                "id": 10,
                "name": "My List",
                "leads": [{"id": 1, "email": "a@b.com"}],
            }
        },
    )

    result_dict = await get_leads_list.ainvoke(_args(leads_list_id="10", limit=20))

    assert isinstance(result_dict, dict)
    result = GetLeadsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "My List"
    assert len(result.leads) == 1


@pytest.mark.asyncio
async def test_list_leads(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/leads?api_key={_API_KEY}&limit=10",
        json={
            "data": {
                "leads": [{"id": 1, "email": "a@b.com"}],
            },
            "meta": {"total": 1, "limit": 10, "offset": 0},
        },
    )

    result_dict = await list_leads.ainvoke(_args(limit=10))

    assert isinstance(result_dict, dict)
    result = ListLeadsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.leads) == 1
    assert result.total == 1


@pytest.mark.asyncio
async def test_list_leads_lists(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/leads_lists?api_key={_API_KEY}&limit=10",
        json={
            "data": {
                "leads_lists": [{"id": 1, "name": "List A"}],
            }
        },
    )

    result_dict = await list_leads_lists.ainvoke(_args(limit=10))

    assert isinstance(result_dict, dict)
    result = ListLeadsListsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.leads_lists) == 1


@pytest.mark.asyncio
async def test_update_lead(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/leads/789?api_key={_API_KEY}",
        status_code=200,
        json={},
    )

    result_dict = await update_lead.ainvoke(
        _args(lead_id="789", first_name="Updated")
    )

    assert isinstance(result_dict, dict)
    result = UpdateLeadOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_account_information_validates_empty_api_key() -> None:
    result_dict = await account_information.ainvoke({"api_key": ""})
    result = AccountInformationOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
