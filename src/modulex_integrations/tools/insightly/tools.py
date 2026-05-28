"""Insightly LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.insightly.outputs import (
    CreateContactOutput,
    CreateTaskOutput,
)

__all__ = [
    "create_contact",
    "create_task",
]


def _base_url(pod: str) -> str:
    return f"https://api.{pod}.insightly.com/v3.1"


# --- Input schemas --------------------------------------------------------


class CreateContactInput(BaseModel):
    first_name: str = Field(description="The first name of the contact")
    last_name: str = Field(description="The last name of the contact")
    email: str = Field(description="The email address of the contact")
    pod: str = Field(description="Insightly pod/region identifier (e.g. na1, au1)")
    api_key: str = Field(description="Insightly API key")
    title: str | None = Field(default=None, description="The title of the contact")
    phone: str | None = Field(default=None, description="The phone number of the contact")
    address_street: str | None = Field(default=None, description="The street address of the contact")
    address_city: str | None = Field(default=None, description="The city of the contact")
    address_state: str | None = Field(default=None, description="The state of the contact")
    address_postcode: str | None = Field(default=None, description="The zip code/postcode of the contact")
    address_country: str | None = Field(default=None, description="The country of the contact")


class CreateTaskInput(BaseModel):
    title: str = Field(description="The title of the task")
    status: str = Field(description="The status of the task. Allowed values: Not Started, In Progress, Completed, Deferred, Waiting")
    due_date: str = Field(description="The due date of the task in YYYY-MM-DD format (e.g. 2023-08-20)")
    pod: str = Field(description="Insightly pod/region identifier (e.g. na1, au1)")
    api_key: str = Field(description="Insightly API key")
    category_id: str | None = Field(default=None, description="Identifier of a task category")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    first_name: str,
    last_name: str,
    email: str,
    pod: str,
    api_key: str,
    title: str | None = None,
    phone: str | None = None,
    address_street: str | None = None,
    address_city: str | None = None,
    address_state: str | None = None,
    address_postcode: str | None = None,
    address_country: str | None = None,
) -> CreateContactOutput:
    """Creates a new contact in Insightly"""
    if not api_key or not api_key.strip():
        return CreateContactOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not pod or not pod.strip():
        return CreateContactOutput(
            success=False,
            error="Pod identifier is empty. Please configure your Insightly pod.",
        )

    body: dict[str, Any] = {
        "FIRST_NAME": first_name,
        "LAST_NAME": last_name,
        "CONTACTINFOS": [
            {
                "TYPE": "EMAIL",
                "LABEL": "Work",
                "DETAIL": email,
            },
        ],
    }
    if title:
        body["TITLE"] = title
    if phone:
        body["CONTACTINFOS"].append(
            {
                "TYPE": "PHONE",
                "LABEL": "Work",
                "DETAIL": phone,
            },
        )
    if any([address_street, address_city, address_state, address_postcode, address_country]):
        body["ADDRESSES"] = [
            {
                "ADDRESS_TYPE": "Work",
                "STREET": address_street or "",
                "CITY": address_city or "",
                "STATE": address_state or "",
                "POSTCODE": address_postcode or "",
                "COUNTRY": address_country or "",
            },
        ]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_base_url(pod)}/Contacts",
                auth=(api_key, ""),
                headers={"Content-Type": "application/json"},
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
        contact_id=data.get("CONTACT_ID"),
        first_name=data.get("FIRST_NAME"),
        last_name=data.get("LAST_NAME"),
        email_address=email,
        title=data.get("TITLE"),
        phone=phone,
    )


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    title: str,
    status: str,
    due_date: str,
    pod: str,
    api_key: str,
    category_id: str | None = None,
) -> CreateTaskOutput:
    """Creates a new task in Insightly"""
    if not api_key or not api_key.strip():
        return CreateTaskOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not pod or not pod.strip():
        return CreateTaskOutput(
            success=False,
            error="Pod identifier is empty. Please configure your Insightly pod.",
        )

    body: dict[str, Any] = {
        "TITLE": title,
        "STATUS": status,
        "DUE_DATE": due_date,
    }
    if category_id:
        body["CATEGORY_ID"] = int(category_id)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_base_url(pod)}/Tasks",
                auth=(api_key, ""),
                headers={"Content-Type": "application/json"},
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateTaskOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTaskOutput(success=False, error=f"Call failed: {exc}")

    return CreateTaskOutput(
        success=True,
        task_id=data.get("TASK_ID"),
        title=data.get("TITLE"),
        status=data.get("STATUS"),
        due_date=data.get("DUE_DATE"),
        category_id=data.get("CATEGORY_ID"),
    )
