# Square

Payment processing, commerce, and business management via the Square Connect API (`connect.squareup.com/v2`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at <https://developer.squareup.com/apps>.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `CUSTOMERS_WRITE`, `CUSTOMERS_READ`, `ORDERS_WRITE`, `ORDERS_READ`, `INVOICES_WRITE`, `INVOICES_READ`, `MERCHANT_PROFILE_READ`
- Required env vars (only when bringing your own OAuth app):
  - `SQUARE_OAUTH2_CLIENT_ID` (format: `sq0idp-xxxxxxxxxxxxxxxx`)
  - `SQUARE_OAUTH2_CLIENT_SECRET` (format: `sq0csp-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_customer` | Create a new customer for a business | _(at least one of given_name, family_name, company_name, email_address, phone_number)_ |
| `create_invoice` | Create a draft invoice for an order | `location_id`, `order_id`, `customer_id`, `due_date`, `accepted_payment_methods` |
| `create_order` | Create a new order with product line items | `location_id` |
| `list_event_types_options` | Retrieve available webhook event types | _(none)_ |
| `list_location_options` | Retrieve locations for the authenticated account | _(none)_ |
| `send_invoice` | Publish the latest version of a specified invoice | `location_id`, `invoice_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Rate limits**: Square enforces per-endpoint rate limits, typically 30-100 requests per 30 seconds depending on the endpoint category.
- **Sandbox**: Square provides a sandbox environment for testing at `connect.squareupsandbox.com`.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising. Square errors include a JSON `errors[]` array with `category`, `code`, and `detail` fields.

## Maintainer

ModuleX core team.
