# GoDaddy

Domain registration, availability checking, and management via the GoDaddy REST API (`api.godaddy.com/v1`).

## Authentication

### GoDaddy API Key + Secret

- Generate your API key and secret at <https://developer.godaddy.com/keys>.
- Required env vars:
  - `GODADDY_API_KEY` (format: `xxxxxxxxxxxxxxxx`)
  - `GODADDY_API_SECRET` (format: `xxxxxxxxxxxxxxxxxxxxxxxx`)
- Optional env var:
  - `GODADDY_API_URL` — defaults to `https://api.godaddy.com`. Set to `https://api.ote-godaddy.com` for the OTE test environment.
- Authorization header format: `sso-key <key>:<secret>`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `check_domain_availability` | Check the availability of a domain for purchase or transfer | `domain` |
| `list_domains` | List domains owned by the authenticated GoDaddy account | _(none)_ |
| `list_tlds_options` | Retrieve the list of available top-level domains (TLDs) | _(none)_ |
| `renew_domain` | Renew a domain registration in GoDaddy | `domain` |
| `suggest_domains` | Suggest available domain names based on given criteria | `query` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential (custom auth, token-style injection).

## Limits & Quotas

- **Production API**: 60 requests per minute per API key (per GoDaddy developer documentation).
- **OTE (test) API**: Lower rate limits; intended for development only.
- **Renewal actions** incur actual charges on the account.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
