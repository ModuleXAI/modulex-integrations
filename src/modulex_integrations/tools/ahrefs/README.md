# Ahrefs

SEO backlink analysis and referring domain data via the Ahrefs REST API (`api.ahrefs.com/v3`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at [Ahrefs API OAuth](https://ahrefs.com/api/oauth).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `api`
- Required env vars (only for custom OAuth app):
  - `AHREFS_OAUTH2_CLIENT_ID` — OAuth App Client ID
  - `AHREFS_OAUTH2_CLIENT_SECRET` — OAuth App Client Secret

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_backlinks` | Get the backlinks for a domain or URL with details for the referring pages | `target`, `select` |
| `get_backlinks_one_per_domain` | Get one backlink with the highest ahrefs_rank per referring domain for a target URL or domain | `target`, `select` |
| `get_referring_domains` | Get the referring domains that contain backlinks to the target URL or domain | `target`, `select` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Rate limits depend on your Ahrefs subscription plan (Lite, Standard, Advanced, Enterprise).
- API usage is metered against monthly "API rows" quota included in your plan.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
