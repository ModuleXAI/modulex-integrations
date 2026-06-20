# Wiza

Find, enrich, and verify B2B contact data with Wiza — prospect search,
company enrichment, individual contact reveal (verified emails and
phone numbers), and credit-balance lookup against the Wiza REST API
(`wiza.co/api`).

## Authentication

Wiza authenticates with a single API key sent as
`Authorization: Bearer <api_key>`. The credential is validated against
`GET /api/meta/credits`.

### API Key

- Log in to your Wiza account at <https://app.wiza.co>.
- Open **Settings → API** and generate a new API key (or copy an
  existing one).
- Required env var: `WIZA_API_KEY`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `prospect_search` | Search prospects by person, company, and financial filters | _(none — all filters optional)_ |
| `company_enrichment` | Enrich a company by name, domain, or LinkedIn identifier | _(at least one identifier)_ |
| `individual_reveal` | Reveal verified email + phone for a contact (starts and polls the reveal) | `enrichment_level` |
| `get_credits` | Read remaining email, phone, export, and API credits | _(none)_ |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Rate limit**: ~30 requests/minute (43,200/day) per key.
- **Credits**: usage is metered in API credits — 2 credits per valid
  email and 5 per phone on `individual_reveal`, 2 credits per
  successful `company_enrichment`; `prospect_search` and `get_credits`
  consume no credits. Credits are charged only when data is returned.
- **Asynchronous reveals**: `individual_reveal` starts a reveal and
  polls `GET /api/individual_reveals/{id}` until the status is terminal
  (`finished`/`failed`) or a 120-second window elapses.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
