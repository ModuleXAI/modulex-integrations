# Canva

Design platform integration for creating, listing, exporting, and importing
visual content via the Canva Connect REST API (`api.canva.com/rest/v1`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at the [Canva Developer Portal](https://www.canva.dev/docs/connect/quick-start/).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars (only when bringing your own OAuth app):
  - `CANVA_OAUTH2_CLIENT_ID` — OAuth App Client ID
  - `CANVA_OAUTH2_CLIENT_SECRET` — OAuth App Client Secret
- Scopes requested: `design:content:read`, `design:content:write`, `design:meta:read`, `asset:read`, `asset:write`

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_design` | Creates a new Canva design with preset or custom dimensions | `design_type` |
| `create_design_import_job` | Starts a job to import an external file as a new Canva design | `title`, `file_url` |
| `export_design` | Starts a job to export a Canva design to a file format | `design_id`, `format_type` |
| `list_designs` | Lists designs owned by or shared with the authenticated Canva user | (none) |
| `upload_asset` | Uploads an asset to Canva from a URL | `name`, `file_url` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth2 credential.

## Limits & Quotas

- **Rate limits**: Canva Connect API enforces per-app rate limits (varies by plan; typically 100 requests/minute for standard apps).
- **Export/Import jobs**: Asynchronous — the tool polls until completion (up to ~60 seconds). Large designs may take longer.
- **File uploads**: Maximum file size varies by asset type (images up to 25 MB, videos up to 1 GB).
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
