# ZeroBounce

Real-time email validation and deliverability checks against the
ZeroBounce v2 REST API (`api.zerobounce.net`). Flag invalid,
catch-all, spamtrap, abuse, and do-not-mail addresses before outreach,
and check the validation credits remaining on your account.

## Authentication

One method supported. The credential is validated against
`GET /v2/getcredits`, which returns a `Credits` balance for a valid
key.

### API Key

- Sign in at <https://www.zerobounce.net>, open your account and go to
  the **API** section, then copy your API key.
- Required env var: `ZEROBOUNCE_API_KEY`.

The key is passed to ZeroBounce as the `api_key` query parameter. Every
tool takes an additional `api_key` parameter that the runtime fills in
from the resolved credential.

## Tools

| name | description | required params |
| --- | --- | --- |
| `verify_email` | Validate an email address deliverability in real time (uses one credit) | `email` |
| `get_credits` | Retrieve the remaining validation credits for the account | _none_ |

## Limits & Quotas

- **`/validate`**: up to 80,000 requests per 10 seconds per key
  (~480,000/min).
- **`/getcredits`**: up to 80,000 requests per hour (100,000 for
  ZeroBounce ONE customers) before a temporary block.
- Each `verify_email` call consumes one validation credit.
- **Error model**: ZeroBounce can answer HTTP 200 with an
  `{"error": ...}` envelope (invalid key / out of credits), and
  `getcredits` signals an invalid key with `{"Credits": -1}`. Non-2xx
  responses, error envelopes, and timeouts are caught and returned as
  `success=False` + `error` rather than raising. Plan retries on the
  agent side based on the error string.

## Maintainer

ModuleX core team.
