"""HubSpot LangChain ``@tool`` functions.

Wraps the **synchronous** ``hubspot-api-client`` SDK inside async tool
functions (same pattern as snowflake — preserved from legacy). 26
actions across contacts / companies / deals / tickets / engagements /
properties; shared helpers factor the four repeated shapes
(recent_*, get_*_by_id, create_*, update_*, search_*) into one
implementation each.

Token-based runtime convention (``auth_type, auth_data`` first args).
Paired ``oauth2 + bearer_token`` schemas.

Legacy did not wrap SDK calls in try/except; this migration wraps
them so SDK errors flow through our standard ``success=False``
envelope rather than propagating as exceptions to the modulex
runtime. Otherwise behavior is preserved verbatim.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "create_company",
    "create_contact",
    "create_deal",
    "create_meeting",
    "create_note",
    "create_task",
    "create_ticket",
    "get_company_activity",
    "get_company_by_id",
    "get_contact_by_id",
    "get_deal_by_id",
    "get_property",
    "get_recent_companies",
    "get_recent_contacts",
    "get_recent_deals",
    "get_recent_tickets",
    "get_ticket_by_id",
    "list_properties",
    "search_companies",
    "search_contacts",
    "search_deals",
    "search_tickets",
    "update_company",
    "update_contact",
    "update_deal",
    "update_ticket",
]


# --- Auth / SDK helpers ----------------------------------------------------


def _client(auth_type: str, auth_data: dict[str, Any]) -> Any:
    """Return an initialized HubSpot SDK client.

    Lazy import so manifest inspection works without the SDK installed.
    """
    from hubspot import HubSpot  # type: ignore[import-untyped]

    if auth_type == "oauth2":
        token = auth_data.get("access_token")
    elif auth_type == "bearer_token":
        token = auth_data.get("token")
    else:
        token = auth_data.get("access_token") or auth_data.get("token")
    return HubSpot(access_token=token)


def _validate(auth_data: dict[str, Any], action: str) -> str | None:
    if not (auth_data.get("access_token") or auth_data.get("token")):
        return f"HubSpot access token missing for {action}"
    return None


def _convert_datetimes(value: Any) -> Any:
    """Recursively convert ``datetime`` values to ISO strings."""
    if isinstance(value, dict):
        return {k: _convert_datetimes(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert_datetimes(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _to_dict(obj: Any) -> dict[str, Any]:
    """Map an SDK response object to a plain JSON-safe dict."""
    if hasattr(obj, "to_dict"):
        raw = obj.to_dict()
    else:
        raw = dict(obj) if obj else {}
    coerced = _convert_datetimes(raw)
    assert isinstance(coerced, dict)
    return coerced


# Imports for each object type's create/update SDK classes live at the
# module-call site; doing them lazily keeps the integration importable
# even when the SDK is missing.

_SEARCH_OBJECT_MODULES = {
    "contacts": "hubspot.crm.contacts",
    "companies": "hubspot.crm.companies",
    "deals": "hubspot.crm.deals",
    "tickets": "hubspot.crm.tickets",
}


def _public_object_search_request(object_type: str, **kwargs: Any) -> Any:
    import importlib

    mod = importlib.import_module(_SEARCH_OBJECT_MODULES[object_type])
    return mod.PublicObjectSearchRequest(**kwargs)


def _simple_create_input(object_type: str, **kwargs: Any) -> Any:
    import importlib

    mod = importlib.import_module(_SEARCH_OBJECT_MODULES[object_type])
    return mod.SimplePublicObjectInputForCreate(**kwargs)


def _simple_update_input(object_type: str, properties: dict[str, Any]) -> Any:
    import importlib

    mod = importlib.import_module(_SEARCH_OBJECT_MODULES[object_type])
    return mod.SimplePublicObjectInput(properties=properties)


def _engagement_create_input(sub_path: str, **kwargs: Any) -> Any:
    """Build a SimplePublicObjectInputForCreate for an engagement sub-type."""
    import importlib

    mod = importlib.import_module(f"hubspot.crm.objects.{sub_path}")
    return mod.SimplePublicObjectInputForCreate(**kwargs)


_DEFAULT_PROPERTIES = {
    "contacts": ["firstname", "lastname", "email", "phone", "company"],
    "companies": ["name", "domain", "website", "phone", "industry"],
    "deals": ["dealname", "amount", "dealstage", "pipeline", "closedate"],
    "tickets": [
        "subject",
        "content",
        "hs_pipeline",
        "hs_pipeline_stage",
        "hs_ticket_priority",
    ],
}

_RECENT_SORT_FIELD = {
    "contacts": "lastmodifieddate",
    "companies": "hs_lastmodifieddate",
    "deals": "hs_lastmodifieddate",
    "tickets": "hs_lastmodifieddate",
}


def _api_for(client: Any, object_type: str) -> Any:
    """Return the ``client.crm.<object_type>`` namespace."""
    return getattr(client.crm, object_type)


def _do_recent(
    client: Any, object_type: str, limit: int, extra_properties: list[str]
) -> list[dict[str, Any]]:
    properties = _DEFAULT_PROPERTIES[object_type] + extra_properties
    request = _public_object_search_request(
        object_type,
        sorts=[
            {
                "propertyName": _RECENT_SORT_FIELD[object_type],
                "direction": "DESCENDING",
            }
        ],
        limit=limit,
        properties=properties,
    )
    response = _api_for(client, object_type).search_api.do_search(
        public_object_search_request=request
    )
    return [_to_dict(item) for item in response.results]


def _do_search(
    client: Any,
    object_type: str,
    query: str,
    limit: int,
    properties: list[str] | None,
) -> tuple[list[dict[str, Any]], int]:
    request = _public_object_search_request(
        object_type,
        query=query,
        limit=limit,
        properties=properties or _DEFAULT_PROPERTIES[object_type],
    )
    response = _api_for(client, object_type).search_api.do_search(
        public_object_search_request=request
    )
    return [_to_dict(item) for item in response.results], int(response.total)


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2 or bearer_token)")
    auth_data: dict[str, Any] = Field(
        description="Auth data carrying access_token / token"
    )


class GetRecentInput(_AuthFields):
    limit: int = Field(default=10, description="Maximum results")


class GetByIdInput(_AuthFields):
    properties: list[str] | None = Field(default=None)


class GetContactByIdInput(GetByIdInput):
    contact_id: str = Field(description="HubSpot contact ID")


class GetCompanyByIdInput(GetByIdInput):
    company_id: str = Field(description="HubSpot company ID")


class GetDealByIdInput(GetByIdInput):
    deal_id: str = Field(description="HubSpot deal ID")


class GetTicketByIdInput(GetByIdInput):
    ticket_id: str = Field(description="HubSpot ticket ID")


class CreateContactInput(_AuthFields):
    email: str = Field(description="Contact email address")
    firstname: str | None = None
    lastname: str | None = None
    phone: str | None = None
    company: str | None = None
    website: str | None = None
    properties: dict[str, Any] | None = None


class CreateCompanyInput(_AuthFields):
    name: str = Field(description="Company name")
    domain: str | None = None
    industry: str | None = None
    phone: str | None = None
    website: str | None = None
    properties: dict[str, Any] | None = None


class CreateDealInput(_AuthFields):
    dealname: str = Field(description="Deal name")
    pipeline: str | None = None
    dealstage: str | None = None
    amount: float | None = None
    closedate: str | None = None
    properties: dict[str, Any] | None = None


class CreateTicketInput(_AuthFields):
    subject: str = Field(description="Ticket subject")
    content: str | None = None
    hs_pipeline: str | None = None
    hs_pipeline_stage: str | None = None
    hs_ticket_priority: str | None = None
    properties: dict[str, Any] | None = None


class UpdateInput(_AuthFields):
    properties: dict[str, Any] = Field(description="Properties to update")


class UpdateContactInput(UpdateInput):
    contact_id: str = Field(description="Contact ID to update")


class UpdateCompanyInput(UpdateInput):
    company_id: str = Field(description="Company ID to update")


class UpdateDealInput(UpdateInput):
    deal_id: str = Field(description="Deal ID to update")


class UpdateTicketInput(UpdateInput):
    ticket_id: str = Field(description="Ticket ID to update")


class SearchInput(_AuthFields):
    query: str = Field(description="Search query string")
    limit: int = Field(default=10)
    properties: list[str] | None = None


class GetCompanyActivityInput(_AuthFields):
    company_id: str = Field(description="HubSpot company ID")


class _EngagementAssoc(BaseModel):
    contact_ids: list[str] | None = None
    company_ids: list[str] | None = None
    deal_ids: list[str] | None = None


class CreateNoteInput(_AuthFields, _EngagementAssoc):
    body: str = Field(description="Note body content")


class CreateTaskInput(_AuthFields, _EngagementAssoc):
    subject: str = Field(description="Task subject")
    body: str | None = None
    due_date: str | None = None
    priority: str = Field(default="NONE")
    status: str = Field(default="NOT_STARTED")


class CreateMeetingInput(_AuthFields, _EngagementAssoc):
    title: str = Field(description="Meeting title")
    start_time: str = Field(description="Start time")
    end_time: str = Field(description="End time")
    body: str | None = None


class GetPropertyInput(_AuthFields):
    object_type: str = Field(description="contacts/companies/deals/tickets")
    property_name: str = Field(description="Property name")


class ListPropertiesInput(_AuthFields):
    object_type: str = Field(description="contacts/companies/deals/tickets")


# --- Engagement association helpers ---------------------------------------

# (association_type_id, contact, company, deal) per engagement sub-type.
_ENGAGEMENT_ASSOC_IDS = {
    "notes": {"contacts": 202, "companies": 190, "deals": 214},
    "tasks": {"contacts": 204, "companies": 192, "deals": 216},
    "meetings": {"contacts": 200, "companies": 188, "deals": 212},
}


def _build_associations(
    sub_path: str,
    contact_ids: list[str] | None,
    company_ids: list[str] | None,
    deal_ids: list[str] | None,
) -> list[dict[str, Any]] | None:
    ids_for_kind = _ENGAGEMENT_ASSOC_IDS[sub_path]
    out: list[dict[str, Any]] = []
    for kind, ids in (
        ("contacts", contact_ids),
        ("companies", company_ids),
        ("deals", deal_ids),
    ):
        if not ids:
            continue
        type_id = ids_for_kind[kind]
        for obj_id in ids:
            out.append(
                {
                    "to": {"id": obj_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": type_id,
                        }
                    ],
                }
            )
    return out or None


# --- Tools — Contacts ------------------------------------------------------


@tool(args_schema=GetRecentInput)
@serialize_pydantic_return
async def get_recent_contacts(
    auth_type: str, auth_data: dict[str, Any], limit: int = 10
) -> GetRecentContactsOutput:
    """List recently modified contacts."""
    err = _validate(auth_data, "get_recent_contacts")
    if err:
        return GetRecentContactsOutput(success=False, error=err)
    try:
        rows = _do_recent(
            _client(auth_type, auth_data),
            "contacts",
            limit,
            ["hs_lastmodifieddate", "lastmodifieddate"],
        )
    except Exception as exc:
        return GetRecentContactsOutput(success=False, error=str(exc))
    return GetRecentContactsOutput(success=True, contacts=rows, total=len(rows))


@tool(args_schema=GetContactByIdInput)
@serialize_pydantic_return
async def get_contact_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    properties: list[str] | None = None,
) -> GetContactByIdOutput:
    """Retrieve a contact by its HubSpot ID."""
    err = _validate(auth_data, "get_contact_by_id")
    if err:
        return GetContactByIdOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        contact = client.crm.contacts.basic_api.get_by_id(
            contact_id=contact_id, properties=properties, archived=False
        )
    except Exception as exc:
        return GetContactByIdOutput(success=False, error=str(exc))
    return GetContactByIdOutput(success=True, result=_to_dict(contact))


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    email: str,
    firstname: str | None = None,
    lastname: str | None = None,
    phone: str | None = None,
    company: str | None = None,
    website: str | None = None,
    properties: dict[str, Any] | None = None,
) -> CreateContactOutput:
    """Create a new contact (email required)."""
    err = _validate(auth_data, "create_contact")
    if err:
        return CreateContactOutput(success=False, error=err)
    body: dict[str, Any] = {"email": email}
    for field, value in (
        ("firstname", firstname),
        ("lastname", lastname),
        ("phone", phone),
        ("company", company),
        ("website", website),
    ):
        if value:
            body[field] = value
    if properties:
        body.update(properties)
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.contacts.basic_api.create(
            simple_public_object_input_for_create=_simple_create_input(
                "contacts", properties=body
            )
        )
    except Exception as exc:
        return CreateContactOutput(success=False, error=str(exc))
    return CreateContactOutput(success=True, result=_to_dict(response))


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    properties: dict[str, Any],
) -> UpdateContactOutput:
    """Update a contact's properties."""
    err = _validate(auth_data, "update_contact")
    if err:
        return UpdateContactOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        contact = client.crm.contacts.basic_api.update(
            contact_id=contact_id,
            simple_public_object_input=_simple_update_input("contacts", properties),
        )
    except Exception as exc:
        return UpdateContactOutput(success=False, error=str(exc))
    return UpdateContactOutput(success=True, result=_to_dict(contact))


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    limit: int = 10,
    properties: list[str] | None = None,
) -> SearchContactsOutput:
    """Search contacts by query string."""
    err = _validate(auth_data, "search_contacts")
    if err:
        return SearchContactsOutput(success=False, error=err)
    try:
        rows, total = _do_search(
            _client(auth_type, auth_data), "contacts", query, limit, properties
        )
    except Exception as exc:
        return SearchContactsOutput(success=False, error=str(exc))
    return SearchContactsOutput(success=True, contacts=rows, total=total)


