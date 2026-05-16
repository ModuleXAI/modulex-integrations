"""Apollo.io LangChain ``@tool`` functions.

27 actions across enrichment, search, contacts, accounts, deals,
sequences, tasks, and lookup endpoints — all going through one
shared ``_call`` helper. Apollo authenticates via the ``X-Api-Key``
header.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "add_contacts_to_sequence",
    "bulk_organization_enrichment",
    "bulk_people_enrichment",
    "create_account",
    "create_contact",
    "create_deal",
    "create_task",
    "get_api_usage",
    "list_account_stages",
    "list_contact_stages",
    "list_deal_stages",
    "list_deals",
    "list_users",
    "organization_enrichment",
    "organization_job_postings",
    "organization_search",
    "people_enrichment",
    "people_search",
    "search_accounts",
    "search_contacts",
    "search_sequences",
    "search_tasks",
    "update_account",
    "update_contact",
    "update_deal",
    "view_account",
    "view_contact",
    "view_deal",
]

_API_BASE = "https://api.apollo.io/api/v1"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Accept": "application/json",
        "X-Api-Key": api_key,
    }


def _empty_key_error(name: str) -> str:
    return (
        f"Apollo.io API key is empty for {name}. "
        "Please configure a valid credential."
    )


def _filter_none(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def _clean_domain(domain: str) -> str:
    """Strip scheme/www/path to leave bare hostname."""
    clean = domain.strip().lower().replace("https://", "").replace("http://", "")
    return clean.replace("www.", "").split("/")[0]


async def _call(
    path: str,
    api_key: str,
    *,
    method: str = "POST",
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[bool, str | None, dict[str, Any] | None]:
    """Single HTTP path for every Apollo action. Returns (ok, error, body)."""
    url = f"{_API_BASE}{path}"
    method_upper = method.upper()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            if method_upper == "POST":
                response = await client.post(
                    url, headers=_headers(api_key), json=json_data or {}
                )
            elif method_upper == "GET":
                response = await client.get(
                    url, headers=_headers(api_key), params=params
                )
            elif method_upper == "PATCH":
                response = await client.patch(
                    url, headers=_headers(api_key), json=json_data or {}
                )
            elif method_upper == "PUT":
                response = await client.put(
                    url, headers=_headers(api_key), json=json_data or {}
                )
            else:
                return False, f"Unsupported HTTP method: {method}", None
    except Exception as exc:
        return False, f"Apollo request failed: {exc}", None

    if response.status_code >= 400:
        return False, (
            f"API error ({response.status_code}): {response.text}"
        ), None

    try:
        body = response.json()
    except Exception as exc:
        return False, f"Failed to parse Apollo response: {exc}", None

    if not isinstance(body, dict):
        return True, None, {"value": body}
    return True, None, body


# --- Input schemas ---------------------------------------------------------


class _ApiKeyOnly(BaseModel):
    api_key: str = Field(description="Apollo.io API key (provided by credential system)")


class PeopleEnrichmentInput(_ApiKeyOnly):
    first_name: str | None = Field(default=None, description="First name")
    last_name: str | None = Field(default=None, description="Last name")
    name: str | None = Field(default=None, description="Full name")
    email: str | None = Field(default=None, description="Email")
    organization_name: str | None = Field(default=None, description="Employer name")
    domain: str | None = Field(default=None, description="Employer domain")
    linkedin_url: str | None = Field(default=None, description="LinkedIn URL")
    reveal_personal_emails: bool = Field(default=False, description="Personal emails")
    reveal_phone_number: bool = Field(default=False, description="Phone numbers")


class BulkPeopleEnrichmentInput(_ApiKeyOnly):
    details: list[dict[str, Any]] = Field(description="Person detail dicts (max 10)")
    reveal_personal_emails: bool = Field(default=False, description="Personal emails")


class OrganizationEnrichmentInput(_ApiKeyOnly):
    domain: str = Field(description="Company domain")


class BulkOrganizationEnrichmentInput(_ApiKeyOnly):
    domains: list[str] = Field(description="Company domains (max 10)")


class PeopleSearchInput(_ApiKeyOnly):
    person_titles: list[str] | None = Field(default=None, description="Job titles")
    person_seniorities: list[str] | None = Field(default=None, description="Seniorities")
    person_locations: list[str] | None = Field(default=None, description="Person locations")
    organization_locations: list[str] | None = Field(default=None, description="Org locations")
    q_organization_domains: list[str] | None = Field(default=None, description="Org domains")
    organization_ids: list[str] | None = Field(default=None, description="Apollo org IDs")
    organization_num_employees_ranges: list[str] | None = Field(
        default=None, description="Employee ranges"
    )
    contact_email_status: list[str] | None = Field(
        default=None, description="Email verification status"
    )
    q_keywords: str | None = Field(default=None, description="Keyword search")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Results per page (max 100)")


class OrganizationSearchInput(_ApiKeyOnly):
    q_organization_name: str | None = Field(default=None, description="Company name")
    organization_locations: list[str] | None = Field(default=None, description="HQ locations")
    organization_not_locations: list[str] | None = Field(
        default=None, description="Exclude locations"
    )
    organization_num_employees_ranges: list[str] | None = Field(
        default=None, description="Employee ranges"
    )
    revenue_range_min: int | None = Field(default=None, description="Min revenue")
    revenue_range_max: int | None = Field(default=None, description="Max revenue")
    currently_using_any_of_technology_uids: list[str] | None = Field(
        default=None, description="Tech UIDs"
    )
    q_organization_keyword_tags: list[str] | None = Field(
        default=None, description="Industry keywords"
    )
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Results per page (max 100)")


class OrganizationJobPostingsInput(_ApiKeyOnly):
    organization_id: str = Field(description="Apollo organization ID")


class CreateContactInput(_ApiKeyOnly):
    email: str | None = Field(default=None, description="Contact email")
    first_name: str | None = Field(default=None, description="First name")
    last_name: str | None = Field(default=None, description="Last name")
    title: str | None = Field(default=None, description="Job title")
    organization_name: str | None = Field(default=None, description="Company name")
    account_id: str | None = Field(default=None, description="Account link")
    phone_number: str | None = Field(default=None, description="Phone number")
    linkedin_url: str | None = Field(default=None, description="LinkedIn URL")
    present_raw_address: str | None = Field(default=None, description="Address")
    label_names: list[str] | None = Field(default=None, description="Labels/tags")


class UpdateContactInput(_ApiKeyOnly):
    contact_id: str = Field(description="Contact ID to update")
    email: str | None = Field(default=None, description="New email")
    first_name: str | None = Field(default=None, description="New first name")
    last_name: str | None = Field(default=None, description="New last name")
    title: str | None = Field(default=None, description="New title")
    phone_number: str | None = Field(default=None, description="New phone")
    account_id: str | None = Field(default=None, description="New account")


class SearchContactsInput(_ApiKeyOnly):
    q_keywords: str | None = Field(default=None, description="Keyword search")
    contact_stage_ids: list[str] | None = Field(default=None, description="Stages")
    contact_owner_ids: list[str] | None = Field(default=None, description="Owners")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page (max 100)")


class ViewContactInput(_ApiKeyOnly):
    contact_id: str = Field(description="Contact ID to view")


class CreateAccountInput(_ApiKeyOnly):
    name: str = Field(description="Account/company name")
    domain: str = Field(description="Company domain")
    phone_number: str | None = Field(default=None, description="Phone number")
    raw_address: str | None = Field(default=None, description="Address")
    owner_id: str | None = Field(default=None, description="Owner user ID")


class UpdateAccountInput(_ApiKeyOnly):
    account_id: str = Field(description="Account ID to update")
    name: str | None = Field(default=None, description="New name")
    phone_number: str | None = Field(default=None, description="New phone")
    raw_address: str | None = Field(default=None, description="New address")
    owner_id: str | None = Field(default=None, description="New owner ID")


class SearchAccountsInput(_ApiKeyOnly):
    q_organization_name: str | None = Field(default=None, description="Name filter")
    account_stage_ids: list[str] | None = Field(default=None, description="Stages")
    account_owner_ids: list[str] | None = Field(default=None, description="Owners")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page (max 100)")


class ViewAccountInput(_ApiKeyOnly):
    account_id: str = Field(description="Account ID to view")


class CreateDealInput(_ApiKeyOnly):
    name: str = Field(description="Deal name")
    deal_stage_id: str = Field(description="Deal stage ID")
    amount: float | None = Field(default=None, description="Deal amount")
    account_id: str | None = Field(default=None, description="Account ID")
    contact_ids: list[str] | None = Field(default=None, description="Contact IDs")
    owner_id: str | None = Field(default=None, description="Owner user ID")
    closed_date: str | None = Field(default=None, description="YYYY-MM-DD")


class UpdateDealInput(_ApiKeyOnly):
    deal_id: str = Field(description="Deal ID to update")
    name: str | None = Field(default=None, description="New name")
    deal_stage_id: str | None = Field(default=None, description="New stage ID")
    amount: float | None = Field(default=None, description="New amount")
    owner_id: str | None = Field(default=None, description="New owner ID")


class ListDealsInput(_ApiKeyOnly):
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page")


class ViewDealInput(_ApiKeyOnly):
    deal_id: str = Field(description="Deal ID to view")


class SearchSequencesInput(_ApiKeyOnly):
    q_name: str | None = Field(default=None, description="Sequence name filter")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page")


class AddContactsToSequenceInput(_ApiKeyOnly):
    sequence_id: str = Field(description="Sequence ID")
    contact_ids: list[str] = Field(description="Contact IDs to enroll")
    emailer_campaign_id: str | None = Field(default=None, description="Email campaign ID")
    send_email_from_email_account_id: str | None = Field(
        default=None, description="Sender email account ID"
    )


class CreateTaskInput(_ApiKeyOnly):
    name: str = Field(description="Task name/subject")
    due_date: str = Field(description="Due date (YYYY-MM-DD)")
    priority: str = Field(default="normal", description="'low', 'normal', 'high'")
    contact_id: str | None = Field(default=None, description="Associated contact")
    account_id: str | None = Field(default=None, description="Associated account")
    user_id: str | None = Field(default=None, description="Assigned user")
    note: str | None = Field(default=None, description="Task notes")


class SearchTasksInput(_ApiKeyOnly):
    status: str | None = Field(default=None, description="Status filter")
    user_ids: list[str] | None = Field(default=None, description="Filter by users")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page")


class GetApiUsageInput(_ApiKeyOnly):
    pass


class ListUsersInput(_ApiKeyOnly):
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page")


class ListContactStagesInput(_ApiKeyOnly):
    pass


class ListAccountStagesInput(_ApiKeyOnly):
    pass


class ListDealStagesInput(_ApiKeyOnly):
    pass


# --- Tools -----------------------------------------------------------------


@tool(args_schema=PeopleEnrichmentInput)
@serialize_pydantic_return
async def people_enrichment(
    api_key: str,
    first_name: str | None = None,
    last_name: str | None = None,
    name: str | None = None,
    email: str | None = None,
    organization_name: str | None = None,
    domain: str | None = None,
    linkedin_url: str | None = None,
    reveal_personal_emails: bool = False,
    reveal_phone_number: bool = False,
) -> PeopleEnrichmentOutput:
    """Enrich a single person's profile."""
    if not api_key or not api_key.strip():
        return PeopleEnrichmentOutput(success=False, error=_empty_key_error("people_enrichment"))
    payload = _filter_none(
        {
            "first_name": first_name,
            "last_name": last_name,
            "name": name,
            "email": email,
            "organization_name": organization_name,
            "domain": domain,
            "linkedin_url": linkedin_url,
            "reveal_personal_emails": reveal_personal_emails,
            "reveal_phone_number": reveal_phone_number,
        }
    )
    ok, err, body = await _call("/people/match", api_key, json_data=payload)
    return PeopleEnrichmentOutput(success=ok, error=err, result=body)


