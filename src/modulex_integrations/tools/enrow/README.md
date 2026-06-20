# Enrow

Find and verify B2B email addresses with triple-verified accuracy
against the Enrow REST API (`api.enrow.io`). Resolve a professional
email from a full name and company, or check the deliverability of an
existing address — including deterministic handling of catch-all
domains.

## Authentication

Authenticate with your Enrow API key, passed as the `x-api-key`
header. The credential is validated against `GET /account/info`.

### API Key

- Sign in to your Enrow account at <https://enrow.io>, open the
  **Integrations** section, and copy your API key (or create a new
  one).
- Required env var: `ENROW_API_KEY`.

The runtime injects the key as the `api_key` parameter on every tool
call (the modulex `api_key` injection convention — not the
`auth_type`/`auth_data` pair used by some other integrations).

## Tools

| name | description | required params |
| --- | --- | --- |
| `find_email` | Find a verified B2B email from a full name and company domain/name | `fullname` |
| `verify_email` | Verify the deliverability of an email address | `email` |

For `find_email`, supply `company_domain` (preferred) or
`company_name`. Both actions are asynchronous on Enrow's side: the
tool submits the job and polls the result endpoint (HTTP 202 while
running, HTTP 200 on completion) until it resolves or a ~120-second
polling cap is reached — all inside a single call.

## Limits & Quotas

- **Rate limit**: roughly ~50 requests/second; keep bursts modest,
  especially during result polling.
- **Pricing** (approx., per the Enrow Starter plan): `find_email`
  charges 1 credit per valid email found; `verify_email` charges
  0.25 credits per verification.
- **Error model**: non-2xx responses, request timeouts, and an
  expired polling window are caught and returned as `success=False`
  + `error` rather than raising. Plan retries on the agent side based
  on the error string.

## Maintainer

ModuleX core team.
