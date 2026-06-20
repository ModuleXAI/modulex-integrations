# Granola

Retrieve meeting notes, summaries, attendees, calendar event details,
and transcripts from Granola through its REST API
(`public-api.granola.ai`).

## Authentication

### API Key

- A Granola Business plan is required to create API keys. Open
  **Settings → API / Developer**, create a key, and copy it.
- Required env var: `GRANOLA_API_KEY` (format:
  `grn_xxxxxxxxxxxxxxxxxxxxxxxx`).
- Sent on every request as `Authorization: Bearer <api_key>`.
- The credential is validated by listing a single folder
  (`GET /v1/folders?page_size=1`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_notes` | List meeting notes with optional date filters and pagination | none |
| `get_note` | Get a single note by ID (summary, attendees, calendar details, optional transcript) | `note_id` |
| `list_folders` | List folders, sorted alphabetically, with pagination | none |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (the modulex `api_key` injection
convention).

## Limits & Quotas

- The API only returns notes that have a generated AI summary and
  transcript; notes still processing or never summarized are omitted
  from list responses and return `404` on direct access.
- `page_size` accepts `1-30` (default `10`) for `list_notes` and
  `list_folders`.
- Rate limits are applied per user or workspace depending on the key's
  access scope; exceeding them returns `429 Too Many Requests`.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