@tool(args_schema=BulkPeopleEnrichmentInput)
@serialize_pydantic_return
async def bulk_people_enrichment(
    api_key: str,
    details: list[dict[str, Any]],
    reveal_personal_emails: bool = False,
) -> BulkPeopleEnrichmentOutput:
    """Enrich up to 10 people in a single request."""
    if not api_key or not api_key.strip():
        return BulkPeopleEnrichmentOutput(
            success=False, error=_empty_key_error("bulk_people_enrichment")
        )
    ok, err, body = await _call(
        "/people/bulk_match",
        api_key,
        json_data={"details": details[:10], "reveal_personal_emails": reveal_personal_emails},
    )
    return BulkPeopleEnrichmentOutput(success=ok, error=err, result=body)


@tool(args_schema=OrganizationEnrichmentInput)
@serialize_pydantic_return
async def organization_enrichment(
    api_key: str, domain: str
) -> OrganizationEnrichmentOutput:
    """Enrich a company's profile by domain."""
    if not api_key or not api_key.strip():
        return OrganizationEnrichmentOutput(
            success=False, error=_empty_key_error("organization_enrichment")
        )
    ok, err, body = await _call(
        "/organizations/enrich",
        api_key,
        method="GET",
        params={"domain": _clean_domain(domain)},
    )
    return OrganizationEnrichmentOutput(success=ok, error=err, result=body)