# --- Tools — Companies -----------------------------------------------------


@tool(args_schema=GetRecentInput)
@serialize_pydantic_return
async def get_recent_companies(
    auth_type: str, auth_data: dict[str, Any], limit: int = 10
) -> GetRecentCompaniesOutput:
    """List recently modified companies."""
    err = _validate(auth_data, "get_recent_companies")
    if err:
        return GetRecentCompaniesOutput(success=False, error=err)
    try:
        rows = _do_recent(
            _client(auth_type, auth_data),
            "companies",
            limit,
            ["hs_lastmodifieddate"],
        )
    except Exception as exc:
        return GetRecentCompaniesOutput(success=False, error=str(exc))
    return GetRecentCompaniesOutput(success=True, companies=rows, total=len(rows))


@tool(args_schema=GetCompanyByIdInput)
@serialize_pydantic_return
async def get_company_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    company_id: str,
    properties: list[str] | None = None,
) -> GetCompanyByIdOutput:
    """Retrieve a company by its HubSpot ID."""
    err = _validate(auth_data, "get_company_by_id")
    if err:
        return GetCompanyByIdOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        company = client.crm.companies.basic_api.get_by_id(
            company_id=company_id, properties=properties, archived=False
        )
    except Exception as exc:
        return GetCompanyByIdOutput(success=False, error=str(exc))
    return GetCompanyByIdOutput(success=True, result=_to_dict(company))


