# Heroku

Cloud platform for building, deploying, and managing applications via the
Heroku Platform API (`api.heroku.com`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at <https://dashboard.heroku.com/account/applications>.
- Set redirect URI to `https://api.modulex.dev/credentials/oauth2/callback`.
- Scopes requested: `global`.
- Required env vars (only when bringing your own OAuth app):
  - `HEROKU_OAUTH2_CLIENT_ID` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
  - `HEROKU_OAUTH2_CLIENT_SECRET` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_apps` | List all apps accessible by the authenticated user | _(none)_ |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth credential.

## Limits & Quotas

- Heroku Platform API rate limit: 4,500 requests per hour per OAuth token.
- Rate limit headers: `RateLimit-Remaining` and `RateLimit-Reset` are returned
  on every response.
- Error model: non-2xx responses raise (Pattern A). The caller receives an
  `httpx.HTTPStatusError` surfaced by the modulex runtime.

## Maintainer

ModuleX core team.
