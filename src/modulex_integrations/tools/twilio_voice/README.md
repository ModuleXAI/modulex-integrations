# Twilio Voice

Make and manage phone calls with Twilio Programmable Voice — place
outbound calls driven by TwiML, list call logs, and retrieve call
recordings against the Twilio REST API (`api.twilio.com/2010-04-01`).

## Authentication

Twilio uses HTTP Basic authentication: your **Account SID** is the
username and your **Auth Token** is the password. In modulex terms this
maps to the `api_key` convention — the Auth Token is injected as
`api_key`, and the Account SID is supplied to each action as
`account_sid`. The credential test fetches the Account resource.

### Account SID & Auth Token

- Sign in to the [Twilio Console](https://console.twilio.com).
- Copy your **Account SID** (starts with `AC`) from the dashboard.
- Reveal and copy your **Auth Token**.
- Required env vars: `TWILIO_ACCOUNT_SID`
  (format: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) and
  `TWILIO_AUTH_TOKEN`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `make_call` | Place an outbound call with TwiML instructions or a TwiML URL | `to`, `from`, `account_sid` |
| `list_calls` | Retrieve call logs filtered by number, status, and date range | `account_sid` |
| `get_recording` | Fetch recording metadata and media URL by recording SID | `recording_sid`, `account_sid` |

Every tool takes an additional `api_key` parameter (the Twilio Auth
Token) that the runtime fills in from the resolved credential. The
`account_sid` parameter is likewise resolved from the credential data.
For `make_call`, provide either `twiml` (raw TwiML XML) or a `url`
pointing at hosted TwiML instructions.

## Limits & Quotas

- **Concurrency**: outbound call throughput depends on your account
  tier and number of phone numbers; long calls and the call queue are
  subject to Twilio's per-account limits.
- **List pagination**: `list_calls` accepts `page_size` (max 1000,
  default 50); when `include_recordings` is enabled it issues one extra
  request per call that has recordings.
- **Pricing**: per-minute voice rates and per-recording charges vary by
  destination and feature — see Twilio's pricing pages.
- **Error model**: non-2xx responses, timeouts, and Twilio
  `error_code`/`message` failures are caught and returned as
  `success=False` + `error` rather than raising. Plan retries on the
  agent side based on the error string.

## Maintainer

ModuleX core team.