@tool(args_schema=BulkOrganizationEnrichmentInput)
@serialize_pydantic_return
async def bulk_organization_enrichment(
    api_key: str, domains: list[str]
) -> BulkOrganizationEnrichmentOutput:
    """Enrich up to 10 organizations in a single request."""
    if not api_key or not api_key.strip():
        return BulkOrganizationEnrichmentOutput(
            success=False, error=_empty_key_error("bulk_organization_enrichment")
        )
    cleaned = [_clean_domain(d) for d in domains[:10]]
    ok, err, body = await _call(
        "/organizations/bulk_enrich", api_key, json_data={"domains": cleaned}
    )
    return BulkOrganizationEnrichmentOutput(success=ok, error=err, result=body)


@tool(args_schema=PeopleSearchInput)
@serialize_pydantic_return
async def people_search(
    api_key: str,
    person_titles: list[str] | None = None,
    person_seniorities: list[str] | None = None,
    person_locations: list[str] | None = None,
    organization_locations: list[str] | None = None,
    q_organization_domains: list[str] | None = None,
    organization_ids: list[str] | None = None,
    organization_num_employees_ranges: list[str] | None = None,
    contact_email_status: list[str] | None = None,
    q_keywords: str | None = None,
    page: int = 1,
    per_page: int = 25,
) -> PeopleSearchOutput:
    """Search Apollo's people database."""
    if not api_key or not api_key.strip():
        return PeopleSearchOutput(success=False, error=_empty_key_error("people_search"))
    payload: dict[str, Any] = {"page": page, "per_page": min(per_page, 100)}
    if person_titles:
        payload["person_titles"] = person_titles
    if person_seniorities:
        payload["person_seniorities"] = person_seniorities
    if person_locations:
        payload["person_locations"] = person_locations
    if organization_locations:
        payload["organization_locations"] = organization_locations
    if q_organization_domains:
        payload["q_organization_domains_list"] = q_organization_domains
    if organization_ids:
        payload["organization_ids"] = organization_ids
    if organization_num_employees_ranges:
        payload["organization_num_employees_ranges"] = organization_num_employees_ranges
    if contact_email_status:
        payload["contact_email_status"] = contact_email_status
    if q_keywords:
        payload["q_keywords"] = q_keywords
    ok, err, body = await _call("/mixed_people/search", api_key, json_data=payload)
    return PeopleSearchOutput(success=ok, error=err, result=body)


