"""Square LangChain @tool functions."""
from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.square.outputs import (
    CreateCustomerOutput,
    CreateInvoiceOutput,
    CreateOrderOutput,
    CustomerResource,
    InvoiceResource,
    ListEventTypesOptionsOutput,
    ListLocationOptionsOutput,
    LocationOption,
    OrderResource,
    SendInvoiceOutput,
)

__all__ = [
    "create_customer",
    "create_invoice",
    "create_order",
    "list_event_types_options",
    "list_location_options",
    "send_invoice",
]

_BASE_URL = "https://connect.squareup.com/v2"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Square API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class CreateCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    given_name: str | None = Field(default=None, description="The first name associated with the customer profile")
    family_name: str | None = Field(default=None, description="The last name associated with the customer profile")
    company_name: str | None = Field(default=None, description="A business name associated with the customer profile")
    email_address: str | None = Field(default=None, description="The email address associated with the customer profile")
    phone_number: str | None = Field(default=None, description="Phone number (9-16 digits, optional + prefix and country code)")
    reference_id: str | None = Field(default=None, description="An optional second ID to associate the customer with an entity in another system")
    note: str | None = Field(default=None, description="A custom note associated with the customer profile")


class CreateInvoiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    location_id: str = Field(description="The ID of the Square location")
    order_id: str = Field(description="The ID of the order associated with the invoice")
    customer_id: str = Field(description="The ID of the customer who will receive the invoice")
    due_date: str = Field(description="The due date for the payment request, in YYYY-MM-DD format")
    accepted_payment_methods: list[str] = Field(description="Payment methods customers can use. Valid values: card, square_gift_card, bank_account, buy_now_pay_later, cash_app_pay")


class CreateOrderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    location_id: str = Field(description="The ID of the Square location for the order")
    customer_id: str | None = Field(default=None, description="The ID of the customer associated with the order")
    reference_id: str | None = Field(default=None, description="An optional second ID to associate the order with an entity in another system")
    line_items: list[dict[str, Any]] | None = Field(default=None, description="Line items for the order. Array of objects, each with: quantity (string), name (string), base_price_money ({amount: int in cents, currency: string e.g. 'USD'})")


class ListEventTypesOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListLocationOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class SendInvoiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    location_id: str = Field(description="The ID of the Square location")
    invoice_id: str = Field(description="The ID of the invoice to publish")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateCustomerInput)
