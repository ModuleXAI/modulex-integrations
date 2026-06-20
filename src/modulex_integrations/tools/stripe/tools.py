"""Stripe LangChain ``@tool`` functions.

Fifty async tools wrapping the Stripe REST API (``api.stripe.com/v1``).
**The calling convention is key-based**: the modulex ``ToolExecutor``
injects an ``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair.

Two Stripe-specific request rules are honored throughout:

1. Stripe expects ``application/x-www-form-urlencoded`` bodies, never JSON.
   Requests send a flat ``dict[str, str]`` via httpx ``data=`` (POST) or
   ``params=`` (GET). Nested objects and arrays use PHP bracket notation
   (``metadata[key]``, ``items[0][price]``, ``created[gt]``); see
   ``_flatten_form``.
2. Booleans must be lowercase ``"true"``/``"false"`` — Python's
   ``str(True)`` (``"True"``) is rejected. ``_flatten_form`` emits the
   lowercase form for every boolean.

Error model: non-2xx responses, timeouts, and unexpected exceptions are
caught and returned as ``success=False`` + ``error`` rather than raising.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.stripe.outputs import (
    ChargeListOutput,
    ChargeMetadata,
    ChargeOutput,
    CustomerDeleteOutput,
    CustomerListOutput,
    CustomerMetadata,
    CustomerOutput,
    EventListOutput,
    EventMetadata,
    EventOutput,
    InvoiceDeleteOutput,
    InvoiceListOutput,
    InvoiceMetadata,
    InvoiceOutput,
    ListMetadata,
    PaymentIntentListOutput,
    PaymentIntentMetadata,
    PaymentIntentOutput,
    PriceListOutput,
    PriceMetadata,
    PriceOutput,
    ProductDeleteOutput,
    ProductListOutput,
    ProductMetadata,
    ProductOutput,
    SubscriptionListOutput,
    SubscriptionMetadata,
    SubscriptionOutput,
)

__all__ = [
    "cancel_payment_intent",
    "cancel_subscription",
    "capture_charge",
    "capture_payment_intent",
    "confirm_payment_intent",
    "create_charge",
    "create_customer",
    "create_invoice",
    "create_payment_intent",
    "create_price",
    "create_product",
    "create_subscription",
    "delete_customer",
    "delete_invoice",
    "delete_product",
    "finalize_invoice",
    "list_charges",
    "list_customers",
    "list_events",
    "list_invoices",
    "list_payment_intents",
    "list_prices",
    "list_products",
    "list_subscriptions",
    "pay_invoice",
    "resume_subscription",
    "retrieve_charge",
    "retrieve_customer",
    "retrieve_event",
    "retrieve_invoice",
    "retrieve_payment_intent",
    "retrieve_price",
    "retrieve_product",
    "retrieve_subscription",
    "search_charges",
    "search_customers",
    "search_invoices",
    "search_payment_intents",
    "search_prices",
    "search_products",
    "search_subscriptions",
    "send_invoice",
    "update_charge",
    "update_customer",
    "update_invoice",
    "update_payment_intent",
    "update_price",
    "update_product",
    "update_subscription",
    "void_invoice",
]

_BASE_URL = "https://api.stripe.com/v1"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = (
    "Stripe API key is empty. Provide a valid secret key (sk_...)."
)


# --- Form-encoding helpers -------------------------------------------------


def _flatten_form(prefix: str, value: Any, out: dict[str, str]) -> None:
    """Flatten a value into Stripe's bracketed form-encoding.

    Booleans become lowercase ``"true"``/``"false"``; nested dicts and
    lists recurse into ``prefix[key]`` / ``prefix[index]`` keys; ``None``
    is dropped.
    """
    if isinstance(value, bool):
        out[prefix] = "true" if value else "false"
    elif isinstance(value, dict):
        for key, item in value.items():
            _flatten_form(f"{prefix}[{key}]", item, out)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _flatten_form(f"{prefix}[{index}]", item, out)
    elif value is not None:
        out[prefix] = str(value)


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class CreatePaymentIntentInput(BaseModel):
    amount: int = Field(description="Amount in cents (e.g., 2000 for $20.00)")
    currency: str = Field(description="Three-letter ISO currency code (e.g., usd, eur)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    customer: str | None = Field(default=None, description="Customer ID to associate")
    payment_method: str | None = Field(default=None, description="Payment method ID")
    description: str | None = Field(default=None, description="Description of the payment")
    receipt_email: str | None = Field(default=None, description="Email to send receipt to")
    metadata: dict[str, Any] | None = Field(default=None, description="Key-value pairs")
    automatic_payment_methods: dict[str, Any] | None = Field(
        default=None,
        description='Enable automatic payment methods (e.g., {"enabled": true})',
    )


class RetrievePaymentIntentInput(BaseModel):
    id: str = Field(description="Payment Intent ID (e.g., pi_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class UpdatePaymentIntentInput(BaseModel):
    id: str = Field(description="Payment Intent ID (e.g., pi_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    amount: int | None = Field(default=None, description="Updated amount in cents")
    currency: str | None = Field(default=None, description="Three-letter ISO currency code")
    customer: str | None = Field(default=None, description="Customer ID")
    description: str | None = Field(default=None, description="Updated description")
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata")


class ConfirmPaymentIntentInput(BaseModel):
    id: str = Field(description="Payment Intent ID (e.g., pi_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    payment_method: str | None = Field(
        default=None, description="Payment method ID to confirm with"
    )


class CapturePaymentIntentInput(BaseModel):
    id: str = Field(description="Payment Intent ID (e.g., pi_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    amount_to_capture: int | None = Field(
        default=None, description="Amount to capture in cents (defaults to full amount)"
    )


class CancelPaymentIntentInput(BaseModel):
    id: str = Field(description="Payment Intent ID (e.g., pi_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    cancellation_reason: str | None = Field(
        default=None,
        description=(
            "Reason for cancellation (duplicate, fraudulent, "
            "requested_by_customer, abandoned)"
        ),
    )


class ListPaymentIntentsInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")
    customer: str | None = Field(default=None, description="Filter by customer ID")
    created: dict[str, Any] | None = Field(
        default=None, description='Filter by creation date (e.g., {"gt": 1633024800})'
    )


class SearchPaymentIntentsInput(BaseModel):
    query: str = Field(description="Search query (e.g., \"status:'succeeded' AND currency:'usd'\")")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")


class CreateCustomerInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    email: str | None = Field(default=None, description="Customer email address")
    name: str | None = Field(default=None, description="Customer full name")
    phone: str | None = Field(default=None, description="Customer phone number")
    description: str | None = Field(default=None, description="Description of the customer")
    address: dict[str, Any] | None = Field(default=None, description="Customer address object")
    metadata: dict[str, Any] | None = Field(default=None, description="Key-value pairs")
    payment_method: str | None = Field(default=None, description="Payment method ID to attach")


class RetrieveCustomerInput(BaseModel):
    id: str = Field(description="Customer ID (e.g., cus_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class UpdateCustomerInput(BaseModel):
    id: str = Field(description="Customer ID (e.g., cus_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    email: str | None = Field(default=None, description="Updated email address")
    name: str | None = Field(default=None, description="Updated name")
    phone: str | None = Field(default=None, description="Updated phone number")
    description: str | None = Field(default=None, description="Updated description")
    address: dict[str, Any] | None = Field(default=None, description="Updated address object")
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata")


class DeleteCustomerInput(BaseModel):
    id: str = Field(description="Customer ID (e.g., cus_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class ListCustomersInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")
    email: str | None = Field(default=None, description="Filter by email address")
    created: dict[str, Any] | None = Field(default=None, description="Filter by creation date")


class SearchCustomersInput(BaseModel):
    query: str = Field(description="Search query (e.g., \"email:'customer@example.com'\")")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")


class CreateSubscriptionInput(BaseModel):
    customer: str = Field(description="Customer ID to subscribe")
    items: list[dict[str, Any]] = Field(
        description='Array of items with price IDs (e.g., [{"price": "price_xxx", "quantity": 1}])'
    )
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    trial_period_days: int | None = Field(default=None, description="Number of trial days")
    default_payment_method: str | None = Field(default=None, description="Payment method ID")
    cancel_at_period_end: bool | None = Field(
        default=None, description="Cancel subscription at period end"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Key-value pairs")


class RetrieveSubscriptionInput(BaseModel):
    id: str = Field(description="Subscription ID (e.g., sub_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class UpdateSubscriptionInput(BaseModel):
    id: str = Field(description="Subscription ID (e.g., sub_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    items: list[dict[str, Any]] | None = Field(
        default=None, description="Updated array of items with price IDs"
    )
    cancel_at_period_end: bool | None = Field(
        default=None, description="Cancel subscription at period end"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata")


class CancelSubscriptionInput(BaseModel):
    id: str = Field(description="Subscription ID (e.g., sub_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    prorate: bool | None = Field(default=None, description="Whether to prorate the cancellation")
    invoice_now: bool | None = Field(default=None, description="Whether to invoice immediately")


class ResumeSubscriptionInput(BaseModel):
    id: str = Field(description="Subscription ID (e.g., sub_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class ListSubscriptionsInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")
    customer: str | None = Field(default=None, description="Filter by customer ID")
    status: str | None = Field(
        default=None,
        description=(
            "Filter by status (active, past_due, unpaid, canceled, incomplete, "
            "incomplete_expired, trialing, all)"
        ),
    )
    price: str | None = Field(default=None, description="Filter by price ID")


class SearchSubscriptionsInput(BaseModel):
    query: str = Field(
        description="Search query (e.g., \"status:'active' AND customer:'cus_xxx'\")"
    )
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")


class CreateInvoiceInput(BaseModel):
    customer: str = Field(description="Customer ID (e.g., cus_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    description: str | None = Field(default=None, description="Description of the invoice")
    metadata: dict[str, Any] | None = Field(default=None, description="Key-value pairs")
    auto_advance: bool | None = Field(default=None, description="Auto-finalize the invoice")
    collection_method: str | None = Field(
        default=None,
        description="Collection method: charge_automatically or send_invoice",
    )


class RetrieveInvoiceInput(BaseModel):
    id: str = Field(description="Invoice ID (e.g., in_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class UpdateInvoiceInput(BaseModel):
    id: str = Field(description="Invoice ID (e.g., in_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    description: str | None = Field(default=None, description="Description of the invoice")
    metadata: dict[str, Any] | None = Field(default=None, description="Key-value pairs")
    auto_advance: bool | None = Field(default=None, description="Auto-finalize the invoice")


class DeleteInvoiceInput(BaseModel):
    id: str = Field(description="Invoice ID (e.g., in_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class FinalizeInvoiceInput(BaseModel):
    id: str = Field(description="Invoice ID (e.g., in_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    auto_advance: bool | None = Field(default=None, description="Auto-advance the invoice")


class PayInvoiceInput(BaseModel):
    id: str = Field(description="Invoice ID (e.g., in_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    paid_out_of_band: bool | None = Field(
        default=None, description="Mark invoice as paid out of band"
    )


class VoidInvoiceInput(BaseModel):
    id: str = Field(description="Invoice ID (e.g., in_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class SendInvoiceInput(BaseModel):
    id: str = Field(description="Invoice ID (e.g., in_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class ListInvoicesInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")
    customer: str | None = Field(default=None, description="Filter by customer ID")
    status: str | None = Field(default=None, description="Filter by invoice status")


class SearchInvoicesInput(BaseModel):
    query: str = Field(description="Search query (e.g., \"customer:'cus_1234567890'\")")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")


class CreateChargeInput(BaseModel):
    amount: int = Field(description="Amount in cents (e.g., 2000 for $20.00)")
    currency: str = Field(description="Three-letter ISO currency code (e.g., usd, eur)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    customer: str | None = Field(default=None, description="Customer ID to associate")
    source: str | None = Field(
        default=None, description="Payment source ID (e.g., card token or saved card ID)"
    )
    description: str | None = Field(default=None, description="Description of the charge")
    metadata: dict[str, Any] | None = Field(default=None, description="Key-value pairs")
    capture: bool | None = Field(
        default=None, description="Whether to immediately capture the charge (defaults to true)"
    )


class RetrieveChargeInput(BaseModel):
    id: str = Field(description="Charge ID (e.g., ch_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class UpdateChargeInput(BaseModel):
    id: str = Field(description="Charge ID (e.g., ch_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    description: str | None = Field(default=None, description="Updated description")
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata")


class CaptureChargeInput(BaseModel):
    id: str = Field(description="Charge ID (e.g., ch_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    amount: int | None = Field(
        default=None, description="Amount to capture in cents (defaults to full amount)"
    )


class ListChargesInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")
    customer: str | None = Field(default=None, description="Filter by customer ID")
    created: dict[str, Any] | None = Field(
        default=None, description='Filter by creation date (e.g., {"gt": 1633024800})'
    )


class SearchChargesInput(BaseModel):
    query: str = Field(description="Search query (e.g., \"status:'succeeded' AND currency:'usd'\")")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")


class CreateProductInput(BaseModel):
    name: str = Field(description="Product name")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    description: str | None = Field(default=None, description="Product description")
    active: bool | None = Field(default=None, description="Whether the product is active")
    images: list[str] | None = Field(
        default=None, description="Array of image URLs for the product"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Key-value pairs")


class RetrieveProductInput(BaseModel):
    id: str = Field(description="Product ID (e.g., prod_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class UpdateProductInput(BaseModel):
    id: str = Field(description="Product ID (e.g., prod_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    name: str | None = Field(default=None, description="Updated product name")
    description: str | None = Field(default=None, description="Updated product description")
    active: bool | None = Field(default=None, description="Updated active status")
    images: list[str] | None = Field(default=None, description="Updated array of image URLs")
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata")


class DeleteProductInput(BaseModel):
    id: str = Field(description="Product ID (e.g., prod_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class ListProductsInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")
    active: bool | None = Field(default=None, description="Filter by active status")


class SearchProductsInput(BaseModel):
    query: str = Field(description="Search query (e.g., \"name:'shirt'\")")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")


class CreatePriceInput(BaseModel):
    product: str = Field(description="Product ID (e.g., prod_1234567890)")
    currency: str = Field(description="Three-letter ISO currency code (e.g., usd, eur)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    unit_amount: int | None = Field(
        default=None, description="Amount in cents (e.g., 1000 for $10.00)"
    )
    recurring: dict[str, Any] | None = Field(
        default=None,
        description="Recurring billing configuration (interval: day/week/month/year)",
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Key-value pairs")
    billing_scheme: str | None = Field(
        default=None, description="Billing scheme (per_unit or tiered)"
    )


class RetrievePriceInput(BaseModel):
    id: str = Field(description="Price ID (e.g., price_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class UpdatePriceInput(BaseModel):
    id: str = Field(description="Price ID (e.g., price_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    active: bool | None = Field(default=None, description="Whether the price is active")
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata")


class ListPricesInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")
    product: str | None = Field(default=None, description="Filter by product ID")
    active: bool | None = Field(default=None, description="Filter by active status")


class SearchPricesInput(BaseModel):
    query: str = Field(description="Search query (e.g., \"active:'true' AND currency:'usd'\")")
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")


class RetrieveEventInput(BaseModel):
    id: str = Field(description="Event ID (e.g., evt_1234567890)")
    api_key: str = Field(description="Stripe API key (provided by credential system)")


class ListEventsInput(BaseModel):
    api_key: str = Field(description="Stripe API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Number of results (default 10, max 100)")
    type: str | None = Field(
        default=None, description="Filter by event type (e.g., payment_intent.created)"
    )
    created: dict[str, Any] | None = Field(
        default=None, description='Filter by creation date (e.g., {"gt": 1633024800})'
    )


# --- Payment Intent tools --------------------------------------------------


@tool(args_schema=CreatePaymentIntentInput)
@serialize_pydantic_return
async def create_payment_intent(
    amount: int,
    currency: str,
    api_key: str,
    customer: str | None = None,
    payment_method: str | None = None,
    description: str | None = None,
    receipt_email: str | None = None,
    metadata: dict[str, Any] | None = None,
    automatic_payment_methods: dict[str, Any] | None = None,
) -> PaymentIntentOutput:
    """Create a new Payment Intent to process a payment."""
    if not api_key or not api_key.strip():
        return PaymentIntentOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    _flatten_form("amount", amount, form)
    _flatten_form("currency", currency, form)
    if customer is not None:
        _flatten_form("customer", customer, form)
    if payment_method is not None:
        _flatten_form("payment_method", payment_method, form)
    if description is not None:
        _flatten_form("description", description, form)
    if receipt_email is not None:
        _flatten_form("receipt_email", receipt_email, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)
    if automatic_payment_methods and automatic_payment_methods.get("enabled"):
        form["automatic_payment_methods[enabled]"] = "true"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/payment_intents", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return PaymentIntentOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PaymentIntentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PaymentIntentOutput(success=False, error=f"Create payment intent failed: {exc}")

    return PaymentIntentOutput(
        success=True,
        payment_intent=data,
        metadata=PaymentIntentMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=RetrievePaymentIntentInput)
@serialize_pydantic_return
async def retrieve_payment_intent(id: str, api_key: str) -> PaymentIntentOutput:
    """Retrieve an existing Payment Intent by ID."""
    if not api_key or not api_key.strip():
        return PaymentIntentOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/payment_intents/{id}", headers=_headers(api_key)
            )
        if response.status_code not in (200, 201):
            return PaymentIntentOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PaymentIntentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PaymentIntentOutput(success=False, error=f"Retrieve payment intent failed: {exc}")

    return PaymentIntentOutput(
        success=True,
        payment_intent=data,
        metadata=PaymentIntentMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=UpdatePaymentIntentInput)
@serialize_pydantic_return
async def update_payment_intent(
    id: str,
    api_key: str,
    amount: int | None = None,
    currency: str | None = None,
    customer: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> PaymentIntentOutput:
    """Update an existing Payment Intent."""
    if not api_key or not api_key.strip():
        return PaymentIntentOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if amount is not None:
        _flatten_form("amount", amount, form)
    if currency is not None:
        _flatten_form("currency", currency, form)
    if customer is not None:
        _flatten_form("customer", customer, form)
    if description is not None:
        _flatten_form("description", description, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/payment_intents/{id}", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return PaymentIntentOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PaymentIntentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PaymentIntentOutput(success=False, error=f"Update payment intent failed: {exc}")

    return PaymentIntentOutput(
        success=True,
        payment_intent=data,
        metadata=PaymentIntentMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=ConfirmPaymentIntentInput)
@serialize_pydantic_return
async def confirm_payment_intent(
    id: str, api_key: str, payment_method: str | None = None
) -> PaymentIntentOutput:
    """Confirm a Payment Intent to complete the payment."""
    if not api_key or not api_key.strip():
        return PaymentIntentOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if payment_method is not None:
        _flatten_form("payment_method", payment_method, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/payment_intents/{id}/confirm",
                headers=_headers(api_key),
                data=form,
            )
        if response.status_code not in (200, 201):
            return PaymentIntentOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PaymentIntentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PaymentIntentOutput(success=False, error=f"Confirm payment intent failed: {exc}")

    return PaymentIntentOutput(
        success=True,
        payment_intent=data,
        metadata=PaymentIntentMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=CapturePaymentIntentInput)
@serialize_pydantic_return
async def capture_payment_intent(
    id: str, api_key: str, amount_to_capture: int | None = None
) -> PaymentIntentOutput:
    """Capture an authorized Payment Intent."""
    if not api_key or not api_key.strip():
        return PaymentIntentOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if amount_to_capture is not None:
        _flatten_form("amount_to_capture", amount_to_capture, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/payment_intents/{id}/capture",
                headers=_headers(api_key),
                data=form,
            )
        if response.status_code not in (200, 201):
            return PaymentIntentOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PaymentIntentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PaymentIntentOutput(success=False, error=f"Capture payment intent failed: {exc}")

    return PaymentIntentOutput(
        success=True,
        payment_intent=data,
        metadata=PaymentIntentMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=CancelPaymentIntentInput)
@serialize_pydantic_return
async def cancel_payment_intent(
    id: str, api_key: str, cancellation_reason: str | None = None
) -> PaymentIntentOutput:
    """Cancel a Payment Intent."""
    if not api_key or not api_key.strip():
        return PaymentIntentOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if cancellation_reason is not None:
        _flatten_form("cancellation_reason", cancellation_reason, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/payment_intents/{id}/cancel",
                headers=_headers(api_key),
                data=form,
            )
        if response.status_code not in (200, 201):
            return PaymentIntentOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PaymentIntentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PaymentIntentOutput(success=False, error=f"Cancel payment intent failed: {exc}")

    return PaymentIntentOutput(
        success=True,
        payment_intent=data,
        metadata=PaymentIntentMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=ListPaymentIntentsInput)
@serialize_pydantic_return
async def list_payment_intents(
    api_key: str,
    limit: int | None = None,
    customer: str | None = None,
    created: dict[str, Any] | None = None,
) -> PaymentIntentListOutput:
    """List all Payment Intents."""
    if not api_key or not api_key.strip():
        return PaymentIntentListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {}
    if limit is not None:
        _flatten_form("limit", limit, params)
    if customer is not None:
        _flatten_form("customer", customer, params)
    if created is not None:
        _flatten_form("created", created, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/payment_intents", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return PaymentIntentListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PaymentIntentListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PaymentIntentListOutput(success=False, error=f"List payment intents failed: {exc}")

    items = data.get("data") or []
    return PaymentIntentListOutput(
        success=True,
        payment_intents=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


@tool(args_schema=SearchPaymentIntentsInput)
@serialize_pydantic_return
async def search_payment_intents(
    query: str, api_key: str, limit: int | None = None
) -> PaymentIntentListOutput:
    """Search for Payment Intents using query syntax."""
    if not api_key or not api_key.strip():
        return PaymentIntentListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {"query": query}
    if limit is not None:
        _flatten_form("limit", limit, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/payment_intents/search", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return PaymentIntentListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PaymentIntentListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PaymentIntentListOutput(
            success=False, error=f"Search payment intents failed: {exc}"
        )

    items = data.get("data") or []
    return PaymentIntentListOutput(
        success=True,
        payment_intents=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


# --- Customer tools --------------------------------------------------------


@tool(args_schema=CreateCustomerInput)
@serialize_pydantic_return
async def create_customer(
    api_key: str,
    email: str | None = None,
    name: str | None = None,
    phone: str | None = None,
    description: str | None = None,
    address: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    payment_method: str | None = None,
) -> CustomerOutput:
    """Create a new customer object."""
    if not api_key or not api_key.strip():
        return CustomerOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if email is not None:
        _flatten_form("email", email, form)
    if name is not None:
        _flatten_form("name", name, form)
    if phone is not None:
        _flatten_form("phone", phone, form)
    if description is not None:
        _flatten_form("description", description, form)
    if payment_method is not None:
        _flatten_form("payment_method", payment_method, form)
    if address is not None:
        _flatten_form("address", address, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/customers", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return CustomerOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CustomerOutput(success=False, error=f"Create customer failed: {exc}")

    return CustomerOutput(
        success=True,
        customer=data,
        metadata=CustomerMetadata(
            id=data.get("id"), email=data.get("email"), name=data.get("name")
        ),
    )


@tool(args_schema=RetrieveCustomerInput)
@serialize_pydantic_return
async def retrieve_customer(id: str, api_key: str) -> CustomerOutput:
    """Retrieve an existing customer by ID."""
    if not api_key or not api_key.strip():
        return CustomerOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/customers/{id}", headers=_headers(api_key)
            )
        if response.status_code not in (200, 201):
            return CustomerOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CustomerOutput(success=False, error=f"Retrieve customer failed: {exc}")

    return CustomerOutput(
        success=True,
        customer=data,
        metadata=CustomerMetadata(
            id=data.get("id"), email=data.get("email"), name=data.get("name")
        ),
    )


@tool(args_schema=UpdateCustomerInput)
@serialize_pydantic_return
async def update_customer(
    id: str,
    api_key: str,
    email: str | None = None,
    name: str | None = None,
    phone: str | None = None,
    description: str | None = None,
    address: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> CustomerOutput:
    """Update an existing customer."""
    if not api_key or not api_key.strip():
        return CustomerOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if email is not None:
        _flatten_form("email", email, form)
    if name is not None:
        _flatten_form("name", name, form)
    if phone is not None:
        _flatten_form("phone", phone, form)
    if description is not None:
        _flatten_form("description", description, form)
    if address is not None:
        _flatten_form("address", address, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/customers/{id}", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return CustomerOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CustomerOutput(success=False, error=f"Update customer failed: {exc}")

    return CustomerOutput(
        success=True,
        customer=data,
        metadata=CustomerMetadata(
            id=data.get("id"), email=data.get("email"), name=data.get("name")
        ),
    )


@tool(args_schema=DeleteCustomerInput)
@serialize_pydantic_return
async def delete_customer(id: str, api_key: str) -> CustomerDeleteOutput:
    """Permanently delete a customer."""
    if not api_key or not api_key.strip():
        return CustomerDeleteOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/customers/{id}", headers=_headers(api_key)
            )
        if response.status_code not in (200, 201):
            return CustomerDeleteOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CustomerDeleteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CustomerDeleteOutput(success=False, error=f"Delete customer failed: {exc}")

    return CustomerDeleteOutput(success=True, deleted=data.get("deleted"), id=data.get("id"))


@tool(args_schema=ListCustomersInput)
@serialize_pydantic_return
async def list_customers(
    api_key: str,
    limit: int | None = None,
    email: str | None = None,
    created: dict[str, Any] | None = None,
) -> CustomerListOutput:
    """List all customers."""
    if not api_key or not api_key.strip():
        return CustomerListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {}
    if limit is not None:
        _flatten_form("limit", limit, params)
    if email is not None:
        _flatten_form("email", email, params)
    if created is not None:
        _flatten_form("created", created, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/customers", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return CustomerListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CustomerListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CustomerListOutput(success=False, error=f"List customers failed: {exc}")

    items = data.get("data") or []
    return CustomerListOutput(
        success=True,
        customers=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


@tool(args_schema=SearchCustomersInput)
@serialize_pydantic_return
async def search_customers(
    query: str, api_key: str, limit: int | None = None
) -> CustomerListOutput:
    """Search for customers using query syntax."""
    if not api_key or not api_key.strip():
        return CustomerListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {"query": query}
    if limit is not None:
        _flatten_form("limit", limit, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/customers/search", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return CustomerListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CustomerListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CustomerListOutput(success=False, error=f"Search customers failed: {exc}")

    items = data.get("data") or []
    return CustomerListOutput(
        success=True,
        customers=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


# --- Subscription tools ----------------------------------------------------


@tool(args_schema=CreateSubscriptionInput)
@serialize_pydantic_return
async def create_subscription(
    customer: str,
    items: list[dict[str, Any]],
    api_key: str,
    trial_period_days: int | None = None,
    default_payment_method: str | None = None,
    cancel_at_period_end: bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> SubscriptionOutput:
    """Create a new subscription for a customer."""
    if not api_key or not api_key.strip():
        return SubscriptionOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    _flatten_form("customer", customer, form)
    if items:
        _flatten_form("items", items, form)
    if trial_period_days is not None:
        _flatten_form("trial_period_days", trial_period_days, form)
    if default_payment_method is not None:
        _flatten_form("default_payment_method", default_payment_method, form)
    if cancel_at_period_end is not None:
        _flatten_form("cancel_at_period_end", cancel_at_period_end, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/subscriptions", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return SubscriptionOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SubscriptionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubscriptionOutput(success=False, error=f"Create subscription failed: {exc}")

    return SubscriptionOutput(
        success=True,
        subscription=data,
        metadata=SubscriptionMetadata(
            id=data.get("id"), status=data.get("status"), customer=data.get("customer")
        ),
    )


@tool(args_schema=RetrieveSubscriptionInput)
@serialize_pydantic_return
async def retrieve_subscription(id: str, api_key: str) -> SubscriptionOutput:
    """Retrieve an existing subscription by ID."""
    if not api_key or not api_key.strip():
        return SubscriptionOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/subscriptions/{id}", headers=_headers(api_key)
            )
        if response.status_code not in (200, 201):
            return SubscriptionOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SubscriptionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubscriptionOutput(success=False, error=f"Retrieve subscription failed: {exc}")

    return SubscriptionOutput(
        success=True,
        subscription=data,
        metadata=SubscriptionMetadata(
            id=data.get("id"), status=data.get("status"), customer=data.get("customer")
        ),
    )


@tool(args_schema=UpdateSubscriptionInput)
@serialize_pydantic_return
async def update_subscription(
    id: str,
    api_key: str,
    items: list[dict[str, Any]] | None = None,
    cancel_at_period_end: bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> SubscriptionOutput:
    """Update an existing subscription."""
    if not api_key or not api_key.strip():
        return SubscriptionOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if items:
        _flatten_form("items", items, form)
    if cancel_at_period_end is not None:
        _flatten_form("cancel_at_period_end", cancel_at_period_end, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/subscriptions/{id}", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return SubscriptionOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SubscriptionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubscriptionOutput(success=False, error=f"Update subscription failed: {exc}")

    return SubscriptionOutput(
        success=True,
        subscription=data,
        metadata=SubscriptionMetadata(
            id=data.get("id"), status=data.get("status"), customer=data.get("customer")
        ),
    )


@tool(args_schema=CancelSubscriptionInput)
@serialize_pydantic_return
async def cancel_subscription(
    id: str,
    api_key: str,
    prorate: bool | None = None,
    invoice_now: bool | None = None,
) -> SubscriptionOutput:
    """Cancel a subscription."""
    if not api_key or not api_key.strip():
        return SubscriptionOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if prorate is not None:
        _flatten_form("prorate", prorate, form)
    if invoice_now is not None:
        _flatten_form("invoice_now", invoice_now, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                "DELETE",
                f"{_BASE_URL}/subscriptions/{id}",
                headers=_headers(api_key),
                data=form,
            )
        if response.status_code not in (200, 201):
            return SubscriptionOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SubscriptionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubscriptionOutput(success=False, error=f"Cancel subscription failed: {exc}")

    return SubscriptionOutput(
        success=True,
        subscription=data,
        metadata=SubscriptionMetadata(
            id=data.get("id"), status=data.get("status"), customer=data.get("customer")
        ),
    )


@tool(args_schema=ResumeSubscriptionInput)
@serialize_pydantic_return
async def resume_subscription(id: str, api_key: str) -> SubscriptionOutput:
    """Resume a subscription that was scheduled for cancellation."""
    if not api_key or not api_key.strip():
        return SubscriptionOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/subscriptions/{id}/resume", headers=_headers(api_key), data={}
            )
        if response.status_code not in (200, 201):
            return SubscriptionOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SubscriptionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubscriptionOutput(success=False, error=f"Resume subscription failed: {exc}")

    return SubscriptionOutput(
        success=True,
        subscription=data,
        metadata=SubscriptionMetadata(
            id=data.get("id"), status=data.get("status"), customer=data.get("customer")
        ),
    )


@tool(args_schema=ListSubscriptionsInput)
@serialize_pydantic_return
async def list_subscriptions(
    api_key: str,
    limit: int | None = None,
    customer: str | None = None,
    status: str | None = None,
    price: str | None = None,
) -> SubscriptionListOutput:
    """List all subscriptions."""
    if not api_key or not api_key.strip():
        return SubscriptionListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {}
    if limit is not None:
        _flatten_form("limit", limit, params)
    if customer is not None:
        _flatten_form("customer", customer, params)
    if status is not None:
        _flatten_form("status", status, params)
    if price is not None:
        _flatten_form("price", price, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/subscriptions", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return SubscriptionListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SubscriptionListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubscriptionListOutput(success=False, error=f"List subscriptions failed: {exc}")

    items = data.get("data") or []
    return SubscriptionListOutput(
        success=True,
        subscriptions=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


@tool(args_schema=SearchSubscriptionsInput)
@serialize_pydantic_return
async def search_subscriptions(
    query: str, api_key: str, limit: int | None = None
) -> SubscriptionListOutput:
    """Search for subscriptions using query syntax."""
    if not api_key or not api_key.strip():
        return SubscriptionListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {"query": query}
    if limit is not None:
        _flatten_form("limit", limit, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/subscriptions/search", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return SubscriptionListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SubscriptionListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubscriptionListOutput(success=False, error=f"Search subscriptions failed: {exc}")

    items = data.get("data") or []
    return SubscriptionListOutput(
        success=True,
        subscriptions=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


# --- Invoice tools ---------------------------------------------------------


@tool(args_schema=CreateInvoiceInput)
@serialize_pydantic_return
async def create_invoice(
    customer: str,
    api_key: str,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    auto_advance: bool | None = None,
    collection_method: str | None = None,
) -> InvoiceOutput:
    """Create a new invoice."""
    if not api_key or not api_key.strip():
        return InvoiceOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    _flatten_form("customer", customer, form)
    if description is not None:
        _flatten_form("description", description, form)
    if auto_advance is not None:
        _flatten_form("auto_advance", auto_advance, form)
    if collection_method is not None:
        _flatten_form("collection_method", collection_method, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invoices", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return InvoiceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceOutput(success=False, error=f"Create invoice failed: {exc}")

    return InvoiceOutput(
        success=True,
        invoice=data,
        metadata=InvoiceMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount_due=data.get("amount_due"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=RetrieveInvoiceInput)
@serialize_pydantic_return
async def retrieve_invoice(id: str, api_key: str) -> InvoiceOutput:
    """Retrieve an existing invoice by ID."""
    if not api_key or not api_key.strip():
        return InvoiceOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/invoices/{id}", headers=_headers(api_key)
            )
        if response.status_code not in (200, 201):
            return InvoiceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceOutput(success=False, error=f"Retrieve invoice failed: {exc}")

    return InvoiceOutput(
        success=True,
        invoice=data,
        metadata=InvoiceMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount_due=data.get("amount_due"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=UpdateInvoiceInput)
@serialize_pydantic_return
async def update_invoice(
    id: str,
    api_key: str,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    auto_advance: bool | None = None,
) -> InvoiceOutput:
    """Update an existing invoice."""
    if not api_key or not api_key.strip():
        return InvoiceOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if description is not None:
        _flatten_form("description", description, form)
    if auto_advance is not None:
        _flatten_form("auto_advance", auto_advance, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invoices/{id}", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return InvoiceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceOutput(success=False, error=f"Update invoice failed: {exc}")

    return InvoiceOutput(
        success=True,
        invoice=data,
        metadata=InvoiceMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount_due=data.get("amount_due"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=DeleteInvoiceInput)
@serialize_pydantic_return
async def delete_invoice(id: str, api_key: str) -> InvoiceDeleteOutput:
    """Permanently delete a draft invoice."""
    if not api_key or not api_key.strip():
        return InvoiceDeleteOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/invoices/{id}", headers=_headers(api_key)
            )
        if response.status_code not in (200, 201):
            return InvoiceDeleteOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceDeleteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceDeleteOutput(success=False, error=f"Delete invoice failed: {exc}")

    return InvoiceDeleteOutput(success=True, deleted=data.get("deleted"), id=data.get("id"))


@tool(args_schema=FinalizeInvoiceInput)
@serialize_pydantic_return
async def finalize_invoice(
    id: str, api_key: str, auto_advance: bool | None = None
) -> InvoiceOutput:
    """Finalize a draft invoice."""
    if not api_key or not api_key.strip():
        return InvoiceOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if auto_advance is not None:
        _flatten_form("auto_advance", auto_advance, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invoices/{id}/finalize", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return InvoiceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceOutput(success=False, error=f"Finalize invoice failed: {exc}")

    return InvoiceOutput(
        success=True,
        invoice=data,
        metadata=InvoiceMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount_due=data.get("amount_due"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=PayInvoiceInput)
@serialize_pydantic_return
async def pay_invoice(
    id: str, api_key: str, paid_out_of_band: bool | None = None
) -> InvoiceOutput:
    """Pay an invoice."""
    if not api_key or not api_key.strip():
        return InvoiceOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if paid_out_of_band is not None:
        _flatten_form("paid_out_of_band", paid_out_of_band, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invoices/{id}/pay", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return InvoiceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceOutput(success=False, error=f"Pay invoice failed: {exc}")

    return InvoiceOutput(
        success=True,
        invoice=data,
        metadata=InvoiceMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount_due=data.get("amount_due"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=VoidInvoiceInput)
@serialize_pydantic_return
async def void_invoice(id: str, api_key: str) -> InvoiceOutput:
    """Void an invoice."""
    if not api_key or not api_key.strip():
        return InvoiceOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invoices/{id}/void", headers=_headers(api_key), data={}
            )
        if response.status_code not in (200, 201):
            return InvoiceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceOutput(success=False, error=f"Void invoice failed: {exc}")

    return InvoiceOutput(
        success=True,
        invoice=data,
        metadata=InvoiceMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount_due=data.get("amount_due"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=SendInvoiceInput)
@serialize_pydantic_return
async def send_invoice(id: str, api_key: str) -> InvoiceOutput:
    """Send an invoice to the customer."""
    if not api_key or not api_key.strip():
        return InvoiceOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invoices/{id}/send", headers=_headers(api_key), data={}
            )
        if response.status_code not in (200, 201):
            return InvoiceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceOutput(success=False, error=f"Send invoice failed: {exc}")

    return InvoiceOutput(
        success=True,
        invoice=data,
        metadata=InvoiceMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount_due=data.get("amount_due"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=ListInvoicesInput)
@serialize_pydantic_return
async def list_invoices(
    api_key: str,
    limit: int | None = None,
    customer: str | None = None,
    status: str | None = None,
) -> InvoiceListOutput:
    """List all invoices."""
    if not api_key or not api_key.strip():
        return InvoiceListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {}
    if limit is not None:
        _flatten_form("limit", limit, params)
    if customer is not None:
        _flatten_form("customer", customer, params)
    if status is not None:
        _flatten_form("status", status, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/invoices", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return InvoiceListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceListOutput(success=False, error=f"List invoices failed: {exc}")

    items = data.get("data") or []
    return InvoiceListOutput(
        success=True,
        invoices=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


@tool(args_schema=SearchInvoicesInput)
@serialize_pydantic_return
async def search_invoices(
    query: str, api_key: str, limit: int | None = None
) -> InvoiceListOutput:
    """Search for invoices using query syntax."""
    if not api_key or not api_key.strip():
        return InvoiceListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {"query": query}
    if limit is not None:
        _flatten_form("limit", limit, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/invoices/search", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return InvoiceListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return InvoiceListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InvoiceListOutput(success=False, error=f"Search invoices failed: {exc}")

    items = data.get("data") or []
    return InvoiceListOutput(
        success=True,
        invoices=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


# --- Charge tools ----------------------------------------------------------


@tool(args_schema=CreateChargeInput)
@serialize_pydantic_return
async def create_charge(
    amount: int,
    currency: str,
    api_key: str,
    customer: str | None = None,
    source: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    capture: bool | None = None,
) -> ChargeOutput:
    """Create a new charge to process a payment."""
    if not api_key or not api_key.strip():
        return ChargeOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    _flatten_form("amount", amount, form)
    _flatten_form("currency", currency, form)
    if customer is not None:
        _flatten_form("customer", customer, form)
    if source is not None:
        _flatten_form("source", source, form)
    if description is not None:
        _flatten_form("description", description, form)
    if capture is not None:
        _flatten_form("capture", capture, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/charges", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return ChargeOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChargeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChargeOutput(success=False, error=f"Create charge failed: {exc}")

    return ChargeOutput(
        success=True,
        charge=data,
        metadata=ChargeMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
            paid=data.get("paid"),
        ),
    )


@tool(args_schema=RetrieveChargeInput)
@serialize_pydantic_return
async def retrieve_charge(id: str, api_key: str) -> ChargeOutput:
    """Retrieve an existing charge by ID."""
    if not api_key or not api_key.strip():
        return ChargeOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/charges/{id}", headers=_headers(api_key))
        if response.status_code not in (200, 201):
            return ChargeOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChargeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChargeOutput(success=False, error=f"Retrieve charge failed: {exc}")

    return ChargeOutput(
        success=True,
        charge=data,
        metadata=ChargeMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
            paid=data.get("paid"),
        ),
    )


@tool(args_schema=UpdateChargeInput)
@serialize_pydantic_return
async def update_charge(
    id: str,
    api_key: str,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ChargeOutput:
    """Update an existing charge."""
    if not api_key or not api_key.strip():
        return ChargeOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if description is not None:
        _flatten_form("description", description, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/charges/{id}", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return ChargeOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChargeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChargeOutput(success=False, error=f"Update charge failed: {exc}")

    return ChargeOutput(
        success=True,
        charge=data,
        metadata=ChargeMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
            paid=data.get("paid"),
        ),
    )


@tool(args_schema=CaptureChargeInput)
@serialize_pydantic_return
async def capture_charge(id: str, api_key: str, amount: int | None = None) -> ChargeOutput:
    """Capture an uncaptured charge."""
    if not api_key or not api_key.strip():
        return ChargeOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if amount is not None:
        _flatten_form("amount", amount, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/charges/{id}/capture", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return ChargeOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChargeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChargeOutput(success=False, error=f"Capture charge failed: {exc}")

    return ChargeOutput(
        success=True,
        charge=data,
        metadata=ChargeMetadata(
            id=data.get("id"),
            status=data.get("status"),
            amount=data.get("amount"),
            currency=data.get("currency"),
            paid=data.get("paid"),
        ),
    )


@tool(args_schema=ListChargesInput)
@serialize_pydantic_return
async def list_charges(
    api_key: str,
    limit: int | None = None,
    customer: str | None = None,
    created: dict[str, Any] | None = None,
) -> ChargeListOutput:
    """List all charges."""
    if not api_key or not api_key.strip():
        return ChargeListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {}
    if limit is not None:
        _flatten_form("limit", limit, params)
    if customer is not None:
        _flatten_form("customer", customer, params)
    if created is not None:
        _flatten_form("created", created, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/charges", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return ChargeListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChargeListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChargeListOutput(success=False, error=f"List charges failed: {exc}")

    items = data.get("data") or []
    return ChargeListOutput(
        success=True,
        charges=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


@tool(args_schema=SearchChargesInput)
@serialize_pydantic_return
async def search_charges(query: str, api_key: str, limit: int | None = None) -> ChargeListOutput:
    """Search for charges using query syntax."""
    if not api_key or not api_key.strip():
        return ChargeListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {"query": query}
    if limit is not None:
        _flatten_form("limit", limit, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/charges/search", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return ChargeListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChargeListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChargeListOutput(success=False, error=f"Search charges failed: {exc}")

    items = data.get("data") or []
    return ChargeListOutput(
        success=True,
        charges=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


# --- Product tools ---------------------------------------------------------


@tool(args_schema=CreateProductInput)
@serialize_pydantic_return
async def create_product(
    name: str,
    api_key: str,
    description: str | None = None,
    active: bool | None = None,
    images: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProductOutput:
    """Create a new product object."""
    if not api_key or not api_key.strip():
        return ProductOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    _flatten_form("name", name, form)
    if description is not None:
        _flatten_form("description", description, form)
    if active is not None:
        _flatten_form("active", active, form)
    if images is not None:
        _flatten_form("images", images, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/products", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return ProductOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ProductOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ProductOutput(success=False, error=f"Create product failed: {exc}")

    return ProductOutput(
        success=True,
        product=data,
        metadata=ProductMetadata(
            id=data.get("id"), name=data.get("name"), active=data.get("active")
        ),
    )


@tool(args_schema=RetrieveProductInput)
@serialize_pydantic_return
async def retrieve_product(id: str, api_key: str) -> ProductOutput:
    """Retrieve an existing product by ID."""
    if not api_key or not api_key.strip():
        return ProductOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/products/{id}", headers=_headers(api_key))
        if response.status_code not in (200, 201):
            return ProductOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ProductOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ProductOutput(success=False, error=f"Retrieve product failed: {exc}")

    return ProductOutput(
        success=True,
        product=data,
        metadata=ProductMetadata(
            id=data.get("id"), name=data.get("name"), active=data.get("active")
        ),
    )


@tool(args_schema=UpdateProductInput)
@serialize_pydantic_return
async def update_product(
    id: str,
    api_key: str,
    name: str | None = None,
    description: str | None = None,
    active: bool | None = None,
    images: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProductOutput:
    """Update an existing product."""
    if not api_key or not api_key.strip():
        return ProductOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if name is not None:
        _flatten_form("name", name, form)
    if description is not None:
        _flatten_form("description", description, form)
    if active is not None:
        _flatten_form("active", active, form)
    if images is not None:
        _flatten_form("images", images, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/products/{id}", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return ProductOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ProductOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ProductOutput(success=False, error=f"Update product failed: {exc}")

    return ProductOutput(
        success=True,
        product=data,
        metadata=ProductMetadata(
            id=data.get("id"), name=data.get("name"), active=data.get("active")
        ),
    )


@tool(args_schema=DeleteProductInput)
@serialize_pydantic_return
async def delete_product(id: str, api_key: str) -> ProductDeleteOutput:
    """Permanently delete a product."""
    if not api_key or not api_key.strip():
        return ProductDeleteOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/products/{id}", headers=_headers(api_key)
            )
        if response.status_code not in (200, 201):
            return ProductDeleteOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ProductDeleteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ProductDeleteOutput(success=False, error=f"Delete product failed: {exc}")

    return ProductDeleteOutput(success=True, deleted=data.get("deleted"), id=data.get("id"))


@tool(args_schema=ListProductsInput)
@serialize_pydantic_return
async def list_products(
    api_key: str, limit: int | None = None, active: bool | None = None
) -> ProductListOutput:
    """List all products."""
    if not api_key or not api_key.strip():
        return ProductListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {}
    if limit is not None:
        _flatten_form("limit", limit, params)
    if active is not None:
        _flatten_form("active", active, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/products", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return ProductListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ProductListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ProductListOutput(success=False, error=f"List products failed: {exc}")

    items = data.get("data") or []
    return ProductListOutput(
        success=True,
        products=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


@tool(args_schema=SearchProductsInput)
@serialize_pydantic_return
async def search_products(
    query: str, api_key: str, limit: int | None = None
) -> ProductListOutput:
    """Search for products using query syntax."""
    if not api_key or not api_key.strip():
        return ProductListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {"query": query}
    if limit is not None:
        _flatten_form("limit", limit, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/products/search", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return ProductListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ProductListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ProductListOutput(success=False, error=f"Search products failed: {exc}")

    items = data.get("data") or []
    return ProductListOutput(
        success=True,
        products=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


# --- Price tools -----------------------------------------------------------


@tool(args_schema=CreatePriceInput)
@serialize_pydantic_return
async def create_price(
    product: str,
    currency: str,
    api_key: str,
    unit_amount: int | None = None,
    recurring: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    billing_scheme: str | None = None,
) -> PriceOutput:
    """Create a new price for a product."""
    if not api_key or not api_key.strip():
        return PriceOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    _flatten_form("product", product, form)
    _flatten_form("currency", currency, form)
    if unit_amount is not None:
        _flatten_form("unit_amount", unit_amount, form)
    if billing_scheme is not None:
        _flatten_form("billing_scheme", billing_scheme, form)
    if recurring is not None:
        _flatten_form("recurring", recurring, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/prices", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return PriceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PriceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PriceOutput(success=False, error=f"Create price failed: {exc}")

    return PriceOutput(
        success=True,
        price=data,
        metadata=PriceMetadata(
            id=data.get("id"),
            product=data.get("product"),
            unit_amount=data.get("unit_amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=RetrievePriceInput)
@serialize_pydantic_return
async def retrieve_price(id: str, api_key: str) -> PriceOutput:
    """Retrieve an existing price by ID."""
    if not api_key or not api_key.strip():
        return PriceOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/prices/{id}", headers=_headers(api_key))
        if response.status_code not in (200, 201):
            return PriceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PriceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PriceOutput(success=False, error=f"Retrieve price failed: {exc}")

    return PriceOutput(
        success=True,
        price=data,
        metadata=PriceMetadata(
            id=data.get("id"),
            product=data.get("product"),
            unit_amount=data.get("unit_amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=UpdatePriceInput)
@serialize_pydantic_return
async def update_price(
    id: str,
    api_key: str,
    active: bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> PriceOutput:
    """Update an existing price."""
    if not api_key or not api_key.strip():
        return PriceOutput(success=False, error=_EMPTY_KEY_ERROR)

    form: dict[str, str] = {}
    if active is not None:
        _flatten_form("active", active, form)
    if metadata is not None:
        _flatten_form("metadata", metadata, form)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/prices/{id}", headers=_headers(api_key), data=form
            )
        if response.status_code not in (200, 201):
            return PriceOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PriceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PriceOutput(success=False, error=f"Update price failed: {exc}")

    return PriceOutput(
        success=True,
        price=data,
        metadata=PriceMetadata(
            id=data.get("id"),
            product=data.get("product"),
            unit_amount=data.get("unit_amount"),
            currency=data.get("currency"),
        ),
    )


@tool(args_schema=ListPricesInput)
@serialize_pydantic_return
async def list_prices(
    api_key: str,
    limit: int | None = None,
    product: str | None = None,
    active: bool | None = None,
) -> PriceListOutput:
    """List all prices."""
    if not api_key or not api_key.strip():
        return PriceListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {}
    if limit is not None:
        _flatten_form("limit", limit, params)
    if product is not None:
        _flatten_form("product", product, params)
    if active is not None:
        _flatten_form("active", active, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/prices", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return PriceListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PriceListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PriceListOutput(success=False, error=f"List prices failed: {exc}")

    items = data.get("data") or []
    return PriceListOutput(
        success=True,
        prices=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


@tool(args_schema=SearchPricesInput)
@serialize_pydantic_return
async def search_prices(query: str, api_key: str, limit: int | None = None) -> PriceListOutput:
    """Search for prices using query syntax."""
    if not api_key or not api_key.strip():
        return PriceListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {"query": query}
    if limit is not None:
        _flatten_form("limit", limit, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/prices/search", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return PriceListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PriceListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PriceListOutput(success=False, error=f"Search prices failed: {exc}")

    items = data.get("data") or []
    return PriceListOutput(
        success=True,
        prices=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )


# --- Event tools -----------------------------------------------------------


@tool(args_schema=RetrieveEventInput)
@serialize_pydantic_return
async def retrieve_event(id: str, api_key: str) -> EventOutput:
    """Retrieve an existing Event by ID."""
    if not api_key or not api_key.strip():
        return EventOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/events/{id}", headers=_headers(api_key))
        if response.status_code not in (200, 201):
            return EventOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return EventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EventOutput(success=False, error=f"Retrieve event failed: {exc}")

    return EventOutput(
        success=True,
        event=data,
        metadata=EventMetadata(
            id=data.get("id"), type=data.get("type"), created=data.get("created")
        ),
    )


@tool(args_schema=ListEventsInput)
@serialize_pydantic_return
async def list_events(
    api_key: str,
    limit: int | None = None,
    type: str | None = None,
    created: dict[str, Any] | None = None,
) -> EventListOutput:
    """List all Events."""
    if not api_key or not api_key.strip():
        return EventListOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, str] = {}
    if limit is not None:
        _flatten_form("limit", limit, params)
    if type is not None:
        _flatten_form("type", type, params)
    if created is not None:
        _flatten_form("created", created, params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/events", headers=_headers(api_key), params=params
            )
        if response.status_code not in (200, 201):
            return EventListOutput(
                success=False,
                error=f"Stripe API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return EventListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EventListOutput(success=False, error=f"List events failed: {exc}")

    items = data.get("data") or []
    return EventListOutput(
        success=True,
        events=items,
        metadata=ListMetadata(count=len(items), has_more=data.get("has_more") or False),
    )