@tool(args_schema=OrganizationSearchInput)
@serialize_pydantic_return
async def organization_search(
    api_key: str,
    q_organization_name: str | None = None,
    organization_locations: list[str] | None = None,
    organization_not_locations: list[str] | None = None,
    organization_num_employees_ranges: list[str] | None = None,
    revenue_range_min: int | None = None,
    revenue_range_max: int | None = None,
    currently_using_any_of_technology_uids: list[str] | None = None,
    q_organization_keyword_tags: list[str] | None = None,
    page: int = 1,
    per_page: int = 25,
) -> OrganizationSearchOutput:
    """Search Apollo's organization database."""
    if not api_key or not api_key.strip():
        return OrganizationSearchOutput(
            success=False, error=_empty_key_error("organization_search")
        )
    payload: dict[str, Any] = {"page": page, "per_page": min(per_page, 100)}
    if q_organization_name:
        payload["q_organization_name"] = q_organization_name
    if organization_locations:
        payload["organization_locations"] = organization_locations
    if organization_not_locations:
        payload["organization_not_locations"] = organization_not_locations
    if organization_num_employees_ranges:
        payload["organization_num_employees_ranges"] = organization_num_employees_ranges
    if revenue_range_min or revenue_range_max:
        rr: dict[str, int] = {}
        if revenue_range_min:
            rr["min"] = revenue_range_min
        if revenue_range_max:
            rr["max"] = revenue_range_max
        payload["revenue_range"] = rr
    if currently_using_any_of_technology_uids:
        payload["currently_using_any_of_technology_uids"] = (
            currently_using_any_of_technology_uids
        )
    if q_organization_keyword_tags:
        payload["q_organization_keyword_tags"] = q_organization_keyword_tags
    ok, err, body = await _call("/mixed_companies/search", api_key, json_data=payload)
    return OrganizationSearchOutput(success=ok, error=err, result=body)


