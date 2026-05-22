"""Pipedrive LangChain @tool functions."""
from __future__ import annotations

from html import unescape
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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
    LabelOption,
    LeadItem,
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
    UserOption,
)

__all__ = [
    "add_activity",
    "add_deal",
    "add_labels",
    "add_lead",
    "add_note",
    "add_organization",
    "add_person",
    "get_all_leads",
    "get_deal",
    "get_lead_by_id",
    "get_person_details",
    "list_deals",
    "list_lead_label_ids_options",
    "list_organization_label_ids_options",
    "list_person_label_ids_options",
    "list_user_id_options",
    "merge_deals",
    "merge_persons",
    "remove_duplicate_notes",
    "remove_labels",
    "search_leads",
    "search_notes",
    "search_persons",
    "update_deal",
    "update_lead",
    "update_person",
]

_TIMEOUT = 30.0


def _base_url(auth_data: dict[str, Any]) -> str:
    domain: str = str(auth_data.get("api_domain", "https://api.pipedrive.com"))
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    return domain.rstrip("/")


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class AddActivityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subject: str = Field(description="Subject of the activity")
    type: str = Field(description="Type of the activity (e.g. call, meeting, task)")
    owner_id: int | None = Field(default=None, description="ID of the user to assign to")
    deal_id: str | None = Field(default=None, description="ID of the associated deal")
    lead_id: str | None = Field(default=None, description="ID of the associated lead")
    org_id: int | None = Field(default=None, description="ID of the associated organization")
    project_id: str | None = Field(default=None, description="ID of the associated project")
    due_date: str | None = Field(default=None, description="Due date. Format: YYYY-MM-DD")
    due_time: str | None = Field(default=None, description="Due time in UTC. Format: HH:MM")
    duration: str | None = Field(default=None, description="Duration. Format: HH:MM")
    busy: bool | None = Field(default=None, description="Set as Busy or Free")
    done: bool | None = Field(default=None, description="Whether the activity is done")
    note: str | None = Field(default=None, description="Note in HTML format")
    public_description: str | None = Field(default=None, description="Public description for external calendar sync")


class AddDealInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="Deal title")
    owner_id: int | None = Field(default=None, description="ID of the owner user")
    person_id: int | None = Field(default=None, description="ID of the associated person")
    org_id: int | None = Field(default=None, description="ID of the associated organization")
    pipeline_id: int | None = Field(default=None, description="ID of the pipeline")
    stage_id: int | None = Field(default=None, description="ID of the stage")
    value: str | None = Field(default=None, description="Value of the deal")
    currency: str | None = Field(default=None, description="Currency (3-character code)")
    status: str | None = Field(default=None, description="Status: open, won, lost, deleted")
    probability: int | None = Field(default=None, description="Probability percentage")
    lost_reason: str | None = Field(default=None, description="Reason for loss")
    visible_to: int | None = Field(default=None, description="Visibility: 1=private, 3=shared")
    expected_close_date: str | None = Field(default=None, description="Expected close date. Format: YYYY-MM-DD")
    note: str | None = Field(default=None, description="Note to attach after creation")


class AddLabelsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    type: str = Field(description="Item type: lead, person, deal, organization")
    label_ids: list[str] = Field(description="Label IDs to add")
    lead_id: str | None = Field(default=None, description="Lead ID (when type=lead)")
    person_id: int | None = Field(default=None, description="Person ID (when type=person)")
    deal_id: str | None = Field(default=None, description="Deal ID (when type=deal)")
    organization_id: int | None = Field(default=None, description="Organization ID (when type=organization)")
    replace_existing_labels: bool = Field(default=False, description="Replace existing labels instead of appending")


class AddLeadInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="The name of the lead")
    person_id: int | None = Field(default=None, description="Person ID to link to")
    organization_id: int | None = Field(default=None, description="Organization ID to link to")
    owner_id: int | None = Field(default=None, description="Owner user ID")
    label_ids: list[str] | None = Field(default=None, description="Lead label IDs (UUIDs)")
    expected_close_date: str | None = Field(default=None, description="Expected close date. Format: YYYY-MM-DD")
    visible_to: str | None = Field(default=None, description="Visibility: 1, 3, 5, 7")
    was_seen: bool | None = Field(default=None, description="Whether the lead was seen")
    note: str | None = Field(default=None, description="A note to add")


class AddNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    content: str = Field(description="Note content in HTML format")
    lead_id: str | None = Field(default=None, description="Lead ID to attach to")
    deal_id: str | None = Field(default=None, description="Deal ID to attach to")
    person_id: int | None = Field(default=None, description="Person ID to attach to")
    organization_id: int | None = Field(default=None, description="Organization ID to attach to")
    user_id: int | None = Field(default=None, description="Author user ID (admin only)")
    pinned_to_deal_flag: bool = Field(default=False, description="Pin to deal")
    pinned_to_lead_flag: bool = Field(default=False, description="Pin to lead")
    pinned_to_org_flag: bool = Field(default=False, description="Pin to organization")
    pinned_to_person_flag: bool = Field(default=False, description="Pin to person")


class AddOrganizationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="Organization name")
    owner_id: int | None = Field(default=None, description="Owner user ID")
    visible_to: int | None = Field(default=None, description="Visibility: 1=private, 3=shared")


class AddPersonInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="Person name")
    owner_id: int | None = Field(default=None, description="Owner user ID")
    org_id: int | None = Field(default=None, description="Organization ID")
    emails: list[dict[str, Any]] | None = Field(default=None, description="Email addresses: [{value, primary, label}]")
    phones: list[dict[str, Any]] | None = Field(default=None, description="Phone numbers: [{value, primary, label}]")
    visible_to: int | None = Field(default=None, description="Visibility: 1=private, 3=shared")


class GetAllLeadsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_results: int | None = Field(default=None, description="Maximum results to return")
    owner_id: int | None = Field(default=None, description="Filter by owner user ID")
    person_id: int | None = Field(default=None, description="Filter by person ID")
    organization_id: int | None = Field(default=None, description="Filter by organization ID")
    filter_id: int | None = Field(default=None, description="Filter ID to apply")
    sort: str | None = Field(default=None, description="Sort field and direction")


class GetDealInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    deal_id: str = Field(description="The ID of the deal")


class GetLeadByIdInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    lead_id: str = Field(description="The ID of the lead")


class GetPersonDetailsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    person_id: int = Field(description="The ID of the person")


class ListDealsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    filter_id: int | None = Field(default=None, description="Filter ID")
    owner_id: int | None = Field(default=None, description="Owner user ID")
    person_id: int | None = Field(default=None, description="Person ID")
    organization_id: int | None = Field(default=None, description="Organization ID")
    pipeline_id: int | None = Field(default=None, description="Pipeline ID")
    stage_id: int | None = Field(default=None, description="Stage ID")
    status: str | None = Field(default=None, description="Status: open, won, lost, deleted")
    sort_by: str | None = Field(default=None, description="Sort by: id, update_time, add_time")
    sort_direction: str | None = Field(default=None, description="Sort direction: asc, desc")
    limit: int | None = Field(default=None, description="Limit (max 500)")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class ListLeadLabelIdsOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListOrganizationLabelIdsOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListPersonLabelIdsOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListUserIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class MergeDealsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    deal_id: str = Field(description="ID of the deal to merge")
    target_deal_id: str = Field(description="ID of the target deal to merge into")


class MergePersonsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    person_id: int = Field(description="ID of the person to merge")
    target_person_id: int = Field(description="ID of the target person to merge into")


class RemoveDuplicateNotesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    lead_id: str | None = Field(default=None, description="Lead ID")
    deal_id: str | None = Field(default=None, description="Deal ID")
    person_id: int | None = Field(default=None, description="Person ID")
    organization_id: int | None = Field(default=None, description="Organization ID")
    user_id: int | None = Field(default=None, description="User ID")
    project_id: str | None = Field(default=None, description="Project ID")
    keyword: str | None = Field(default=None, description="Only deduplicate notes containing this keyword")


class RemoveLabelsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    type: str = Field(description="Item type: lead, person, deal, organization")
    entity_id: str = Field(description="ID of the entity")
    label_ids: list[str] = Field(description="Label IDs to remove")


class SearchLeadsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    term: str = Field(description="Search term (min 2 chars, or 1 with exact_match)")
    exact_match: bool | None = Field(default=None, description="Only exact matches")
    fields: list[str] | None = Field(default=None, description="Fields to search: custom_fields, notes, title")
    person_id: int | None = Field(default=None, description="Filter by person ID")
    organization_id: int | None = Field(default=None, description="Filter by organization ID")
    include_fields: str | None = Field(default=None, description="Include fields: lead.was_seen")


class SearchNotesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search_term: str | None = Field(default=None, description="Term to search in note content")
    lead_id: str | None = Field(default=None, description="Filter by lead ID")
    deal_id: str | None = Field(default=None, description="Filter by deal ID")
    person_id: int | None = Field(default=None, description="Filter by person ID")
    organization_id: int | None = Field(default=None, description="Filter by organization ID")
    user_id: int | None = Field(default=None, description="Filter by user ID")
    sort_field: str | None = Field(default=None, description="Sort field")
    sort_direction: str | None = Field(default=None, description="Sort direction: ASC, DESC")
    start_date: str | None = Field(default=None, description="Start date. Format: YYYY-MM-DD")
    end_date: str | None = Field(default=None, description="End date. Format: YYYY-MM-DD")
    max_results: int | None = Field(default=None, description="Max results")


class SearchPersonsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    term: str = Field(description="Search term (min 2 chars, or 1 with exact_match)")
    fields: list[str] | None = Field(default=None, description="Fields: custom_fields, email, notes, phone, name")
    exact_match: bool | None = Field(default=None, description="Only exact matches")
    organization_id: int | None = Field(default=None, description="Filter by organization ID")
    include_fields: str | None = Field(default=None, description="Include fields: person.picture")
    start: int | None = Field(default=None, description="Pagination start")
    limit: int | None = Field(default=None, description="Items per page")


class UpdateDealInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    deal_id: str = Field(description="ID of the deal to update")
    title: str | None = Field(default=None, description="New title")
    owner_id: int | None = Field(default=None, description="New owner user ID")
    person_id: int | None = Field(default=None, description="Person ID")
    org_id: int | None = Field(default=None, description="Organization ID")
    pipeline_id: int | None = Field(default=None, description="Pipeline ID")
    stage_id: int | None = Field(default=None, description="Stage ID")
    value: str | None = Field(default=None, description="Deal value")
    currency: str | None = Field(default=None, description="Currency code")
    status: str | None = Field(default=None, description="Status: open, won, lost, deleted")
    probability: int | None = Field(default=None, description="Probability percentage")
    lost_reason: str | None = Field(default=None, description="Reason for loss")
    visible_to: int | None = Field(default=None, description="Visibility: 1=private, 3=shared")
    note: str | None = Field(default=None, description="Note to add")


class UpdateLeadInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    lead_id: str = Field(description="ID of the lead to update")
    title: str | None = Field(default=None, description="New title")
    person_id: int | None = Field(default=None, description="Person ID to link to")
    organization_id: int | None = Field(default=None, description="Organization ID to link to")
    owner_id: int | None = Field(default=None, description="New owner user ID")
    label_ids: list[str] | None = Field(default=None, description="Lead label IDs (UUIDs)")
    expected_close_date: str | None = Field(default=None, description="Expected close date. Format: YYYY-MM-DD")
    visible_to: str | None = Field(default=None, description="Visibility: 1, 3, 5, 7")
    was_seen: bool | None = Field(default=None, description="Whether seen in UI")
    is_archived: bool | None = Field(default=None, description="Whether archived")


class UpdatePersonInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    person_id: int = Field(description="ID of the person to update")
    name: str | None = Field(default=None, description="New name")
    owner_id: int | None = Field(default=None, description="New owner user ID")
    org_id: int | None = Field(default=None, description="Organization ID")
    emails: list[dict[str, Any]] | None = Field(default=None, description="Emails: [{value, primary, label}]")
    phones: list[dict[str, Any]] | None = Field(default=None, description="Phones: [{value, primary, label}]")
    visible_to: int | None = Field(default=None, description="Visibility: 1=private, 3=shared")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddActivityInput)
@serialize_pydantic_return
async def add_activity(
    auth_type: str,
    auth_data: dict[str, Any],
    subject: str,
    type: str,
    owner_id: int | None = None,
    deal_id: str | None = None,
    lead_id: str | None = None,
    org_id: int | None = None,
    project_id: str | None = None,
    due_date: str | None = None,
    due_time: str | None = None,
    duration: str | None = None,
    busy: bool | None = None,
    done: bool | None = None,
    note: str | None = None,
    public_description: str | None = None,
) -> AddActivityOutput:
    """Add a new activity in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return AddActivityOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {"subject": subject, "type": type}
    for key, val in [
        ("owner_id", owner_id), ("deal_id", deal_id), ("lead_id", lead_id),
        ("org_id", org_id), ("project_id", project_id), ("due_date", due_date),
        ("due_time", due_time), ("duration", duration), ("busy_flag", busy),
        ("done", done), ("note", note), ("public_description", public_description),
    ]:
        if val is not None:
            body[key] = val
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{base}/api/v2/activities", headers=headers, json=body)
        if response.status_code not in (200, 201):
            return AddActivityOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return AddActivityOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddActivityOutput(success=False, error=f"Call failed: {exc}")
    return AddActivityOutput(success=True, data=data.get("data"))


@tool(args_schema=AddDealInput)
@serialize_pydantic_return
async def add_deal(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    owner_id: int | None = None,
    person_id: int | None = None,
    org_id: int | None = None,
    pipeline_id: int | None = None,
    stage_id: int | None = None,
    value: str | None = None,
    currency: str | None = None,
    status: str | None = None,
    probability: int | None = None,
    lost_reason: str | None = None,
    visible_to: int | None = None,
    expected_close_date: str | None = None,
    note: str | None = None,
) -> AddDealOutput:
    """Add a new deal in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return AddDealOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {"title": title}
    for key, val in [
        ("owner_id", owner_id), ("person_id", person_id), ("org_id", org_id),
        ("pipeline_id", pipeline_id), ("stage_id", stage_id), ("value", value),
        ("currency", currency), ("status", status), ("probability", probability),
        ("lost_reason", lost_reason), ("visible_to", visible_to),
        ("expected_close_date", expected_close_date),
    ]:
        if val is not None:
            body[key] = val
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{base}/api/v2/deals", headers=headers, json=body)
        if response.status_code not in (200, 201):
            return AddDealOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
        deal_data = data.get("data")
        if note and deal_data:
            deal_id_val = deal_data.get("id")
            if deal_id_val:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    await client.post(
                        f"{base}/api/v1/notes",
                        headers=headers,
                        json={"content": note, "deal_id": deal_id_val},
                    )
    except httpx.TimeoutException:
        return AddDealOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddDealOutput(success=False, error=f"Call failed: {exc}")
    return AddDealOutput(success=True, data=deal_data)


