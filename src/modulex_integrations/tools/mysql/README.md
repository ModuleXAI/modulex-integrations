# MySQL

MySQL database integration via the `aiomysql` driver. Provides raw
SQL execution + CRUD + stored procedures + introspection.

## Authentication

- **`custom` auth_type** (DB connection params, not a single API key).
- Env vars: `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`,
  `MYSQL_DATABASE` (required), plus optional `MYSQL_PORT` (3306) and
  `MYSQL_SSL_MODE`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)` and
opens a fresh `aiomysql` connection per call (`autocommit=True` —
matches legacy).

## Tools

| name | description |
| --- | --- |
| `execute_raw_query` | Any SQL statement; uses `%s` placeholders. |
| `create_row` | `INSERT INTO ... (...) VALUES (...)`. |
| `delete_row` | `DELETE FROM ... WHERE ...`; `?` placeholders. |
| `update_row` | `UPDATE ... SET ... WHERE ...`. |
| `find_row` | `SELECT * FROM table WHERE column <op> value`. |
| `execute_query_with_condition` | `SELECT * FROM table WHERE <condition>`. |
| `execute_stored_procedure` | `CALL proc(args)` with multi-result-set support. |
| `list_tables` | `SHOW FULL TABLES`. |
| `describe_table` | `SHOW COLUMNS FROM table`. |

## Placeholders

CRUD tools accept `?` placeholders and rewrite them to `%s` before
sending to aiomysql. `execute_raw_query` accepts `%s` directly
(DB-API style).

## Limits & Quotas

- 60s connection timeout.
- Connections are not pooled — opened per call, closed via the
  context manager.
- `find_row` operator allowlist: `=`, `>`, `>=`, `<`, `!=`, `<=`,
  `LIKE`.
- `aiomysql` is imported lazily so the manifest can be inspected
  without the driver installed.

## Maintainer

ModuleX core team.
