# AgentMail

API-first email for agents and automation: create inboxes, send and
receive messages, reply to and forward threads, manage drafts, and
organize conversations with labels — over the AgentMail REST API
(`api.agentmail.to`).

## Authentication

### API Key

- Sign up or log in at <https://agentmail.to>, open the dashboard, and
  go to the **API Keys** section to create or copy your key.
- Required env var: `AGENTMAIL_API_KEY`.
- The key is sent as `Authorization: Bearer <api_key>`; the credential
  is validated with a minimal `GET /v0/inboxes?limit=1` probe.

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (the modulex `api_key` injection
convention, not the `auth_type`/`auth_data` pair).

## Tools

| name | description | required params |
| --- | --- | --- |
| `send_message` | Send an email message from an inbox | `inbox_id`, `to`, `subject` |
| `reply_message` | Reply to an existing message | `inbox_id`, `message_id` |
| `forward_message` | Forward a message to new recipients | `inbox_id`, `message_id`, `to` |
| `list_threads` | List email threads (label/date filters) | `inbox_id` |
| `get_thread` | Get a thread and its messages | `inbox_id`, `thread_id` |
| `update_thread` | Add/remove labels on a thread | `inbox_id`, `thread_id` |
| `delete_thread` | Delete a thread (trash or permanent) | `inbox_id`, `thread_id` |
| `list_messages` | List messages in an inbox | `inbox_id` |
| `get_message` | Get a single message | `inbox_id`, `message_id` |
| `update_message` | Add/remove labels on a message | `inbox_id`, `message_id` |
| `create_draft` | Create a new draft | `inbox_id` |
| `list_drafts` | List drafts in an inbox | `inbox_id` |
| `get_draft` | Get a single draft | `inbox_id`, `draft_id` |
| `update_draft` | Update an existing draft | `inbox_id`, `draft_id` |
| `delete_draft` | Delete a draft | `inbox_id`, `draft_id` |
| `send_draft` | Send an existing draft | `inbox_id`, `draft_id` |
| `create_inbox` | Create a new inbox | (none) |
| `list_inboxes` | List all inboxes | (none) |
| `get_inbox` | Get a single inbox | `inbox_id` |
| `update_inbox` | Update an inbox display name | `inbox_id`, `display_name` |
| `delete_inbox` | Delete an inbox | `inbox_id` |

## Limits & Quotas

- All calls go to `https://api.agentmail.to/v0` over HTTPS with a 30s
  client timeout.
- List endpoints are paginated: pass `limit` and the returned
  `next_page_token` (via `page_token`) to page through results.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