@tool(args_schema=AddLabelsInput)
@serialize_pydantic_return
async def add_labels(
    auth_type: str,
    auth_data: dict[str, Any],
    type: str,
    label_ids: list[str],
    lead_id: str | None = None,
    person_id: int | None = None,
    deal_id: str | None = None,
    organization_id: int | None = None,
    replace_existing_labels: bool = False,
) -> AddLabelsOutput:
    """Add labels to a lead, person, deal, or organization in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return AddLabelsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            final_labels = list(label_ids)
            if not replace_existing_labels:
                if type == "lead" and lead_id:
                    r = await client.get(f"{base}/api/v1/leads/{lead_id}", headers=headers)
                    if r.status_code == 200:
                        existing = r.json().get("data", {}).get("label_ids", [])
                        final_labels = list(set(existing + label_ids))
                elif type == "deal" and deal_id:
                    r = await client.get(f"{base}/api/v2/deals/{deal_id}", headers=headers)
                    if r.status_code == 200:
                        existing = r.json().get("data", {}).get("label_ids", [])
                        final_labels = list(set([str(x) for x in existing] + label_ids))
                elif type == "person" and person_id:
                    r = await client.get(f"{base}/api/v2/persons/{person_id}", headers=headers)
                    if r.status_code == 200:
                        existing = r.json().get("data", {}).get("label_ids", [])
                        final_labels = list(set([str(x) for x in existing] + label_ids))
                elif type == "organization" and organization_id:
                    r = await client.get(f"{base}/api/v2/organizations/{organization_id}", headers=headers)
                    if r.status_code == 200:
                        existing = r.json().get("data", {}).get("label_ids", [])
                        final_labels = list(set([str(x) for x in existing] + label_ids))
            update_body: dict[str, Any] = {"label_ids": final_labels}
            if type == "lead" and lead_id:
                response = await client.patch(f"{base}/api/v1/leads/{lead_id}", headers=headers, json=update_body)
            elif type == "deal" and deal_id:
                response = await client.patch(f"{base}/api/v2/deals/{deal_id}", headers=headers, json=update_body)
            elif type == "person" and person_id:
                response = await client.patch(f"{base}/api/v2/persons/{person_id}", headers=headers, json=update_body)
            elif type == "organization" and organization_id:
                response = await client.patch(f"{base}/api/v2/organizations/{organization_id}", headers=headers, json=update_body)
            else:
                return AddLabelsOutput(success=False, error=f"Missing entity ID for type '{type}'")
        if response.status_code not in (200, 201):
            return AddLabelsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return AddLabelsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddLabelsOutput(success=False, error=f"Call failed: {exc}")
    return AddLabelsOutput(success=True, data=data.get("data"))


@tool(args_schema=AddLeadInput)
@serialize_pydantic_return
async def add_lead(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    person_id: int | None = None,
    organization_id: int | None = None,
    owner_id: int | None = None,
    label_ids: list[str] | None = None,
    expected_close_date: str | None = None,
    visible_to: str | None = None,
    was_seen: bool | None = None,
    note: str | None = None,
) -> AddLeadOutput:
    """Create a new lead in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return AddLeadOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {"title": title}
    for key, val in [
        ("person_id", person_id), ("organization_id", organization_id),
        ("owner_id", owner_id), ("label_ids", label_ids),
        ("expected_close_date", expected_close_date), ("visible_to", visible_to),
        ("was_seen", was_seen),
    ]:
        if val is not None:
            body[key] = val
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{base}/api/v1/leads", headers=headers, json=body)
        if response.status_code not in (200, 201):
            return AddLeadOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
        lead_data = data.get("data")
        if note and lead_data:
            new_lead_id = lead_data.get("id")
            if new_lead_id:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    await client.post(
                        f"{base}/api/v1/notes",
                        headers=headers,
                        json={"content": note, "lead_id": new_lead_id},
                    )
    except httpx.TimeoutException:
        return AddLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddLeadOutput(success=False, error=f"Call failed: {exc}")
    return AddLeadOutput(success=True, data=lead_data)


@tool(args_schema=AddNoteInput)
@serialize_pydantic_return
async def add_note(
    auth_type: str,
    auth_data: dict[str, Any],
    content: str,
    lead_id: str | None = None,
    deal_id: str | None = None,
    person_id: int | None = None,
    organization_id: int | None = None,
    user_id: int | None = None,
    pinned_to_deal_flag: bool = False,
    pinned_to_lead_flag: bool = False,
    pinned_to_org_flag: bool = False,
    pinned_to_person_flag: bool = False,
) -> AddNoteOutput:
    """Add a new note to a lead, deal, person, or organization in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return AddNoteOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {"content": content}
    for key, val in [
        ("lead_id", lead_id), ("deal_id", deal_id), ("person_id", person_id),
        ("org_id", organization_id), ("user_id", user_id),
    ]:
        if val is not None:
            body[key] = val
    if pinned_to_deal_flag:
        body["pinned_to_deal_flag"] = 1
    if pinned_to_lead_flag:
        body["pinned_to_lead_flag"] = 1
    if pinned_to_org_flag:
        body["pinned_to_organization_flag"] = 1
    if pinned_to_person_flag:
        body["pinned_to_person_flag"] = 1
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{base}/api/v1/notes", headers=headers, json=body)
        if response.status_code not in (200, 201):
            return AddNoteOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return AddNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddNoteOutput(success=False, error=f"Call failed: {exc}")
    return AddNoteOutput(success=True, data=data.get("data"))


@tool(args_schema=AddOrganizationInput)
@serialize_pydantic_return
async def add_organization(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    owner_id: int | None = None,
    visible_to: int | None = None,
) -> AddOrganizationOutput:
    """Add a new organization in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return AddOrganizationOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {"name": name}
    if owner_id is not None:
        body["owner_id"] = owner_id
    if visible_to is not None:
        body["visible_to"] = visible_to
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{base}/api/v2/organizations", headers=headers, json=body)
        if response.status_code not in (200, 201):
            return AddOrganizationOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return AddOrganizationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddOrganizationOutput(success=False, error=f"Call failed: {exc}")
    return AddOrganizationOutput(success=True, data=data.get("data"))


