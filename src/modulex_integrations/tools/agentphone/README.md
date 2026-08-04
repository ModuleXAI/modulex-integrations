# AgentPhone

API-first voice and messaging for AI agents: provision SMS- and
voice-enabled phone numbers, place outbound voice calls and read their
transcripts, send SMS/MMS/iMessage plus tapback reactions, manage
conversations and contacts, and track account usage — over the
AgentPhone REST API (`api.agentphone.ai`).

## Authentication

### API Key

- Sign up or log in at <https://agentphone.ai>, open the dashboard, and
  go to the **API Keys** section to create or copy your key.
- Required env var: `AGENTPHONE_API_KEY`.
- The key is sent as `Authorization: Bearer <api_key>`; the credential
  is validated with a `GET /v1/usage` probe.

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (the modulex `api_key` injection
convention, not the `auth_type`/`auth_data` pair).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_number` | Provision a new SMS- and voice-enabled phone number | (none) |
| `list_numbers` | List all provisioned phone numbers | (none) |
| `release_number` | Release (delete) a phone number — irreversible | `number_id` |
| `get_number_messages` | Fetch messages received on a phone number | `number_id` |
| `create_call` | Initiate an outbound voice call from an agent | `agent_id`, `to_number` |
| `list_calls` | List voice calls (status/direction/type/search filters) | (none) |
| `get_call` | Fetch a call and its full transcript turns | `call_id` |
| `get_call_transcript` | Get the flat ordered transcript for a call | `call_id` |
| `list_conversations` | List conversations (message threads) | (none) |
| `get_conversation` | Get a conversation with its recent messages | `conversation_id` |
| `update_conversation` | Set or clear conversation metadata | `conversation_id` |
| `get_conversation_messages` | Get paginated messages for a conversation | `conversation_id` |
| `send_message` | Send an outbound SMS or iMessage | `agent_id`, `to_number`, `body` |
| `react_to_message` | Send an iMessage tapback reaction | `message_id`, `reaction` |
| `create_contact` | Create a new contact | `phone_number`, `name` |
| `list_contacts` | List contacts (optional name/number search) | (none) |
| `get_contact` | Fetch a single contact by ID | `contact_id` |
| `update_contact` | Update a contact's fields | `contact_id` |
| `delete_contact` | Delete a contact by ID | `contact_id` |
| `get_usage` | Current plan limits, number usage, and counters | (none) |
| `get_usage_daily` | Daily usage breakdown for the last N days | (none) |
| `get_usage_monthly` | Monthly usage aggregation for the last N months | (none) |

## Limits & Quotas

- All calls go to `https://api.agentphone.ai/v1` over HTTPS with a 30s
  client timeout.
- List endpoints use `limit`/`offset` (numbers, calls, conversations,
  contacts) and return `has_more` plus `total`; message endpoints use
  `limit` with `before`/`after` ISO 8601 cursors and return `has_more`.
- Plan-level ceilings (numbers, messages per month, voice minutes per
  month, max call duration, concurrent calls) are readable through
  `get_usage` — check them before bulk sends or calls.
- `release_number` and `delete_contact` are irreversible.
- `react_to_message` works on iMessage conversations only.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. The API's
  `detail`/`message` payload is unwrapped into the error string.

## Maintainer

ModuleX core team.
