# Lemon Squeezy

Read-only access to the Lemon Squeezy v1 REST API
(`api.lemonsqueezy.com/v1`): customers, orders, products,
subscriptions, and stores.

## Authentication

### API Key (Bearer)

- Required env var: `LEMON_SQUEEZY_API_KEY`.
- Created in your Lemon Squeezy dashboard —
  <https://docs.lemonsqueezy.com/api#authentication>.
- Sent as `Authorization: Bearer <key>` with the
  `application/vnd.api+json` content/accept headers (JSON:API).

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_customers` | Page through customers | — |
| `retrieve_customer` | Get one customer | `customer_id` |
| `list_orders` | Page through orders (filterable) | — |
| `retrieve_order` | Get one order | `order_id` |
| `list_products` | Page through products (filterable) | — |
| `retrieve_product` | Get one product | `product_id` |
| `list_subscriptions` | Page through subscriptions (filterable) | — |
| `retrieve_subscription` | Get one subscription | `subscription_id` |
| `list_stores` | Page through stores | — |
| `retrieve_store` | Get one store | `store_id` |

## Limits & Quotas

- Pagination via JSON:API `page[number]` / `page[size]`; `per_page` is
  clamped to 100.
- List endpoints return both `data` (array of resources) and `meta`
  (pagination block); retrievals return just `data`.
- 404 retrievals return `success=False` with a "not found" message;
  other non-200 responses surface the body verbatim.

## Maintainer

ModuleX core team.
