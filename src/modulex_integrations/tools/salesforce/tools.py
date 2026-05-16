"""Salesforce LangChain ``@tool`` functions.

Pure HTTP integration against the Salesforce REST API. Token-based
runtime convention (``auth_type, auth_data`` first args); ``auth_data``
carries both ``access_token`` AND ``instance_url`` (Salesforce returns
the per-org instance URL with the OAuth token exchange).

16 actions across SOQL/SOSL, generic record CRUD, and convenience
helpers for the common SObjects (Account/Contact/Lead/Opportunity/
Task/Case) + Campaign member creation + schema introspection.
All actions wrap in try/except → unified ``success=False`` envelope.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "add_contact_to_campaign",
    "add_lead_to_campaign",
    "create_account",
    "create_case",
    "create_contact",
    "create_lead",
    "create_opportunity",
    "create_record",
    "create_task",
    "delete_record",
    "describe_object",
    "get_record",
    "list_objects",
    "soql_query",
    "sosl_search",
    "update_record",
]

_API_VERSION = "v62.0"
_TIMEOUT = 30.0


def _headers(auth_data: dict[str, Any]) -> dict[str, str]:
    token = auth_data.get("access_token", "")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base_url(auth_data: dict[str, Any]) -> str:
    instance_url = (auth_data.get("instance_url") or "").rstrip("/")
    return f"{instance_url}/services/data/{_API_VERSION}"


def _validate(auth_data: dict[str, Any], action: str) -> str | None:
    if not auth_data.get("access_token"):
        return f"Salesforce access_token missing for {action}"
    if not auth_data.get("instance_url"):
        return f"Salesforce instance_url missing for {action}"
    return None


def _api_err(status: int, body: str) -> str:
    return f"API error {status}: {body}"


async def _call(
    method: str,
    auth_type: str,
    auth_data: dict[str, Any],
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    success_codes: tuple[int, ...] = (200,),
) -> tuple[bool, str | None, dict[str, Any]]:
    """Make one Salesforce REST call."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method,
                f"{_base_url(auth_data)}{path}",
                headers=_headers(auth_data),
                json=json_body,
                params=params,
            )
        if response.status_code not in success_codes:
            return False, _api_err(response.status_code, response.text), {}
        if response.status_code == 204 or not response.content:
            return True, None, {}
        return True, None, response.json() or {}
    except httpx.TimeoutException:
        return False, "Request timed out", {}
    except Exception as exc:
        return False, str(exc), {}


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2 or bearer_token)")
    auth_data: dict[str, Any] = Field(
        description="access_token + instance_url"
    )


class SoqlQueryInput(_AuthFields):
    query: str = Field(description="SOQL query")


class SoslSearchInput(_AuthFields):
    search: str = Field(description="SOSL search query")


class GetRecordInput(_AuthFields):
    object_type: str = Field(description="Salesforce object type")
    record_id: str = Field(description="Record ID")
    fields: list[str] | None = None


class CreateRecordInput(_AuthFields):
    object_type: str = Field(description="Salesforce object type")
    data: dict[str, Any] = Field(description="Record data")


class UpdateRecordInput(_AuthFields):
    object_type: str = Field(description="Salesforce object type")
    record_id: str = Field(description="Record ID")
    data: dict[str, Any] = Field(description="Updated fields")


class DeleteRecordInput(_AuthFields):
    object_type: str = Field(description="Salesforce object type")
    record_id: str = Field(description="Record ID")


class CreateAccountInput(_AuthFields):
    name: str
    description: str | None = None
    website: str | None = None
    phone: str | None = None
    industry: str | None = None
    annual_revenue: float | None = None
    number_of_employees: int | None = None
    billing_street: str | None = None
    billing_city: str | None = None
    billing_state: str | None = None
    billing_postal_code: str | None = None
    billing_country: str | None = None
    additional_fields: dict[str, Any] | None = None


