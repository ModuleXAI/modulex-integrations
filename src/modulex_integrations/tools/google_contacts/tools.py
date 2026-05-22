"""Google Contacts LangChain @tool functions (Google People API v1)."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_contacts.outputs import (
    ContactSummary,
    CreateContactOutput,
    DeleteContactOutput,
    GetContactOutput,
    ListContactsOutput,
    ListDirectoryContactsOutput,
    UpdateContactOutput,
)

__all__ = [
    "create_contact",
    "delete_contact",
    "get_contact",
    "list_contacts",
    "list_directory_contacts",
    "update_contact",
]

_BASE_URL = "https://people.googleapis.com/v1"


# ---------------------------------------------------------------------------
# Auth helper — token-style. OAuth2 only (Google People API).
# ---------------------------------------------------------------------------


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# ---------------------------------------------------------------------------
# Internal helpers — Person <-> ContactSummary projection.
# ---------------------------------------------------------------------------


def _person_to_summary(person: dict[str, Any]) -> ContactSummary:
    """Project a Google People `Person` object onto the trimmed ContactSummary."""
    names = person.get("names") or []
    primary_name = names[0] if names else {}
    return ContactSummary(
        resource_name=person.get("resourceName"),
        etag=person.get("etag"),
        display_name=primary_name.get("displayName"),
        given_name=primary_name.get("givenName"),
        family_name=primary_name.get("familyName"),
        middle_name=primary_name.get("middleName"),
        email_addresses=[
            e.get("value")
            for e in (person.get("emailAddresses") or [])
            if e.get("value")
        ],
        phone_numbers=[
            p.get("value")
            for p in (person.get("phoneNumbers") or [])
            if p.get("value")
        ],
        organizations=person.get("organizations") or [],
        addresses=person.get("addresses") or [],
        biographies=person.get("biographies") or [],
        urls=person.get("urls") or [],
        birthdays=person.get("birthdays") or [],
        genders=person.get("genders") or [],
        raw=person,
    )


def _build_request_body(
    person_fields: list[str],
    *,
    first_name: str | None,
    middle_name: str | None,
    last_name: str | None,
    email: str | None,
    phone_number: str | None,
    street_address: str | None,
    city: str | None,
    state: str | None,
    zip_code: str | None,
    country: str | None,
    biography: str | None,
    birthday: str | None,
    calendar_url: str | None,
    gender: str | None,
    urls: list[str] | None,
    additional_fields: dict[str, Any] | None,
) -> dict[str, Any]:
    """Mirror of pipedream's getRequestBody — assembles a Person body from flat params."""
    body: dict[str, Any] = {}
    if "addresses" in person_fields:
        body["addresses"] = [
            {
                "streetAddress": street_address,
                "city": city,
                "region": state,
                "postalCode": zip_code,
                "country": country,
            }
        ]
    if "emailAddresses" in person_fields and email is not None:
        body["emailAddresses"] = [{"value": email}]
    if "names" in person_fields:
        body["names"] = [
            {
                "familyName": last_name,
                "middleName": middle_name,
                "givenName": first_name,
            }
        ]
    if "phoneNumbers" in person_fields and phone_number is not None:
        body["phoneNumbers"] = [{"value": phone_number}]
    if "biographies" in person_fields and biography is not None:
        body["biographies"] = [{"value": biography}]
    if "birthdays" in person_fields and birthday is not None:
        try:
            year, month, day = birthday.split("-")
            body["birthdays"] = [
                {
                    "date": {
                        "year": int(year),
                        "month": int(month),
                        "day": int(day),
                    }
                }
            ]
        except (ValueError, AttributeError) as exc:
            raise ValueError(
                "Error parsing birthday. Make sure it is a string in the format `YYYY-MM-DD`."
            ) from exc
    if "calendarUrls" in person_fields and calendar_url is not None:
        body["calendarUrls"] = [{"url": calendar_url}]
    if "genders" in person_fields and gender is not None:
        body["genders"] = [{"value": gender}]
    if "urls" in person_fields and urls is not None:
        body["urls"] = [{"value": v} for v in urls]
    if additional_fields:
        for key, value in additional_fields.items():
            body[key] = value
    return body


