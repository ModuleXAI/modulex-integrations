# Ahrefs

SEO backlink analysis and referring domain data via the Ahrefs REST API (`api.ahrefs.com/v3`).

## Authentication

### API Key (bearer token)

- Sign in to Ahrefs as a workspace owner or admin and create a key under
  **Account settings → API keys** ([docs](https://docs.ahrefs.com/en/api/docs/api-keys-creation-and-management)).
- Requires an eligible paid Ahrefs plan; each key is valid for 1 year.
- Env var: `AHREFS_API_TOKEN` — the Ahrefs API v3 key.
- Sent on every request as `Authorization: Bearer <key>`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_backlinks` | Get the backlinks for a domain or URL with details for the referring pages | `target`, `select` |
| `get_backlinks_one_per_domain` | Get one backlink with the highest ahrefs_rank per referring domain for a target URL or domain | `target`, `select` |
| `get_referring_domains` | Get the referring domains that contain backlinks to the target URL or domain | `target`, `select` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved API-key credential.

## Limits & Quotas

- Rate limits depend on your Ahrefs subscription plan (Lite, Standard, Advanced, Enterprise).
- API usage is metered against monthly "API rows" quota included in your plan.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
