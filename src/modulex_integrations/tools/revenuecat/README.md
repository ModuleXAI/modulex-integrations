# RevenueCat

Manage in-app subscriptions and entitlements against the RevenueCat
REST API v1 (`api.revenuecat.com/v1`). Look up subscribers, grant or
revoke promotional entitlements, record purchases, update subscriber
attributes, and manage Google Play subscription billing.

## Authentication

### API Key

- Sign in at <https://app.revenuecat.com>, open **Project Settings →
  API Keys**, and create or copy a key. A **secret key** (`sk_...`) is
  required for write operations (granting entitlements, deleting
  subscribers, refunds); a public key suffices for read-only customer
  lookups.
- Required env var: `REVENUECAT_API_KEY` (format:
  `sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- The key is sent as `Authorization: Bearer <api_key>`. The credential
  is validated with a `GET /subscribers/{id}` probe, which returns 200.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_customer` | Retrieve subscriber info by app user ID | `app_user_id` |
| `delete_customer` | Permanently delete a subscriber | `app_user_id` |
| `create_purchase` | Record a purchase (receipt) for a subscriber | `app_user_id`, `fetch_token`, `platform` |
| `grant_entitlement` | Grant a promotional entitlement | `app_user_id`, `entitlement_identifier` |
| `revoke_entitlement` | Revoke promotional entitlements | `app_user_id`, `entitlement_identifier` |
| `list_offerings` | List offerings configured for the project | `app_user_id` |
| `update_subscriber_attributes` | Set custom subscriber attributes | `app_user_id`, `attributes` |
| `defer_google_subscription` | Extend a Google Play subscription's billing date | `app_user_id`, `product_id` |
| `refund_google_subscription` | Refund a store transaction and revoke access | `app_user_id`, `store_transaction_id` |
| `revoke_google_subscription` | Revoke a Google Play subscription and refund | `app_user_id`, `product_id` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (the `api_key` injection
convention — not the `auth_type`/`auth_data` pair used by OAuth tools).

## Limits & Quotas

- **Rate limits**: RevenueCat applies per-endpoint rate limits; the
  `429` responses include a `Retry-After` header. Plan retries on the
  agent side.
- **Grant / revoke entitlement** is for *promotional* entitlements
  only and requires a secret key.
- **Defer / refund / revoke Google subscription** apply to Google Play
  purchases only. `grant_entitlement` and `defer_google_subscription`
  require exactly one of their two mutually-exclusive time parameters.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. RevenueCat
  returns `{code, message}` on errors, which is surfaced in `error`.

## Maintainer

ModuleX core team.