@tool(args_schema=OrganizationJobPostingsInput)
@serialize_pydantic_return
async def organization_job_postings(
    api_key: str, organization_id: str
) -> OrganizationJobPostingsOutput:
    """Get active job postings for a specific Apollo organization."""
    if not api_key or not api_key.strip():
        return OrganizationJobPostingsOutput(
            success=False, error=_empty_key_error("organization_job_postings")
        )
    ok, err, body = await _call(
        f"/organizations/{organization_id}/job_postings", api_key, method="GET"
    )
    return OrganizationJobPostingsOutput(success=ok, error=err, result=body)


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    api_key: str,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    title: str | None = None,
    organization_name: str | None = None,
    account_id: str | None = None,
    phone_number: str | None = None,
    linkedin_url: str | None = None,
    present_raw_address: str | None = None,
    label_names: list[str] | None = None,
) -> CreateContactOutput:
    """Create a new contact in your Apollo database."""
    if not api_key or not api_key.strip():
        return CreateContactOutput(success=False, error=_empty_key_error("create_contact"))
    payload = _filter_none(
        {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "organization_name": organization_name,
            "account_id": account_id,
            "phone_number": phone_number,
            "linkedin_url": linkedin_url,
            "present_raw_address": present_raw_address,
            "label_names": label_names,
        }
    )
    ok, err, body = await _call("/contacts", api_key, json_data=payload)
    return CreateContactOutput(success=ok, error=err, result=body)


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    api_key: str,
    contact_id: str,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    title: str | None = None,
    phone_number: str | None = None,
    account_id: str | None = None,
) -> UpdateContactOutput:
    """Update an existing contact."""
    if not api_key or not api_key.strip():
        return UpdateContactOutput(success=False, error=_empty_key_error("update_contact"))
    payload = _filter_none(
        {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "phone_number": phone_number,
            "account_id": account_id,
        }
    )
    ok, err, body = await _call(
        f"/contacts/{contact_id}", api_key, method="PATCH", json_data=payload
    )
    return UpdateContactOutput(success=ok, error=err, result=body)


@tool(args_schema=SearchContactsInput)
@serialize_pydantic_return
async def search_contacts(
    api_key: str,
    q_keywords: str | None = None,
    contact_stage_ids: list[str] | None = None,
    contact_owner_ids: list[str] | None = None,
    page: int = 1,
    per_page: int = 25,
) -> SearchContactsOutput:
    """Search contacts in your Apollo database."""
    if not api_key or not api_key.strip():
        return SearchContactsOutput(success=False, error=_empty_key_error("search_contacts"))
    payload: dict[str, Any] = {"page": page, "per_page": min(per_page, 100)}
    if q_keywords:
        payload["q_keywords"] = q_keywords
    if contact_stage_ids:
        payload["contact_stage_ids"] = contact_stage_ids
    if contact_owner_ids:
        payload["contact_owner_ids"] = contact_owner_ids
    ok, err, body = await _call("/contacts/search", api_key, json_data=payload)
    return SearchContactsOutput(success=ok, error=err, result=body)


