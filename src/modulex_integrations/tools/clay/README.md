# Clay

Push records into a [Clay](https://www.clay.com) table through that
table's inbound webhook so Clay can run its data-enrichment waterfall
on prospects and accounts.

## Authentication

Clay table webhooks accept HTTP POST requests at a per-table URL. A
table may optionally require an auth token, sent in the
`x-clay-webhook-auth` header — most webhooks do not require one.

### Webhook Auth Token

- In a Clay workbook, click **+ Add**, search for **Webhooks**, then
  **Monitor webhook**.
- Copy the webhook URL Clay shows for the table — pass it as the
  `webhook_url` action parameter.
- If the table has webhook authentication enabled, copy the auth token
  Clay displays (shown only once) and configure it as the credential
  (`CLAY_WEBHOOK_AUTH_TOKEN`). Otherwise leave it blank.

The token is injected into each tool call as the `api_key` parameter;
the runtime attaches it as `x-clay-webhook-auth` only when it is
non-empty.

## Tools

| name | description | required params |
| --- | --- | --- |
| `populate` | Send a record to a Clay table webhook for enrichment | `webhook_url`, `data` |

`data` is a JSON object whose keys map to the Clay table's column names
(for example `name`, `email`, `company`, `domain`). The record is sent
under a `data` field in the request body.

## Limits & Quotas

- **Asynchronous enrichment**: the webhook acknowledges receipt
  immediately; Clay runs its enrichment waterfall afterward, so the
  enriched columns appear inside Clay, not in the tool response.
- **Response shape**: the tool returns whatever the webhook
  acknowledges (`data`) plus transport `metadata` (HTTP status, status
  text, response headers, a call-time ISO-8601 UTC timestamp, and the
  content type). A non-JSON acknowledgment is wrapped as
  `{"message": "<text>"}`.
- **Error model**: non-2xx responses, timeouts, and unexpected
  exceptions are caught and returned as `success=False` + `error`
  rather than raising.

## Maintainer

ModuleX core team.