@tool(args_schema=CreateCompanyInput)
@serialize_pydantic_return
async def create_company(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    domain: str | None = None,
    industry: str | None = None,
    phone: str | None = None,
    website: str | None = None,
    properties: dict[str, Any] | None = None,
) -> CreateCompanyOutput:
    """Create a new company (name required)."""
    err = _validate(auth_data, "create_company")
    if err:
        return CreateCompanyOutput(success=False, error=err)
    body: dict[str, Any] = {"name": name}
    for field, value in (
        ("domain", domain),
        ("industry", industry),
        ("phone", phone),
        ("website", website),
    ):
        if value:
            body[field] = value
    if properties:
        body.update(properties)
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.companies.basic_api.create(
            simple_public_object_input_for_create=_simple_create_input(
                "companies", properties=body
            )
        )
    except Exception as exc:
        return CreateCompanyOutput(success=False, error=str(exc))
    return CreateCompanyOutput(success=True, result=_to_dict(response))


@tool(args_schema=UpdateCompanyInput)
@serialize_pydantic_return
async def update_company(
    auth_type: str,
    auth_data: dict[str, Any],
    company_id: str,
    properties: dict[str, Any],
) -> UpdateCompanyOutput:
    """Update a company's properties."""
    err = _validate(auth_data, "update_company")
    if err:
        return UpdateCompanyOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        company = client.crm.companies.basic_api.update(
            company_id=company_id,
            simple_public_object_input=_simple_update_input("companies", properties),
        )
    except Exception as exc:
        return UpdateCompanyOutput(success=False, error=str(exc))
    return UpdateCompanyOutput(success=True, result=_to_dict(company))


