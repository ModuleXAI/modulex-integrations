"""Cogmento LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.cogmento.outputs import (
    CreateContactOutput,
    CreateDealOutput,
    CreateTaskOutput,
    ListUserIdsOptionsOutput,
    UserOption,
)

__all__ = [
    "create_contact",
    "create_deal",
    "create_task",
    "list_user_ids_options",
]

_BASE_URL = "https://api.cogmento.com/api/1"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Cogmento API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Token {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class CreateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    first_name: str = Field(description="First name of the contact")
    last_name: str = Field(description="Last name of the contact")
    email: str | None = Field(default=None, description="Email address of the contact")
    phone: str | None = Field(default=None, description="Phone number of the contact")
    description: str | None = Field(default=None, description="Description of the contact")
    tags: list[str] | None = Field(default=None, description="List of tags associated with the contact")
    do_not_call: bool | None = Field(default=None, description="Set to true to mark as Do Not Call")
    do_not_text: bool | None = Field(default=None, description="Set to true to mark as Do Not Text")
    do_not_email: bool | None = Field(default=None, description="Set to true to mark as Do Not Email")


class CreateDealInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="The title of the deal")
    description: str | None = Field(default=None, description="A description of the deal")
    assignee_ids: list[str] | None = Field(default=None, description="List of user IDs to assign to the deal")
    tags: list[str] | None = Field(default=None, description="List of tags associated with the deal")
    close_date: str | None = Field(default=None, description="The date the deal was completed (YYYY-MM-DD)")
    product_ids: list[str] | None = Field(default=None, description="List of product IDs to include in the deal")
    amount: str | None = Field(default=None, description="The final deal value (numeric string)")


class CreateTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="The title of the task")
    description: str | None = Field(default=None, description="A description of the task")
    due_date: str | None = Field(default=None, description="The task's deadline (YYYY-MM-DD)")
    assignee_ids: list[str] | None = Field(default=None, description="List of user IDs to assign to the task")
    deal_id: str | None = Field(default=None, description="Identifier of a deal to associate with the task")
    contact_id: str | None = Field(default=None, description="Identifier of a contact to associate with the task")


class ListUserIdsOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    first_name: str,
    last_name: str,
    email: str | None = None,
    phone: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    do_not_call: bool | None = None,
    do_not_text: bool | None = None,
    do_not_email: bool | None = None,
) -> CreateContactOutput:
    """Create a new contact in Cogmento CRM"""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return CreateContactOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    payload: dict[str, Any] = {
        "first_name": first_name,
        "last_name": last_name,
    }

    channels: list[dict[str, str]] = []
    if email:
        channels.append({"channel_type": "email", "value": email})
    if phone:
        channels.append({"channel_type": "phone", "value": phone})
    if channels:
        payload["channels"] = channels

    if description is not None:
        payload["description"] = description
    if tags is not None:
        payload["tags"] = tags
    if do_not_call is not None:
        payload["do_not_call"] = do_not_call
    if do_not_text is not None:
        payload["do_not_text"] = do_not_text
    if do_not_email is not None:
        payload["do_not_email"] = do_not_email

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/contacts/",
                headers=headers,
                json=payload,
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

    return CreateContactOutput(success=True, contact=data)


@tool(args_schema=CreateDealInput)
@serialize_pydantic_return
async def create_deal(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    description: str | None = None,
    assignee_ids: list[str] | None = None,
    tags: list[str] | None = None,
    close_date: str | None = None,
    product_ids: list[str] | None = None,
    amount: str | None = None,
) -> CreateDealOutput:
    """Create a new deal in Cogmento CRM"""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return CreateDealOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    payload: dict[str, Any] = {"title": title}

    if description is not None:
        payload["description"] = description
    if assignee_ids is not None:
        payload["assigned_to"] = [{"id": uid} for uid in assignee_ids]
    if tags is not None:
        payload["tags"] = tags
    if close_date is not None:
        payload["close_date"] = close_date
    if product_ids is not None:
        payload["products"] = [{"id": pid} for pid in product_ids]
    if amount is not None:
        payload["amount"] = float(amount)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/deals/",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return CreateDealOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDealOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDealOutput(success=False, error=f"Call failed: {exc}")

    return CreateDealOutput(success=True, deal=data)


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    description: str | None = None,
    due_date: str | None = None,
    assignee_ids: list[str] | None = None,
    deal_id: str | None = None,
    contact_id: str | None = None,
) -> CreateTaskOutput:
    """Create a new task in Cogmento CRM"""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return CreateTaskOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    payload: dict[str, Any] = {"title": title}

    if description is not None:
        payload["description"] = description
    if due_date is not None:
        payload["due_date"] = due_date
    if assignee_ids is not None:
        payload["assigned_to"] = [{"id": uid} for uid in assignee_ids]
    if deal_id is not None:
        payload["deal"] = {"id": deal_id}
    if contact_id is not None:
        payload["contact"] = {"id": contact_id}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/tasks/",
                headers=headers,
                json=payload,
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

    return CreateTaskOutput(success=True, task=data)


@tool(args_schema=ListUserIdsOptionsInput)
@serialize_pydantic_return
async def list_user_ids_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListUserIdsOptionsOutput:
    """Retrieve available user options for assignment fields"""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ListUserIdsOptionsOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/auth/user",
                headers=headers,
            )
        if response.status_code != 200:
            return ListUserIdsOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListUserIdsOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListUserIdsOptionsOutput(success=False, error=f"Call failed: {exc}")

    users_list = data if isinstance(data, list) else [data]
    users = [
        UserOption(
            label=u.get("name") or u.get("email", ""),
            value=str(u.get("id", "")),
        )
        for u in users_list
    ]

    return ListUserIdsOptionsOutput(success=True, users=users)
