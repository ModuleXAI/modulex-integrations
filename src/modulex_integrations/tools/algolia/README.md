# Algolia

Search and indexing platform for building fast, relevant search experiences via the Algolia REST API (`{application_id}-dsn.algolia.net` for reads, `{application_id}.algolia.net` for writes).

## Authentication

### API Key Authentication

- Go to [Algolia Dashboard > API Keys](https://dashboard.algolia.com/account/api-keys/all) and sign in.
- Copy your **Application ID** (semi-public identifier) and **Admin API Key** (secret).
- Required env vars:
  - `ALGOLIA_APPLICATION_ID` (format: `ABCDEF1234`)
  - `ALGOLIA_API_KEY` (format: 32-character hex string)

## Tools

| name | description | required params |
| --- | --- | --- |
| `browse_records` | Browse for records in the given index | `index_name` |
| `delete_records` | Delete records from the given index by object IDs | `index_name`, `record_ids` |
| `list_index_name_options` | Retrieves available index names for the application | (none) |
| `save_records` | Adds or updates records in the given index | `index_name`, `records` |

Every tool takes additional `application_id` and `api_key` parameters that the runtime fills in from the resolved credential.

## Limits & Quotas

- Rate limits depend on the Algolia plan (Community, Standard, Premium). Community plans have lower indexing and search operation limits.
- Search operations: typically thousands per second on paid plans.
- Indexing operations: batch limits vary by plan (10 MB per batch maximum payload size).
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
