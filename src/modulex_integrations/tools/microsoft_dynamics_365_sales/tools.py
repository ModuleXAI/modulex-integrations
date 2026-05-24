"""Microsoft Dynamics 365 Sales LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_dynamics_365_sales.outputs import (
    CreateAppointmentOutput,
    CreateCustomEntityOutput,
    FindContactOutput,
    GetAccountOutput,
    ListAccountsOutput,
    ListAppointmentCategoriesOutput,
    ListAppointmentCategoryOptionsOutput,
    ListAppointmentsOutput,
    ListSolutionIdOptionsOutput,
    SearchAccountsOutput,
    UpdateAppointmentOutput,
)

__all__ = [
    "create_appointment",
    "create_custom_entity",
    "find_contact",
    "get_account",
    "list_accounts",
    "list_appointment_categories",
    "list_appointment_category_options",
    "list_appointments",
    "list_solution_id_options",
    "search_accounts",
    "update_appointment",
]

_TIMEOUT = 30.0


def _base_url(auth_data: dict[str, Any]) -> str:
    api_url = auth_data.get("api_url", "")
    if not api_url:
        api_url = "org.crm.dynamics.com"
    if not api_url.startswith("http"):
        api_url = f"https://{api_url}"
    return f"{api_url}/api/data/v9.2"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class CreateAppointmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subject: str = Field(description="Title of the appointment")
    scheduledstart: str = Field(description="Start date/time in ISO 8601 format")
    scheduledend: str = Field(description="End date/time in ISO 8601 format")
    regarding_account_id: str = Field(description="Account ID the appointment is regarding")
    required_attendee_email: str = Field(description="Email of the Dynamics system user to add as attendee")
    category: int | None = Field(default=None, description="Optional category value (numeric)")


class CreateCustomEntityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    solution_id: str = Field(description="Solution ID to associate the entity with")
    display_name: str = Field(description="Display name for the new entity")
    primary_attribute: str = Field(description="Primary name attribute of the new entity")
    language_code: int = Field(default=1033, description="Language code (e.g. 1033 for English US)")
    additional_attributes: dict[str, Any] | None = Field(default=None, description="Additional attribute definitions")
    description: str | None = Field(default=None, description="Description of the new entity")
    has_activities: bool = Field(default=False, description="Whether the entity supports activities")
    has_notes: bool = Field(default=False, description="Whether the entity supports notes")


class FindContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str | None = Field(default=None, description="Contact GUID to look up directly")
    name: str | None = Field(default=None, description="Find contacts whose full name contains this value")
    filter: str | None = Field(default=None, description="Custom OData $filter expression")


class GetAccountInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="Account GUID to retrieve")


class ListAccountsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    filter: str | None = Field(default=None, description="Optional OData $filter expression")
    records_per_page: int = Field(default=50, description="Number of records per page (max 5000)")


class ListAppointmentCategoriesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListAppointmentCategoryOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListAppointmentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    filter: str | None = Field(default=None, description="Optional OData $filter expression")
    records_per_page: int = Field(default=25, description="Number of appointments to return (max 100)")


class ListSolutionIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class SearchAccountsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search_term: str = Field(description="Substring to match against account name")


class UpdateAppointmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    appointment_id: str = Field(description="Appointment activity GUID to update")
    subject: str | None = Field(default=None, description="Updated subject/title")
    scheduledstart: str | None = Field(default=None, description="Updated start in ISO 8601")
    scheduledend: str | None = Field(default=None, description="Updated end in ISO 8601")
    category: int | None = Field(default=None, description="Updated category value (numeric)")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateAppointmentInput)
@serialize_pydantic_return
async def create_appointment(
    auth_type: str,
    auth_data: dict[str, Any],
    subject: str,
    scheduledstart: str,
    scheduledend: str,
    regarding_account_id: str,
    required_attendee_email: str,
    category: int | None = None,
) -> CreateAppointmentOutput:
    """Create a new appointment linked to an account with a required attendee (system user)."""
    if not auth_data.get("access_token"):
        return CreateAppointmentOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Look up system user by email
            escaped_email = required_attendee_email.replace("'", "''")
            user_resp = await client.get(
                f"{base}/systemusers",
                headers=headers,
                params={"$filter": f"internalemailaddress eq '{escaped_email}'", "$select": "systemuserid"},
            )
            if user_resp.status_code != 200:
                return CreateAppointmentOutput(
                    success=False,
                    error=f"Failed to look up system user ({user_resp.status_code}): {user_resp.text}",
                )
            users = user_resp.json().get("value", [])
            if not users:
                return CreateAppointmentOutput(
                    success=False,
                    error=f"No system user found with email '{required_attendee_email}'",
                )
            user_id = users[0]["systemuserid"]

            # Build appointment payload
            body: dict[str, Any] = {
                "subject": subject,
                "scheduledstart": scheduledstart,
                "scheduledend": scheduledend,
                "regardingobjectid_account@odata.bind": f"/accounts({regarding_account_id})",
                "appointment_activity_parties": [
                    {
                        "partyid_systemuser@odata.bind": f"/systemusers({user_id})",
                        "participationtypemask": 5,
                    },
                ],
            }
            if category is not None:
                body["category"] = category

            create_headers = {**headers, "Content-Type": "application/json", "Prefer": "return=representation"}
            resp = await client.post(
                f"{base}/appointments",
                headers=create_headers,
                json=body,
            )
            if resp.status_code not in (200, 201):
                return CreateAppointmentOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
            data = resp.json()
            appointment_id = data.get("activityid", "")
    except httpx.TimeoutException:
        return CreateAppointmentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateAppointmentOutput(success=False, error=f"Call failed: {exc}")

    api_url = auth_data.get("api_url", "")
    deep_link = f"https://{api_url}/main.aspx?etn=appointment&id={appointment_id}&pagetype=entityrecord" if api_url else None
    return CreateAppointmentOutput(
        success=True,
        appointment_id=appointment_id,
        deep_link=deep_link,
        appointment=data,
    )


@tool(args_schema=CreateCustomEntityInput)
@serialize_pydantic_return
async def create_custom_entity(
    auth_type: str,
    auth_data: dict[str, Any],
    solution_id: str,
    display_name: str,
    primary_attribute: str,
    language_code: int = 1033,
    additional_attributes: dict[str, Any] | None = None,
    description: str | None = None,
    has_activities: bool = False,
    has_notes: bool = False,
) -> CreateCustomEntityOutput:
    """Create a custom entity definition in Dynamics 365."""
    if not auth_data.get("access_token"):
        return CreateCustomEntityOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Resolve solution unique name
            sol_resp = await client.get(
                f"{base}/solutions({solution_id})",
                headers=headers,
                params={"$select": "uniquename,publisherid"},
            )
            if sol_resp.status_code != 200:
                return CreateCustomEntityOutput(
                    success=False,
                    error=f"Failed to resolve solution ({sol_resp.status_code}): {sol_resp.text}",
                )
            sol_data = sol_resp.json()
            solution_unique_name = sol_data.get("uniquename", "")

            # Build schema name from display_name
            schema_name = display_name.replace(" ", "").lower()
            plural_name = schema_name + "s"

            body: dict[str, Any] = {
                "SchemaName": schema_name,
                "DisplayName": {
                    "@odata.type": "Microsoft.Dynamics.CRM.Label",
                    "LocalizedLabels": [
                        {"Label": display_name, "LanguageCode": language_code},
                    ],
                },
                "DisplayCollectionName": {
                    "@odata.type": "Microsoft.Dynamics.CRM.Label",
                    "LocalizedLabels": [
                        {"Label": plural_name, "LanguageCode": language_code},
                    ],
                },
                "HasActivities": has_activities,
                "HasNotes": has_notes,
                "PrimaryNameAttribute": primary_attribute.replace(" ", "").lower(),
                "Attributes": [
                    {
                        "SchemaName": primary_attribute.replace(" ", "").lower(),
                        "AttributeType": "String",
                        "AttributeTypeName": {"Value": "StringType"},
                        "MaxLength": 100,
                        "DisplayName": {
                            "@odata.type": "Microsoft.Dynamics.CRM.Label",
                            "LocalizedLabels": [
                                {"Label": primary_attribute, "LanguageCode": language_code},
                            ],
                        },
                    },
                ],
            }
            if description:
                body["Description"] = {
                    "@odata.type": "Microsoft.Dynamics.CRM.Label",
                    "LocalizedLabels": [
                        {"Label": description, "LanguageCode": language_code},
                    ],
                }

            create_headers = {
                **headers,
                "Content-Type": "application/json",
                "MSCRM.SolutionUniqueName": solution_unique_name,
            }
            resp = await client.post(
                f"{base}/EntityDefinitions",
                headers=create_headers,
                json=body,
            )
            if resp.status_code not in (200, 201, 204):
                return CreateCustomEntityOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )

            # Try to get the created entity
            entity_id_header = resp.headers.get("odata-entityid", "")
            entity_data: dict[str, Any] | None = None
            if entity_id_header:
                entity_resp = await client.get(entity_id_header, headers=headers)
                if entity_resp.status_code == 200:
                    entity_data = entity_resp.json()
    except httpx.TimeoutException:
        return CreateCustomEntityOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCustomEntityOutput(success=False, error=f"Call failed: {exc}")

    return CreateCustomEntityOutput(success=True, entity=entity_data)


@tool(args_schema=FindContactInput)
@serialize_pydantic_return
async def find_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str | None = None,
    name: str | None = None,
    filter: str | None = None,
) -> FindContactOutput:
    """Search for a contact by ID, name, or custom OData filter."""
    if not auth_data.get("access_token"):
        return FindContactOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            if contact_id:
                resp = await client.get(f"{base}/contacts({contact_id})", headers=headers)
                if resp.status_code != 200:
                    return FindContactOutput(
                        success=False,
                        error=f"API error ({resp.status_code}): {resp.text}",
                    )
                return FindContactOutput(success=True, contacts=[resp.json()])

            filters: list[str] = []
            if name:
                escaped_name = name.replace("'", "''")
                filters.append(f"contains(fullname,'{escaped_name}')")
            if filter:
                filters.append(filter)
            params: dict[str, str] = {}
            if filters:
                params["$filter"] = " and ".join(filters)

            resp = await client.get(f"{base}/contacts", headers=headers, params=params)
            if resp.status_code != 200:
                return FindContactOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
            data = resp.json()
    except httpx.TimeoutException:
        return FindContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindContactOutput(success=False, error=f"Call failed: {exc}")

    return FindContactOutput(success=True, contacts=data.get("value", []))


@tool(args_schema=GetAccountInput)
@serialize_pydantic_return
async def get_account(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
) -> GetAccountOutput:
    """Retrieve a single account by its GUID."""
    if not auth_data.get("access_token"):
        return GetAccountOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{base}/accounts({account_id})", headers=headers)
            if resp.status_code != 200:
                return GetAccountOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
            data = resp.json()
    except httpx.TimeoutException:
        return GetAccountOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAccountOutput(success=False, error=f"Call failed: {exc}")

    return GetAccountOutput(success=True, account=data)


@tool(args_schema=ListAccountsInput)
@serialize_pydantic_return
async def list_accounts(
    auth_type: str,
    auth_data: dict[str, Any],
    filter: str | None = None,
    records_per_page: int = 50,
) -> ListAccountsOutput:
    """List accounts with optional OData filter and pagination."""
    if not auth_data.get("access_token"):
        return ListAccountsOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Prefer"] = f"odata.maxpagesize={records_per_page}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            params: dict[str, str] = {
                "$select": "accountid,name,telephone1,emailaddress1,_primarycontactid_value",
            }
            if filter:
                params["$filter"] = filter

            resp = await client.get(f"{base}/accounts", headers=headers, params=params)
            if resp.status_code != 200:
                return ListAccountsOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
            data = resp.json()
    except httpx.TimeoutException:
        return ListAccountsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAccountsOutput(success=False, error=f"Call failed: {exc}")

    return ListAccountsOutput(success=True, accounts=data.get("value", []))


@tool(args_schema=ListAppointmentCategoriesInput)
@serialize_pydantic_return
async def list_appointment_categories(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListAppointmentCategoriesOutput:
    """List available appointment category values from metadata or existing rows."""
    if not auth_data.get("access_token"):
        return ListAppointmentCategoriesOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Try picklist metadata first
            resp = await client.get(
                f"{base}/EntityDefinitions(LogicalName='appointment')/Attributes(LogicalName='category')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata",
                headers=headers,
                params={"$expand": "OptionSet"},
            )
            if resp.status_code == 200:
                data = resp.json()
                option_set = data.get("OptionSet", {})
                options = option_set.get("Options", [])
                categories = [
                    {"value": opt.get("Value"), "label": (opt.get("Label", {}).get("UserLocalizedLabel", {}) or {}).get("Label", "")}
                    for opt in options
                ]
                return ListAppointmentCategoriesOutput(
                    success=True,
                    category_type="picklist",
                    categories=categories,
                )

            # Fallback: distinct values from existing appointments
            resp2 = await client.get(
                f"{base}/appointments",
                headers=headers,
                params={"$select": "category", "$filter": "category ne null"},
            )
            if resp2.status_code != 200:
                return ListAppointmentCategoriesOutput(
                    success=False,
                    error=f"API error ({resp2.status_code}): {resp2.text}",
                )
            rows = resp2.json().get("value", [])
            seen: set[str] = set()
            categories_text: list[dict[str, Any]] = []
            for row in rows:
                val = str(row.get("category", ""))
                if val and val not in seen:
                    seen.add(val)
                    categories_text.append({"value": val, "label": val})
    except httpx.TimeoutException:
        return ListAppointmentCategoriesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAppointmentCategoriesOutput(success=False, error=f"Call failed: {exc}")

    return ListAppointmentCategoriesOutput(
        success=True,
        category_type="text",
        categories=categories_text,
    )


@tool(args_schema=ListAppointmentCategoryOptionsInput)
@serialize_pydantic_return
async def list_appointment_category_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListAppointmentCategoryOptionsOutput:
    """Retrieve available options for the appointment Category picklist field."""
    if not auth_data.get("access_token"):
        return ListAppointmentCategoryOptionsOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{base}/EntityDefinitions(LogicalName='appointment')/Attributes(LogicalName='category')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata",
                headers=headers,
                params={"$expand": "OptionSet"},
            )
            if resp.status_code != 200:
                return ListAppointmentCategoryOptionsOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
            data = resp.json()
            option_set = data.get("OptionSet", {})
            options_raw = option_set.get("Options", [])
            options = [
                {"value": opt.get("Value"), "label": (opt.get("Label", {}).get("UserLocalizedLabel", {}) or {}).get("Label", "")}
                for opt in options_raw
            ]
    except httpx.TimeoutException:
        return ListAppointmentCategoryOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAppointmentCategoryOptionsOutput(success=False, error=f"Call failed: {exc}")

    return ListAppointmentCategoryOptionsOutput(success=True, options=options)


@tool(args_schema=ListAppointmentsInput)
@serialize_pydantic_return
async def list_appointments(
    auth_type: str,
    auth_data: dict[str, Any],
    filter: str | None = None,
    records_per_page: int = 25,
) -> ListAppointmentsOutput:
    """List appointments ordered by scheduled start descending."""
    if not auth_data.get("access_token"):
        return ListAppointmentsOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Prefer"] = f"odata.maxpagesize={records_per_page}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            params: dict[str, str] = {"$orderby": "scheduledstart desc"}
            if filter:
                params["$filter"] = filter

            resp = await client.get(f"{base}/appointments", headers=headers, params=params)
            if resp.status_code != 200:
                return ListAppointmentsOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
            data = resp.json()
    except httpx.TimeoutException:
        return ListAppointmentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAppointmentsOutput(success=False, error=f"Call failed: {exc}")

    return ListAppointmentsOutput(success=True, appointments=data.get("value", []))


@tool(args_schema=ListSolutionIdOptionsInput)
@serialize_pydantic_return
async def list_solution_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListSolutionIdOptionsOutput:
    """Retrieve available solutions with their IDs and names."""
    if not auth_data.get("access_token"):
        return ListSolutionIdOptionsOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{base}/solutions",
                headers=headers,
                params={"$select": "solutionid,friendlyname,uniquename"},
            )
            if resp.status_code != 200:
                return ListSolutionIdOptionsOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
            data = resp.json()
            solutions = [
                {"value": s.get("solutionid"), "label": s.get("friendlyname", s.get("uniquename", ""))}
                for s in data.get("value", [])
            ]
    except httpx.TimeoutException:
        return ListSolutionIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSolutionIdOptionsOutput(success=False, error=f"Call failed: {exc}")

    return ListSolutionIdOptionsOutput(success=True, solutions=solutions)


@tool(args_schema=SearchAccountsInput)
@serialize_pydantic_return
async def search_accounts(
    auth_type: str,
    auth_data: dict[str, Any],
    search_term: str,
) -> SearchAccountsOutput:
    """Search accounts by company name substring."""
    if not auth_data.get("access_token"):
        return SearchAccountsOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    escaped = search_term.replace("'", "''")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{base}/accounts",
                headers=headers,
                params={
                    "$filter": f"contains(name,'{escaped}')",
                    "$select": "accountid,name,telephone1,emailaddress1",
                },
            )
            if resp.status_code != 200:
                return SearchAccountsOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
            data = resp.json()
    except httpx.TimeoutException:
        return SearchAccountsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchAccountsOutput(success=False, error=f"Call failed: {exc}")

    return SearchAccountsOutput(success=True, accounts=data.get("value", []))


@tool(args_schema=UpdateAppointmentInput)
@serialize_pydantic_return
async def update_appointment(
    auth_type: str,
    auth_data: dict[str, Any],
    appointment_id: str,
    subject: str | None = None,
    scheduledstart: str | None = None,
    scheduledend: str | None = None,
    category: int | None = None,
) -> UpdateAppointmentOutput:
    """Update an existing appointment (only supplied fields are modified)."""
    if not auth_data.get("access_token"):
        return UpdateAppointmentOutput(success=False, error="Missing access_token in auth_data.")
    base = _base_url(auth_data)
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    updated_fields: list[str] = []

    if subject is not None:
        body["subject"] = subject
        updated_fields.append("subject")
    if scheduledstart is not None:
        body["scheduledstart"] = scheduledstart
        updated_fields.append("scheduledstart")
    if scheduledend is not None:
        body["scheduledend"] = scheduledend
        updated_fields.append("scheduledend")
    if category is not None:
        body["category"] = category
        updated_fields.append("category")

    if not body:
        return UpdateAppointmentOutput(
            success=False,
            error="No fields provided to update.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            patch_headers = {**headers, "Content-Type": "application/json"}
            resp = await client.patch(
                f"{base}/appointments({appointment_id})",
                headers=patch_headers,
                json=body,
            )
            if resp.status_code not in (200, 204):
                return UpdateAppointmentOutput(
                    success=False,
                    error=f"API error ({resp.status_code}): {resp.text}",
                )
    except httpx.TimeoutException:
        return UpdateAppointmentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateAppointmentOutput(success=False, error=f"Call failed: {exc}")

    return UpdateAppointmentOutput(
        success=True,
        appointment_id=appointment_id,
        updated_fields=updated_fields,
    )
