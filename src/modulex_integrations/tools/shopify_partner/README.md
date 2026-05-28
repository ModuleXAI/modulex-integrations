# Shopify Partner

Verify incoming Shopify webhooks and interact with the Shopify Partner API (`partners.shopify.com/<org_id>/api/`).

## Authentication

### API Key (Partner Credentials)

- Log in to your [Shopify Partner Dashboard](https://partners.shopify.com) and note your Organization ID from the URL.
- Navigate to **Settings > Partner API clients** to create or copy your API access token.
- Required env vars:
  - `SHOPIFY_PARTNER_ORGANIZATION_ID` (format: `12345678`)
  - `SHOPIFY_PARTNER_API_KEY` (format: `shppa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `verify_webhook` | Verify an incoming webhook from Shopify by validating its HMAC-SHA256 signature | `app_secret_key`, `shopify_hmac`, `body` |

Every tool takes additional `organization_id` and `api_key` parameters that the runtime fills in from the resolved credential.

## Limits & Quotas

- The `verify_webhook` action performs local HMAC computation and does not call the Shopify Partner API, so no rate limits apply to it.
- The Shopify Partner GraphQL API (for future actions) has a cost-based throttle of 1,000 points per second with a bucket size of 2,000.
- Error model: failures are returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
