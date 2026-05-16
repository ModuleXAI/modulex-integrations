# Gmail

Gmail integration via the Gmail REST v1 API
(`www.googleapis.com/gmail/v1`). Send/read/search/list/draft + label
management + archive/trash. Pure HTTP — does **not** depend on the
`google-api-python-client` SDK.

## Authentication

### OAuth 2.0 — and bearer_token Access Token

- **Paired `oauth2 + bearer_token` schemas.** Both Bearer-authed;
  the helper accepts `access_token` (oauth2), `token` or
  `bearer_token` (bearer_token) out of `auth_data`.
- OAuth env vars: `GMAIL_OAUTH2_CLIENT_ID`,
  `GMAIL_OAUTH2_CLIENT_SECRET` (both `only_for_custom=True`).
- Bearer env var: `GMAIL_ACCESS_TOKEN`.
- OAuth flow uses Google's standard endpoints with the four Gmail
  scopes (`send`, `readonly`, `modify`, `labels`).
- Both `test_endpoint`s GET `/users/me/profile`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `send_message` | Send a new email | `to`, `subject`, `body` |
| `read_message` | Read a message by ID | `message_id` |
| `search_messages` | Search via Gmail query syntax | `query` |
| `list_messages` | List messages from labels/folders | — |
| `create_draft` | Create an email draft | `to`, `subject`, `body` |
| `mark_as_read` | Remove UNREAD label | `message_id` |
| `mark_as_unread` | Add UNREAD label | `message_id` |
| `archive_message` | Remove INBOX label | `message_id` |
| `unarchive_message` | Add INBOX label | `message_id` |
| `delete_message` | Move to Trash | `message_id` |
| `add_label` / `remove_label` | Add/remove labels | `message_id`, `label_ids` |
| `list_labels` | All Gmail labels (system + user-created) | — |

## Multi-call workflows

`search_messages` and `list_messages` both do an **N+1 metadata
fetch**: GET `/messages?q=…` returns IDs only, then for each ID GET
`/messages/{id}?format=metadata&metadataHeaders=Subject,From,Date` to
pull the displayable header values. Preserved from legacy. The
alternative (`history.list`) needs a different OAuth scope.

## Limits & Quotas

- `send_message` and `create_draft` build base64url-encoded MIME
  messages locally (no SDK dep).
- `max_results` is clamped at 500 (Gmail's max per request).
- Sending is limited to 500 messages/day (consumer accounts) or
  2000/day (Google Workspace).
- 60s timeout for send/draft, 30s for everything else.

## Maintainer

ModuleX core team.
