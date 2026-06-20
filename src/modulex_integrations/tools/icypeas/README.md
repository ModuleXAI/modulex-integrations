# Icypeas

Find and verify professional email addresses against the Icypeas REST
API (`app.icypeas.com`). Resolve a likely professional email from a
person's name and company domain, or check whether an existing address
is valid and deliverable. Both operations run asynchronously: a job is
submitted, then the result is fetched by polling.

## Authentication

### API Key

- Sign in at <https://www.icypeas.com> (the app lives at
  <https://app.icypeas.com>), then open your account's API settings and
  generate or copy your key.
- Required env var: `ICYPEAS_API_KEY`.
- The key is sent as the raw `Authorization` header value (no `Bearer`
  prefix), alongside `Content-Type: application/json`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `find_email` | Find a professional email from a name and company domain/name | `domain_or_company` |
| `verify_email` | Verify whether an email address is valid and deliverable | `email` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (the modulex `api_key` injection
convention — not the `auth_type`/`auth_data` pair).

`find_email` also accepts optional `firstname` and `lastname` to
improve match accuracy.

## Limits & Quotas

- **Async polling**: each call submits a job, then polls the read
  endpoint roughly every 3 seconds for up to 120 seconds. If the job
  does not reach a terminal status in that window, the call returns
  `success=False` with an explanatory error.
- **Terminal statuses**: `FOUND`, `DEBITED`, `NOT_FOUND`,
  `DEBITED_NOT_FOUND`, `BAD_INPUT`, `INSUFFICIENT_FUNDS`, `ABORTED`. A
  clean no-match (`NOT_FOUND`) is still a successful run — `email` is
  simply `null` and, for verification, `valid` is `false`.
- **Rate limits**: approximately 60 requests/minute.
- **Pricing** (approx., per vendor pricing page): email finding ~1
  credit per found email; email verification ~0.1 credit per check.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