def _merge_person_fields(person_fields: list[str], extras: dict[str, Any] | None) -> str:
    """Mirror of pipedream's getPersonFields — return a comma-joined unique field list."""
    merged = list(person_fields)
    if extras:
        for key in extras.keys():
            if key not in merged:
                merged.append(key)
    return ",".join(merged)


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class CreateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data (contains access_token)")
    person_fields: list[str] = Field(
        description=(
            "Contact fields to populate and return — any of: names, emailAddresses, phoneNumbers, "
            "addresses, biographies, birthdays, calendarUrls, genders, urls."
        )
    )
    first_name: str | None = Field(default=None, description="First name.")
    middle_name: str | None = Field(default=None, description="Middle name.")
    last_name: str | None = Field(default=None, description="Last name.")
    email: str | None = Field(default=None, description="Email address.")
    phone_number: str | None = Field(default=None, description="Phone number.")
    street_address: str | None = Field(default=None, description="Street address.")
    city: str | None = Field(default=None, description="City.")
    state: str | None = Field(default=None, description="State / region.")
    zip_code: str | None = Field(default=None, description="Postal / zip code.")
    country: str | None = Field(default=None, description="Country.")
    biography: str | None = Field(default=None, description="Biography text.")
    birthday: str | None = Field(default=None, description="Birthday in YYYY-MM-DD format.")
    calendar_url: str | None = Field(default=None, description="Calendar URL.")
    gender: str | None = Field(default=None, description="Gender: male, female, or unspecified.")
    urls: list[str] | None = Field(default=None, description="List of associated URLs.")
    additional_fields: dict[str, Any] | None = Field(
        default=None,
        description="Extra fields merged into the Person request body.",
    )


class DeleteContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data (contains access_token)")
    resource_name: str = Field(
        description="People API resource name, e.g. 'people/c123456789'.",
    )


class GetContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data (contains access_token)")
    resource_name: str = Field(description="People API resource name, e.g. 'people/c123456789'.")
    fields: list[str] = Field(description="personFields list to fetch.")


class ListContactsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data (contains access_token)")
    fields: list[str] = Field(description="personFields list to fetch for every result.")
    max_pages: int = Field(default=50, description="Maximum number of pages to fetch (1-500). Prevents runaway pagination.")


class ListDirectoryContactsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data (contains access_token)")
    fields: list[str] = Field(description="readMask fields to return.")
    source: str = Field(
        description=(
            "Directory source: 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT' or "
            "'DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE'."
        )
    )
    merge_sources: list[str] | None = Field(
        default=None,
        description=(
            "Optional. Additional merge sources: 'DIRECTORY_MERGE_SOURCE_TYPE_UNSPECIFIED' or "
            "'DIRECTORY_MERGE_SOURCE_TYPE_CONTACT'."
        ),
    )
    page_size: int = Field(default=100, description="Page size 1-1000.")
    page_token: str | None = Field(default=None, description="Page token from a previous response.")
    request_sync_token: bool = Field(
        default=False, description="Whether the response should include a nextSyncToken."
    )
    sync_token: str | None = Field(
        default=None,
        description="Sync token from a previous response — incremental sync.",
    )


class UpdateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data (contains access_token)")
    resource_name: str = Field(description="People API resource name to update.")
    update_person_fields: list[str] = Field(
        description=(
            "Sections to update — any of: names, emailAddresses, phoneNumbers, addresses, "
            "biographies, birthdays, calendarUrls, genders, urls."
        )
    )
    first_name: str | None = Field(default=None, description="Updated first name.")
    middle_name: str | None = Field(default=None, description="Updated middle name.")
    last_name: str | None = Field(default=None, description="Updated last name.")
    email: str | None = Field(default=None, description="Updated email.")
    phone_number: str | None = Field(default=None, description="Updated phone number.")
    street_address: str | None = Field(default=None, description="Updated street address.")
    city: str | None = Field(default=None, description="Updated city.")
    state: str | None = Field(default=None, description="Updated state.")
    zip_code: str | None = Field(default=None, description="Updated zip code.")
    country: str | None = Field(default=None, description="Updated country.")
    biography: str | None = Field(default=None, description="Updated biography.")
    birthday: str | None = Field(default=None, description="Updated birthday YYYY-MM-DD.")
    calendar_url: str | None = Field(default=None, description="Updated calendar URL.")
    gender: str | None = Field(default=None, description="Updated gender.")
    urls: list[str] | None = Field(default=None, description="Updated list of URLs.")
    additional_fields: dict[str, Any] | None = Field(
        default=None,
        description="Extra fields merged into the Person request body.",
    )