class CreateContactInput(_AuthFields):
    last_name: str
    first_name: str | None = None
    account_id: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile_phone: str | None = None
    title: str | None = None
    department: str | None = None
    mailing_street: str | None = None
    mailing_city: str | None = None
    mailing_state: str | None = None
    mailing_postal_code: str | None = None
    mailing_country: str | None = None
    additional_fields: dict[str, Any] | None = None


class CreateLeadInput(_AuthFields):
    last_name: str
    company: str
    first_name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    status: str | None = None
    rating: str | None = None
    industry: str | None = None
    annual_revenue: float | None = None
    lead_source: str | None = None
    additional_fields: dict[str, Any] | None = None


class CreateOpportunityInput(_AuthFields):
    name: str
    stage_name: str
    close_date: str
    account_id: str | None = None
    amount: float | None = None
    probability: int | None = None
    type: str | None = None
    lead_source: str | None = None
    description: str | None = None
    additional_fields: dict[str, Any] | None = None


class CreateTaskInput(_AuthFields):
    subject: str
    status: str = "Not Started"
    priority: str = "Normal"
    activity_date: str | None = None
    what_id: str | None = None
    who_id: str | None = None
    description: str | None = None
    additional_fields: dict[str, Any] | None = None


class CreateCaseInput(_AuthFields):
    subject: str
    status: str = "New"
    priority: str = "Medium"
    origin: str | None = None
    account_id: str | None = None
    contact_id: str | None = None
    description: str | None = None
    type: str | None = None
    reason: str | None = None
    additional_fields: dict[str, Any] | None = None


class AddContactToCampaignInput(_AuthFields):
    campaign_id: str
    contact_id: str
    status: str | None = None


class AddLeadToCampaignInput(_AuthFields):
    campaign_id: str
    lead_id: str
    status: str | None = None


class DescribeObjectInput(_AuthFields):
    object_type: str = Field(description="Object type to describe")


class ListObjectsInput(_AuthFields):
    pass


# --- Generic helpers -------------------------------------------------------


def _add_if(data: dict[str, Any], key: str, value: Any) -> None:
    if value is not None and value != "":
        data[key] = value


async def _do_create(
    auth_type: str,
    auth_data: dict[str, Any],
    object_type: str,
    body: dict[str, Any],
) -> tuple[bool, str | None, dict[str, Any]]:
    return await _call(
        "POST",
        auth_type,
        auth_data,
        f"/sobjects/{object_type}",
        json_body=body,
        success_codes=(200, 201),
    )


# --- Tools — query / record CRUD ------------------------------------------


@tool(args_schema=SoqlQueryInput)
@serialize_pydantic_return
async def soql_query(
    auth_type: str, auth_data: dict[str, Any], query: str
) -> SoqlQueryOutput:
    """Execute a SOQL query."""
    err = _validate(auth_data, "soql_query")
    if err:
        return SoqlQueryOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET", auth_type, auth_data, "/query", params={"q": query}
    )
    if not ok:
        return SoqlQueryOutput(success=False, error=e)
    return SoqlQueryOutput(
        success=True,
        total_size=int(data.get("totalSize", 0)),
        done=bool(data.get("done", True)),
        next_records_url=data.get("nextRecordsUrl"),
        records=data.get("records") or [],
    )


@tool(args_schema=SoslSearchInput)
@serialize_pydantic_return
async def sosl_search(
    auth_type: str, auth_data: dict[str, Any], search: str
) -> SoslSearchOutput:
    """Execute a SOSL cross-object search."""
    err = _validate(auth_data, "sosl_search")
    if err:
        return SoslSearchOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET", auth_type, auth_data, "/search", params={"q": search}
    )
    if not ok:
        return SoslSearchOutput(success=False, error=e)
    return SoslSearchOutput(
        success=True,
        search_records=data.get("searchRecords", data) if isinstance(data, dict) else data,
    )


