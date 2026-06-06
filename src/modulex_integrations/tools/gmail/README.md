# Gmail

Gmail integration via the Gmail REST v1 API
(`www.googleapis.com/gmail/v1`). Send email + list labels. Pure
HTTP — does **not** depend on the `google-api-python-client` SDK.

## Authentication

### OAuth 2.0 — and bearer_token Access Token

- **Paired `oauth2 + bearer_token` schemas.** Both Bearer-authed;
  the helper accepts `access_token` (oauth2), `token` or
  `bearer_token` (bearer_token) out of `auth_data`.
- OAuth env vars: `GMAIL_OAUTH2_CLIENT_ID`,
  `GMAIL_OAUTH2_CLIENT_SECRET` (both `only_for_custom=True`).
- Bearer env var: `GMAIL_ACCESS_TOKEN`.
- OAuth flow uses Google's standard endpoints with two Gmail
  scopes (`send`, `labels`).
- Both `test_endpoint`s GET `/users/me/labels`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `send_message` | Send a new email | `to`, `subject`, `body` |
| `list_labels` | All Gmail labels (system + user-created) | — |

## Limits & Quotas

- `send_message` builds a base64url-encoded MIME message locally
  (no SDK dep).
- Sending is limited to 500 messages/day (consumer accounts) or
  2000/day (Google Workspace).
- 60s timeout for send, 30s for label listing.

## Maintainer

ModuleX core team.
