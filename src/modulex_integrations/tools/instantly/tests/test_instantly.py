"""Happy-path tests per action + failure-path (non-2xx → success=False)
and empty-credential tests."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.instantly import (
    TOOLS,
    activate_campaign,
    create_campaign,
    create_lead,
    create_lead_list,
    delete_leads,
    get_lead,
    list_campaigns,
    list_emails,
    list_lead_lists,
    list_leads,
    manifest,
    patch_campaign,
    reply_to_email,
    update_lead_interest_status,
)
from modulex_integrations.tools.instantly.outputs import (
    ActivateCampaignOutput,
    CreateCampaignOutput,
    CreateLeadListOutput,
    CreateLeadOutput,
    DeleteLeadsOutput,
    GetLeadOutput,
    ListCampaignsOutput,
    ListEmailsOutput,
    ListLeadListsOutput,
    ListLeadsOutput,
    PatchCampaignOutput,
    ReplyToEmailOutput,
    UpdateLeadInterestStatusOutput,
)

API = "https://api.instantly.ai/api/v2"
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


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/leads/list",
        json={
            "items": [{"id": "lead-1", "email": "jane@example.com", "first_name": "Jane"}],
            "next_starting_after": "cursor-2",
        },
    )

    result_dict = await list_leads.ainvoke(_args(search="jane"))
    assert isinstance(result_dict, dict)

    result = ListLeadsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.leads[0].email == "jane@example.com"
    assert result.next_starting_after == "cursor-2"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_get_lead(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/leads/lead-1",
        json={"id": "lead-1", "email": "jane@example.com", "campaign": "camp-1", "status": 1},
    )

    result = GetLeadOutput.model_validate(await get_lead.ainvoke(_args(lead_id="lead-1")))
    assert result.success is True
    assert result.id == "lead-1"
    assert result.email_address == "jane@example.com"
    assert result.campaign == "camp-1"


@pytest.mark.asyncio
async def test_create_lead(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/leads",
        json={"id": "lead-9", "email": "new@example.com", "first_name": "New"},
    )

    result = CreateLeadOutput.model_validate(
        await create_lead.ainvoke(
            _args(campaign="camp-1", email="new@example.com", first_name="New")
        )
    )
    assert result.success is True
    assert result.id == "lead-9"
    assert result.email_address == "new@example.com"


@pytest.mark.asyncio
async def test_delete_leads(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/leads", json={"count": 5})

    result = DeleteLeadsOutput.model_validate(
        await delete_leads.ainvoke(_args(campaign_id="camp-1", limit=100))
    )
    assert result.success is True
    assert result.count == 5


@pytest.mark.asyncio
async def test_update_lead_interest_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/leads/update-interest-status",
        json={"message": "Job submitted"},
    )

    result = UpdateLeadInterestStatusOutput.model_validate(
        await update_lead_interest_status.ainvoke(
            _args(lead_email="jane@example.com", interest_value=1)
        )
    )
    assert result.success is True
    assert result.message == "Job submitted"

    sent = httpx_mock.get_requests()[0]
    assert b'"interest_value"' in sent.content


@pytest.mark.asyncio
async def test_list_campaigns(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/campaigns?limit=10",
        json={"items": [{"id": "camp-1", "name": "Q1 Outreach", "status": 1}]},
    )

    result = ListCampaignsOutput.model_validate(
        await list_campaigns.ainvoke(_args(limit=10))
    )
    assert result.success is True
    assert result.count == 1
    assert result.campaigns[0].name == "Q1 Outreach"


@pytest.mark.asyncio
async def test_create_campaign(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/campaigns",
        json={"id": "camp-9", "name": "New Campaign", "status": 0},
    )

    result = CreateCampaignOutput.model_validate(
        await create_campaign.ainvoke(
            _args(name="New Campaign", campaign_schedule={"schedules": []})
        )
    )
    assert result.success is True
    assert result.id == "camp-9"
    assert result.name == "New Campaign"


@pytest.mark.asyncio
async def test_patch_campaign(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/campaigns/camp-1",
        json={"id": "camp-1", "name": "Renamed", "status": 1},
    )

    result = PatchCampaignOutput.model_validate(
        await patch_campaign.ainvoke(_args(campaign_id="camp-1", name="Renamed"))
    )
    assert result.success is True
    assert result.name == "Renamed"


@pytest.mark.asyncio
async def test_activate_campaign(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/campaigns/camp-1/activate",
        json={"id": "camp-1", "name": "Q1 Outreach", "status": 1},
    )

    result = ActivateCampaignOutput.model_validate(
        await activate_campaign.ainvoke(_args(campaign_id="camp-1"))
    )
    assert result.success is True
    assert result.status == 1


@pytest.mark.asyncio
async def test_list_emails(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/emails?limit=5",
        json={
            "items": [
                {"id": "email-1", "subject": "Re: Hello", "thread_id": "thread-1"}
            ],
            "next_starting_after": "cursor-x",
        },
    )

    result = ListEmailsOutput.model_validate(await list_emails.ainvoke(_args(limit=5)))
    assert result.success is True
    assert result.count == 1
    assert result.emails[0].subject == "Re: Hello"
    assert result.next_starting_after == "cursor-x"


@pytest.mark.asyncio
async def test_reply_to_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/emails/reply",
        json={"id": "email-9", "subject": "Re: Inquiry", "thread_id": "thread-9"},
    )

    result = ReplyToEmailOutput.model_validate(
        await reply_to_email.ainvoke(
            _args(
                eaccount="sender@example.com",
                reply_to_uuid="email-1",
                subject="Re: Inquiry",
                body_text="Thanks for reaching out.",
            )
        )
    )
    assert result.success is True
    assert result.id == "email-9"
    assert result.thread_id == "thread-9"

    sent = httpx_mock.get_requests()[0]
    assert b'"text"' in sent.content


@pytest.mark.asyncio
async def test_list_lead_lists(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lead-lists?limit=10",
        json={"items": [{"id": "list-1", "name": "Prospects", "has_enrichment_task": True}]},
    )

    result = ListLeadListsOutput.model_validate(
        await list_lead_lists.ainvoke(_args(limit=10))
    )
    assert result.success is True
    assert result.count == 1
    assert result.lead_lists[0].name == "Prospects"


@pytest.mark.asyncio
async def test_create_lead_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lead-lists",
        json={"id": "list-9", "name": "My Lead List"},
    )

    result = CreateLeadListOutput.model_validate(
        await create_lead_list.ainvoke(_args(name="My Lead List"))
    )
    assert result.success is True
    assert result.id == "list-9"
    assert result.name == "My Lead List"


# --- Failure-path + empty-credential ---------------------------------------


@pytest.mark.asyncio
async def test_list_leads_non_2xx_sets_success_false(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/leads/list",
        status_code=401,
        json={"message": "Unauthorized"},
    )

    result = ListLeadsOutput.model_validate(await list_leads.ainvoke(_args()))
    assert result.success is False
    assert result.error == "Unauthorized"


@pytest.mark.asyncio
async def test_get_lead_empty_api_key() -> None:
    result = GetLeadOutput.model_validate(
        await get_lead.ainvoke({"api_key": "  ", "lead_id": "lead-1"})
    )
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error


@pytest.mark.asyncio
async def test_create_campaign_empty_api_key() -> None:
    result = CreateCampaignOutput.model_validate(
        await create_campaign.ainvoke(
            {"api_key": "", "name": "X", "campaign_schedule": {}}
        )
    )
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error