@tool(args_schema=GetCompanyActivityInput)
@serialize_pydantic_return
async def get_company_activity(
    auth_type: str, auth_data: dict[str, Any], company_id: str
) -> GetCompanyActivityOutput:
    """Get the engagement history for a company (N+1 fetch)."""
    err = _validate(auth_data, "get_company_activity")
    if err:
        return GetCompanyActivityOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        associations = client.crm.associations.v4.basic_api.get_page(
            object_type="companies",
            object_id=company_id,
            to_object_type="engagements",
            limit=500,
        )
        engagement_ids = [
            r.to_object_id for r in getattr(associations, "results", []) or []
        ]
        activities: list[dict[str, Any]] = []
        for engagement_id in engagement_ids:
            try:
                response = client.api_request(
                    {
                        "method": "GET",
                        "path": f"/engagements/v1/engagements/{engagement_id}",
                    }
                ).json()
                engagement = response.get("engagement") or {}
                activities.append(
                    {
                        "id": engagement.get("id"),
                        "type": engagement.get("type"),
                        "created_at": engagement.get("createdAt"),
                        "last_updated": engagement.get("lastUpdated"),
                        "created_by": engagement.get("createdBy"),
                        "timestamp": engagement.get("timestamp"),
                        "associations": response.get("associations") or {},
                        "metadata": response.get("metadata") or {},
                    }
                )
            except Exception:
                continue
    except Exception as exc:
        return GetCompanyActivityOutput(success=False, error=str(exc))
    return GetCompanyActivityOutput(
        success=True, activities=_convert_datetimes(activities), total=len(activities)
    )


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search_companies(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    limit: int = 10,
    properties: list[str] | None = None,
) -> SearchCompaniesOutput:
    """Search companies by query string."""
    err = _validate(auth_data, "search_companies")
    if err:
        return SearchCompaniesOutput(success=False, error=err)
    try:
        rows, total = _do_search(
            _client(auth_type, auth_data), "companies", query, limit, properties
        )
    except Exception as exc:
        return SearchCompaniesOutput(success=False, error=str(exc))
    return SearchCompaniesOutput(success=True, companies=rows, total=total)


