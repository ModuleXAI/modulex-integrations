# Google Merchant Center

Manage product listings in Google Merchant Center via the Shopping Content API
(`shoppingcontent.googleapis.com/content/v2.1`).

## Authentication

### OAuth2 Authentication

- Register an OAuth app at the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required scope: `https://www.googleapis.com/auth/content`
- Required configuration: Merchant ID (numeric account ID from [Merchant Center](https://merchants.google.com/mc/overview))

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_product` | Creates a product in your Google Merchant Center account | `offer_id`, `content_language`, `target_country`, `channel` |
| `update_product` | Updates an existing product in your Google Merchant Center account | `product_id`, `updated_values` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- **Rate limits**: Google Shopping Content API has per-project and per-user quotas managed via the Google Cloud Console. Default is approximately 7,000 requests per 100 seconds per project.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
