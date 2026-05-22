# Google Ads

Google Ads API integration covering GAQL reports across Campaigns, Ad Groups, Ads, and Customers; Customer Match list management; offline conversion uploads; and keyword idea generation against the REST API at `googleads.googleapis.com`.

## Authentication

One method supported. Validation calls `GET /v21/customers:listAccessibleCustomers` with both the OAuth access token and the developer-token header.

### OAuth2 Authentication

- Sign in at <https://console.cloud.google.com/apis/credentials>, create an OAuth 2.0 Client ID (Web application), and add `https://api.modulex.dev/credentials/oauth2/callback` as an authorized redirect URI.
- Required env vars:
  - `GOOGLE_ADS_OAUTH2_CLIENT_ID` (format: `123456789-xxxxxxxxxxxxxxxx.apps.googleusercontent.com`)
  - `GOOGLE_ADS_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-xxxxxxxxxxxxxxxxxxxx`)
  - `GOOGLE_ADS_DEVELOPER_TOKEN` — approved developer token from your Google Ads Manager Account at <https://ads.google.com/aw/apicenter>. The Google Ads API rejects requests without this header, so the OAuth schema collects it alongside the client credentials. See <https://developers.google.com/google-ads/api/docs/get-started/dev-token>.
- Scopes requested: `https://www.googleapis.com/auth/adwords`.
- The token must be issued against a Google account that has access to at least one Google Ads Manager Account (used as the `login-customer-id` header).

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_contact_to_list_by_email` | Add a contact to a Customer Match user list by email (SHA-256 hashed locally). | `account_id`, `user_list_id`, `contact_email` |
| `create_ad_group_report` | Run a GAQL search report for the `ad_group` resource. | `account_id` |
| `create_ad_report` | Run a GAQL search report for the `ad_group_ad` resource. | `account_id` |
| `create_campaign_report` | Run a GAQL search report for the `campaign` resource. | `account_id` |
| `create_customer_list` | Create a UserList (CRM / Rule / Logical / Basic / Lookalike). | `account_id`, `name`, `list_type` |
| `create_customer_report` | Run a GAQL search report for the `customer` resource. | `account_id` |
| `create_report` | Run a GAQL search report against an arbitrary resource. | `account_id`, `resource` |
| `generate_keyword_ideas` | Generate keyword ideas via `KeywordPlanIdeaService.generateKeywordIdeas`. | `account_id`, `customer_client_id` |
| `list_account_id_options` | List customer resources directly accessible by the authenticated user. | (none) |
| `send_offline_conversion` | Create a ConversionAction (offline conversion tracking). | `account_id`, `name`, `type` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential. The Google Ads API also expects `login-customer-id` and `developer-token` headers; both are constructed inside each tool from `account_id` and `auth_data["developer_token"]` respectively.

## Limits & Quotas

- **Daily operations quota** depends on the developer-token access level (Test, Basic, Standard). Standard tokens allow 15,000 operations/day initially. See <https://developers.google.com/google-ads/api/docs/access-levels>.
- **Customer Match lists** typically take 6 to 12 hours to update after `add_contact_to_list_by_email` runs.
- **`generate_keyword_ideas`** counts against the same quota and may be rate-limited per minute on Basic-access tokens.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising. The error string includes the API status code and body excerpt.

## Maintainer

ModuleX core team.
