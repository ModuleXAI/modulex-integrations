# Google Docs

Create, read, and edit Google Docs documents via the Google Docs API (`docs.googleapis.com/v1`).

## Authentication

### OAuth2 Authentication

- Create OAuth credentials at the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
- Enable the Google Docs API in your project. The Google Drive API must also be
  enabled so the OAuth token can be validated against the Drive `about`
  endpoint with the `drive.file` scope.
- Required env vars: `GOOGLE_DOCS_OAUTH2_CLIENT_ID` and `GOOGLE_DOCS_OAUTH2_CLIENT_SECRET` (only when using your own OAuth app).
- Scopes requested: `https://www.googleapis.com/auth/drive.file`.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`.

> **Per-file access.** `drive.file` grants access only to documents this
> application created, or that the user has explicitly shared with it through a
> file picker. Actions that take a `doc_id` for a pre-existing document the app
> did not create will fail until that document is shared with the app.

## Tools

| name | description | required params |
| --- | --- | --- |
| `append_image` | Append an image to the end of a Google Docs document | `doc_id`, `image_uri` |
| `append_text` | Append text to an existing Google Docs document | `doc_id`, `text` |
| `create_document` | Create a new Google Docs document with optional text content | `title` |
| `get_document` | Get the contents of a Google Docs document | `doc_id` |
| `get_tab_content` | Get the content of specific tabs in a Google Docs document | `doc_id`, `tab_ids` |
| `insert_page_break` | Insert a page break into a Google Docs document at a specified index | `doc_id` |
| `insert_table` | Insert a table into a Google Docs document at a specified index | `doc_id`, `rows`, `columns` |
| `insert_text` | Insert text into a Google Docs document at a specified index | `doc_id`, `text` |
| `replace_image` | Replace an existing image in a Google Docs document with a new one | `doc_id`, `image_id`, `image_uri` |
| `replace_text` | Replace all instances of matched text in a Google Docs document | `doc_id`, `text_to_replace`, `new_text` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Google Docs API: 300 read requests per minute per user, 60 write requests per minute per user.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
