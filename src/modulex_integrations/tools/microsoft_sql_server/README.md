# Microsoft SQL Server

Execute queries and manage data in Microsoft SQL Server databases via direct TCP connections using `pymssql`.

## Authentication

### SQL Server Connection

Connect using standard SQL Server credentials (host, port, username, password, database).

- Required env vars: `MSSQL_HOST`, `MSSQL_PORT`, `MSSQL_USERNAME`, `MSSQL_PASSWORD`, `MSSQL_DATABASE`
- Optional env vars: `MSSQL_ENCRYPT` (true/false, use true for Azure SQL), `MSSQL_TRUST_SERVER_CERTIFICATE` (true/false, use true for local dev with self-signed certs)
- Connection uses TDS protocol via pymssql

## Tools

| name | description | required params |
| --- | --- | --- |
| `execute_raw_query` | Execute a raw SQL query against the database and return results | `query` |
| `execute_query` | Execute a parameterized SQL query with named inputs | `query` |
| `insert_row` | Insert a new row into a specified table | `table`, `data` |
| `list_table_options` | List all available base tables in the database | (none) |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- No API rate limits apply; performance depends on the SQL Server instance capacity and network latency.
- Connection timeout defaults to pymssql's default (dependent on server responsiveness).
- Query execution is wrapped in `asyncio.to_thread` so it does not block the event loop.
- Error model: connection failures, query syntax errors, and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
