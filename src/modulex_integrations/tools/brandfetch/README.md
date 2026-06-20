# Brandfetch

Look up brand assets, logos, colors, fonts, and company firmographics by
domain, ticker, ISIN, or crypto symbol — and resolve brand names to
domains — against the Brandfetch REST API (`api.brandfetch.io`).

## Authentication

One method supported. The credential is validated against
`GET /v2/brands/brandfetch.com`, a free lookup that does not count
toward your usage quota.

### API Key

- Sign up or log in at <https://developers.brandfetch.com>, open your
  dashboard, and copy your API key.
- Required env var: `BRANDFETCH_API_KEY`.
- The key is sent as `Authorization: Bearer <key>` on every request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_brand` | Retrieve brand assets (logos, colors, fonts) and company info by domain, ticker, ISIN, or crypto symbol | `identifier` |
| `search` | Search for brands by name and return matching domains and icons | `name` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Rate limit**: approximately 30 requests/minute.
- **Brand API** (`get_brand`): metered per request on paid tiers;
  requests for the `brandfetch.com` domain are free.
- **Brand Search API** (`search`): free under fair use (up to ~500,000
  requests/month).
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
