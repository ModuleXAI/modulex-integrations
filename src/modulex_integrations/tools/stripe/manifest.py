"""Stripe integration manifest.

Exposes 50 actions across eight Stripe resource groups (payment intents,
customers, subscriptions, invoices, charges, products, prices, events)
against the Stripe REST API (``api.stripe.com/v1``).

This integration uses the ``api_key`` runtime convention: the modulex
``ToolExecutor`` injects the resolved secret key as ``api_key: str`` into
each tool. Authentication is bring-your-own-key via ``ApiKeyAuthSchema``
(your own Stripe secret key) — Stripe is a pure BYOK service. The
credential test reads ``GET /v1/customers?limit=1``.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


# --- Reusable parameter definitions ----------------------------------------


def _id_param(resource: str, example: str) -> ParameterDef:
    return ParameterDef(
        type="string",
        description=f"{resource} ID (e.g., {example})",
        required=True,
    )


_LIMIT = ParameterDef(
    type="integer",
    description="Number of results to return (default 10, max 100)",
)
_QUERY = ParameterDef(
    type="string",
    description="Search query using Stripe's search query syntax",
    required=True,
)
_METADATA = ParameterDef(
    type="object",
    description="Set of key-value pairs for storing additional information",
)
_CREATED_FILTER = ParameterDef(
    type="object",
    description='Filter by creation date (e.g., {"gt": 1633024800})',
)


_TEST_HEADERS = {"Authorization": "Bearer {api_key}"}
_TEST_PARAMS = {"limit": "1"}
_TEST_SUCCESS = SuccessIndicators(status_codes=[200], response_fields=["object"])


manifest = IntegrationManifest(
    name="stripe",
    display_name="Stripe",
    description=(
        "Integrate Stripe into the workflow. Manage payment intents, customers, "
        "subscriptions, invoices, charges, products, prices, and events through "
        "the Stripe REST API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:stripe-themed",
    app_url="https://stripe.com",
    categories=["Finance & Payments", "payments", "subscriptions"],
    actions=[
        # --- Payment Intents -------------------------------------------------
        ActionDefinition(
            name="create_payment_intent",
            description="Create a new Payment Intent to process a payment.",
            parameters={
                "amount": ParameterDef(
                    type="integer",
                    description="Amount in cents (e.g., 2000 for $20.00)",
                    required=True,
                ),
                "currency": ParameterDef(
                    type="string",
                    description="Three-letter ISO currency code (e.g., usd, eur)",
                    required=True,
                ),
                "customer": ParameterDef(
                    type="string", description="Customer ID to associate with this payment"
                ),
                "payment_method": ParameterDef(type="string", description="Payment method ID"),
                "description": ParameterDef(
                    type="string", description="Description of the payment"
                ),
                "receipt_email": ParameterDef(
                    type="string", description="Email address to send receipt to"
                ),
                "metadata": _METADATA,
                "automatic_payment_methods": ParameterDef(
                    type="object",
                    description='Enable automatic payment methods (e.g., {"enabled": true})',
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_payment_intent",
            description="Retrieve an existing Payment Intent by ID.",
            parameters={"id": _id_param("Payment Intent", "pi_1234567890")},
        ),
        ActionDefinition(
            name="update_payment_intent",
            description="Update an existing Payment Intent.",
            parameters={
                "id": _id_param("Payment Intent", "pi_1234567890"),
                "amount": ParameterDef(type="integer", description="Updated amount in cents"),
                "currency": ParameterDef(
                    type="string", description="Three-letter ISO currency code"
                ),
                "customer": ParameterDef(type="string", description="Customer ID"),
                "description": ParameterDef(type="string", description="Updated description"),
                "metadata": ParameterDef(type="object", description="Updated metadata"),
            },
        ),
        ActionDefinition(
            name="confirm_payment_intent",
            description="Confirm a Payment Intent to complete the payment.",
            parameters={
                "id": _id_param("Payment Intent", "pi_1234567890"),
                "payment_method": ParameterDef(
                    type="string", description="Payment method ID to confirm with"
                ),
            },
        ),
        ActionDefinition(
            name="capture_payment_intent",
            description="Capture an authorized Payment Intent.",
            parameters={
                "id": _id_param("Payment Intent", "pi_1234567890"),
                "amount_to_capture": ParameterDef(
                    type="integer",
                    description="Amount to capture in cents (defaults to full amount)",
                ),
            },
        ),
        ActionDefinition(
            name="cancel_payment_intent",
            description="Cancel a Payment Intent.",
            parameters={
                "id": _id_param("Payment Intent", "pi_1234567890"),
                "cancellation_reason": ParameterDef(
                    type="string",
                    description=(
                        "Reason for cancellation (duplicate, fraudulent, "
                        "requested_by_customer, abandoned)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_payment_intents",
            description="List all Payment Intents.",
            parameters={
                "limit": _LIMIT,
                "customer": ParameterDef(type="string", description="Filter by customer ID"),
                "created": _CREATED_FILTER,
            },
        ),
        ActionDefinition(
            name="search_payment_intents",
            description="Search for Payment Intents using query syntax.",
            parameters={"query": _QUERY, "limit": _LIMIT},
        ),
        # --- Customers -------------------------------------------------------
        ActionDefinition(
            name="create_customer",
            description="Create a new customer object.",
            parameters={
                "email": ParameterDef(type="string", description="Customer email address"),
                "name": ParameterDef(type="string", description="Customer full name"),
                "phone": ParameterDef(type="string", description="Customer phone number"),
                "description": ParameterDef(
                    type="string", description="Description of the customer"
                ),
                "address": ParameterDef(type="object", description="Customer address object"),
                "metadata": _METADATA,
                "payment_method": ParameterDef(
                    type="string", description="Payment method ID to attach"
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_customer",
            description="Retrieve an existing customer by ID.",
            parameters={"id": _id_param("Customer", "cus_1234567890")},
        ),
        ActionDefinition(
            name="update_customer",
            description="Update an existing customer.",
            parameters={
                "id": _id_param("Customer", "cus_1234567890"),
                "email": ParameterDef(type="string", description="Updated email address"),
                "name": ParameterDef(type="string", description="Updated name"),
                "phone": ParameterDef(type="string", description="Updated phone number"),
                "description": ParameterDef(type="string", description="Updated description"),
                "address": ParameterDef(type="object", description="Updated address object"),
                "metadata": ParameterDef(type="object", description="Updated metadata"),
            },
        ),
        ActionDefinition(
            name="delete_customer",
            description="Permanently delete a customer.",
            parameters={"id": _id_param("Customer", "cus_1234567890")},
        ),
        ActionDefinition(
            name="list_customers",
            description="List all customers.",
            parameters={
                "limit": _LIMIT,
                "email": ParameterDef(type="string", description="Filter by email address"),
                "created": ParameterDef(type="object", description="Filter by creation date"),
            },
        ),
        ActionDefinition(
            name="search_customers",
            description="Search for customers using query syntax.",
            parameters={"query": _QUERY, "limit": _LIMIT},
        ),
        # --- Subscriptions ---------------------------------------------------
        ActionDefinition(
            name="create_subscription",
            description="Create a new subscription for a customer.",
            parameters={
                "customer": ParameterDef(
                    type="string", description="Customer ID to subscribe", required=True
                ),
                "items": ParameterDef(
                    type="array",
                    description=(
                        "Array of items with price IDs "
                        '(e.g., [{"price": "price_xxx", "quantity": 1}])'
                    ),
                    required=True,
                ),
                "trial_period_days": ParameterDef(
                    type="integer", description="Number of trial days"
                ),
                "default_payment_method": ParameterDef(
                    type="string", description="Payment method ID"
                ),
                "cancel_at_period_end": ParameterDef(
                    type="boolean", description="Cancel subscription at period end"
                ),
                "metadata": _METADATA,
            },
        ),
        ActionDefinition(
            name="retrieve_subscription",
            description="Retrieve an existing subscription by ID.",
            parameters={"id": _id_param("Subscription", "sub_1234567890")},
        ),
        ActionDefinition(
            name="update_subscription",
            description="Update an existing subscription.",
            parameters={
                "id": _id_param("Subscription", "sub_1234567890"),
                "items": ParameterDef(
                    type="array", description="Updated array of items with price IDs"
                ),
                "cancel_at_period_end": ParameterDef(
                    type="boolean", description="Cancel subscription at period end"
                ),
                "metadata": ParameterDef(type="object", description="Updated metadata"),
            },
        ),
        ActionDefinition(
            name="cancel_subscription",
            description="Cancel a subscription.",
            parameters={
                "id": _id_param("Subscription", "sub_1234567890"),
                "prorate": ParameterDef(
                    type="boolean", description="Whether to prorate the cancellation"
                ),
                "invoice_now": ParameterDef(
                    type="boolean", description="Whether to invoice immediately"
                ),
            },
        ),
        ActionDefinition(
            name="resume_subscription",
            description="Resume a subscription that was scheduled for cancellation.",
            parameters={"id": _id_param("Subscription", "sub_1234567890")},
        ),
        ActionDefinition(
            name="list_subscriptions",
            description="List all subscriptions.",
            parameters={
                "limit": _LIMIT,
                "customer": ParameterDef(type="string", description="Filter by customer ID"),
                "status": ParameterDef(
                    type="string",
                    description=(
                        "Filter by status (active, past_due, unpaid, canceled, "
                        "incomplete, incomplete_expired, trialing, all)"
                    ),
                ),
                "price": ParameterDef(type="string", description="Filter by price ID"),
            },
        ),
        ActionDefinition(
            name="search_subscriptions",
            description="Search for subscriptions using query syntax.",
            parameters={"query": _QUERY, "limit": _LIMIT},
        ),
        # --- Invoices --------------------------------------------------------
        ActionDefinition(
            name="create_invoice",
            description="Create a new invoice.",
            parameters={
                "customer": ParameterDef(
                    type="string", description="Customer ID (e.g., cus_1234567890)", required=True
                ),
                "description": ParameterDef(
                    type="string", description="Description of the invoice"
                ),
                "metadata": _METADATA,
                "auto_advance": ParameterDef(
                    type="boolean", description="Auto-finalize the invoice"
                ),
                "collection_method": ParameterDef(
                    type="string",
                    description="Collection method: charge_automatically or send_invoice",
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_invoice",
            description="Retrieve an existing invoice by ID.",
            parameters={"id": _id_param("Invoice", "in_1234567890")},
        ),
        ActionDefinition(
            name="update_invoice",
            description="Update an existing invoice.",
            parameters={
                "id": _id_param("Invoice", "in_1234567890"),
                "description": ParameterDef(
                    type="string", description="Description of the invoice"
                ),
                "metadata": _METADATA,
                "auto_advance": ParameterDef(
                    type="boolean", description="Auto-finalize the invoice"
                ),
            },
        ),
        ActionDefinition(
            name="delete_invoice",
            description="Permanently delete a draft invoice.",
            parameters={"id": _id_param("Invoice", "in_1234567890")},
        ),
        ActionDefinition(
            name="finalize_invoice",
            description="Finalize a draft invoice.",
            parameters={
                "id": _id_param("Invoice", "in_1234567890"),
                "auto_advance": ParameterDef(
                    type="boolean", description="Auto-advance the invoice"
                ),
            },
        ),
        ActionDefinition(
            name="pay_invoice",
            description="Pay an invoice.",
            parameters={
                "id": _id_param("Invoice", "in_1234567890"),
                "paid_out_of_band": ParameterDef(
                    type="boolean", description="Mark invoice as paid out of band"
                ),
            },
        ),
        ActionDefinition(
            name="void_invoice",
            description="Void an invoice.",
            parameters={"id": _id_param("Invoice", "in_1234567890")},
        ),
        ActionDefinition(
            name="send_invoice",
            description="Send an invoice to the customer.",
            parameters={"id": _id_param("Invoice", "in_1234567890")},
        ),
        ActionDefinition(
            name="list_invoices",
            description="List all invoices.",
            parameters={
                "limit": _LIMIT,
                "customer": ParameterDef(type="string", description="Filter by customer ID"),
                "status": ParameterDef(type="string", description="Filter by invoice status"),
            },
        ),
        ActionDefinition(
            name="search_invoices",
            description="Search for invoices using query syntax.",
            parameters={"query": _QUERY, "limit": _LIMIT},
        ),
        # --- Charges ---------------------------------------------------------
        ActionDefinition(
            name="create_charge",
            description="Create a new charge to process a payment.",
            parameters={
                "amount": ParameterDef(
                    type="integer",
                    description="Amount in cents (e.g., 2000 for $20.00)",
                    required=True,
                ),
                "currency": ParameterDef(
                    type="string",
                    description="Three-letter ISO currency code (e.g., usd, eur)",
                    required=True,
                ),
                "customer": ParameterDef(
                    type="string", description="Customer ID to associate with this charge"
                ),
                "source": ParameterDef(
                    type="string",
                    description="Payment source ID (e.g., card token or saved card ID)",
                ),
                "description": ParameterDef(
                    type="string", description="Description of the charge"
                ),
                "metadata": _METADATA,
                "capture": ParameterDef(
                    type="boolean",
                    description="Whether to immediately capture the charge (defaults to true)",
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_charge",
            description="Retrieve an existing charge by ID.",
            parameters={"id": _id_param("Charge", "ch_1234567890")},
        ),
        ActionDefinition(
            name="update_charge",
            description="Update an existing charge.",
            parameters={
                "id": _id_param("Charge", "ch_1234567890"),
                "description": ParameterDef(type="string", description="Updated description"),
                "metadata": ParameterDef(type="object", description="Updated metadata"),
            },
        ),
        ActionDefinition(
            name="capture_charge",
            description="Capture an uncaptured charge.",
            parameters={
                "id": _id_param("Charge", "ch_1234567890"),
                "amount": ParameterDef(
                    type="integer",
                    description="Amount to capture in cents (defaults to full amount)",
                ),
            },
        ),
        ActionDefinition(
            name="list_charges",
            description="List all charges.",
            parameters={
                "limit": _LIMIT,
                "customer": ParameterDef(type="string", description="Filter by customer ID"),
                "created": _CREATED_FILTER,
            },
        ),
        ActionDefinition(
            name="search_charges",
            description="Search for charges using query syntax.",
            parameters={"query": _QUERY, "limit": _LIMIT},
        ),
        # --- Products --------------------------------------------------------
        ActionDefinition(
            name="create_product",
            description="Create a new product object.",
            parameters={
                "name": ParameterDef(type="string", description="Product name", required=True),
                "description": ParameterDef(type="string", description="Product description"),
                "active": ParameterDef(
                    type="boolean", description="Whether the product is active"
                ),
                "images": ParameterDef(
                    type="array", description="Array of image URLs for the product"
                ),
                "metadata": _METADATA,
            },
        ),
        ActionDefinition(
            name="retrieve_product",
            description="Retrieve an existing product by ID.",
            parameters={"id": _id_param("Product", "prod_1234567890")},
        ),
        ActionDefinition(
            name="update_product",
            description="Update an existing product.",
            parameters={
                "id": _id_param("Product", "prod_1234567890"),
                "name": ParameterDef(type="string", description="Updated product name"),
                "description": ParameterDef(
                    type="string", description="Updated product description"
                ),
                "active": ParameterDef(type="boolean", description="Updated active status"),
                "images": ParameterDef(
                    type="array", description="Updated array of image URLs"
                ),
                "metadata": ParameterDef(type="object", description="Updated metadata"),
            },
        ),
        ActionDefinition(
            name="delete_product",
            description="Permanently delete a product.",
            parameters={"id": _id_param("Product", "prod_1234567890")},
        ),
        ActionDefinition(
            name="list_products",
            description="List all products.",
            parameters={
                "limit": _LIMIT,
                "active": ParameterDef(type="boolean", description="Filter by active status"),
            },
        ),
        ActionDefinition(
            name="search_products",
            description="Search for products using query syntax.",
            parameters={"query": _QUERY, "limit": _LIMIT},
        ),
        # --- Prices ----------------------------------------------------------
        ActionDefinition(
            name="create_price",
            description="Create a new price for a product.",
            parameters={
                "product": ParameterDef(
                    type="string",
                    description="Product ID (e.g., prod_1234567890)",
                    required=True,
                ),
                "currency": ParameterDef(
                    type="string",
                    description="Three-letter ISO currency code (e.g., usd, eur)",
                    required=True,
                ),
                "unit_amount": ParameterDef(
                    type="integer", description="Amount in cents (e.g., 1000 for $10.00)"
                ),
                "recurring": ParameterDef(
                    type="object",
                    description="Recurring billing configuration (interval: day/week/month/year)",
                ),
                "metadata": _METADATA,
                "billing_scheme": ParameterDef(
                    type="string", description="Billing scheme (per_unit or tiered)"
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_price",
            description="Retrieve an existing price by ID.",
            parameters={"id": _id_param("Price", "price_1234567890")},
        ),
        ActionDefinition(
            name="update_price",
            description="Update an existing price.",
            parameters={
                "id": _id_param("Price", "price_1234567890"),
                "active": ParameterDef(
                    type="boolean", description="Whether the price is active"
                ),
                "metadata": ParameterDef(type="object", description="Updated metadata"),
            },
        ),
        ActionDefinition(
            name="list_prices",
            description="List all prices.",
            parameters={
                "limit": _LIMIT,
                "product": ParameterDef(type="string", description="Filter by product ID"),
                "active": ParameterDef(type="boolean", description="Filter by active status"),
            },
        ),
        ActionDefinition(
            name="search_prices",
            description="Search for prices using query syntax.",
            parameters={"query": _QUERY, "limit": _LIMIT},
        ),
        # --- Events ----------------------------------------------------------
        ActionDefinition(
            name="retrieve_event",
            description="Retrieve an existing Event by ID.",
            parameters={"id": _id_param("Event", "evt_1234567890")},
        ),
        ActionDefinition(
            name="list_events",
            description="List all Events.",
            parameters={
                "limit": _LIMIT,
                "type": ParameterDef(
                    type="string",
                    description="Filter by event type (e.g., payment_intent.created)",
                ),
                "created": _CREATED_FILTER,
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Stripe secret API key",
            setup_instructions=[
                "Sign in to your Stripe dashboard at https://dashboard.stripe.com",
                "Open the Developers section and click 'API keys'",
                "Reveal or create a secret key (it starts with sk_test_ or sk_live_)",
                "Paste the secret key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="STRIPE_API_KEY",
                    display_name="Stripe Secret Key",
                    description="Your Stripe secret API key from the Stripe dashboard",
                    required=True,
                    sensitive=True,
                    sample_format="sk_test_...",
                    about_url="https://dashboard.stripe.com/apikeys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.stripe.com/v1/customers",
                method="GET",
                headers=_TEST_HEADERS,
                params=_TEST_PARAMS,
                success_indicators=_TEST_SUCCESS,
                cost_level="free",
                description="Validates the API key by listing one customer",
            ),
        ),
    ],
)