# --- Tools — Deals ---------------------------------------------------------


@tool(args_schema=GetRecentInput)
@serialize_pydantic_return
async def get_recent_deals(
    auth_type: str, auth_data: dict[str, Any], limit: int = 10
) -> GetRecentDealsOutput:
    """List recently modified deals."""
    err = _validate(auth_data, "get_recent_deals")
    if err:
        return GetRecentDealsOutput(success=False, error=err)
    try:
        rows = _do_recent(
            _client(auth_type, auth_data),
            "deals",
            limit,
            ["hs_lastmodifieddate"],
        )
    except Exception as exc:
        return GetRecentDealsOutput(success=False, error=str(exc))
    return GetRecentDealsOutput(success=True, deals=rows, total=len(rows))


@tool(args_schema=GetDealByIdInput)
@serialize_pydantic_return
async def get_deal_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    deal_id: str,
    properties: list[str] | None = None,
) -> GetDealByIdOutput:
    """Retrieve a deal by its HubSpot ID."""
    err = _validate(auth_data, "get_deal_by_id")
    if err:
        return GetDealByIdOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        deal = client.crm.deals.basic_api.get_by_id(
            deal_id=deal_id, properties=properties, archived=False
        )
    except Exception as exc:
        return GetDealByIdOutput(success=False, error=str(exc))
    return GetDealByIdOutput(success=True, result=_to_dict(deal))