@tool(args_schema=ViewContactInput)
@serialize_pydantic_return
async def view_contact(api_key: str, contact_id: str) -> ViewContactOutput:
    """View detailed information for a specific contact."""
    if not api_key or not api_key.strip():
        return ViewContactOutput(success=False, error=_empty_key_error("view_contact"))
    ok, err, body = await _call(f"/contacts/{contact_id}", api_key, method="GET")
    return ViewContactOutput(success=ok, error=err, result=body)


@tool(args_schema=CreateAccountInput)
@serialize_pydantic_return
async def create_account(
    api_key: str,
    name: str,
    domain: str,
    phone_number: str | None = None,
    raw_address: str | None = None,
    owner_id: str | None = None,
) -> CreateAccountOutput:
    """Create a new account (company)."""
    if not api_key or not api_key.strip():
        return CreateAccountOutput(success=False, error=_empty_key_error("create_account"))
    payload: dict[str, Any] = {"name": name, "domain": domain}
    if phone_number:
        payload["phone_number"] = phone_number
    if raw_address:
        payload["raw_address"] = raw_address
    if owner_id:
        payload["owner_id"] = owner_id
    ok, err, body = await _call("/accounts", api_key, json_data=payload)
    return CreateAccountOutput(success=ok, error=err, result=body)


@tool(args_schema=UpdateAccountInput)
@serialize_pydantic_return
async def update_account(
    api_key: str,
    account_id: str,
    name: str | None = None,
    phone_number: str | None = None,
    raw_address: str | None = None,
    owner_id: str | None = None,
) -> UpdateAccountOutput:
    """Update an existing account."""
    if not api_key or not api_key.strip():
        return UpdateAccountOutput(success=False, error=_empty_key_error("update_account"))
    payload = _filter_none(
        {
            "name": name,
            "phone_number": phone_number,
            "raw_address": raw_address,
            "owner_id": owner_id,
        }
    )
    ok, err, body = await _call(
        f"/accounts/{account_id}", api_key, method="PATCH", json_data=payload
    )
    return UpdateAccountOutput(success=ok, error=err, result=body)


@tool(args_schema=SearchAccountsInput)
@serialize_pydantic_return
async def search_accounts(
    api_key: str,
    q_organization_name: str | None = None,
    account_stage_ids: list[str] | None = None,
    account_owner_ids: list[str] | None = None,
    page: int = 1,
    per_page: int = 25,
) -> SearchAccountsOutput:
    """Search accounts in your Apollo database."""
    if not api_key or not api_key.strip():
        return SearchAccountsOutput(success=False, error=_empty_key_error("search_accounts"))
    payload: dict[str, Any] = {"page": page, "per_page": min(per_page, 100)}
    if q_organization_name:
        payload["q_organization_name"] = q_organization_name
    if account_stage_ids:
        payload["account_stage_ids"] = account_stage_ids
    if account_owner_ids:
        payload["account_owner_ids"] = account_owner_ids
    ok, err, body = await _call("/accounts/search", api_key, json_data=payload)
    return SearchAccountsOutput(success=ok, error=err, result=body)


@tool(args_schema=ViewAccountInput)
@serialize_pydantic_return
async def view_account(api_key: str, account_id: str) -> ViewAccountOutput:
    """View detailed information for a specific account."""
    if not api_key or not api_key.strip():
        return ViewAccountOutput(success=False, error=_empty_key_error("view_account"))
    ok, err, body = await _call(f"/accounts/{account_id}", api_key, method="GET")
    return ViewAccountOutput(success=ok, error=err, result=body)


