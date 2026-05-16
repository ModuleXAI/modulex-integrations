# Customer.io

Customer profile sync, event tracking, and manual-segment membership
management against the Customer.io Track API v1.

## Authentication

### Site ID + API Key (Basic Auth)

Customer.io uses HTTP Basic Auth with `site_id:api_key`. The modulex
runtime injects both as separate parameters; this tool builds the
`Authorization: Basic <b64>` header internally.

- Required env vars:
  - `CUSTOMERIO_SITE_ID`
  - `CUSTOMERIO_API_KEY`
- Find both at <https://customer.io>: *Settings > Workspace Settings >
  API Credentials*.

> **Test endpoint caveat:** the package manifest does not currently
> ship a test_endpoint for Customer.io. Modulex's `TestEndpoint`
> schema doesn't yet model Basic-Auth credential validation; the
> credential test path therefore falls back to inline behavior until
> a schema enhancement (`BasicAuthTestEndpoint` or similar) lands.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_or_update_customer` | Create/update a customer profile | `customer_id`, `email` |
| `send_event` | Track a customer event | `customer_id`, `event_name` |
| `add_customers_to_segment` | Add up to 1000 IDs to a manual segment | `segment_id`, `customer_ids` |

## Limits & Quotas

- Manual segment add: max 1000 customer IDs per call (enforced
  client-side; the tool returns `success=False` if the cap is
  exceeded).
- All actions are idempotent on the Customer.io side.

## Maintainer

ModuleX core team.
