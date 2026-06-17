# Intercom

Customer-communication integration for Intercom: contacts (CRUD +
search), notes, tags, admins, conversations (CRUD + search), and
inbound/outbound messaging. All against `api.intercom.io` with the
`Intercom-Version: 2.12` header on every request.

## Authentication

### bearer_token Access Token

- **Single `bearer_token` schema.** Bearer-authed; the helper reads
  `token` (or `access_token`) from `auth_data`.
- Bearer env var: `INTERCOM_ACCESS_TOKEN`.
- `test_endpoint` hits GET `/me`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_contact` | One contact by id | `contact_id` |
| `search_contacts` | Field+operator+value search | `query_value` |
| `upsert_contact` | Create or update by email (2-call) | `email` |
| `create_note` | Note on a contact (auto-attributes to /me admin) | `contact_id`, `body` |
| `add_tag_to_contact` | Tag assignment | `contact_id`, `tag_id` |
| `list_tags` | All workspace tags | — |
| `list_admins` | All teammates | — |
| `get_conversation` | One conversation by id | `conversation_id` |
| `list_conversations` | Cursor-paginated list | — |
| `search_conversations` | Field+operator+value search | `query_value` |
| `send_incoming_message` | User-initiated message (auto user/lead role) | `contact_id`, `body` |
| `send_message_to_contact` | Admin-initiated message | `from_admin_id`, `to_contact_id`, `subject`, `body` |
| `reply_to_conversation` | Reply (user or admin) | `conversation_id`, `reply_type`, `body` |

## Multi-call workflows

Three actions internally chain two API calls — preserved from
legacy:

- **`upsert_contact`**: POST `/contacts/search?email` → if found, PUT
  `/contacts/{id}`; else POST `/contacts`. Tracks the branch in
  `action_type` ("created" | "updated").
- **`create_note`**: GET `/me` to discover the current admin's id,
  then POST `/contacts/{id}/notes` attributing the note to that admin.
- **`send_incoming_message`**: GET `/contacts/{id}` to discover the
  role ("user" or "lead"), then POST `/conversations` with the
  correct `from.type`.

Each surfaces as a single `success`/`error` boundary — the side call's
failure is included in the error message.

## Limits & Quotas

- `per_page` is clamped at 150 (Intercom's max).
- `reply_to_conversation` allows up to 10 attachment URLs (Intercom's
  max).
- Failures (non-2xx, exceptions) surface as `success=False` + `error`.

## Maintainer

ModuleX core team.
