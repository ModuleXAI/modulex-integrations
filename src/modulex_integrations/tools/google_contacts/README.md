# Google Contacts

Manage Google Contacts (People API v1) — create, list, get, update, and delete
the authenticated user's contacts, plus list Google Workspace directory people.
All calls go to `https://people.googleapis.com/v1`.

## Authentication

Google OAuth 2.0 is the only supported auth method. The runtime validates the
token by issuing `GET /people/me?personFields=names` and asserting
`resourceName` comes back in the response body.

### Google OAuth2

- Create or open an OAuth 2.0 Client at
  <https://console.cloud.google.com/apis/credentials>.
- Required env vars:
  - `GOOGLE_CONTACTS_OAUTH2_CLIENT_ID` (format:
    `xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.apps.googleusercontent.com`)
  - `GOOGLE_CONTACTS_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-xxxxxxxx…`)
- Register the redirect URI `https://api.modulex.dev/credentials/oauth2/callback`
  in the Google OAuth client.
- Requested scopes:
  - `https://www.googleapis.com/auth/contacts` — read/write the user's contacts.
  - `https://www.googleapis.com/auth/directory.readonly` — read Google
    Workspace directory people (only needed for `list_directory_contacts`).
- Enable the **People API** in the same Google Cloud project.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_contact` | Create a new contact in the authenticated user's Google Contacts. | `person_fields` |
| `delete_contact` | Delete a contact by its People API resource name (e.g. `people/c123…`). | `resource_name` |
| `get_contact` | Fetch a single contact by its People API resource name. | `resource_name`, `fields` |
| `list_contacts` | List every contact for the authenticated user (auto-paginates). | `fields` |
| `list_directory_contacts` | List contacts from the Google Workspace directory (domain contacts / profiles). | `fields`, `source` |
| `update_contact` | Update an existing contact; refreshes the latest etag first to avoid stale-update errors. | `resource_name`, `update_person_fields` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth2 credential — call sites never see the access
token.

## Limits & Quotas

- Google People API default quota: **90 reads/minute** and
  **60 writes/minute** per user, **1,200 reads/minute** per project. Higher
  limits available via Google Cloud quota request.
- `list_contacts` auto-paginates through `people/me/connections` — beware large
  contact directories (each page is 100 contacts by default; the implementation
  fetches every page in sequence).
- `list_directory_contacts` returns one page per call; supply `page_token` /
  `sync_token` from a previous response for pagination or incremental sync.
- `update_contact` performs an extra `GET` to refresh the etag before the
  `PATCH`. Stale-etag updates are rejected by Google with HTTP 400.
- **Error model**: non-2xx responses raise `httpx.HTTPStatusError`. The
  modulex runtime surfaces these as failed tool calls — plan for retries on the
  agent side if a transient 5xx is possible.

## Maintainer

ModuleX core team.