@tool(args_schema=CreateDealInput)
@serialize_pydantic_return
async def create_deal(
    auth_type: str,
    auth_data: dict[str, Any],
    dealname: str,
    pipeline: str | None = None,
    dealstage: str | None = None,
    amount: float | None = None,
    closedate: str | None = None,
    properties: dict[str, Any] | None = None,
) -> CreateDealOutput:
    """Create a new deal (dealname required)."""
    err = _validate(auth_data, "create_deal")
    if err:
        return CreateDealOutput(success=False, error=err)
    body: dict[str, Any] = {"dealname": dealname}
    if pipeline:
        body["pipeline"] = pipeline
    if dealstage:
        body["dealstage"] = dealstage
    if amount is not None:
        body["amount"] = str(amount)
    if closedate:
        body["closedate"] = closedate
    if properties:
        body.update(properties)
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.deals.basic_api.create(
            simple_public_object_input_for_create=_simple_create_input(
                "deals", properties=body
            )
        )
    except Exception as exc:
        return CreateDealOutput(success=False, error=str(exc))
    return CreateDealOutput(success=True, result=_to_dict(response))


@tool(args_schema=UpdateDealInput)
@serialize_pydantic_return
async def update_deal(
    auth_type: str,
    auth_data: dict[str, Any],
    deal_id: str,
    properties: dict[str, Any],
) -> UpdateDealOutput:
    """Update a deal's properties."""
    err = _validate(auth_data, "update_deal")
    if err:
        return UpdateDealOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        deal = client.crm.deals.basic_api.update(
            deal_id=deal_id,
            simple_public_object_input=_simple_update_input("deals", properties),
        )
    except Exception as exc:
        return UpdateDealOutput(success=False, error=str(exc))
    return UpdateDealOutput(success=True, result=_to_dict(deal))


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search_deals(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    limit: int = 10,
    properties: list[str] | None = None,
) -> SearchDealsOutput:
    """Search deals by query string."""
    err = _validate(auth_data, "search_deals")
    if err:
        return SearchDealsOutput(success=False, error=err)
    try:
        rows, total = _do_search(
            _client(auth_type, auth_data), "deals", query, limit, properties
        )
    except Exception as exc:
        return SearchDealsOutput(success=False, error=str(exc))
    return SearchDealsOutput(success=True, deals=rows, total=total)


# --- Tools — Tickets -------------------------------------------------------


@tool(args_schema=GetRecentInput)
@serialize_pydantic_return
async def get_recent_tickets(
    auth_type: str, auth_data: dict[str, Any], limit: int = 10
) -> GetRecentTicketsOutput:
    """List recently modified tickets."""
    err = _validate(auth_data, "get_recent_tickets")
    if err:
        return GetRecentTicketsOutput(success=False, error=err)
    try:
        rows = _do_recent(
            _client(auth_type, auth_data),
            "tickets",
            limit,
            ["hs_lastmodifieddate"],
        )
    except Exception as exc:
        return GetRecentTicketsOutput(success=False, error=str(exc))
    return GetRecentTicketsOutput(success=True, tickets=rows, total=len(rows))


