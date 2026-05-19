# Supabase

Open-source Firebase alternative providing a Postgres database, authentication, instant APIs, and realtime subscriptions via the Supabase PostgREST API (`https://<subdomain>.supabase.co/rest/v1/`).

## Authentication

### Supabase Service Key

- Go to [Supabase Dashboard](https://app.supabase.com) and open your project.
- Navigate to **Project Settings > API**.
- Copy your **Project URL subdomain** (the part before `.supabase.co`).
- Copy the **service_role** key (NOT the anon key).
- Required env vars:
  - `SUPABASE_SUBDOMAIN` (format: `abcdefghijklmnopqrst`)
  - `SUPABASE_SERVICE_KEY` (format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `select_row` | Select row(s) from a Supabase database table with optional filtering and ordering | `table`, `order_by` |
| `insert_row` | Insert a new row into a Supabase database table | `table`, `data` |
| `update_row` | Update row(s) in a Supabase database table matching a column value | `table`, `column`, `value`, `data` |
| `upsert_row` | Insert a row or update it if it already exists in a Supabase database table | `table`, `data` |
| `delete_row` | Delete row(s) from a Supabase database table matching a column value | `table`, `column`, `value` |
| `batch_insert_rows` | Insert multiple rows into a Supabase database table at once | `table`, `data` |
| `remote_procedure_call` | Call a Postgres function (RPC) in a Supabase database | `function_name` |
| `count_rows` | Count rows in a Supabase database table with optional filtering | `table` |

Every tool takes additional `subdomain` and `service_key` parameters that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Free tier**: 500 MB database, 2 GB bandwidth, 50 MB file storage.
- **Pro tier**: 8 GB database, 250 GB bandwidth, 100 GB file storage.
- **Rate limits**: Supabase does not publish hard API rate limits; PostgREST is limited by connection pool size (default: 60 connections on free tier, higher on paid plans).
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