@serialize_pydantic_return
async def create_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    given_name: str | None = None,
    family_name: str | None = None,
    company_name: str | None = None,
    email_address: str | None = None,
    phone_number: str | None = None,
    reference_id: str | None = None,
    note: str | None = None,
) -> CreateCustomerOutput:
    """Create a new customer for a business. Must provide at least one of: given_name, family_name, company_name, email_address, or phone_number."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return CreateCustomerOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"idempotency_key": str(uuid.uuid4())}
    if given_name:
        body["given_name"] = given_name
    if family_name:
        body["family_name"] = family_name
    if company_name:
        body["company_name"] = company_name
    if email_address:
        body["email_address"] = email_address
    if phone_number:
        body["phone_number"] = phone_number
    if reference_id:
        body["reference_id"] = reference_id
    if note:
        body["note"] = note

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/customers",
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return CreateCustomerOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateCustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCustomerOutput(success=False, error=f"Call failed: {exc}")

    c = data.get("customer", {})
    return CreateCustomerOutput(
        success=True,
        customer=CustomerResource(
            id=c.get("id"),
            given_name=c.get("given_name"),
            family_name=c.get("family_name"),
            company_name=c.get("company_name"),
            email_address=c.get("email_address"),
            phone_number=c.get("phone_number"),
            reference_id=c.get("reference_id"),
            note=c.get("note"),
            created_at=c.get("created_at"),
            updated_at=c.get("updated_at"),
        ),
    )


@tool(args_schema=CreateInvoiceInput)
@serialize_pydantic_return
async def create_invoice(
    auth_type: str,
    auth_data: dict[str, Any],
    location_id: str,
    order_id: str,
    customer_id: str,
    due_date: str,
    accepted_payment_methods: list[str],
) -> CreateInvoiceOutput:
    """Create a draft invoice for an order. You must publish (send) the invoice before Square can process it."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return CreateInvoiceOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    payment_methods_obj: dict[str, bool] = {}
    for method in accepted_payment_methods:
        payment_methods_obj[method] = True

    body: dict[str, Any] = {
        "idempotency_key": str(uuid.uuid4()),
        "invoice": {
            "location_id": location_id,
            "order_id": order_id,
            "primary_recipient": {"customer_id": customer_id},
            "payment_requests": [
                {
                    "request_type": "BALANCE",
                    "due_date": due_date,
                    "automatic_payment_source": "NONE",
                    "reminders": [],
                },
            ],
            "delivery_method": "EMAIL",
            "accepted_payment_methods": payment_methods_obj,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invoices",
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return CreateInvoiceOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateInvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateInvoiceOutput(success=False, error=f"Call failed: {exc}")

    inv = data.get("invoice", {})
    return CreateInvoiceOutput(
        success=True,
        invoice=InvoiceResource(
            id=inv.get("id"),
            version=inv.get("version"),
            location_id=inv.get("location_id"),
            order_id=inv.get("order_id"),
            status=inv.get("status"),
            created_at=inv.get("created_at"),
            updated_at=inv.get("updated_at"),
        ),
    )


@tool(args_schema=CreateOrderInput)
@serialize_pydantic_return
async def create_order(
    auth_type: str,
    auth_data: dict[str, Any],
    location_id: str,
    customer_id: str | None = None,
    reference_id: str | None = None,
    line_items: list[dict[str, Any]] | None = None,
) -> CreateOrderOutput:
    """Create a new order that can include information about products for purchase."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return CreateOrderOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    order: dict[str, Any] = {"location_id": location_id}
    if customer_id:
        order["customer_id"] = customer_id
    if reference_id:
        order["reference_id"] = reference_id
    if line_items:
        order["line_items"] = line_items

    body: dict[str, Any] = {
        "idempotency_key": str(uuid.uuid4()),
        "order": order,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/orders",
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return CreateOrderOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateOrderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateOrderOutput(success=False, error=f"Call failed: {exc}")

    o = data.get("order", {})
    return CreateOrderOutput(
        success=True,
        order=OrderResource(
            id=o.get("id"),
            location_id=o.get("location_id"),
            reference_id=o.get("reference_id"),
            state=o.get("state"),
            created_at=o.get("created_at"),
            updated_at=o.get("updated_at"),
        ),
    )


@tool(args_schema=ListEventTypesOptionsInput)
@serialize_pydantic_return
async def list_event_types_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListEventTypesOptionsOutput:
    """Retrieve the list of available webhook event types from Square."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ListEventTypesOptionsOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/webhooks/event-types",
                headers=headers,
            )
        if response.status_code != 200:
            return ListEventTypesOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListEventTypesOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEventTypesOptionsOutput(success=False, error=f"Call failed: {exc}")

    return ListEventTypesOptionsOutput(
        success=True,
        event_types=data.get("event_types", []),
    )


@tool(args_schema=ListLocationOptionsInput)
@serialize_pydantic_return
async def list_location_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListLocationOptionsOutput:
    """Retrieve the list of locations for the authenticated Square account."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ListLocationOptionsOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/locations",
                headers=headers,
            )
        if response.status_code != 200:
            return ListLocationOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListLocationOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListLocationOptionsOutput(success=False, error=f"Call failed: {exc}")

    locations_data = data.get("locations", [])
    locations = [
        LocationOption(
            id=loc.get("id"),
            name=loc.get("name"),
            status=loc.get("status"),
        )
        for loc in locations_data
    ]
    return ListLocationOptionsOutput(success=True, locations=locations)


@tool(args_schema=SendInvoiceInput)
@serialize_pydantic_return
async def send_invoice(
    auth_type: str,
    auth_data: dict[str, Any],
    location_id: str,
    invoice_id: str,
) -> SendInvoiceOutput:
    """Publish the latest version of a specified invoice so Square can process it."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return SendInvoiceOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            get_response = await client.get(
                f"{_BASE_URL}/invoices/{quote(invoice_id, safe='')}",
                headers=headers,
            )
        if get_response.status_code != 200:
            return SendInvoiceOutput(
                success=False,
                error=f"Failed to retrieve invoice ({get_response.status_code}): {get_response.text}",
            )
        invoice_data = get_response.json().get("invoice", {})
        version = invoice_data.get("version", 0)

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invoices/{quote(invoice_id, safe='')}/publish",
                headers=headers,
                json={
                    "idempotency_key": str(uuid.uuid4()),
                    "version": version,
                },
            )
        if response.status_code != 200:
            return SendInvoiceOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendInvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendInvoiceOutput(success=False, error=f"Call failed: {exc}")

    inv = data.get("invoice", {})
    return SendInvoiceOutput(
        success=True,
        invoice=InvoiceResource(
            id=inv.get("id"),
            version=inv.get("version"),
            location_id=inv.get("location_id"),
            order_id=inv.get("order_id"),
            status=inv.get("status"),
            created_at=inv.get("created_at"),
            updated_at=inv.get("updated_at"),
        ),
    )