@tool(args_schema=GetTicketByIdInput)
@serialize_pydantic_return
async def get_ticket_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    ticket_id: str,
    properties: list[str] | None = None,
) -> GetTicketByIdOutput:
    """Retrieve a ticket by its HubSpot ID."""
    err = _validate(auth_data, "get_ticket_by_id")
    if err:
        return GetTicketByIdOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        ticket = client.crm.tickets.basic_api.get_by_id(
            ticket_id=ticket_id, properties=properties, archived=False
        )
    except Exception as exc:
        return GetTicketByIdOutput(success=False, error=str(exc))
    return GetTicketByIdOutput(success=True, result=_to_dict(ticket))


@tool(args_schema=CreateTicketInput)
@serialize_pydantic_return
async def create_ticket(
    auth_type: str,
    auth_data: dict[str, Any],
    subject: str,
    content: str | None = None,
    hs_pipeline: str | None = None,
    hs_pipeline_stage: str | None = None,
    hs_ticket_priority: str | None = None,
    properties: dict[str, Any] | None = None,
) -> CreateTicketOutput:
    """Create a new ticket (subject required)."""
    err = _validate(auth_data, "create_ticket")
    if err:
        return CreateTicketOutput(success=False, error=err)
    body: dict[str, Any] = {"subject": subject}
    for field, value in (
        ("content", content),
        ("hs_pipeline", hs_pipeline),
        ("hs_pipeline_stage", hs_pipeline_stage),
        ("hs_ticket_priority", hs_ticket_priority),
    ):
        if value:
            body[field] = value
    if properties:
        body.update(properties)
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.tickets.basic_api.create(
            simple_public_object_input_for_create=_simple_create_input(
                "tickets", properties=body
            )
        )
    except Exception as exc:
        return CreateTicketOutput(success=False, error=str(exc))
    return CreateTicketOutput(success=True, result=_to_dict(response))


@tool(args_schema=UpdateTicketInput)
@serialize_pydantic_return
async def update_ticket(
    auth_type: str,
    auth_data: dict[str, Any],
    ticket_id: str,
    properties: dict[str, Any],
) -> UpdateTicketOutput:
    """Update a ticket's properties."""
    err = _validate(auth_data, "update_ticket")
    if err:
        return UpdateTicketOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        ticket = client.crm.tickets.basic_api.update(
            ticket_id=ticket_id,
            simple_public_object_input=_simple_update_input("tickets", properties),
        )
    except Exception as exc:
        return UpdateTicketOutput(success=False, error=str(exc))
    return UpdateTicketOutput(success=True, result=_to_dict(ticket))


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search_tickets(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    limit: int = 10,
    properties: list[str] | None = None,
) -> SearchTicketsOutput:
    """Search tickets by query string."""
    err = _validate(auth_data, "search_tickets")
    if err:
        return SearchTicketsOutput(success=False, error=err)
    try:
        rows, total = _do_search(
            _client(auth_type, auth_data), "tickets", query, limit, properties
        )
    except Exception as exc:
        return SearchTicketsOutput(success=False, error=str(exc))
    return SearchTicketsOutput(success=True, tickets=rows, total=total)


# --- Tools — Engagements ---------------------------------------------------


def _now_ms() -> str:
    return str(int(time.time() * 1000))


