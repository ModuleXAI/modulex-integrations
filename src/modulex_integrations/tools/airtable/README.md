# Airtable

CRUD against the Airtable REST API (`api.airtable.com/v0`): base +
table discovery via `/meta/`, record list/get/create/update/delete
via `/<base>/<table>`.

## Authentication

### Personal Access Token (Bearer)

- Required env var: `AIRTABLE_API_KEY`.
- Create one at <https://airtable.com/create/tokens>.
- Sent as `Authorization: Bearer <token>`.
- `test_endpoint` GETs `/meta/bases` (no record cost).

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_bases` | All bases accessible with the token | — |
| `list_tables` | Tables + fields + views for a base | `base_id` |
| `list_records` | Records with optional filter/sort/view | `base_id`, `table_name` |
| `get_record` | Single record by id | `base_id`, `table_name`, `record_id` |
| `create_records` | Create N records (auto-batched at 10/req) | `base_id`, `table_name`, `records` |
| `update_records` | PATCH N records (auto-batched at 10/req) | `base_id`, `table_name`, `records` |
| `delete_records` | Delete N records (auto-batched at 10/req) | `base_id`, `table_name`, `record_ids` |

## Limits & Quotas

- Airtable caps batch record operations at **10 records per request**;
  `create/update/delete_records` split larger inputs automatically.
- `update_records` accepts both shapes per record:
  `{"id": "rec…", "fields": {"X": 1}}` (canonical) and
  `{"id": "rec…", "X": 1, "Y": 2}` (flat top-level fields). Both
  normalize to the canonical wire shape internally.
- `delete_records` uses `?records[]=rec1&records[]=rec2` query
  parameters (Airtable's documented batch-delete contract).
- Partial-batch failures surface as `success=False` + the count of
  records that completed before the error (via `updated_count` /
  `deleted_count`).

## Maintainer

ModuleX core team.