@tool(args_schema=GetRecordInput)
@serialize_pydantic_return
async def get_record(
    auth_type: str,
    auth_data: dict[str, Any],
    object_type: str,
    record_id: str,
    fields: list[str] | None = None,
) -> GetRecordOutput:
    """Retrieve a record by object type + ID."""
    err = _validate(auth_data, "get_record")
    if err:
        return GetRecordOutput(success=False, error=err)
    params: dict[str, Any] | None = (
        {"fields": ",".join(fields)} if fields else None
    )
    ok, e, data = await _call(
        "GET",
        auth_type,
        auth_data,
        f"/sobjects/{object_type}/{record_id}",
        params=params,
    )
    if not ok:
        return GetRecordOutput(success=False, error=e)
    return GetRecordOutput(success=True, result=data)


@tool(args_schema=CreateRecordInput)
@serialize_pydantic_return
async def create_record(
    auth_type: str,
    auth_data: dict[str, Any],
    object_type: str,
    data: dict[str, Any],
) -> CreateRecordOutput:
    """Generic create — any object type."""
    err = _validate(auth_data, "create_record")
    if err:
        return CreateRecordOutput(success=False, error=err)
    ok, e, result = await _do_create(auth_type, auth_data, object_type, data)
    if not ok:
        return CreateRecordOutput(success=False, error=e)
    return CreateRecordOutput(
        success=True,
        id=result.get("id"),
        object_type=object_type,
        created=bool(result.get("success", True)),
    )


@tool(args_schema=UpdateRecordInput)
@serialize_pydantic_return
async def update_record(
    auth_type: str,
    auth_data: dict[str, Any],
    object_type: str,
    record_id: str,
    data: dict[str, Any],
) -> UpdateRecordOutput:
    """PATCH an existing record."""
    err = _validate(auth_data, "update_record")
    if err:
        return UpdateRecordOutput(success=False, error=err)
    ok, e, _ = await _call(
        "PATCH",
        auth_type,
        auth_data,
        f"/sobjects/{object_type}/{record_id}",
        json_body=data,
        success_codes=(200, 204),
    )
    if not ok:
        return UpdateRecordOutput(success=False, error=e)
    return UpdateRecordOutput(
        success=True, id=record_id, object_type=object_type, updated=True
    )


@tool(args_schema=DeleteRecordInput)
@serialize_pydantic_return
async def delete_record(
    auth_type: str,
    auth_data: dict[str, Any],
    object_type: str,
    record_id: str,
) -> DeleteRecordOutput:
    """DELETE a record."""
    err = _validate(auth_data, "delete_record")
    if err:
        return DeleteRecordOutput(success=False, error=err)
    ok, e, _ = await _call(
        "DELETE",
        auth_type,
        auth_data,
        f"/sobjects/{object_type}/{record_id}",
        success_codes=(200, 204),
    )
    if not ok:
        return DeleteRecordOutput(success=False, error=e)
    return DeleteRecordOutput(
        success=True, id=record_id, object_type=object_type, deleted=True
    )


# --- Tools — convenience creators -----------------------------------------


