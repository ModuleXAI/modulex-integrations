"""PostGrid LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.postgrid.outputs import (
    ContactResource,
    CreateContactOutput,
    CreateLetterOutput,
    CreatePostcardOutput,
    LetterResource,
    PostcardResource,
)

__all__ = [
    "create_contact",
    "create_letter",
    "create_postcard",
]

_BASE_URL = "https://api.postgrid.com/print-mail/v1"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class CreateContactInput(BaseModel):
    first_name: str = Field(description="The first name of the contact")
    address_line1: str = Field(description="The contact's first address line")
    api_key: str = Field(description="PostGrid API key")
    last_name: str | None = Field(default=None, description="The last name of the contact")
    company_name: str | None = Field(default=None, description="The contact's company name")
    address_line2: str | None = Field(default=None, description="The contact's second address line")
    city: str | None = Field(default=None, description="The contact's city")
    province_or_state: str | None = Field(default=None, description="The province or state of the contact")
    email: str | None = Field(default=None, description="The contact's email address")
    phone_number: str | None = Field(default=None, description="The contact's phone number")
    job_title: str | None = Field(default=None, description="The contact's job title")
    postal_or_zip: str | None = Field(default=None, description="The postal code or ZIP code of the contact")
    country_code: str = Field(default="CA", description="ISO 3166-1 country code. Defaults to CA")
    description: str | None = Field(default=None, description="A description for the contact")
    skip_verification: bool | None = Field(default=None, description="If true, skip address verification")


class CreateLetterInput(BaseModel):
    to: str = Field(description="The ID or contact object of the receiver")
    from_contact: str = Field(description="The ID or contact object of the sender")
    html: str = Field(description="The HTML content of the letter")
    api_key: str = Field(description="PostGrid API key")
    address_placement: str | None = Field(default=None, description="Address placement. One of: top_first_page, insert_blank_page")
    double_sided: bool | None = Field(default=None, description="Whether the letter is double sided")
    color: bool | None = Field(default=None, description="Whether the letter will be printed in color")
    perforated_page: int | None = Field(default=None, description="Page number to be perforated")
    extra_service: str | None = Field(default=None, description="Extra services. One of: certified, certified_return_receipt, registered")
    envelope_type: str | None = Field(default=None, description="Envelope type. One of: standard_double_window, flat")
    return_envelope: str | None = Field(default=None, description="The ID of the return envelope")
    send_date: str | None = Field(default=None, description="Desired send date in ISO 8601 format")
    description: str | None = Field(default=None, description="A description for the letter")
    express: bool | None = Field(default=None, description="Whether to use express shipping")
    mailing_class: str | None = Field(default=None, description="Mailing class. One of: standard_class, first_class")
    size: str | None = Field(default=None, description="Letter size. One of: us_letter, us_legal, a4")


class CreatePostcardInput(BaseModel):
    to: str = Field(description="The ID or contact object of the receiver")
    from_contact: str = Field(description="The ID or contact object of the sender")
    front_html: str = Field(description="The HTML content for the front of the postcard")
    back_html: str = Field(description="The HTML content for the back of the postcard")
    size: str = Field(description="Postcard size. One of: 6x4, 9x6, 11x6")
    api_key: str = Field(description="PostGrid API key")
    send_date: str | None = Field(default=None, description="Desired send date in ISO 8601 format")
    express: bool | None = Field(default=None, description="Whether to use express shipping")
    description: str | None = Field(default=None, description="A description for the postcard")
    mailing_class: str | None = Field(default=None, description="Mailing class. One of: standard_class, first_class")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    first_name: str,
    address_line1: str,
    api_key: str,
    last_name: str | None = None,
    company_name: str | None = None,
    address_line2: str | None = None,
    city: str | None = None,
    province_or_state: str | None = None,
    email: str | None = None,
    phone_number: str | None = None,
    job_title: str | None = None,
    postal_or_zip: str | None = None,
    country_code: str = "CA",
    description: str | None = None,
    skip_verification: bool | None = None,
) -> CreateContactOutput:
    """Create a new contact in PostGrid."""
    if not api_key or not api_key.strip():
        return CreateContactOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {
        "firstName": first_name,
        "addressLine1": address_line1,
    }
    if last_name is not None:
        body["lastName"] = last_name
    if company_name is not None:
        body["companyName"] = company_name
    if address_line2 is not None:
        body["addressLine2"] = address_line2
    if city is not None:
        body["city"] = city
    if province_or_state is not None:
        body["provinceOrState"] = province_or_state
    if email is not None:
        body["email"] = email
    if phone_number is not None:
        body["phoneNumber"] = phone_number
    if job_title is not None:
        body["jobTitle"] = job_title
    if postal_or_zip is not None:
        body["postalOrZip"] = postal_or_zip
    if country_code != "CA":
        body["countryCode"] = country_code
    else:
        body["countryCode"] = country_code
    if description is not None:
        body["description"] = description
    if skip_verification is not None:
        body["skipVerification"] = skip_verification

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/contacts",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateContactOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContactOutput(success=False, error=f"Call failed: {exc}")

    return CreateContactOutput(
        success=True,
        contact=ContactResource(
            id=data.get("id"),
            object=data.get("object"),
            live=data.get("live"),
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            company_name=data.get("companyName"),
            address_line1=data.get("addressLine1"),
            address_line2=data.get("addressLine2"),
            city=data.get("city"),
            province_or_state=data.get("provinceOrState"),
            postal_or_zip=data.get("postalOrZip"),
            country=data.get("country"),
            country_code=data.get("countryCode"),
            email=data.get("email"),
            phone_number=data.get("phoneNumber"),
            job_title=data.get("jobTitle"),
            description=data.get("description"),
            address_status=data.get("addressStatus"),
        ),
    )


@tool(args_schema=CreateLetterInput)
@serialize_pydantic_return
async def create_letter(
    to: str,
    from_contact: str,
    html: str,
    api_key: str,
    address_placement: str | None = None,
    double_sided: bool | None = None,
    color: bool | None = None,
    perforated_page: int | None = None,
    extra_service: str | None = None,
    envelope_type: str | None = None,
    return_envelope: str | None = None,
    send_date: str | None = None,
    description: str | None = None,
    express: bool | None = None,
    mailing_class: str | None = None,
    size: str | None = None,
) -> CreateLetterOutput:
    """Create a new letter in PostGrid."""
    if not api_key or not api_key.strip():
        return CreateLetterOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {
        "to": to,
        "from": from_contact,
        "html": html,
    }
    if address_placement is not None:
        body["addressPlacement"] = address_placement
    if double_sided is not None:
        body["doubleSided"] = double_sided
    if color is not None:
        body["color"] = color
    if perforated_page is not None:
        body["perforatedPage"] = perforated_page
    if extra_service is not None:
        body["extraService"] = extra_service
    if envelope_type is not None:
        body["envelopeType"] = envelope_type
    if return_envelope is not None:
        body["returnEnvelope"] = return_envelope
    if send_date is not None:
        body["sendDate"] = send_date
    if description is not None:
        body["description"] = description
    if express is not None:
        body["express"] = express
    if mailing_class is not None:
        body["mailingClass"] = mailing_class
    if size is not None:
        body["size"] = size

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/letters",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateLetterOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateLetterOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateLetterOutput(success=False, error=f"Call failed: {exc}")

    return CreateLetterOutput(
        success=True,
        letter=LetterResource(
            id=data.get("id"),
            object=data.get("object"),
            live=data.get("live"),
            send_date=data.get("sendDate"),
            status=data.get("status"),
            url=data.get("url"),
        ),
    )


@tool(args_schema=CreatePostcardInput)
@serialize_pydantic_return
async def create_postcard(
    to: str,
    from_contact: str,
    front_html: str,
    back_html: str,
    size: str,
    api_key: str,
    send_date: str | None = None,
    express: bool | None = None,
    description: str | None = None,
    mailing_class: str | None = None,
) -> CreatePostcardOutput:
    """Create a new postcard in PostGrid."""
    if not api_key or not api_key.strip():
        return CreatePostcardOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {
        "to": to,
        "from": from_contact,
        "frontHTML": front_html,
        "backHTML": back_html,
        "size": size,
    }
    if send_date is not None:
        body["sendDate"] = send_date
    if express is not None:
        body["express"] = express
    if description is not None:
        body["description"] = description
    if mailing_class is not None:
        body["mailingClass"] = mailing_class

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/postcards",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreatePostcardOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreatePostcardOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreatePostcardOutput(success=False, error=f"Call failed: {exc}")

    return CreatePostcardOutput(
        success=True,
        postcard=PostcardResource(
            id=data.get("id"),
            object=data.get("object"),
            live=data.get("live"),
            send_date=data.get("sendDate"),
            status=data.get("status"),
            size=data.get("size"),
            url=data.get("url"),
        ),
    )