@tool(args_schema=AddPersonInput)
@serialize_pydantic_return
async def add_person(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    owner_id: int | None = None,
    org_id: int | None = None,
    emails: list[dict[str, Any]] | None = None,
    phones: list[dict[str, Any]] | None = None,
    visible_to: int | None = None,
) -> AddPersonOutput:
    """Add a new person (contact) in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return AddPersonOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {"name": name}
    for key, val in [
        ("owner_id", owner_id), ("org_id", org_id), ("emails", emails),
        ("phones", phones), ("visible_to", visible_to),
    ]:
        if val is not None:
            body[key] = val
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{base}/api/v2/persons", headers=headers, json=body)
        if response.status_code not in (200, 201):
            return AddPersonOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return AddPersonOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddPersonOutput(success=False, error=f"Call failed: {exc}")
    return AddPersonOutput(success=True, data=data.get("data"))


@tool(args_schema=GetAllLeadsInput)
@serialize_pydantic_return
async def get_all_leads(
    auth_type: str,
    auth_data: dict[str, Any],
    max_results: int | None = None,
    owner_id: int | None = None,
    person_id: int | None = None,
    organization_id: int | None = None,
    filter_id: int | None = None,
    sort: str | None = None,
) -> GetAllLeadsOutput:
    """Get all leads from Pipedrive with optional filtering."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return GetAllLeadsOutput(success=False, error="Missing access token. Please re-authenticate.")
    params: dict[str, Any] = {}
    if owner_id is not None:
        params["owner_id"] = owner_id
    if person_id is not None:
        params["person_id"] = person_id
    if organization_id is not None:
        params["organization_id"] = organization_id
    if filter_id is not None:
        params["filter_id"] = filter_id
    if sort is not None:
        params["sort"] = sort
    try:
        all_leads: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            start = 0
            pages_seen = 0
            while pages_seen < 50:
                pages_seen += 1
                params["start"] = start
                params["limit"] = 100
                response = await client.get(f"{base}/api/v1/leads", headers=headers, params=params)
                if response.status_code != 200:
                    return GetAllLeadsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
                body = response.json()
                items = body.get("data") or []
                all_leads.extend(items)
                if max_results and len(all_leads) >= max_results:
                    all_leads = all_leads[:max_results]
                    break
                pagination = body.get("additional_data", {}).get("pagination", {})
                if not pagination.get("more_items_in_collection"):
                    break
                start = pagination.get("next_start", start + 100)
    except httpx.TimeoutException:
        return GetAllLeadsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAllLeadsOutput(success=False, error=f"Call failed: {exc}")
    leads = [
        LeadItem(
            id=item.get("id"),
            title=item.get("title"),
            owner_id=item.get("owner_id"),
            person_id=item.get("person_id"),
            organization_id=item.get("organization_id"),
            was_seen=item.get("was_seen"),
            expected_close_date=item.get("expected_close_date"),
            add_time=item.get("add_time"),
            update_time=item.get("update_time"),
        )
        for item in all_leads
    ]
    return GetAllLeadsOutput(success=True, leads=leads, total=len(leads))


@tool(args_schema=GetDealInput)
@serialize_pydantic_return
async def get_deal(
    auth_type: str,
    auth_data: dict[str, Any],
    deal_id: str,
) -> GetDealOutput:
    """Get a deal by its ID in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return GetDealOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v2/deals/{deal_id}", headers=headers)
        if response.status_code != 200:
            return GetDealOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetDealOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDealOutput(success=False, error=f"Call failed: {exc}")
    return GetDealOutput(success=True, data=data.get("data"))


@tool(args_schema=GetLeadByIdInput)
@serialize_pydantic_return
async def get_lead_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    lead_id: str,
) -> GetLeadByIdOutput:
    """Get a lead by its ID in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return GetLeadByIdOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v1/leads/{lead_id}", headers=headers)
        if response.status_code != 200:
            return GetLeadByIdOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetLeadByIdOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetLeadByIdOutput(success=False, error=f"Call failed: {exc}")
    return GetLeadByIdOutput(success=True, data=data.get("data"))


@tool(args_schema=GetPersonDetailsInput)
@serialize_pydantic_return
async def get_person_details(
    auth_type: str,
    auth_data: dict[str, Any],
    person_id: int,
) -> GetPersonDetailsOutput:
    """Get details of a person by their ID in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return GetPersonDetailsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v2/persons/{person_id}", headers=headers)
        if response.status_code != 200:
            return GetPersonDetailsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetPersonDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetPersonDetailsOutput(success=False, error=f"Call failed: {exc}")
    return GetPersonDetailsOutput(success=True, data=data.get("data"))


@tool(args_schema=ListDealsInput)
@serialize_pydantic_return
async def list_deals(
    auth_type: str,
    auth_data: dict[str, Any],
    filter_id: int | None = None,
    owner_id: int | None = None,
    person_id: int | None = None,
    organization_id: int | None = None,
    pipeline_id: int | None = None,
    stage_id: int | None = None,
    status: str | None = None,
    sort_by: str | None = None,
    sort_direction: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> ListDealsOutput:
    """List deals in Pipedrive with optional filtering and pagination."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return ListDealsOutput(success=False, error="Missing access token. Please re-authenticate.")
    params: dict[str, Any] = {}
    for key, val in [
        ("filter_id", filter_id), ("owner_id", owner_id), ("person_id", person_id),
        ("org_id", organization_id), ("pipeline_id", pipeline_id), ("stage_id", stage_id),
        ("status", status), ("sort_by", sort_by), ("sort_direction", sort_direction),
        ("limit", limit), ("cursor", cursor),
    ]:
        if val is not None:
            params[key] = val
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v2/deals", headers=headers, params=params)
        if response.status_code != 200:
            return ListDealsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListDealsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDealsOutput(success=False, error=f"Call failed: {exc}")
    deals = data.get("data") or []
    next_cursor = data.get("additional_data", {}).get("next_cursor")
    return ListDealsOutput(success=True, deals=deals, cursor=next_cursor)


