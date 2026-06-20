# Lemlist

Manage sales-engagement outreach against the Lemlist REST API
(`api.lemlist.com`): retrieve campaign activities and replies, look up
lead details, and send emails through the Lemlist inbox.

## Authentication

One method supported — an API key sent as HTTP Basic auth (empty
username, the key as the password).

### API Key

- In Lemlist, open **Settings -> Team Settings -> Integrations** and
  click **Generate** to create an API key. The key is shown only once,
  so copy it immediately.
- Required env var: `LEMLIST_API_KEY`.
- The runtime sends it as `Authorization: Basic <base64(":" + api_key)>`
  and validates it with a `GET /api/team` probe.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_activities` | Retrieve campaign activities (opens, clicks, replies, bounces, etc.) | none |
| `get_lead` | Look up a lead by email address or lead ID | `lead_identifier` |
| `send_email` | Send an email to a contact through the Lemlist inbox | `send_user_id`, `send_user_email`, `send_user_mailbox_id`, `contact_id`, `lead_id`, `subject`, `message` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Pagination**: `get_activities` accepts `limit` (max 100, default
  100) and `offset` for paging through campaign activity.
- **Send eligibility**: `send_email` requires a configured Lemlist
  sender user, mailbox, and an existing contact/lead — the values come
  from your Lemlist workspace.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
