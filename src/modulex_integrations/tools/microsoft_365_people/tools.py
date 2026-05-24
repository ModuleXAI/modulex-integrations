"""Microsoft 365 People LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_365_people.outputs import (
    ContactFolderOutput,
    ContactOutput,
    CreateContactFolderOutput,
    CreateContactOutput,
    EmailAddress,
    HomeAddress,
    UpdateContactOutput,
)

__all__ = [
    "create_contact",
    "create_contact_folder",
    "update_contact",
]

_BASE_URL = "https://graph.microsoft.com/v1.0"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Microsoft Graph API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _parse_contact(data: dict[str, Any]) -> ContactOutput:
    """Parse a Microsoft Graph contact response into a ContactOutput."""
    email_addresses = [
        EmailAddress(name=e.get("name"), address=e.get("address"))
        for e in (data.get("emailAddresses") or [])
    ]
    home_addr_raw = data.get("homeAddress")
    home_address = (
        HomeAddress(
            street=home_addr_raw.get("street"),
            city=home_addr_raw.get("city"),
            state=home_addr_raw.get("state"),
            postal_code=home_addr_raw.get("postalCode"),
            country_or_region=home_addr_raw.get("countryOrRegion"),
        )
        if home_addr_raw
        else None
    )
    return ContactOutput(
        id=data.get("id"),
        display_name=data.get("displayName"),
        given_name=data.get("givenName"),
        surname=data.get("surname"),
        email_addresses=email_addresses,
        mobile_phone=data.get("mobilePhone"),
        home_phones=data.get("homePhones") or [],
        home_address=home_address,
        created_date_time=data.get("createdDateTime"),
        last_modified_date_time=data.get("lastModifiedDateTime"),
    )


# --- Input schemas --------------------------------------------------------


class CreateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email: str = Field(description="Email address of the contact")
    first_name: str = Field(description="First name of the contact")
    last_name: str | None = Field(default=None, description="Last name of the contact")
    folder_id: str | None = Field(
        default=None,
        description="ID of the contact folder to create the contact in",
    )
    mobile_phone: str | None = Field(default=None, description="Mobile phone number of the contact")
    home_phones: list[str] | None = Field(default=None, description="List of home phone numbers")
    street: str | None = Field(default=None, description="Street address of the contact")
    city: str | None = Field(default=None, description="City of the contact")
    state: str | None = Field(default=None, description="State of the contact")
    postal_code: str | None = Field(default=None, description="Postal code of the contact")
    country_or_region: str | None = Field(default=None, description="Country or region of the contact")


class CreateContactFolderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    display_name: str = Field(description="The display name of the new contact folder")


class UpdateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="ID of the contact to update")
    folder_id: str | None = Field(
        default=None,
        description="ID of the contact folder containing the contact",
    )
    email: str | None = Field(default=None, description="New email address for the contact")
    first_name: str | None = Field(default=None, description="New first name for the contact")
    last_name: str | None = Field(default=None, description="New last name for the contact")
    mobile_phone: str | None = Field(default=None, description="New mobile phone number for the contact")
    home_phones: list[str] | None = Field(default=None, description="New list of home phone numbers")
    street: str | None = Field(default=None, description="New street address for the contact")
    city: str | None = Field(default=None, description="New city for the contact")
    state: str | None = Field(default=None, description="New state for the contact")
    postal_code: str | None = Field(default=None, description="New postal code for the contact")
    country_or_region: str | None = Field(default=None, description="New country or region for the contact")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    email: str,
    first_name: str,
    last_name: str | None = None,
    folder_id: str | None = None,
    mobile_phone: str | None = None,
    home_phones: list[str] | None = None,
    street: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country_or_region: str | None = None,
) -> CreateContactOutput:
    """Create a new contact in Microsoft 365 People."""
    headers = _get_auth_headers(auth_type, auth_data)

    body: dict[str, Any] = {
        "givenName": first_name,
        "emailAddresses": [{"address": email, "name": email}],
    }
    if last_name is not None:
        body["surname"] = last_name
    if mobile_phone is not None:
        body["mobilePhone"] = mobile_phone
    if home_phones is not None:
        body["homePhones"] = home_phones
    if street or city or state or postal_code or country_or_region:
        body["homeAddress"] = {}
        if street is not None:
            body["homeAddress"]["street"] = street
        if city is not None:
            body["homeAddress"]["city"] = city
        if state is not None:
            body["homeAddress"]["state"] = state
        if postal_code is not None:
            body["homeAddress"]["postalCode"] = postal_code
        if country_or_region is not None:
            body["homeAddress"]["countryOrRegion"] = country_or_region

    url = (
        f"{_BASE_URL}/me/contactFolders/{folder_id}/contacts"
        if folder_id
        else f"{_BASE_URL}/me/contacts"
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

    return CreateContactOutput(success=True, contact=_parse_contact(data))


@tool(args_schema=CreateContactFolderInput)
@serialize_pydantic_return
async def create_contact_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    display_name: str,
) -> CreateContactFolderOutput:
    """Create a new contact folder in Microsoft 365 People."""
    headers = _get_auth_headers(auth_type, auth_data)

    body = {"displayName": display_name}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/me/contactFolders",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()

    return CreateContactFolderOutput(
        success=True,
        folder=ContactFolderOutput(
            id=data.get("id"),
            display_name=data.get("displayName"),
            parent_folder_id=data.get("parentFolderId"),
        ),
    )


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    folder_id: str | None = None,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    mobile_phone: str | None = None,
    home_phones: list[str] | None = None,
    street: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country_or_region: str | None = None,
) -> UpdateContactOutput:
    """Update an existing contact in Microsoft 365 People."""
    headers = _get_auth_headers(auth_type, auth_data)

    body: dict[str, Any] = {}
    if email is not None:
        body["emailAddresses"] = [{"address": email, "name": email}]
    if first_name is not None:
        body["givenName"] = first_name
    if last_name is not None:
        body["surname"] = last_name
    if mobile_phone is not None:
        body["mobilePhone"] = mobile_phone
    if home_phones is not None:
        body["homePhones"] = home_phones
    if street or city or state or postal_code or country_or_region:
        body["homeAddress"] = {}
        if street is not None:
            body["homeAddress"]["street"] = street
        if city is not None:
            body["homeAddress"]["city"] = city
        if state is not None:
            body["homeAddress"]["state"] = state
        if postal_code is not None:
            body["homeAddress"]["postalCode"] = postal_code
        if country_or_region is not None:
            body["homeAddress"]["countryOrRegion"] = country_or_region

    url = (
        f"{_BASE_URL}/me/contactFolders/{folder_id}/contacts/{contact_id}"
        if folder_id
        else f"{_BASE_URL}/me/contacts/{contact_id}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.patch(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

    return UpdateContactOutput(success=True, contact=_parse_contact(data))