@tool(args_schema=ListLeadLabelIdsOptionsInput)
@serialize_pydantic_return
async def list_lead_label_ids_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListLeadLabelIdsOptionsOutput:
    """Retrieve available lead label options from Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return ListLeadLabelIdsOptionsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v1/leadLabels", headers=headers)
        if response.status_code != 200:
            return ListLeadLabelIdsOptionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListLeadLabelIdsOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListLeadLabelIdsOptionsOutput(success=False, error=f"Call failed: {exc}")
    items = data.get("data") or []
    options = [LabelOption(label=item.get("name"), value=item.get("id")) for item in items]
    return ListLeadLabelIdsOptionsOutput(success=True, options=options)


@tool(args_schema=ListOrganizationLabelIdsOptionsInput)
@serialize_pydantic_return
async def list_organization_label_ids_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListOrganizationLabelIdsOptionsOutput:
    """Retrieve available organization label options from Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return ListOrganizationLabelIdsOptionsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v2/organizationFields", headers=headers)
        if response.status_code != 200:
            return ListOrganizationLabelIdsOptionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListOrganizationLabelIdsOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListOrganizationLabelIdsOptionsOutput(success=False, error=f"Call failed: {exc}")
    fields = data.get("data") or []
    options: list[LabelOption] = []
    for field in fields:
        if field.get("key") == "label":
            for opt in field.get("options") or []:
                options.append(LabelOption(label=opt.get("label"), value=str(opt.get("id", ""))))
            break
    return ListOrganizationLabelIdsOptionsOutput(success=True, options=options)


@tool(args_schema=ListPersonLabelIdsOptionsInput)
@serialize_pydantic_return
async def list_person_label_ids_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListPersonLabelIdsOptionsOutput:
    """Retrieve available person label options from Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return ListPersonLabelIdsOptionsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v1/personFields", headers=headers)
        if response.status_code != 200:
            return ListPersonLabelIdsOptionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListPersonLabelIdsOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListPersonLabelIdsOptionsOutput(success=False, error=f"Call failed: {exc}")
    fields = data.get("data") or []
    options: list[LabelOption] = []
    for field in fields:
        if field.get("key") == "label":
            for opt in field.get("options") or []:
                options.append(LabelOption(label=opt.get("label"), value=str(opt.get("id", ""))))
            break
    return ListPersonLabelIdsOptionsOutput(success=True, options=options)


@tool(args_schema=ListUserIdOptionsInput)
@serialize_pydantic_return
async def list_user_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListUserIdOptionsOutput:
    """Retrieve available user options from Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return ListUserIdOptionsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v1/users", headers=headers)
        if response.status_code != 200:
            return ListUserIdOptionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListUserIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListUserIdOptionsOutput(success=False, error=f"Call failed: {exc}")
    items = data.get("data") or []
    options = [UserOption(label=item.get("name"), value=item.get("id")) for item in items]
    return ListUserIdOptionsOutput(success=True, options=options)


@tool(args_schema=MergeDealsInput)
@serialize_pydantic_return
async def merge_deals(
    auth_type: str,
    auth_data: dict[str, Any],
    deal_id: str,
    target_deal_id: str,
) -> MergeDealsOutput:
    """Merge two deals in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return MergeDealsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{base}/api/v1/deals/{deal_id}/merge",
                headers=headers,
                json={"merge_with_id": target_deal_id},
            )
        if response.status_code != 200:
            return MergeDealsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return MergeDealsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return MergeDealsOutput(success=False, error=f"Call failed: {exc}")
    return MergeDealsOutput(success=True, data=data.get("data"))


@tool(args_schema=MergePersonsInput)
@serialize_pydantic_return
async def merge_persons(
    auth_type: str,
    auth_data: dict[str, Any],
    person_id: int,
    target_person_id: int,
) -> MergePersonsOutput:
    """Merge two persons in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return MergePersonsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{base}/api/v1/persons/{person_id}/merge",
                headers=headers,
                json={"merge_with_id": target_person_id},
            )
        if response.status_code != 200:
            return MergePersonsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return MergePersonsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return MergePersonsOutput(success=False, error=f"Call failed: {exc}")
    return MergePersonsOutput(success=True, data=data.get("data"))


