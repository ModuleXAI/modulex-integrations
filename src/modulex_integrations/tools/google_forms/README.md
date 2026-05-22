# Google Forms

Create, update, and read Google Forms and their responses via the Google Forms REST API (`forms.googleapis.com/v1`).

## Authentication

Authenticate via Google OAuth 2.0. The user is redirected to Google's consent screen and grants access to manage forms and read responses.

### OAuth2 Authentication

- Create an OAuth 2.0 Client ID in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials). Choose **Web application** as the application type.
- Register `https://api.modulex.dev/credentials/oauth2/callback` as an authorized redirect URI.
- Enable the **Google Forms API** for your Google Cloud project at <https://console.cloud.google.com/apis/library/forms.googleapis.com>.
- Required env vars (only for self-hosted OAuth apps — the ModuleX-hosted default fills these automatically):
  - `GOOGLE_FORMS_OAUTH2_CLIENT_ID` (format: `xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com`)
  - `GOOGLE_FORMS_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx`)
- Scopes requested:
  - `https://www.googleapis.com/auth/forms.body` — manage form content (create, update, read).
  - `https://www.googleapis.com/auth/forms.responses.readonly` — read form responses.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_form` | Creates a new Google Form with the specified title and optional document title. | `title` |
| `create_text_question` | Creates a new text question (short or paragraph) in an existing Google Form via batchUpdate. | `form_id`, `title`, `description`, `index`, `paragraph` |
| `get_form` | Gets information about a Google Form, including its title, settings, and items. | `form_id` |
| `get_form_response` | Gets a single response from a Google Form by response ID. | `form_id`, `response_id` |
| `list_form_responses` | Lists all responses submitted to a Google Form. | `form_id` |
| `update_form_title` | Updates the title of an existing Google Form via batchUpdate. | `form_id`, `title` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- The Google Forms API enforces per-project quotas administered through Google Cloud. Default quota is **300 read requests per minute per project** and **60 write requests per minute per project** (subject to change — see <https://developers.google.com/forms/api/limits>).
- Per-user quotas may apply for OAuth client credentials with many concurrent users.
- A `400 Bad Request` is returned when `index` for `create_text_question` is outside `[0..N)` where N is the current item count.
- **Error model:** non-2xx responses from the API raise `httpx.HTTPStatusError`, which the ModuleX runtime surfaces as a failed tool call with the original API error text included.

## Maintainer

ModuleX core team.