@tool(args_schema=CreateAccountInput)
@serialize_pydantic_return
async def create_account(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    description: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    industry: str | None = None,
    annual_revenue: float | None = None,
    number_of_employees: int | None = None,
    billing_street: str | None = None,
    billing_city: str | None = None,
    billing_state: str | None = None,
    billing_postal_code: str | None = None,
    billing_country: str | None = None,
    additional_fields: dict[str, Any] | None = None,
) -> CreateAccountOutput:
    """Create a Salesforce Account."""
    err = _validate(auth_data, "create_account")
    if err:
        return CreateAccountOutput(success=False, error=err)
    body: dict[str, Any] = {"Name": name}
    _add_if(body, "Description", description)
    _add_if(body, "Website", website)
    _add_if(body, "Phone", phone)
    _add_if(body, "Industry", industry)
    _add_if(body, "AnnualRevenue", annual_revenue)
    _add_if(body, "NumberOfEmployees", number_of_employees)
    _add_if(body, "BillingStreet", billing_street)
    _add_if(body, "BillingCity", billing_city)
    _add_if(body, "BillingState", billing_state)
    _add_if(body, "BillingPostalCode", billing_postal_code)
    _add_if(body, "BillingCountry", billing_country)
    if additional_fields:
        body.update(additional_fields)
    ok, e, result = await _do_create(auth_type, auth_data, "Account", body)
    if not ok:
        return CreateAccountOutput(success=False, error=e)
    return CreateAccountOutput(
        success=True,
        id=result.get("id"),
        name=name,
        created=bool(result.get("success", True)),
    )


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    last_name: str,
    first_name: str | None = None,
    account_id: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    mobile_phone: str | None = None,
    title: str | None = None,
    department: str | None = None,
    mailing_street: str | None = None,
    mailing_city: str | None = None,
    mailing_state: str | None = None,
    mailing_postal_code: str | None = None,
    mailing_country: str | None = None,
    additional_fields: dict[str, Any] | None = None,
) -> CreateContactOutput:
    """Create a Salesforce Contact."""
    err = _validate(auth_data, "create_contact")
    if err:
        return CreateContactOutput(success=False, error=err)
    body: dict[str, Any] = {"LastName": last_name}
    _add_if(body, "FirstName", first_name)
    _add_if(body, "AccountId", account_id)
    _add_if(body, "Email", email)
    _add_if(body, "Phone", phone)
    _add_if(body, "MobilePhone", mobile_phone)
    _add_if(body, "Title", title)
    _add_if(body, "Department", department)
    _add_if(body, "MailingStreet", mailing_street)
    _add_if(body, "MailingCity", mailing_city)
    _add_if(body, "MailingState", mailing_state)
    _add_if(body, "MailingPostalCode", mailing_postal_code)
    _add_if(body, "MailingCountry", mailing_country)
    if additional_fields:
        body.update(additional_fields)
    ok, e, result = await _do_create(auth_type, auth_data, "Contact", body)
    if not ok:
        return CreateContactOutput(success=False, error=e)
    return CreateContactOutput(
        success=True,
        id=result.get("id"),
        last_name=last_name,
        created=bool(result.get("success", True)),
    )


@tool(args_schema=CreateLeadInput)
@serialize_pydantic_return
async def create_lead(
    auth_type: str,
    auth_data: dict[str, Any],
    last_name: str,
    company: str,
    first_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    title: str | None = None,
    status: str | None = None,
    rating: str | None = None,
    industry: str | None = None,
    annual_revenue: float | None = None,
    lead_source: str | None = None,
    additional_fields: dict[str, Any] | None = None,
) -> CreateLeadOutput:
    """Create a Salesforce Lead."""
    err = _validate(auth_data, "create_lead")
    if err:
        return CreateLeadOutput(success=False, error=err)
    body: dict[str, Any] = {"LastName": last_name, "Company": company}
    _add_if(body, "FirstName", first_name)
    _add_if(body, "Email", email)
    _add_if(body, "Phone", phone)
    _add_if(body, "Title", title)
    _add_if(body, "Status", status)
    _add_if(body, "Rating", rating)
    _add_if(body, "Industry", industry)
    _add_if(body, "AnnualRevenue", annual_revenue)
    _add_if(body, "LeadSource", lead_source)
    if additional_fields:
        body.update(additional_fields)
    ok, e, result = await _do_create(auth_type, auth_data, "Lead", body)
    if not ok:
        return CreateLeadOutput(success=False, error=e)
    return CreateLeadOutput(
        success=True,
        id=result.get("id"),
        last_name=last_name,
        company=company,
        created=bool(result.get("success", True)),
    )


