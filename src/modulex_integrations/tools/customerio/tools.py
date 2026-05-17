"""Customer.io LangChain ``@tool`` functions.

Customer.io uses HTTP Basic Auth with ``site_id:api_key``. The modulex
``ToolExecutor`` injects both credentials per-tool (the function
signature takes both as named parameters), and we build the auth
header here. This is a wider injection contract than the single-
``api_key`` pattern used by exa/tavily.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.customerio.outputs import (
    AddCustomersToSegmentOutput,
    CreateOrUpdateCustomerOutput,
    SendEventOutput,
)

__all__ = [
    "add_customers_to_segment",
    "create_or_update_customer",
    "send_event",
]

_BASE_URL = "https://track.customer.io/api/v1"
_ID_TYPES = ("id", "email", "cio_id")


def _headers(site_id: str, api_key: str) -> dict[str, str]:
    """Build Basic-Auth headers for Customer.io."""
    encoded = base64.b64encode(f"{site_id}:{api_key}".encode()).decode()
    return {"Content-Type": "application/json", "Authorization": f"Basic {encoded}"}


def _missing_creds_error() -> str:
    return "Customer.io credentials (site_id and api_key) are required"


class CreateOrUpdateCustomerInput(BaseModel):
    customer_id: str = Field(description="The unique identifier for the customer")
    email: str = Field(description="The customer's email address")
    site_id: str = Field(description="Customer.io Site ID (provided by credential system)")
    api_key: str = Field(description="Customer.io API Key (provided by credential system)")
    created_at: int | None = Field(default=None, description="UNIX timestamp")
    attributes: dict[str, Any] | None = Field(
        default=None, description="Custom attributes (name, plan, etc.)"
    )


class SendEventInput(BaseModel):
    customer_id: str = Field(description="The unique identifier for the customer")
    event_name: str = Field(description="The name of the event to track")
    site_id: str = Field(description="Customer.io Site ID (provided by credential system)")
    api_key: str = Field(description="Customer.io API Key (provided by credential system)")
    event_type: str | None = Field(default=None, description="'page' for page views")
    data: dict[str, Any] | None = Field(default=None, description="Custom data")


class AddCustomersToSegmentInput(BaseModel):
    segment_id: str = Field(description="Segment ID")
    customer_ids: list[str] = Field(description="Customer IDs to add (max 1000)")
    site_id: str = Field(description="Customer.io Site ID (provided by credential system)")
    api_key: str = Field(description="Customer.io API Key (provided by credential system)")
    id_type: str = Field(default="id", description="'id', 'email', or 'cio_id'")


@tool(args_schema=CreateOrUpdateCustomerInput)
@serialize_pydantic_return
async def create_or_update_customer(
    customer_id: str,
    email: str,
    site_id: str,
    api_key: str,
    created_at: int | None = None,
    attributes: dict[str, Any] | None = None,
) -> CreateOrUpdateCustomerOutput:
    """Create or update a customer in Customer.io."""
    if not site_id or not api_key:
        return CreateOrUpdateCustomerOutput(success=False, error=_missing_creds_error())

    payload: dict[str, Any] = {"email": email}
    if created_at is not None:
        payload["created_at"] = created_at
    if attributes:
        payload.update(attributes)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{_BASE_URL}/customers/{customer_id}",
                headers=_headers(site_id, api_key),
                json=payload,
            )
        if response.status_code != 200:
            return CreateOrUpdateCustomerOutput(
                success=False, error=f"API error: {response.status_code} - {response.text}"
            )
    except Exception as exc:
        return CreateOrUpdateCustomerOutput(
            success=False, error=f"Failed to create/update customer: {exc}"
        )

    return CreateOrUpdateCustomerOutput(
        success=True,
        message="Successfully created/updated customer",
        customer_id=customer_id,
        email=email,
    )


@tool(args_schema=SendEventInput)
@serialize_pydantic_return
async def send_event(
    customer_id: str,
    event_name: str,
    site_id: str,
    api_key: str,
    event_type: str | None = None,
    data: dict[str, Any] | None = None,
) -> SendEventOutput:
    """Send a tracking event to a Customer.io customer."""
    if not site_id or not api_key:
        return SendEventOutput(success=False, error=_missing_creds_error())

    payload: dict[str, Any] = {"name": event_name}
    if event_type:
        payload["type"] = event_type
    if data:
        payload["data"] = data

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{_BASE_URL}/customers/{customer_id}/events",
                headers=_headers(site_id, api_key),
                json=payload,
            )
        if response.status_code != 200:
            return SendEventOutput(
                success=False, error=f"API error: {response.status_code} - {response.text}"
            )
    except Exception as exc:
        return SendEventOutput(success=False, error=f"Failed to send event: {exc}")

    return SendEventOutput(
        success=True,
        message="Successfully sent event",
        customer_id=customer_id,
        event_name=event_name,
    )


@tool(args_schema=AddCustomersToSegmentInput)
@serialize_pydantic_return
async def add_customers_to_segment(
    segment_id: str,
    customer_ids: list[str],
    site_id: str,
    api_key: str,
    id_type: str = "id",
) -> AddCustomersToSegmentOutput:
    """Add customers to a manual segment (max 1000 per request)."""
    if not site_id or not api_key:
        return AddCustomersToSegmentOutput(success=False, error=_missing_creds_error())
    if len(customer_ids) > 1000:
        return AddCustomersToSegmentOutput(
            success=False, error="Maximum 1000 customer IDs per request"
        )
    if id_type not in _ID_TYPES:
        return AddCustomersToSegmentOutput(
            success=False, error=f"Invalid id_type. Must be one of: {list(_ID_TYPES)}"
        )

    params = {"id_type": id_type} if id_type != "id" else {}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{_BASE_URL}/segments/{segment_id}/add_customers",
                headers=_headers(site_id, api_key),
                json={"ids": customer_ids},
                params=params,
            )
        if response.status_code != 200:
            return AddCustomersToSegmentOutput(
                success=False, error=f"API error: {response.status_code} - {response.text}"
            )
    except Exception as exc:
        return AddCustomersToSegmentOutput(
            success=False, error=f"Failed to add customers to segment: {exc}"
        )

    return AddCustomersToSegmentOutput(
        success=True,
        message="Successfully added customers to segment",
        segment_id=segment_id,
        customer_count=len(customer_ids),
        id_type=id_type,
    )
