# NeverBounce

Real-time email verification and account credit lookup against the
NeverBounce v4 REST API (`api.neverbounce.com/v4`). Classifies an
address as valid, invalid, catch-all, disposable, or unknown and
surfaces role-account and free-provider flags.

## Authentication

NeverBounce authenticates by passing the API key as a `key` query
parameter on every request. The credential is validated against
`GET /v4/account/info`, which reads the account balance without
consuming a verification credit.

### API Key

- Sign in at <https://app.neverbounce.com>, open **Settings → API**,
  generate or copy your key.
- Required env var: `NEVERBOUNCE_API_KEY` (format:
  `secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `verify_email` | Verify the deliverability of an email address (uses one credit) | `email` |
| `get_credits` | Read remaining paid and free verification credits | _(none)_ |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Rate limit**: ~60 requests/min on standard plans.
- **Credits**: each `verify_email` call consumes one verification
  credit; `get_credits` is free and does not consume credits.
- **Error model**: the v4 API returns HTTP 200 even for API-level
  failures and signals the outcome via the response envelope's
  `status` field. A non-`"success"` status, a non-2xx HTTP response,
  or a timeout is caught and returned as `success=False` + `error`
  rather than raising. Plan for retries on the agent side based on the
  error string.

## Maintainer

ModuleX core team.