@tool(args_schema=RemoveDuplicateNotesInput)
@serialize_pydantic_return
async def remove_duplicate_notes(
    auth_type: str,
    auth_data: dict[str, Any],
    lead_id: str | None = None,
    deal_id: str | None = None,
    person_id: int | None = None,
    organization_id: int | None = None,
    user_id: int | None = None,
    project_id: str | None = None,
    keyword: str | None = None,
) -> RemoveDuplicateNotesOutput:
    """Remove duplicate notes from an object in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return RemoveDuplicateNotesOutput(success=False, error="Missing access token. Please re-authenticate.")
    params: dict[str, Any] = {}
    if lead_id:
        params["lead_id"] = lead_id
    if deal_id:
        params["deal_id"] = deal_id
    if person_id:
        params["person_id"] = person_id
    if organization_id:
        params["org_id"] = organization_id
    if user_id:
        params["user_id"] = user_id
    if project_id:
        params["project_id"] = project_id
    try:
        all_notes: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            start = 0
            pages_seen = 0
            while pages_seen < 50:
                pages_seen += 1
                params["start"] = start
                params["limit"] = 100
                response = await client.get(f"{base}/api/v1/notes", headers=headers, params=params)
                if response.status_code != 200:
                    return RemoveDuplicateNotesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
                body = response.json()
                items = body.get("data") or []
                all_notes.extend(items)
                pagination = body.get("additional_data", {}).get("pagination", {})
                if not pagination.get("more_items_in_collection"):
                    break
                start = pagination.get("next_start", start + 100)
            if keyword:
                kw_lower = keyword.lower()
                all_notes = [n for n in all_notes if kw_lower in unescape(n.get("content", "")).lower()]
            seen: dict[str, dict[str, Any]] = {}
            duplicates: list[dict[str, Any]] = []
            for note_item in all_notes:
                normalized = unescape(note_item.get("content", "")).strip().lower()
                if normalized in seen:
                    duplicates.append(note_item)
                else:
                    seen[normalized] = note_item
            removed: list[dict[str, Any]] = []
            for dup in duplicates:
                note_id = dup.get("id")
                if note_id:
                    del_resp = await client.delete(f"{base}/api/v1/notes/{note_id}", headers=headers)
                    if del_resp.status_code == 200:
                        removed.append(dup)
    except httpx.TimeoutException:
        return RemoveDuplicateNotesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RemoveDuplicateNotesOutput(success=False, error=f"Call failed: {exc}")
    return RemoveDuplicateNotesOutput(
        success=True,
        total_notes=len(all_notes),
        duplicates_found=len(duplicates),
        duplicates_removed=removed,
    )


@tool(args_schema=RemoveLabelsInput)
@serialize_pydantic_return
async def remove_labels(
    auth_type: str,
    auth_data: dict[str, Any],
    type: str,
    entity_id: str,
    label_ids: list[str],
) -> RemoveLabelsOutput:
    """Remove labels from a lead, person, deal, or organization in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return RemoveLabelsOutput(success=False, error="Missing access token. Please re-authenticate.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            if type == "lead":
                r = await client.get(f"{base}/api/v1/leads/{entity_id}", headers=headers)
            elif type == "deal":
                r = await client.get(f"{base}/api/v2/deals/{entity_id}", headers=headers)
            elif type == "person":
                r = await client.get(f"{base}/api/v2/persons/{entity_id}", headers=headers)
            elif type == "organization":
                r = await client.get(f"{base}/api/v2/organizations/{entity_id}", headers=headers)
            else:
                return RemoveLabelsOutput(success=False, error=f"Unknown type: {type}")
            if r.status_code != 200:
                return RemoveLabelsOutput(success=False, error=f"Failed to get entity ({r.status_code}): {r.text}")
            entity_data = r.json().get("data", {})
            current_labels = [str(x) for x in (entity_data.get("label_ids") or [])]
            remove_set = set(label_ids)
            new_labels = [lbl for lbl in current_labels if lbl not in remove_set]
            update_body: dict[str, Any] = {"label_ids": new_labels}
            if type == "lead":
                response = await client.patch(f"{base}/api/v1/leads/{entity_id}", headers=headers, json=update_body)
            elif type == "deal":
                response = await client.patch(f"{base}/api/v2/deals/{entity_id}", headers=headers, json=update_body)
            elif type == "person":
                response = await client.patch(f"{base}/api/v2/persons/{entity_id}", headers=headers, json=update_body)
            else:
                response = await client.patch(f"{base}/api/v2/organizations/{entity_id}", headers=headers, json=update_body)
        if response.status_code not in (200, 201):
            return RemoveLabelsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return RemoveLabelsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RemoveLabelsOutput(success=False, error=f"Call failed: {exc}")
    return RemoveLabelsOutput(success=True, data=data.get("data"))


@tool(args_schema=SearchLeadsInput)
@serialize_pydantic_return
async def search_leads(
    auth_type: str,
    auth_data: dict[str, Any],
    term: str,
    exact_match: bool | None = None,
    fields: list[str] | None = None,
    person_id: int | None = None,
    organization_id: int | None = None,
    include_fields: str | None = None,
) -> SearchLeadsOutput:
    """Search for leads by name or email in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return SearchLeadsOutput(success=False, error="Missing access token. Please re-authenticate.")
    params: dict[str, Any] = {"term": term}
    if exact_match is not None:
        params["exact_match"] = exact_match
    if fields:
        params["fields"] = ",".join(fields)
    if person_id is not None:
        params["person_id"] = person_id
    if organization_id is not None:
        params["organization_id"] = organization_id
    if include_fields:
        params["include_fields"] = include_fields
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v2/leads/search", headers=headers, params=params)
        if response.status_code != 200:
            return SearchLeadsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return SearchLeadsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchLeadsOutput(success=False, error=f"Call failed: {exc}")
    items = data.get("data", {}).get("items") or []
    return SearchLeadsOutput(success=True, items=items)


@tool(args_schema=SearchNotesInput)
@serialize_pydantic_return
async def search_notes(
    auth_type: str,
    auth_data: dict[str, Any],
    search_term: str | None = None,
    lead_id: str | None = None,
    deal_id: str | None = None,
    person_id: int | None = None,
    organization_id: int | None = None,
    user_id: int | None = None,
    sort_field: str | None = None,
    sort_direction: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_results: int | None = None,
) -> SearchNotesOutput:
    """Search for notes in Pipedrive with filtering options."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return SearchNotesOutput(success=False, error="Missing access token. Please re-authenticate.")
    params: dict[str, Any] = {}
    if lead_id:
        params["lead_id"] = lead_id
    if deal_id:
        params["deal_id"] = deal_id
    if person_id is not None:
        params["person_id"] = person_id
    if organization_id is not None:
        params["org_id"] = organization_id
    if user_id is not None:
        params["user_id"] = user_id
    if sort_field:
        params["sort"] = f"{sort_field} {sort_direction or 'DESC'}"
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    try:
        all_notes: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            start_offset = 0
            pages_seen = 0
            while pages_seen < 50:
                pages_seen += 1
                params["start"] = start_offset
                params["limit"] = 100
                response = await client.get(f"{base}/api/v1/notes", headers=headers, params=params)
                if response.status_code != 200:
                    return SearchNotesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
                body = response.json()
                items = body.get("data") or []
                all_notes.extend(items)
                if max_results and len(all_notes) >= max_results:
                    all_notes = all_notes[:max_results]
                    break
                pagination = body.get("additional_data", {}).get("pagination", {})
                if not pagination.get("more_items_in_collection"):
                    break
                start_offset = pagination.get("next_start", start_offset + 100)
    except httpx.TimeoutException:
        return SearchNotesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchNotesOutput(success=False, error=f"Call failed: {exc}")
    if search_term:
        term_lower = search_term.lower()
        all_notes = [n for n in all_notes if term_lower in (n.get("content") or "").lower()]
    return SearchNotesOutput(success=True, notes=all_notes, total=len(all_notes))


@tool(args_schema=SearchPersonsInput)
@serialize_pydantic_return
async def search_persons(
    auth_type: str,
    auth_data: dict[str, Any],
    term: str,
    fields: list[str] | None = None,
    exact_match: bool | None = None,
    organization_id: int | None = None,
    include_fields: str | None = None,
    start: int | None = None,
    limit: int | None = None,
) -> SearchPersonsOutput:
    """Search for persons by name, email, phone, or notes in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return SearchPersonsOutput(success=False, error="Missing access token. Please re-authenticate.")
    params: dict[str, Any] = {"term": term}
    if fields:
        params["fields"] = ",".join(fields)
    if exact_match is not None:
        params["exact_match"] = exact_match
    if organization_id is not None:
        params["organization_id"] = organization_id
    if include_fields:
        params["include_fields"] = include_fields
    if start is not None:
        params["start"] = start
    if limit is not None:
        params["limit"] = limit
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{base}/api/v2/persons/search", headers=headers, params=params)
        if response.status_code != 200:
            return SearchPersonsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return SearchPersonsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchPersonsOutput(success=False, error=f"Call failed: {exc}")
    items = data.get("data", {}).get("items") or []
    return SearchPersonsOutput(success=True, items=items)


@tool(args_schema=UpdateDealInput)
@serialize_pydantic_return
async def update_deal(
    auth_type: str,
    auth_data: dict[str, Any],
    deal_id: str,
    title: str | None = None,
    owner_id: int | None = None,
    person_id: int | None = None,
    org_id: int | None = None,
    pipeline_id: int | None = None,
    stage_id: int | None = None,
    value: str | None = None,
    currency: str | None = None,
    status: str | None = None,
    probability: int | None = None,
    lost_reason: str | None = None,
    visible_to: int | None = None,
    note: str | None = None,
) -> UpdateDealOutput:
    """Update the properties of a deal in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return UpdateDealOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {}
    for key, val in [
        ("title", title), ("owner_id", owner_id), ("person_id", person_id),
        ("org_id", org_id), ("pipeline_id", pipeline_id), ("stage_id", stage_id),
        ("value", value), ("currency", currency), ("status", status),
        ("probability", probability), ("lost_reason", lost_reason), ("visible_to", visible_to),
    ]:
        if val is not None:
            body[key] = val
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(f"{base}/api/v2/deals/{deal_id}", headers=headers, json=body)
        if response.status_code != 200:
            return UpdateDealOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
        if note:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                await client.post(
                    f"{base}/api/v1/notes",
                    headers=headers,
                    json={"content": note, "deal_id": deal_id},
                )
    except httpx.TimeoutException:
        return UpdateDealOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateDealOutput(success=False, error=f"Call failed: {exc}")
    return UpdateDealOutput(success=True, data=data.get("data"))


@tool(args_schema=UpdateLeadInput)
@serialize_pydantic_return
async def update_lead(
    auth_type: str,
    auth_data: dict[str, Any],
    lead_id: str,
    title: str | None = None,
    person_id: int | None = None,
    organization_id: int | None = None,
    owner_id: int | None = None,
    label_ids: list[str] | None = None,
    expected_close_date: str | None = None,
    visible_to: str | None = None,
    was_seen: bool | None = None,
    is_archived: bool | None = None,
) -> UpdateLeadOutput:
    """Update a lead in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return UpdateLeadOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {}
    for key, val in [
        ("title", title), ("person_id", person_id), ("organization_id", organization_id),
        ("owner_id", owner_id), ("label_ids", label_ids),
        ("expected_close_date", expected_close_date), ("visible_to", visible_to),
        ("was_seen", was_seen), ("is_archived", is_archived),
    ]:
        if val is not None:
            body[key] = val
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(f"{base}/api/v1/leads/{lead_id}", headers=headers, json=body)
        if response.status_code != 200:
            return UpdateLeadOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdateLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateLeadOutput(success=False, error=f"Call failed: {exc}")
    return UpdateLeadOutput(success=True, data=data.get("data"))


@tool(args_schema=UpdatePersonInput)
@serialize_pydantic_return
async def update_person(
    auth_type: str,
    auth_data: dict[str, Any],
    person_id: int,
    name: str | None = None,
    owner_id: int | None = None,
    org_id: int | None = None,
    emails: list[dict[str, Any]] | None = None,
    phones: list[dict[str, Any]] | None = None,
    visible_to: int | None = None,
) -> UpdatePersonOutput:
    """Update an existing person in Pipedrive."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    if not auth_data.get("access_token"):
        return UpdatePersonOutput(success=False, error="Missing access token. Please re-authenticate.")
    body: dict[str, Any] = {}
    for key, val in [
        ("name", name), ("owner_id", owner_id), ("org_id", org_id),
        ("emails", emails), ("phones", phones), ("visible_to", visible_to),
    ]:
        if val is not None:
            body[key] = val
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(f"{base}/api/v2/persons/{person_id}", headers=headers, json=body)
        if response.status_code != 200:
            return UpdatePersonOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdatePersonOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdatePersonOutput(success=False, error=f"Call failed: {exc}")
    return UpdatePersonOutput(success=True, data=data.get("data"))
