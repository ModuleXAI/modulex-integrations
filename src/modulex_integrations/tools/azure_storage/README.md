# Azure Storage

Manage blobs and containers in Microsoft Azure Blob Storage via the Azure Blob
Storage REST API (`https://<account>.blob.core.windows.net`).

## Authentication

### Microsoft OAuth2 (recommended)

- Register an Azure AD application at the
  [Azure Portal App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
- Add redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Grant the application **Storage Blob Data Contributor** role on your storage
  account.
- Scopes requested: `https://storage.azure.com/user_impersonation`,
  `offline_access`
- Required env vars:
  - `AZURE_STORAGE_OAUTH2_CLIENT_ID` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
  - `AZURE_STORAGE_OAUTH2_CLIENT_SECRET`
  - `AZURE_STORAGE_ACCOUNT_NAME` (your storage account name, e.g. `mystorageaccount`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_container` | Create a new container under the specified storage account | `container_name` |
| `delete_blob` | Delete a specific blob from a container in Azure Storage | `container_name`, `blob_name` |
| `list_containers` | List all containers in the storage account | _(none)_ |
| `upload_blob` | Upload content from a URL to a blob in Azure Storage | `container_name`, `blob_name`, `file_url` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth credential. The `storage_account_name` field
is read from `auth_data` to construct the per-account endpoint URL.

## Limits & Quotas

- Azure Storage limits vary by account type and tier; see
  [Azure Storage scalability targets](https://learn.microsoft.com/en-us/azure/storage/common/scalability-targets-standard-account).
- Blob REST API requests are subject to per-account throughput limits
  (up to 20,000 requests/sec for general-purpose v2 accounts).
- Error model: non-2xx responses are caught and returned as
  `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