# ---------------------------------------------------------------------------
# @tool functions
# ---------------------------------------------------------------------------


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    person_fields: list[str],
    first_name: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone_number: str | None = None,
    street_address: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    country: str | None = None,
    biography: str | None = None,
    birthday: str | None = None,
    calendar_url: str | None = None,
    gender: str | None = None,
    urls: list[str] | None = None,
    additional_fields: dict[str, Any] | None = None,
) -> CreateContactOutput:
    """Create a new contact in the authenticated user's Google Contacts."""
    headers = _get_auth_headers(auth_type, auth_data)
    body = _build_request_body(
        person_fields,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        street_address=street_address,
        city=city,
        state=state,
        zip_code=zip_code,
        country=country,
        biography=biography,
        birthday=birthday,
        calendar_url=calendar_url,
        gender=gender,
        urls=urls,
        additional_fields=additional_fields,
    )
    params = {"personFields": _merge_person_fields(person_fields, additional_fields)}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/people:createContact",
            headers=headers,
            params=params,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return CreateContactOutput(success=True, contact=_person_to_summary(data))


@tool(args_schema=DeleteContactInput)
@serialize_pydantic_return
async def delete_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    resource_name: str,
) -> DeleteContactOutput:
    """Delete a contact by its People API resource name."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{_BASE_URL}/{resource_name}:deleteContact",
            headers=headers,
        )
        response.raise_for_status()
    return DeleteContactOutput(success=True, resource_name=resource_name)


@tool(args_schema=GetContactInput)
@serialize_pydantic_return
async def get_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    resource_name: str,
    fields: list[str],
) -> GetContactOutput:
    """Fetch a single contact by its People API resource name."""
    headers = _get_auth_headers(auth_type, auth_data)
    params = {"personFields": ",".join(fields)}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/{resource_name}",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    return GetContactOutput(success=True, contact=_person_to_summary(data))


@tool(args_schema=ListContactsInput)
@serialize_pydantic_return
async def list_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    fields: list[str],
    max_pages: int = 50,
) -> ListContactsOutput:
    """List every contact for the authenticated user (auto-paginates)."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"personFields": ",".join(fields)}
    contacts: list[ContactSummary] = []
    page_token: str | None = None
    pages_seen = 0
    async with httpx.AsyncClient() as client:
        while pages_seen < max_pages:
            pages_seen += 1
            if page_token:
                params["pageToken"] = page_token
            else:
                params.pop("pageToken", None)
            response = await client.get(
                f"{_BASE_URL}/people/me/connections",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            for person in data.get("connections") or []:
                contacts.append(_person_to_summary(person))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
    return ListContactsOutput(success=True, contacts=contacts, total=len(contacts))


@tool(args_schema=ListDirectoryContactsInput)
@serialize_pydantic_return
async def list_directory_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    fields: list[str],
    source: str,
    merge_sources: list[str] | None = None,
    page_size: int = 100,
    page_token: str | None = None,
    request_sync_token: bool = False,
    sync_token: str | None = None,
) -> ListDirectoryContactsOutput:
    """List contacts from the Google Workspace directory (one page per call)."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {
        "readMask": ",".join(fields),
        "sources": source,
        "pageSize": page_size,
    }
    if merge_sources:
        params["mergeSources"] = ",".join(merge_sources)
    if page_token:
        params["pageToken"] = page_token
    if request_sync_token:
        params["requestSyncToken"] = "true"
    if sync_token:
        params["syncToken"] = sync_token
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/people:listDirectoryPeople",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    people = [_person_to_summary(p) for p in (data.get("people") or [])]
    return ListDirectoryContactsOutput(
        success=True,
        people=people,
        next_page_token=data.get("nextPageToken"),
        next_sync_token=data.get("nextSyncToken"),
        total=len(people),
    )


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    resource_name: str,
    update_person_fields: list[str],
    first_name: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone_number: str | None = None,
    street_address: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    country: str | None = None,
    biography: str | None = None,
    birthday: str | None = None,
    calendar_url: str | None = None,
    gender: str | None = None,
    urls: list[str] | None = None,
    additional_fields: dict[str, Any] | None = None,
) -> UpdateContactOutput:
    """Update an existing contact (fetches the latest etag first)."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        # Fetch latest etag — Google rejects updates with stale etags.
        etag_resp = await client.get(
            f"{_BASE_URL}/{resource_name}",
            headers=headers,
            params={"personFields": "names"},
        )
        etag_resp.raise_for_status()
        etag = etag_resp.json().get("etag")

        body = _build_request_body(
            update_person_fields,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zip_code,
            country=country,
            biography=biography,
            birthday=birthday,
            calendar_url=calendar_url,
            gender=gender,
            urls=urls,
            additional_fields=additional_fields,
        )
        body["etag"] = etag

        params = {
            "updatePersonFields": _merge_person_fields(
                update_person_fields, additional_fields
            ),
        }
        update_resp = await client.patch(
            f"{_BASE_URL}/{resource_name}:updateContact",
            headers=headers,
            params=params,
            json=body,
        )
        update_resp.raise_for_status()
        data = update_resp.json()
    return UpdateContactOutput(success=True, contact=_person_to_summary(data))
