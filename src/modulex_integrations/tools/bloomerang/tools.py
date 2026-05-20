"""Bloomerang LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.bloomerang.outputs import (
    AddInteractionOutput,
    CreateConstituentOutput,
    CreateDonationOutput,
)

__all__ = [
    "add_interaction",
    "create_constituent",
    "create_donation",
]

_BASE_URL = "https://api.bloomerang.co/v2"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class CreateConstituentInput(BaseModel):
    api_key: str = Field(description="Bloomerang API key")
    type: str = Field(description="Constituent type. Valid values: Individual, Organization")
    first_name: str | None = Field(default=None, description="First name (used when type is Individual)")
    last_name: str | None = Field(default=None, description="Last name (used when type is Individual)")
    full_name: str | None = Field(default=None, description="Organization name (used when type is Organization)")
    status: str | None = Field(default=None, description="Status. Valid values: Active, Inactive, Deceased")
    middle_name: str | None = Field(default=None, description="Middle name")
    prefix: str | None = Field(default=None, description="Prefix/title (e.g. Mr., Mrs., Dr.)")
    suffix: str | None = Field(default=None, description="Suffix (e.g. Jr., Sr., Ph.D.)")
    job_title: str | None = Field(default=None, description="Job title")
    gender: str | None = Field(default=None, description="Gender. Valid values: Male, Female, Other")
    birthdate: str | None = Field(default=None, description="Birth date (ISO format YYYY-MM-DD)")
    employer: str | None = Field(default=None, description="Employer")
    website: str | None = Field(default=None, description="Website URL")
    facebook_id: str | None = Field(default=None, description="Facebook page URL")
    twitter_id: str | None = Field(default=None, description="Twitter/X handle")
    linked_in_id: str | None = Field(default=None, description="LinkedIn page URL")
    preferred_communication_channel: str | None = Field(default=None, description="Preferred communication channel. Valid values: Email, Phone, Text Message, Mail")


class CreateDonationInput(BaseModel):
    api_key: str = Field(description="Bloomerang API key")
    constituent_id: str = Field(description="ID of the constituent (donor)")
    date: str = Field(description="Date of the donation (ISO format YYYY-MM-DD)")
    amount: str = Field(description="Donation amount as a numeric string")
    fund_id: str = Field(description="ID of the fund for the donation")
    payment_method: str = Field(description="Payment method. Valid values: None, Cash, Check, CreditCard, Eft, InKind, ApplePay, GooglePay, PayPal, Venmo")
    campaign_id: str | None = Field(default=None, description="ID of the campaign")
    appeal_id: str | None = Field(default=None, description="ID of the appeal")
    note: str | None = Field(default=None, description="Note for the donation")


class AddInteractionInput(BaseModel):
    api_key: str = Field(description="Bloomerang API key")
    constituent_id: str = Field(description="ID of the constituent")
    date: str = Field(description="Date of the interaction (ISO format YYYY-MM-DD)")
    subject: str = Field(description="Subject of the interaction")
    channel: str = Field(description="Channel. Valid values: Email, InPerson, Mail, MassEmail, Other, Phone, SocialMedia, TextMessage, VideoCall, Webinar, Website")
    purpose: str = Field(description="Purpose. Valid values: Acknowledgement, ImpactCultivation, Newsletter, Receipt, Solicitation, SpecialEvent, VolunteerActivity, PledgeReminder, Welcome, Other")
    note: str | None = Field(default=None, description="Note for the interaction")
    is_inbound: bool | None = Field(default=None, description="Whether the interaction was initiated by the constituent")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateConstituentInput)
@serialize_pydantic_return
async def create_constituent(
    api_key: str,
    type: str,
    first_name: str | None = None,
    last_name: str | None = None,
    full_name: str | None = None,
    status: str | None = None,
    middle_name: str | None = None,
    prefix: str | None = None,
    suffix: str | None = None,
    job_title: str | None = None,
    gender: str | None = None,
    birthdate: str | None = None,
    employer: str | None = None,
    website: str | None = None,
    facebook_id: str | None = None,
    twitter_id: str | None = None,
    linked_in_id: str | None = None,
    preferred_communication_channel: str | None = None,
) -> CreateConstituentOutput:
    """Creates a new constituent in Bloomerang"""
    if not api_key or not api_key.strip():
        return CreateConstituentOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"Type": type}
    if first_name is not None:
        body["FirstName"] = first_name
    if last_name is not None:
        body["LastName"] = last_name
    if full_name is not None:
        body["FullName"] = full_name
    if status is not None:
        body["Status"] = status
    if middle_name is not None:
        body["MiddleName"] = middle_name
    if prefix is not None:
        body["Prefix"] = prefix
    if suffix is not None:
        body["Suffix"] = suffix
    if job_title is not None:
        body["JobTitle"] = job_title
    if gender is not None:
        body["Gender"] = gender
    if birthdate is not None:
        body["Birthdate"] = birthdate
    if employer is not None:
        body["Employer"] = employer
    if website is not None:
        body["Website"] = website
    if facebook_id is not None:
        body["FacebookId"] = facebook_id
    if twitter_id is not None:
        body["TwitterId"] = twitter_id
    if linked_in_id is not None:
        body["LinkedInId"] = linked_in_id
    if preferred_communication_channel is not None:
        body["PreferredCommunicationChannel"] = preferred_communication_channel

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/constituent",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateConstituentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateConstituentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateConstituentOutput(success=False, error=f"Call failed: {exc}")

    return CreateConstituentOutput(
        success=True,
        id=data.get("Id"),
        first_name=data.get("FirstName"),
        last_name=data.get("LastName"),
        full_name=data.get("FullName"),
        type=data.get("Type"),
    )


@tool(args_schema=CreateDonationInput)
@serialize_pydantic_return
async def create_donation(
    api_key: str,
    constituent_id: str,
    date: str,
    amount: str,
    fund_id: str,
    payment_method: str,
    campaign_id: str | None = None,
    appeal_id: str | None = None,
    note: str | None = None,
) -> CreateDonationOutput:
    """Creates a new donation record in Bloomerang"""
    if not api_key or not api_key.strip():
        return CreateDonationOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    designation: dict[str, Any] = {
        "Type": "Donation",
        "Amount": float(amount),
        "Fund": {"Id": int(fund_id)},
    }
    if campaign_id is not None:
        designation["Campaign"] = {"Id": int(campaign_id)}
    if appeal_id is not None:
        designation["Appeal"] = {"Id": int(appeal_id)}

    body: dict[str, Any] = {
        "AccountId": int(constituent_id),
        "Date": date,
        "Method": payment_method,
        "Designations": [designation],
    }
    if note is not None:
        body["Note"] = note

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/transaction",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateDonationOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDonationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDonationOutput(success=False, error=f"Call failed: {exc}")

    return CreateDonationOutput(
        success=True,
        id=data.get("Id"),
        amount=data.get("Amount"),
        date=data.get("Date"),
    )


@tool(args_schema=AddInteractionInput)
@serialize_pydantic_return
async def add_interaction(
    api_key: str,
    constituent_id: str,
    date: str,
    subject: str,
    channel: str,
    purpose: str,
    note: str | None = None,
    is_inbound: bool | None = None,
) -> AddInteractionOutput:
    """Adds an interaction to an existing constituent in Bloomerang"""
    if not api_key or not api_key.strip():
        return AddInteractionOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {
        "AccountId": int(constituent_id),
        "Date": date,
        "Subject": subject,
        "Channel": channel,
        "Purpose": purpose,
    }
    if note is not None:
        body["Note"] = note
    if is_inbound is not None:
        body["IsInbound"] = is_inbound

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/interaction",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return AddInteractionOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddInteractionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddInteractionOutput(success=False, error=f"Call failed: {exc}")

    return AddInteractionOutput(
        success=True,
        id=data.get("Id"),
        subject=data.get("Subject"),
        channel=data.get("Channel"),
    )
