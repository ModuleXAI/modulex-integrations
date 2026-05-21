# Crunchbase

Access Crunchbase company and organization data for business intelligence and research via the Crunchbase REST API (`api.crunchbase.com/v4/data`).

## Authentication

### API Key Authentication

- Sign in at <https://data.crunchbase.com> and navigate to your account settings or API key management.
- Required env var: `CRUNCHBASE_USER_KEY` (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- The key is sent as the `X-cb-user-key` header on every request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_organization` | Retrieve details about an organization by UUID or permalink | `entity_id` |
| `search_organizations` | Search for organizations based on specified criteria | `field_ids` |

Every tool takes an additional `user_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- Rate limits depend on your Crunchbase plan tier (Basic, Pro, Enterprise).
- Enterprise plans typically allow higher request volumes; check your account dashboard for current limits.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
