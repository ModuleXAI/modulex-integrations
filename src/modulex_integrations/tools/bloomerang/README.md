# Bloomerang

Nonprofit donor management and fundraising CRM platform integration against the Bloomerang REST API (`api.bloomerang.co/v2`).

## Authentication

### API Key Authentication

- Log in to your Bloomerang account and navigate to Settings > API Keys.
- Create a new API key or copy your existing one.
- Required env var: `BLOOMERANG_API_KEY` (format: alphanumeric key string).
- Documentation: <https://bloomerang.co/product/integrations-data-management/api/rest-api/>

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_constituent` | Creates a new constituent in Bloomerang | `type` |
| `create_donation` | Creates a new donation record in Bloomerang | `constituent_id`, `date`, `amount`, `fund_id`, `payment_method` |
| `add_interaction` | Adds an interaction to an existing constituent in Bloomerang | `constituent_id`, `date`, `subject`, `channel`, `purpose` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- No publicly documented rate limits for the Bloomerang REST API v2.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