@tool(args_schema=CreateDealInput)
@serialize_pydantic_return
async def create_deal(
    api_key: str,
    name: str,
    deal_stage_id: str,
    amount: float | None = None,
    account_id: str | None = None,
    contact_ids: list[str] | None = None,
    owner_id: str | None = None,
    closed_date: str | None = None,
) -> CreateDealOutput:
    """Create a new deal/opportunity."""
    if not api_key or not api_key.strip():
        return CreateDealOutput(success=False, error=_empty_key_error("create_deal"))
    payload: dict[str, Any] = {"name": name, "deal_stage_id": deal_stage_id}
    if amount is not None:
        payload["amount"] = amount
    if account_id:
        payload["account_id"] = account_id
    if contact_ids:
        payload["contact_ids"] = contact_ids
    if owner_id:
        payload["owner_id"] = owner_id
    if closed_date:
        payload["closed_date"] = closed_date
    ok, err, body = await _call("/opportunities", api_key, json_data=payload)
    return CreateDealOutput(success=ok, error=err, result=body)


@tool(args_schema=UpdateDealInput)
@serialize_pydantic_return
async def update_deal(
    api_key: str,
    deal_id: str,
    name: str | None = None,
    deal_stage_id: str | None = None,
    amount: float | None = None,
    owner_id: str | None = None,
) -> UpdateDealOutput:
    """Update an existing deal."""
    if not api_key or not api_key.strip():
        return UpdateDealOutput(success=False, error=_empty_key_error("update_deal"))
    payload = _filter_none(
        {
            "name": name,
            "deal_stage_id": deal_stage_id,
            "amount": amount,
            "owner_id": owner_id,
        }
    )
    ok, err, body = await _call(
        f"/opportunities/{deal_id}", api_key, method="PUT", json_data=payload
    )
    return UpdateDealOutput(success=ok, error=err, result=body)


@tool(args_schema=ListDealsInput)
@serialize_pydantic_return
async def list_deals(
    api_key: str, page: int = 1, per_page: int = 25
) -> ListDealsOutput:
    """List all deals in your Apollo account."""
    if not api_key or not api_key.strip():
        return ListDealsOutput(success=False, error=_empty_key_error("list_deals"))
    ok, err, body = await _call(
        "/opportunities/search",
        api_key,
        json_data={"page": page, "per_page": per_page},
    )
    return ListDealsOutput(success=ok, error=err, result=body)


@tool(args_schema=ViewDealInput)
@serialize_pydantic_return
async def view_deal(api_key: str, deal_id: str) -> ViewDealOutput:
    """View detailed information for a specific deal."""
    if not api_key or not api_key.strip():
        return ViewDealOutput(success=False, error=_empty_key_error("view_deal"))
    ok, err, body = await _call(f"/opportunities/{deal_id}", api_key, method="GET")
    return ViewDealOutput(success=ok, error=err, result=body)


@tool(args_schema=SearchSequencesInput)
@serialize_pydantic_return
async def search_sequences(
    api_key: str,
    q_name: str | None = None,
    page: int = 1,
    per_page: int = 25,
) -> SearchSequencesOutput:
    """Search for email sequences."""
    if not api_key or not api_key.strip():
        return SearchSequencesOutput(success=False, error=_empty_key_error("search_sequences"))
    payload: dict[str, Any] = {"page": page, "per_page": per_page}
    if q_name:
        payload["q_name"] = q_name
    ok, err, body = await _call("/emailer_campaigns/search", api_key, json_data=payload)
    return SearchSequencesOutput(success=ok, error=err, result=body)


