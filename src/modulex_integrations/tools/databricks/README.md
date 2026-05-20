# Databricks

Manage Databricks jobs, runs, SQL warehouses, and vector search indexes via the Databricks REST API (`{domain}.cloud.databricks.com`).

## Authentication

### Databricks Personal Access Token

- Generate a personal access token in your Databricks workspace under **User Settings > Developer > Access tokens** (<https://docs.databricks.com/en/dev-tools/auth/pat.html>).
- Required env vars:
  - `DATABRICKS_DOMAIN` — your workspace subdomain (format: `my-workspace`)
  - `DATABRICKS_ACCESS_TOKEN` — your personal access token (format: `dapi0123456789abcdef0123456789abcdef`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `cancel_all_runs` | Cancel all active runs for a job. | — |
| `cancel_run` | Cancel a job run. The run is canceled asynchronously. | `run_id` |
| `create_endpoint` | Create a new vector search endpoint. | `name` |
| `create_job` | Create a new Databricks job. | `tasks` |
| `create_sql_warehouse` | Create a new SQL Warehouse in Databricks. | `name`, `cluster_size` |
| `create_vector_search_index` | Create a new vector search index in Databricks. | `name`, `endpoint_name`, `index_type`, `primary_key` |
| `delete_endpoint` | Delete a vector search endpoint. | `endpoint_name` |
| `delete_job` | Delete a job. Deleted jobs cannot be recovered. | `job_id` |
| `delete_run` | Delete a non-active run. | `run_id` |
| `delete_sql_warehouse` | Delete a SQL Warehouse by ID. | `warehouse_id` |
| `delete_vector_search_index` | Delete a vector search index. | `index_name` |
| `delete_vector_search_index_data` | Delete rows from a Direct Access vector index by primary-key values. | `index_name`, `primary_keys` |
| `edit_sql_warehouse` | Edit the configuration of an existing SQL Warehouse. | `warehouse_id` |
| `export_run` | Export and retrieve the job run task. | `run_id` |
| `get_endpoint` | Get details of a specific vector search endpoint. | `endpoint_name` |
| `get_job` | Retrieve the details for a single job. | `job_id` |
| `get_job_permissions` | Get permissions of a job. | `job_id` |
| `get_run` | Retrieve the metadata of a run. | `run_id` |
| `get_run_output` | Retrieve the output and metadata of a single task run. | `run_id` |
| `get_sql_warehouse` | Retrieve details for a specific SQL Warehouse. | `warehouse_id` |
| `get_sql_warehouse_config` | Retrieve the global configuration for SQL Warehouses. | — |
| `get_sql_warehouse_permissions` | Retrieve the permissions for a specific SQL Warehouse. | `warehouse_id` |
| `get_vector_search_index` | Retrieve details about a specific vector search index. | `index_name` |
| `list_endpoints` | List all vector search endpoints. | — |
| `list_jobs` | List all jobs using automatic pagination. | — |
| `list_runs` | List all runs available to the user. | — |
| `list_sql_warehouses` | List all SQL Warehouses available in the workspace. | — |
| `list_vector_search_indexes` | List all vector search indexes for a given endpoint. | `endpoint_name` |
| `query_vector_search_index` | Query a specific vector search index. | `index_name`, `columns` |
| `repair_run` | Re-run one or more tasks. | `run_id` |
| `reset_job` | Overwrite all settings for a job. | `job_id`, `new_settings` |
| `run_job_now` | Run a job now and return the ID of the triggered run. | `job_id` |
| `scan_vector_search_index` | Scan a vector search index and return entries after a given primary key. | `index_name` |
| `set_job_permissions` | Set permissions on a job. | `job_id`, `access_control_list` |
| `set_sql_warehouse_config` | Update the global configuration for SQL Warehouses. | — |
| `set_sql_warehouse_permissions` | Update the permissions for a specific SQL Warehouse. | `warehouse_id`, `access_control_list` |
| `start_sql_warehouse` | Start a SQL Warehouse by ID. | `warehouse_id` |
| `stop_sql_warehouse` | Stop a SQL Warehouse by ID. | `warehouse_id` |
| `sync_vector_search_index` | Synchronize a Delta Sync vector search index. | `index_name` |
| `update_job` | Update an existing job. Only the fields provided will be updated. | `job_id`, `new_settings` |
| `upsert_vector_search_index_data` | Upsert data into an existing vector search index. | `index_name`, `inputs_json` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- Databricks API rate limits vary by endpoint and workspace tier. Consult your workspace admin for specific limits.
- Jobs API: typically 30 requests/second per workspace.
- Vector Search API: limits depend on endpoint configuration and provisioned capacity.
- SQL Warehouses API: standard REST API limits apply.
- Error model: non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