@tool(args_schema=CreateOpportunityInput)
@serialize_pydantic_return
async def create_opportunity(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    stage_name: str,
    close_date: str,
    account_id: str | None = None,
    amount: float | None = None,
    probability: int | None = None,
    type: str | None = None,
    lead_source: str | None = None,
    description: str | None = None,
    additional_fields: dict[str, Any] | None = None,
) -> CreateOpportunityOutput:
    """Create a Salesforce Opportunity."""
    err = _validate(auth_data, "create_opportunity")
    if err:
        return CreateOpportunityOutput(success=False, error=err)
    body: dict[str, Any] = {
        "Name": name,
        "StageName": stage_name,
        "CloseDate": close_date,
    }
    _add_if(body, "AccountId", account_id)
    _add_if(body, "Amount", amount)
    _add_if(body, "Probability", probability)
    _add_if(body, "Type", type)
    _add_if(body, "LeadSource", lead_source)
    _add_if(body, "Description", description)
    if additional_fields:
        body.update(additional_fields)
    ok, e, result = await _do_create(auth_type, auth_data, "Opportunity", body)
    if not ok:
        return CreateOpportunityOutput(success=False, error=e)
    return CreateOpportunityOutput(
        success=True,
        id=result.get("id"),
        name=name,
        created=bool(result.get("success", True)),
    )


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    auth_type: str,
    auth_data: dict[str, Any],
    subject: str,
    status: str = "Not Started",
    priority: str = "Normal",
    activity_date: str | None = None,
    what_id: str | None = None,
    who_id: str | None = None,
    description: str | None = None,
    additional_fields: dict[str, Any] | None = None,
) -> CreateTaskOutput:
    """Create a Salesforce Task."""
    err = _validate(auth_data, "create_task")
    if err:
        return CreateTaskOutput(success=False, error=err)
    body: dict[str, Any] = {
        "Subject": subject,
        "Status": status,
        "Priority": priority,
    }
    _add_if(body, "ActivityDate", activity_date)
    _add_if(body, "WhatId", what_id)
    _add_if(body, "WhoId", who_id)
    _add_if(body, "Description", description)
    if additional_fields:
        body.update(additional_fields)
    ok, e, result = await _do_create(auth_type, auth_data, "Task", body)
    if not ok:
        return CreateTaskOutput(success=False, error=e)
    return CreateTaskOutput(
        success=True,
        id=result.get("id"),
        subject=subject,
        created=bool(result.get("success", True)),
    )


@tool(args_schema=CreateCaseInput)
@serialize_pydantic_return
async def create_case(
    auth_type: str,
    auth_data: dict[str, Any],
    subject: str,
    status: str = "New",
    priority: str = "Medium",
    origin: str | None = None,
    account_id: str | None = None,
    contact_id: str | None = None,
    description: str | None = None,
    type: str | None = None,
    reason: str | None = None,
    additional_fields: dict[str, Any] | None = None,
) -> CreateCaseOutput:
    """Create a Salesforce Case."""
    err = _validate(auth_data, "create_case")
    if err:
        return CreateCaseOutput(success=False, error=err)
    body: dict[str, Any] = {
        "Subject": subject,
        "Status": status,
        "Priority": priority,
    }
    _add_if(body, "Origin", origin)
    _add_if(body, "AccountId", account_id)
    _add_if(body, "ContactId", contact_id)
    _add_if(body, "Description", description)
    _add_if(body, "Type", type)
    _add_if(body, "Reason", reason)
    if additional_fields:
        body.update(additional_fields)
    ok, e, result = await _do_create(auth_type, auth_data, "Case", body)
    if not ok:
        return CreateCaseOutput(success=False, error=e)
    return CreateCaseOutput(
        success=True,
        id=result.get("id"),
        subject=subject,
        created=bool(result.get("success", True)),
    )


# --- Tools — campaign members + describe ----------------------------------


