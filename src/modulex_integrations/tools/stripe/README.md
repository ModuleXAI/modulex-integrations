# Stripe

Process payments and manage commerce data through the Stripe REST API
(`api.stripe.com/v1`). Covers payment intents, customers, subscriptions,
invoices, charges, products, prices, and events — 50 actions in all.

## Authentication

Two methods supported — both validate against `GET /v1/customers?limit=1`
with a `Bearer` secret key.

### API Key (recommended)

- Sign in at <https://dashboard.stripe.com>, open **Developers > API
  keys**, and reveal or create a secret key.
- Required env var: `STRIPE_API_KEY` (format: `sk_test_...` for sandbox,
  `sk_live_...` for production).

### ModuleX Managed Key

Uses ModuleX's managed Stripe key with usage tracked against the
account's credit limit. No env vars to configure — the runtime injects
the credential automatically.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_payment_intent` | Create a Payment Intent to collect a payment | `amount`, `currency` |
| `retrieve_payment_intent` | Retrieve a Payment Intent by ID | `id` |
| `update_payment_intent` | Update a Payment Intent | `id` |
| `confirm_payment_intent` | Confirm a Payment Intent | `id` |
| `capture_payment_intent` | Capture an authorized Payment Intent | `id` |
| `cancel_payment_intent` | Cancel a Payment Intent | `id` |
| `list_payment_intents` | List Payment Intents | — |
| `search_payment_intents` | Search Payment Intents by query | `query` |
| `create_customer` | Create a customer | — |
| `retrieve_customer` | Retrieve a customer by ID | `id` |
| `update_customer` | Update a customer | `id` |
| `delete_customer` | Delete a customer | `id` |
| `list_customers` | List customers | — |
| `search_customers` | Search customers by query | `query` |
| `create_subscription` | Create a subscription | `customer`, `items` |
| `retrieve_subscription` | Retrieve a subscription by ID | `id` |
| `update_subscription` | Update a subscription | `id` |
| `cancel_subscription` | Cancel a subscription | `id` |
| `resume_subscription` | Resume a subscription | `id` |
| `list_subscriptions` | List subscriptions | — |
| `search_subscriptions` | Search subscriptions by query | `query` |
| `create_invoice` | Create an invoice | `customer` |
| `retrieve_invoice` | Retrieve an invoice by ID | `id` |
| `update_invoice` | Update an invoice | `id` |
| `delete_invoice` | Delete a draft invoice | `id` |
| `finalize_invoice` | Finalize a draft invoice | `id` |
| `pay_invoice` | Pay an invoice | `id` |
| `void_invoice` | Void an invoice | `id` |
| `send_invoice` | Send an invoice to the customer | `id` |
| `list_invoices` | List invoices | — |
| `search_invoices` | Search invoices by query | `query` |
| `create_charge` | Create a charge | `amount`, `currency` |
| `retrieve_charge` | Retrieve a charge by ID | `id` |
| `update_charge` | Update a charge | `id` |
| `capture_charge` | Capture an uncaptured charge | `id` |
| `list_charges` | List charges | — |
| `search_charges` | Search charges by query | `query` |
| `create_product` | Create a product | `name` |
| `retrieve_product` | Retrieve a product by ID | `id` |
| `update_product` | Update a product | `id` |
| `delete_product` | Delete a product | `id` |
| `list_products` | List products | — |
| `search_products` | Search products by query | `query` |
| `create_price` | Create a price for a product | `product`, `currency` |
| `retrieve_price` | Retrieve a price by ID | `id` |
| `update_price` | Update a price | `id` |
| `list_prices` | List prices | — |
| `search_prices` | Search prices by query | `query` |
| `retrieve_event` | Retrieve an event by ID | `id` |
| `list_events` | List events | — |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Rate limits**: Stripe allows ~100 read and ~100 write requests per
  second in live mode (lower in test mode). Search endpoints have their
  own, lower limits.
- **Request format**: requests are sent as
  `application/x-www-form-urlencoded` with Stripe's bracketed key
  notation for nested objects and arrays.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