@tool(args_schema=CreateNoteInput)
@serialize_pydantic_return
async def create_note(
    auth_type: str,
    auth_data: dict[str, Any],
    body: str,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> CreateNoteOutput:
    """Create a note engagement."""
    err = _validate(auth_data, "create_note")
    if err:
        return CreateNoteOutput(success=False, error=err)
    properties = {"hs_note_body": body, "hs_timestamp": _now_ms()}
    associations = _build_associations(
        "notes", contact_ids, company_ids, deal_ids
    )
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.objects.notes.basic_api.create(
            simple_public_object_input_for_create=_engagement_create_input(
                "notes", properties=properties, associations=associations
            )
        )
    except Exception as exc:
        return CreateNoteOutput(success=False, error=str(exc))
    return CreateNoteOutput(success=True, result=_to_dict(response))


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    auth_type: str,
    auth_data: dict[str, Any],
    subject: str,
    body: str | None = None,
    due_date: str | None = None,
    priority: str = "NONE",
    status: str = "NOT_STARTED",
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> CreateTaskOutput:
    """Create a task engagement."""
    err = _validate(auth_data, "create_task")
    if err:
        return CreateTaskOutput(success=False, error=err)
    properties: dict[str, Any] = {
        "hs_task_subject": subject,
        "hs_task_status": status,
        "hs_task_priority": priority,
        "hs_timestamp": _now_ms(),
    }
    if body:
        properties["hs_task_body"] = body
    if due_date:
        properties["hs_task_due_date"] = due_date
    associations = _build_associations(
        "tasks", contact_ids, company_ids, deal_ids
    )
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.objects.tasks.basic_api.create(
            simple_public_object_input_for_create=_engagement_create_input(
                "tasks", properties=properties, associations=associations
            )
        )
    except Exception as exc:
        return CreateTaskOutput(success=False, error=str(exc))
    return CreateTaskOutput(success=True, result=_to_dict(response))


@tool(args_schema=CreateMeetingInput)
@serialize_pydantic_return
async def create_meeting(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    start_time: str,
    end_time: str,
    body: str | None = None,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> CreateMeetingOutput:
    """Create a meeting engagement."""
    err = _validate(auth_data, "create_meeting")
    if err:
        return CreateMeetingOutput(success=False, error=err)
    properties: dict[str, Any] = {
        "hs_meeting_title": title,
        "hs_meeting_start_time": start_time,
        "hs_meeting_end_time": end_time,
        "hs_timestamp": _now_ms(),
    }
    if body:
        properties["hs_meeting_body"] = body
    associations = _build_associations(
        "meetings", contact_ids, company_ids, deal_ids
    )
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.objects.meetings.basic_api.create(
            simple_public_object_input_for_create=_engagement_create_input(
                "meetings", properties=properties, associations=associations
            )
        )
    except Exception as exc:
        return CreateMeetingOutput(success=False, error=str(exc))
    return CreateMeetingOutput(success=True, result=_to_dict(response))


# --- Tools — Properties ---------------------------------------------------


@tool(args_schema=GetPropertyInput)
@serialize_pydantic_return
async def get_property(
    auth_type: str,
    auth_data: dict[str, Any],
    object_type: str,
    property_name: str,
) -> GetPropertyOutput:
    """Get a single property definition by name."""
    err = _validate(auth_data, "get_property")
    if err:
        return GetPropertyOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.properties.core_api.get_by_name(
            object_type=object_type,
            property_name=property_name,
            archived=False,
        )
    except Exception as exc:
        return GetPropertyOutput(success=False, error=str(exc))
    return GetPropertyOutput(success=True, result=_to_dict(response))


@tool(args_schema=ListPropertiesInput)
@serialize_pydantic_return
async def list_properties(
    auth_type: str, auth_data: dict[str, Any], object_type: str
) -> ListPropertiesOutput:
    """List all property definitions for an object type."""
    err = _validate(auth_data, "list_properties")
    if err:
        return ListPropertiesOutput(success=False, error=err)
    try:
        client = _client(auth_type, auth_data)
        response = client.crm.properties.core_api.get_all(
            object_type=object_type, archived=False
        )
        properties = [_to_dict(item) for item in response.results]
    except Exception as exc:
        return ListPropertiesOutput(success=False, error=str(exc))
    return ListPropertiesOutput(
        success=True, properties=properties, total=len(properties)
    )
