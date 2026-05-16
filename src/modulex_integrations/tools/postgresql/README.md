# PostgreSQL

PostgreSQL database integration via the `asyncpg` driver. Provides
raw SQL execution + CRUD + upsert + introspection.

## Authentication

- **`custom` auth_type** (DB connection params, not a single API key).
- Env vars: `POSTGRESQL_HOST`, `POSTGRESQL_USER`, `POSTGRESQL_PASSWORD`,
  `POSTGRESQL_DATABASE` (all required), plus `POSTGRESQL_PORT` (defaults
  to 5432) and `POSTGRESQL_SSL_MODE` (`verify`, `skip_verification`,
  `disabled`).

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)` and
opens a fresh `asyncpg` connection per call (matches legacy — no pool
held across invocations).

## Tools

| name | description |
| --- | --- |
| `execute_raw_query` | Any SQL statement; uses `$1, $2, ...` placeholders. |
| `create_row` | `INSERT ... RETURNING *`. |
| `delete_row` | `DELETE ... WHERE <condition> RETURNING *`; `?` placeholders. |
| `update_row` | `UPDATE ... SET ... WHERE ... RETURNING *`. |
| `upsert_row` | `INSERT ... ON CONFLICT (...) DO UPDATE SET ...`. |
| `find_row` | `SELECT * FROM table WHERE column <op> value`. |
| `execute_query_with_condition` | `SELECT * FROM table WHERE <condition>`. |
| `list_schemas` | All user-visible schemas. |
| `list_tables` | Tables + views in a schema. |
| `describe_table` | Column metadata + primary keys. |

## Placeholders

CRUD tools accept `?` placeholders and rewrite them to `$1, $2, ...`
before sending to asyncpg. `execute_raw_query` accepts `$N` directly.

## Limits & Quotas

- 60s connection timeout.
- `find_row` operator allowlist: `=`, `>`, `>=`, `<`, `!=`, `<=`,
  `LIKE`, `ILIKE` (case-insensitive accepted as `like`/`ilike` too).
- `asyncpg` is imported lazily so the manifest can be inspected
  even without the driver installed.

## Maintainer

ModuleX core team.
