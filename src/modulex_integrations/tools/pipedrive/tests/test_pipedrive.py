"""Happy-path tests for every pipedrive @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.pipedrive import (
    TOOLS,
    add_activity,
    add_deal,
    add_labels,
    add_lead,
    add_note,
    add_organization,
    add_person,
    get_all_leads,
    get_deal,
    get_lead_by_id,
    get_person_details,
    list_deals,
    list_lead_label_ids_options,
    list_organization_label_ids_options,
    list_person_label_ids_options,
    list_user_id_options,
    manifest,
    merge_deals,
    merge_persons,
    remove_duplicate_notes,
    remove_labels,
    search_leads,
    search_notes,
    search_persons,
    update_deal,
    update_lead,
    update_person,
)
from modulex_integrations.tools.pipedrive.outputs import (
    AddActivityOutput,
    AddDealOutput,
    AddLabelsOutput,
    AddLeadOutput,
    AddNoteOutput,
    AddOrganizationOutput,
    AddPersonOutput,
    GetAllLeadsOutput,
    GetDealOutput,
    GetLeadByIdOutput,
    GetPersonDetailsOutput,
    ListDealsOutput,
    ListLeadLabelIdsOptionsOutput,
    ListOrganizationLabelIdsOptionsOutput,
    ListPersonLabelIdsOptionsOutput,
    ListUserIdOptionsOutput,
    MergeDealsOutput,
    MergePersonsOutput,
    RemoveDuplicateNotesOutput,
    RemoveLabelsOutput,
    SearchLeadsOutput,
    SearchNotesOutput,
    SearchPersonsOutput,
    UpdateDealOutput,
    UpdateLeadOutput,
    UpdatePersonOutput,
)

API = "https://mycompany.pipedrive.com"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token", "api_domain": API},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_26_actions(self) -> None:
        assert len(manifest.actions) == 26

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_activity(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/v2/activities",
        json={
            # TODO: fill in a representative response from the Pipedrive API docs
            "success": True,
            "data": {"id": 1, "subject": "Call", "type": "call"},
        },
    )

    result_dict = await add_activity.ainvoke(_args(subject="Call", type="call"))

    assert isinstance(result_dict, dict)
    result = AddActivityOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_deal(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/v2/deals",
        json={
            "success": True,
            "data": {"id": 10, "title": "Big Deal"},
        },
    )

    result_dict = await add_deal.ainvoke(_args(title="Big Deal"))

    assert isinstance(result_dict, dict)
    result = AddDealOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_labels(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v2/deals/5",
        json={"success": True, "data": {"id": 5, "label_ids": [1]}},
    )
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/v2/deals/5",
        json={"success": True, "data": {"id": 5, "label_ids": [1, 2]}},
    )

    result_dict = await add_labels.ainvoke(_args(type="deal", label_ids=["2"], deal_id="5"))

    assert isinstance(result_dict, dict)
    result = AddLabelsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_lead(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/v1/leads",
        json={
            "success": True,
            "data": {"id": "abc-123", "title": "New Lead"},
        },
    )

    result_dict = await add_lead.ainvoke(_args(title="New Lead", person_id=1))

    assert isinstance(result_dict, dict)
    result = AddLeadOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_note(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/v1/notes",
        json={
            "success": True,
            "data": {"id": 100, "content": "<p>Hello</p>"},
        },
    )

    result_dict = await add_note.ainvoke(_args(content="<p>Hello</p>", deal_id="5"))

    assert isinstance(result_dict, dict)
    result = AddNoteOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_organization(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/v2/organizations",
        json={
            "success": True,
            "data": {"id": 50, "name": "Acme Corp"},
        },
    )

    result_dict = await add_organization.ainvoke(_args(name="Acme Corp"))

    assert isinstance(result_dict, dict)
    result = AddOrganizationOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_person(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/v2/persons",
        json={
            "success": True,
            "data": {"id": 30, "name": "Jane Doe"},
        },
    )

    result_dict = await add_person.ainvoke(_args(name="Jane Doe"))

    assert isinstance(result_dict, dict)
    result = AddPersonOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_all_leads(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v1/leads?start=0&limit=100",
        json={
            "success": True,
            "data": [{"id": "lead-1", "title": "Lead One"}],
            "additional_data": {"pagination": {"more_items_in_collection": False}},
        },
    )

    result_dict = await get_all_leads.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetAllLeadsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_get_deal(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v2/deals/10",
        json={
            "success": True,
            "data": {"id": 10, "title": "Big Deal"},
        },
    )

    result_dict = await get_deal.ainvoke(_args(deal_id="10"))

    assert isinstance(result_dict, dict)
    result = GetDealOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_lead_by_id(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v1/leads/abc-123",
        json={
            "success": True,
            "data": {"id": "abc-123", "title": "Lead One"},
        },
    )

    result_dict = await get_lead_by_id.ainvoke(_args(lead_id="abc-123"))

    assert isinstance(result_dict, dict)
    result = GetLeadByIdOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_person_details(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v2/persons/30",
        json={
            "success": True,
            "data": {"id": 30, "name": "Jane Doe"},
        },
    )

    result_dict = await get_person_details.ainvoke(_args(person_id=30))

    assert isinstance(result_dict, dict)
    result = GetPersonDetailsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_deals(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v2/deals",
        json={
            "success": True,
            "data": [{"id": 1, "title": "Deal A"}],
            "additional_data": {"next_cursor": None},
        },
    )

    result_dict = await list_deals.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListDealsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.deals) == 1


@pytest.mark.asyncio
async def test_list_lead_label_ids_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v1/leadLabels",
        json={
            "success": True,
            "data": [{"id": "uuid-1", "name": "Hot"}],
        },
    )

    result_dict = await list_lead_label_ids_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListLeadLabelIdsOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.options) == 1


@pytest.mark.asyncio
async def test_list_organization_label_ids_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v2/organizationFields",
        json={
            "success": True,
            "data": [{"key": "label", "options": [{"id": 1, "label": "Partner"}]}],
        },
    )

    result_dict = await list_organization_label_ids_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListOrganizationLabelIdsOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.options) == 1


@pytest.mark.asyncio
async def test_list_person_label_ids_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v1/personFields",
        json={
            "success": True,
            "data": [{"key": "label", "options": [{"id": 1, "label": "VIP"}]}],
        },
    )

    result_dict = await list_person_label_ids_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListPersonLabelIdsOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.options) == 1


@pytest.mark.asyncio
async def test_list_user_id_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v1/users",
        json={
            "success": True,
            "data": [{"id": 1, "name": "Admin User"}],
        },
    )

    result_dict = await list_user_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListUserIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.options) == 1


@pytest.mark.asyncio
async def test_merge_deals(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/api/v1/deals/5/merge",
        json={
            "success": True,
            "data": {"id": 10, "title": "Merged Deal"},
        },
    )

    result_dict = await merge_deals.ainvoke(_args(deal_id="5", target_deal_id="10"))

    assert isinstance(result_dict, dict)
    result = MergeDealsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_merge_persons(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/api/v1/persons/5/merge",
        json={
            "success": True,
            "data": {"id": 10, "name": "Merged Person"},
        },
    )

    result_dict = await merge_persons.ainvoke(_args(person_id=5, target_person_id=10))

    assert isinstance(result_dict, dict)
    result = MergePersonsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_remove_duplicate_notes(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v1/notes?deal_id=5&start=0&limit=100",
        json={
            "success": True,
            "data": [
                {"id": 1, "content": "Hello"},
                {"id": 2, "content": "Hello"},
            ],
            "additional_data": {"pagination": {"more_items_in_collection": False}},
        },
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/api/v1/notes/2",
        json={"success": True},
    )

    result_dict = await remove_duplicate_notes.ainvoke(_args(deal_id="5"))

    assert isinstance(result_dict, dict)
    result = RemoveDuplicateNotesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.duplicates_found == 1


@pytest.mark.asyncio
async def test_remove_labels(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v2/deals/5",
        json={"success": True, "data": {"id": 5, "label_ids": [1, 2, 3]}},
    )
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/v2/deals/5",
        json={"success": True, "data": {"id": 5, "label_ids": [1, 3]}},
    )

    result_dict = await remove_labels.ainvoke(_args(type="deal", entity_id="5", label_ids=["2"]))

    assert isinstance(result_dict, dict)
    result = RemoveLabelsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_leads(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v2/leads/search?term=test",
        json={
            "success": True,
            "data": {"items": [{"id": "lead-1", "title": "Test Lead"}]},
        },
    )

    result_dict = await search_leads.ainvoke(_args(term="test"))

    assert isinstance(result_dict, dict)
    result = SearchLeadsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_search_notes(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v1/notes?deal_id=5&start=0&limit=100",
        json={
            "success": True,
            "data": [{"id": 1, "content": "Important note about project"}],
            "additional_data": {"pagination": {"more_items_in_collection": False}},
        },
    )

    result_dict = await search_notes.ainvoke(_args(deal_id="5", search_term="project"))

    assert isinstance(result_dict, dict)
    result = SearchNotesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_search_persons(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/v2/persons/search?term=jane",
        json={
            "success": True,
            "data": {"items": [{"id": 30, "name": "Jane Doe"}]},
        },
    )

    result_dict = await search_persons.ainvoke(_args(term="jane"))

    assert isinstance(result_dict, dict)
    result = SearchPersonsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_update_deal(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/v2/deals/10",
        json={
            "success": True,
            "data": {"id": 10, "title": "Updated Deal"},
        },
    )

    result_dict = await update_deal.ainvoke(_args(deal_id="10", title="Updated Deal"))

    assert isinstance(result_dict, dict)
    result = UpdateDealOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_lead(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/v1/leads/abc-123",
        json={
            "success": True,
            "data": {"id": "abc-123", "title": "Updated Lead"},
        },
    )

    result_dict = await update_lead.ainvoke(_args(lead_id="abc-123", title="Updated Lead"))

    assert isinstance(result_dict, dict)
    result = UpdateLeadOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_person(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/v2/persons/30",
        json={
            "success": True,
            "data": {"id": 30, "name": "Jane Smith"},
        },
    )

    result_dict = await update_person.ainvoke(_args(person_id=30, name="Jane Smith"))

    assert isinstance(result_dict, dict)
    result = UpdatePersonOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_deal_empty_credential(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """Failure path: empty access_token returns error without hitting the wire."""
    result_dict = await get_deal.ainvoke(
        _args(deal_id="10", auth_data={"access_token": "", "api_domain": "https://api.pipedrive.com"})
    )
    assert isinstance(result_dict, dict)
    result = GetDealOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
