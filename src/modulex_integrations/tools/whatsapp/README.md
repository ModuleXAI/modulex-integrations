# WhatsApp

Send WhatsApp messages through the WhatsApp Cloud API (Meta Graph API,
`graph.facebook.com`). Deliver plain-text messages with optional link
previews directly to recipients on WhatsApp.

## Authentication

One method supported: a WhatsApp Business API access token used as the
bearer credential on every request.

### API Key (WhatsApp Business access token)

- Go to <https://developers.facebook.com> and open your Meta app, then add
  the **WhatsApp** product and configure a Business Phone Number.
- Copy the **WhatsApp Business API access token**. A temporary token is
  available in the dashboard; generate a permanent System User token for
  production use.
- Required env var: `WHATSAPP_ACCESS_TOKEN` (sensitive).
- Each send call also needs your **WhatsApp Business Phone Number ID**,
  passed as the `phone_number_id` action parameter.

## Tools

| name | description | required params |
| --- | --- | --- |
| `send_message` | Send a text message through the WhatsApp Cloud API | `phone_number`, `message`, `phone_number_id` |

`send_message` also accepts an optional `preview_url` (boolean) to render a
link preview for the first URL in the message. Every tool takes an
additional `api_key` parameter that the runtime fills in from the resolved
credential (the WhatsApp Business access token, sent as
`Authorization: Bearer`).

## Limits & Quotas

- **Messaging tiers**: WhatsApp enforces per-business-phone-number
  conversation/message throughput tiers (1K, 10K, 100K, unlimited
  business-initiated conversations per 24h), scaling with quality rating.
- **24-hour window**: free-form text messages can only be sent inside an
  open 24-hour customer service window; outside it, an approved message
  template is required (template sending is not exposed by this tool).
- **Error model**: non-2xx responses and timeouts are caught and returned
  as `success=False` + `error` rather than raising. A successful send that
  lacks a message ID is also reported as `success=False`. Plan for retries
  on the agent side based on the error string.

## Maintainer

ModuleX core team.