@tool(args_schema=AddContactToCampaignInput)
@serialize_pydantic_return
async def add_contact_to_campaign(
    auth_type: str,
    auth_data: dict[str, Any],
    campaign_id: str,
    contact_id: str,
    status: str | None = None,
) -> AddContactToCampaignOutput:
    """Create a CampaignMember linking a Contact to a Campaign."""
    err = _validate(auth_data, "add_contact_to_campaign")
    if err:
        return AddContactToCampaignOutput(success=False, error=err)
    body: dict[str, Any] = {"CampaignId": campaign_id, "ContactId": contact_id}
    if status:
        body["Status"] = status
    ok, e, result = await _do_create(auth_type, auth_data, "CampaignMember", body)
    if not ok:
        return AddContactToCampaignOutput(success=False, error=e)
    return AddContactToCampaignOutput(
        success=True,
        id=result.get("id"),
        campaign_id=campaign_id,
        contact_id=contact_id,
        created=bool(result.get("success", True)),
    )


@tool(args_schema=AddLeadToCampaignInput)
@serialize_pydantic_return
async def add_lead_to_campaign(
    auth_type: str,
    auth_data: dict[str, Any],
    campaign_id: str,
    lead_id: str,
    status: str | None = None,
) -> AddLeadToCampaignOutput:
    """Create a CampaignMember linking a Lead to a Campaign."""
    err = _validate(auth_data, "add_lead_to_campaign")
    if err:
        return AddLeadToCampaignOutput(success=False, error=err)
    body: dict[str, Any] = {"CampaignId": campaign_id, "LeadId": lead_id}
    if status:
        body["Status"] = status
    ok, e, result = await _do_create(auth_type, auth_data, "CampaignMember", body)
    if not ok:
        return AddLeadToCampaignOutput(success=False, error=e)
    return AddLeadToCampaignOutput(
        success=True,
        id=result.get("id"),
        campaign_id=campaign_id,
        lead_id=lead_id,
        created=bool(result.get("success", True)),
    )


@tool(args_schema=DescribeObjectInput)
@serialize_pydantic_return
async def describe_object(
    auth_type: str, auth_data: dict[str, Any], object_type: str
) -> DescribeObjectOutput:
    """Describe an object's fields + capabilities."""
    err = _validate(auth_data, "describe_object")
    if err:
        return DescribeObjectOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET",
        auth_type,
        auth_data,
        f"/sobjects/{object_type}/describe",
    )
    if not ok:
        return DescribeObjectOutput(success=False, error=e)
    fields_summary = [
        {
            "name": f.get("name"),
            "label": f.get("label"),
            "type": f.get("type"),
            "required": not f.get("nillable", True) and f.get("createable", False),
            "createable": f.get("createable", False),
            "updateable": f.get("updateable", False),
        }
        for f in data.get("fields") or []
    ]
    return DescribeObjectOutput(
        success=True,
        name=data.get("name"),
        label=data.get("label"),
        key_prefix=data.get("keyPrefix"),
        createable=data.get("createable"),
        updateable=data.get("updateable"),
        deletable=data.get("deletable"),
        queryable=data.get("queryable"),
        searchable=data.get("searchable"),
        fields=fields_summary,
        field_count=len(fields_summary),
    )


@tool(args_schema=ListObjectsInput)
@serialize_pydantic_return
async def list_objects(
    auth_type: str, auth_data: dict[str, Any]
) -> ListObjectsOutput:
    """List all queryable Salesforce objects in the org."""
    err = _validate(auth_data, "list_objects")
    if err:
        return ListObjectsOutput(success=False, error=err)
    ok, e, data = await _call("GET", auth_type, auth_data, "/sobjects")
    if not ok:
        return ListObjectsOutput(success=False, error=e)
    sobjects = data.get("sobjects") or []
    objects = [
        {
            "name": obj.get("name"),
            "label": obj.get("label"),
            "key_prefix": obj.get("keyPrefix"),
            "queryable": obj.get("queryable"),
            "createable": obj.get("createable"),
            "custom": obj.get("custom", False),
        }
        for obj in sobjects
        if obj.get("queryable", False)
    ]
    return ListObjectsOutput(success=True, objects=objects, total_count=len(objects))
