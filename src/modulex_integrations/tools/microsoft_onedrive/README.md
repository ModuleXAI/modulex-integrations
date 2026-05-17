# Microsoft OneDrive

Access and manage files in Microsoft OneDrive through the Microsoft Graph API
(`https://graph.microsoft.com/v1.0`) — search, list, upload, download files,
create folders, and produce sharing links using a user's delegated
permissions.

## Authentication

This integration supports a single auth method: Microsoft Entra (Azure AD)
OAuth 2.0 against the Microsoft Graph API. The end user signs in with their
Microsoft account; ModuleX obtains a delegated access token plus a refresh
token via the `offline_access` scope.

### OAuth2 Authentication

- Register an app at <https://entra.microsoft.com> -> **App registrations** ->
  **New registration**.
- Choose supported account types (commonly *Accounts in any organizational
  directory and personal Microsoft accounts*).
- Add the redirect URI under **Web**:
  `https://api.modulex.dev/credentials/oauth2/callback`.
- Under **API permissions**, add Microsoft Graph delegated permissions:
  `Files.ReadWrite.All`, `Sites.ReadWrite.All`, `User.Read`, `offline_access`.
- Under **Certificates & secrets**, create a client secret and copy its value.
- Copy the **Application (client) ID** as well.
- Required env vars:
  - `MICROSOFT_ONEDRIVE_OAUTH2_CLIENT_ID` (format:
    `00000000-0000-0000-0000-000000000000`)
  - `MICROSOFT_ONEDRIVE_OAUTH2_CLIENT_SECRET` (sensitive)
- Scopes requested: `Files.ReadWrite.All Sites.ReadWrite.All User.Read offline_access`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_folder` | Create a new folder in a drive (root, an existing folder, or a shared drive reference). | `folder_name` |
| `create_link` | Create a sharing link (`view`, `edit`, or `embed`) for a DriveItem. | `drive_item_id`, `type` |
| `download_file` | Download a file (by ID or path), optionally converting to PDF or HTML. Returns base64 content and a `/tmp` path. | `new_file_name` |
| `find_file_by_name` | Search for a file or folder by name. | `name` |
| `get_excel_table` | Retrieve a named table from an Excel (.xlsx) workbook. | `item_id`, `table_name` |
| `get_file_by_id` | Retrieve metadata for a single DriveItem by its ID. | `file_id` |
| `list_files_in_folder` | List the immediate children of a folder. | `folder_id` |
| `list_my_drives` | List every drive the signed-in user has access to (personal OneDrive plus shared/SharePoint drives). | _none_ |
| `list_shared_folder_reference_options` | List available shared folder references usable as input to `create_folder`'s `shared_folder_reference`. | _none_ |
| `search_files` | Full-text search across the user's drive. | `q` |
| `upload_file` | Upload a file to OneDrive by providing a publicly-accessible source URL. | `upload_folder_id`, `file_url`, `filename` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Microsoft Graph applies per-app and per-user throttling — bursty workloads
  may receive `429` responses with `Retry-After` hints. See
  <https://learn.microsoft.com/en-us/graph/throttling> for current limits.
- `download_file` saves the file under the backend's `/tmp` directory **and**
  returns the content base64-encoded. For very large files, prefer routing
  through the workflow-engine layer.
- `upload_file` accepts only a publicly-accessible source URL. Uploading from
  a local `/tmp` path is not supported.
- Dynamic dropdowns for folder, file, drive, and table selection are not
  exposed — supply IDs and names directly. Use `list_my_drives`,
  `list_files_in_folder`, `search_files`, or `find_file_by_name` to discover
  IDs.
- Webhook-style notifications (new file / new folder created) are not exposed
  in this integration; route those needs to the workflow-engine layer.
- **Error model**: non-2xx responses, timeouts, and unexpected exceptions are
  caught and returned as `success=False` + `error` rather than raising. Agents
  should branch on the error string to decide whether to retry or surface to
  the user.

## Maintainer

ModuleX core team.