@tool(args_schema=AddContactsToSequenceInput)
@serialize_pydantic_return
async def add_contacts_to_sequence(
    api_key: str,
    sequence_id: str,
    contact_ids: list[str],
    emailer_campaign_id: str | None = None,
    send_email_from_email_account_id: str | None = None,
) -> AddContactsToSequenceOutput:
    """Add contacts to an email sequence."""
    if not api_key or not api_key.strip():
        return AddContactsToSequenceOutput(
            success=False, error=_empty_key_error("add_contacts_to_sequence")
        )
    payload: dict[str, Any] = {"contact_ids": contact_ids}
    if emailer_campaign_id:
        payload["emailer_campaign_id"] = emailer_campaign_id
    if send_email_from_email_account_id:
        payload["send_email_from_email_account_id"] = send_email_from_email_account_id
    ok, err, body = await _call(
        f"/emailer_campaigns/{sequence_id}/add_contact_ids", api_key, json_data=payload
    )
    return AddContactsToSequenceOutput(success=ok, error=err, result=body)


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    api_key: str,
    name: str,
    due_date: str,
    priority: str = "normal",
    contact_id: str | None = None,
    account_id: str | None = None,
    user_id: str | None = None,
    note: str | None = None,
) -> CreateTaskOutput:
    """Create a new task/reminder."""
    if not api_key or not api_key.strip():
        return CreateTaskOutput(success=False, error=_empty_key_error("create_task"))
    payload: dict[str, Any] = {"name": name, "due_date": due_date, "priority": priority}
    if contact_id:
        payload["contact_id"] = contact_id
    if account_id:
        payload["account_id"] = account_id
    if user_id:
        payload["user_id"] = user_id
    if note:
        payload["note"] = note
    ok, err, body = await _call("/tasks", api_key, json_data=payload)
    return CreateTaskOutput(success=ok, error=err, result=body)


@tool(args_schema=SearchTasksInput)
@serialize_pydantic_return
async def search_tasks(
    api_key: str,
    status: str | None = None,
    user_ids: list[str] | None = None,
    page: int = 1,
    per_page: int = 25,
) -> SearchTasksOutput:
    """Search tasks in your Apollo account."""
    if not api_key or not api_key.strip():
        return SearchTasksOutput(success=False, error=_empty_key_error("search_tasks"))
    payload: dict[str, Any] = {"page": page, "per_page": per_page}
    if status:
        payload["status"] = status
    if user_ids:
        payload["user_ids"] = user_ids
    ok, err, body = await _call("/tasks/search", api_key, json_data=payload)
    return SearchTasksOutput(success=ok, error=err, result=body)


@tool(args_schema=GetApiUsageInput)
@serialize_pydantic_return
async def get_api_usage(api_key: str) -> GetApiUsageOutput:
    """Get API usage statistics and rate limit information."""
    if not api_key or not api_key.strip():
        return GetApiUsageOutput(success=False, error=_empty_key_error("get_api_usage"))
    ok, err, body = await _call("/account/stats", api_key, json_data={})
    return GetApiUsageOutput(success=ok, error=err, result=body)


@tool(args_schema=ListUsersInput)
@serialize_pydantic_return
async def list_users(
    api_key: str, page: int = 1, per_page: int = 25
) -> ListUsersOutput:
    """List all team members in your Apollo account."""
    if not api_key or not api_key.strip():
        return ListUsersOutput(success=False, error=_empty_key_error("list_users"))
    ok, err, body = await _call(
        "/users/search", api_key, json_data={"page": page, "per_page": per_page}
    )
    return ListUsersOutput(success=ok, error=err, result=body)


@tool(args_schema=ListContactStagesInput)
@serialize_pydantic_return
async def list_contact_stages(api_key: str) -> ListContactStagesOutput:
    """List all contact stages."""
    if not api_key or not api_key.strip():
        return ListContactStagesOutput(
            success=False, error=_empty_key_error("list_contact_stages")
        )
    ok, err, body = await _call("/contact_stages", api_key, method="GET")
    return ListContactStagesOutput(success=ok, error=err, result=body)


@tool(args_schema=ListAccountStagesInput)
@serialize_pydantic_return
async def list_account_stages(api_key: str) -> ListAccountStagesOutput:
    """List all account stages."""
    if not api_key or not api_key.strip():
        return ListAccountStagesOutput(
            success=False, error=_empty_key_error("list_account_stages")
        )
    ok, err, body = await _call("/account_stages", api_key, method="GET")
    return ListAccountStagesOutput(success=ok, error=err, result=body)


@tool(args_schema=ListDealStagesInput)
@serialize_pydantic_return
async def list_deal_stages(api_key: str) -> ListDealStagesOutput:
    """List all deal stages."""
    if not api_key or not api_key.strip():
        return ListDealStagesOutput(
            success=False, error=_empty_key_error("list_deal_stages")
        )
    ok, err, body = await _call("/opportunity_stages", api_key, method="GET")
    return ListDealStagesOutput(success=ok, error=err, result=body)
