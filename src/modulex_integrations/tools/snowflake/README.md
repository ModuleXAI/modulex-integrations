# Snowflake

Snowflake data warehouse integration via `snowflake-connector-python`
(the official driver). Provides SQL execution, batched inserts, and
introspection (databases/schemas/tables/warehouses).

## Authentication

- **`custom` auth_type** (warehouse credentials, not a single API key).
- Env vars (required): `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`,
  `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_WAREHOUSE`.
- Optional: `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`, `SNOWFLAKE_ROLE`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.

**The Snowflake driver is synchronous.** These tools are
`async def` (matches legacy + the LangChain `@tool` contract), but
the underlying `cursor.execute` blocks the event loop. Preserved
verbatim — improving it is a future-wave concern.

## Tools

| name | description |
| --- | --- |
| `execute_sql_query` | Any SQL; `%s` bind placeholders. |
| `insert_row` | Single row from a dict. |
| `insert_multiple_rows` | Batched INSERT (clamp 10-1000 per batch). |
| `list_databases` | `SHOW DATABASES`. |
| `list_schemas` | `SHOW SCHEMAS IN DATABASE`. |
| `list_tables` | `SHOW TABLES IN SCHEMA`. |
| `list_warehouses` | `SHOW WAREHOUSES`. |
| `describe_table` | `DESCRIBE TABLE` — column metadata. |
| `get_table_sample` | `SELECT * FROM table LIMIT N` (clamp 1-1000). |

## Notes

- All actions wrap the body in try/except → `success=False`
  envelope; per-batch errors in `insert_multiple_rows` carry through
  `batch_results` (the action only fails *overall* when every batch
  fails).
- `application` connection param is set to `"MODULEX_INTEGRATION"`
  for Snowflake-side query tagging.
- `snowflake.connector` is imported lazily so manifest inspection
  works without the driver installed.

## Maintainer

ModuleX core team.
