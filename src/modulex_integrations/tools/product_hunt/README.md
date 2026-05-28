# Product Hunt

Discover and explore tech products, topics, and community posts via the Product Hunt GraphQL API (`api.producthunt.com/v2/api/graphql`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth application at <https://www.producthunt.com/v2/oauth/applications>.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `public`, `private`
- Required env vars (only for custom OAuth apps):
  - `PRODUCT_HUNT_OAUTH2_CLIENT_ID` (format: 40-char hex string)
  - `PRODUCT_HUNT_OAUTH2_CLIENT_SECRET` (format: 40-char hex string, sensitive)

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_topic_options` | Retrieves available topic options with slug and display name | _(none)_ |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Product Hunt API v2 rate limits are not publicly documented in detail; typical observed limit is approximately 450 requests per 15-minute window per token.
- No per-request pricing; API access is free for authorized applications.
- Error model: non-2xx responses and GraphQL-level errors are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
