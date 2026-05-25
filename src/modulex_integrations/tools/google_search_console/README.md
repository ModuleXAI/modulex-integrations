# Google Search Console

Access Google Search Console search analytics and URL indexing via the
Search Console API (`searchconsole.googleapis.com`) and the Indexing API
(`indexing.googleapis.com`).

## Authentication

### OAuth2 Authentication

- Create OAuth credentials at <https://console.cloud.google.com/apis/credentials>.
- Required scopes: `https://www.googleapis.com/auth/webmasters.readonly`,
  `https://www.googleapis.com/auth/indexing`.
- Redirect URI to register: `https://api.modulex.dev/credentials/oauth2/callback`.
- Env vars (only for custom OAuth app): `GOOGLE_SEARCH_CONSOLE_OAUTH2_CLIENT_ID`,
  `GOOGLE_SEARCH_CONSOLE_OAUTH2_CLIENT_SECRET`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `retrieve_site_performance_data` | Fetches search analytics from Google Search Console for a verified site | `site_url`, `start_date`, `end_date` |
| `submit_url_for_indexing` | Sends a URL update notification to the Google Indexing API | `site_url` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth credential.

## Limits & Quotas

- **Search Analytics API**: 1,200 queries per minute per project (default quota).
- **Indexing API**: 200 publish requests per day per site property (standard quota).
- **Error model**: non-2xx responses are caught and returned as `success=False` + `error`
  rather than raising.

## Maintainer

ModuleX core team.
