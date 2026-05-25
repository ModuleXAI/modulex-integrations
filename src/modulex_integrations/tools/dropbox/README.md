# Dropbox

Cloud file storage, sharing, and collaboration via the Dropbox HTTP API (`api.dropboxapi.com/2`).

## Authentication

### OAuth2 Authentication

- Register an OAuth app at <https://www.dropbox.com/developers/apps>.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars (only for custom OAuth app): `DROPBOX_OAUTH2_CLIENT_ID`, `DROPBOX_OAUTH2_CLIENT_SECRET`
- Scopes requested: `files.metadata.read`, `files.metadata.write`, `files.content.read`, `files.content.write`, `sharing.read`, `sharing.write`, `account_info.read`

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_folder` | Create a new folder in the user's Dropbox | `name` |
| `search_files_folders` | Search for files and folders by name or content | `query` |
| `list_file_folders_in_a_folder` | List all files and subfolders in a specified folder | `path` |
| `delete_file_folder` | Permanently delete a file or folder from Dropbox | `path` |
| `move_file_folder` | Move a file or folder to a different location in Dropbox | `path_from`, `path_to` |
| `rename_file_folder` | Rename a file or folder in Dropbox | `path_from`, `new_name` |
| `create_a_text_file` | Create a new text file from plain text content | `name`, `content` |
| `create_or_append_to_a_text_file` | Append a line to an existing text file, or create the file if it does not exist | `name`, `content` |
| `create_update_share_link` | Create or update a public share link for a file or folder | `path` |
| `list_shared_links` | List shared links for a file or folder path | |
| `get_shared_link_metadata` | Get metadata for a shared link URL | `shared_link_url` |
| `list_file_revisions` | List revision history for a file | `path` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Rate limits**: Dropbox applies per-app and per-user rate limits. Individual apps are limited to approximately 25,000 HTTP requests per month for free-tier apps and higher for production apps.
- **List folder**: Maximum 2,000 entries per single request (pagination via cursor for more).
- **File upload**: Maximum 150 MB per single upload request (content upload endpoint).
- **Error model**: Non-2xx responses are caught and returned as `success=False` + `error` rather than raising. Plan for retries on 429 (rate limit) responses.

## Maintainer

ModuleX core team.
