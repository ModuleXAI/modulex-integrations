"""Databricks integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="databricks",
    display_name="Databricks",
    description="Manage Databricks jobs, runs, SQL warehouses, and vector search indexes.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:databricks",
    app_url="https://www.databricks.com",
    categories=["Data Engineering", "Analytics", "Machine Learning"],
    actions=[
        ActionDefinition(
            name="cancel_all_runs",
            description="Cancel all active runs for a job.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of a job. If omitted with all_queued_runs=true, cancels all queued runs in the workspace.",
                ),
                "all_queued_runs": ParameterDef(
                    type="boolean",
                    description="Cancel all queued runs. If no job_id is provided, all queued runs in the workspace are canceled.",
                ),
            },
        ),
        ActionDefinition(
            name="cancel_run",
            description="Cancel a job run. The run is canceled asynchronously.",
            parameters={
                "run_id": ParameterDef(
                    type="string",
                    description="Identifier of the run to cancel.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_endpoint",
            description="Create a new vector search endpoint.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The name of the vector search endpoint to create.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_job",
            description="Create a new Databricks job.",
            parameters={
                "tasks": ParameterDef(
                    type="string",
                    description="JSON string of task specifications for this job.",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="An optional name for the job.",
                ),
                "tags": ParameterDef(
                    type="string",
                    description="JSON string of tags associated with the job.",
                ),
                "job_clusters": ParameterDef(
                    type="string",
                    description="JSON string of job cluster specifications.",
                ),
                "email_notifications": ParameterDef(
                    type="string",
                    description="JSON string of email notification settings.",
                ),
                "webhook_notifications": ParameterDef(
                    type="string",
                    description="JSON string of webhook notification settings.",
                ),
                "timeout_seconds": ParameterDef(
                    type="integer",
                    description="Timeout in seconds applied to each run of this job.",
                ),
                "schedule": ParameterDef(
                    type="string",
                    description="JSON string of schedule definition with quartz_cron_expression and timezone_id.",
                ),
                "max_concurrent_runs": ParameterDef(
                    type="integer",
                    description="Maximum number of concurrent runs for the job.",
                ),
                "git_source": ParameterDef(
                    type="string",
                    description="JSON string specifying a remote Git repository for task source code.",
                ),
                "access_control_list": ParameterDef(
                    type="string",
                    description="JSON string of permissions to set on the job.",
                ),
            },
        ),
        ActionDefinition(
            name="create_sql_warehouse",
            description="Create a new SQL Warehouse in Databricks.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="A human-readable name for the warehouse.",
                    required=True,
                ),
                "cluster_size": ParameterDef(
                    type="string",
                    description="Size of the cluster: 2X-Small, X-Small, Small, Medium, Large, X-Large, 2X-Large, 3X-Large, 4X-Large.",
                    required=True,
                ),
                "auto_stop_minutes": ParameterDef(
                    type="integer",
                    description="Minutes of inactivity before auto-stop. 0 disables. Must be 0 or >= 10.",
                    default=10,
                ),
                "min_num_clusters": ParameterDef(
                    type="integer",
                    description="Minimum number of clusters to maintain.",
                    default=1,
                ),
                "max_num_clusters": ParameterDef(
                    type="integer",
                    description="Maximum number of clusters for autoscaling.",
                    default=1,
                ),
                "enable_photon": ParameterDef(
                    type="boolean",
                    description="Whether to use Photon optimized clusters.",
                ),
                "enable_serverless_compute": ParameterDef(
                    type="boolean",
                    description="Whether to use serverless compute.",
                ),
                "warehouse_type": ParameterDef(
                    type="string",
                    description="Warehouse type: TYPE_UNSPECIFIED, CLASSIC, or PRO.",
                ),
                "spot_instance_policy": ParameterDef(
                    type="string",
                    description="Spot instance policy: POLICY_UNSPECIFIED, COST_OPTIMIZED, RELIABILITY_OPTIMIZED.",
                ),
                "channel": ParameterDef(
                    type="string",
                    description="JSON string of channel details.",
                ),
                "tags": ParameterDef(
                    type="string",
                    description="JSON string of custom key-value tags.",
                ),
            },
        ),
        ActionDefinition(
            name="create_vector_search_index",
            description="Create a new vector search index in Databricks.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="A unique name for the index (e.g., main_catalog.docs.en_wiki_index).",
                    required=True,
                ),
                "endpoint_name": ParameterDef(
                    type="string",
                    description="The name of the vector search endpoint.",
                    required=True,
                ),
                "index_type": ParameterDef(
                    type="string",
                    description="Type of index: DELTA_SYNC or DIRECT_ACCESS.",
                    required=True,
                ),
                "primary_key": ParameterDef(
                    type="string",
                    description="The primary key column for the index.",
                    required=True,
                ),
                "source_table": ParameterDef(
                    type="string",
                    description="The Delta table backing the index (required for DELTA_SYNC).",
                ),
                "columns_to_sync": ParameterDef(
                    type="string",
                    description="JSON array of column names to sync from the source Delta table.",
                ),
                "embedding_source_columns": ParameterDef(
                    type="string",
                    description="JSON array of embedding source column configs.",
                ),
                "index_schema_json": ParameterDef(
                    type="string",
                    description="The schema of the index in JSON format (required for DIRECT_ACCESS). Sent on the wire as `schema_json`.",
                ),
                "pipeline_type": ParameterDef(
                    type="string",
                    description="Pipeline type: TRIGGERED or CONTINUOUS.",
                    default="TRIGGERED",
                ),
            },
        ),
        ActionDefinition(
            name="delete_endpoint",
            description="Delete a vector search endpoint.",
            parameters={
                "endpoint_name": ParameterDef(
                    type="string",
                    description="The name of the vector search endpoint to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_job",
            description="Delete a job. Deleted jobs cannot be recovered.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of the job to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_run",
            description="Delete a non-active run. Returns an error if the run is active.",
            parameters={
                "run_id": ParameterDef(
                    type="string",
                    description="Identifier of the run to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_sql_warehouse",
            description="Delete a SQL Warehouse by ID.",
            parameters={
                "warehouse_id": ParameterDef(
                    type="string",
                    description="The ID of the SQL Warehouse to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_vector_search_index",
            description="Delete a vector search index.",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the vector search index to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_vector_search_index_data",
            description="Delete rows from a Direct Access vector index by primary-key values.",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the vector search index.",
                    required=True,
                ),
                "primary_keys": ParameterDef(
                    type="string",
                    description="JSON array of primary key values to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="edit_sql_warehouse",
            description="Edit the configuration of an existing SQL Warehouse.",
            parameters={
                "warehouse_id": ParameterDef(
                    type="string",
                    description="The ID of the SQL Warehouse to edit.",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="New logical name for the warehouse.",
                ),
                "cluster_size": ParameterDef(
                    type="string",
                    description="Size of clusters: 2X-Small, X-Small, Small, Medium, Large, X-Large, 2X-Large, 3X-Large, 4X-Large.",
                ),
                "auto_stop_mins": ParameterDef(
                    type="integer",
                    description="Minutes of inactivity before auto-stop. 0 disables. Must be 0 or >= 10.",
                ),
                "min_num_clusters": ParameterDef(
                    type="integer",
                    description="Minimum number of clusters.",
                ),
                "max_num_clusters": ParameterDef(
                    type="integer",
                    description="Maximum number of clusters for autoscaling.",
                ),
                "enable_photon": ParameterDef(
                    type="boolean",
                    description="Whether to use Photon optimized clusters.",
                ),
                "enable_serverless_compute": ParameterDef(
                    type="boolean",
                    description="Whether to use serverless compute.",
                ),
                "warehouse_type": ParameterDef(
                    type="string",
                    description="Warehouse type: TYPE_UNSPECIFIED, CLASSIC, or PRO.",
                ),
                "spot_instance_policy": ParameterDef(
                    type="string",
                    description="Spot instance policy: POLICY_UNSPECIFIED, COST_OPTIMIZED, RELIABILITY_OPTIMIZED.",
                ),
                "tags": ParameterDef(
                    type="string",
                    description="JSON string of custom key-value tags.",
                ),
                "channel": ParameterDef(
                    type="string",
                    description="JSON string of channel details.",
                ),
            },
        ),
        ActionDefinition(
            name="export_run",
            description="Export and retrieve the job run task.",
            parameters={
                "run_id": ParameterDef(
                    type="string",
                    description="Identifier of the run to export.",
                    required=True,
                ),
                "views_to_export": ParameterDef(
                    type="string",
                    description="Which views to export: CODE, DASHBOARDS, or ALL. Defaults to CODE.",
                ),
            },
        ),
        ActionDefinition(
            name="get_endpoint",
            description="Get details of a specific vector search endpoint.",
            parameters={
                "endpoint_name": ParameterDef(
                    type="string",
                    description="The name of the vector search endpoint.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_job",
            description="Retrieve the details for a single job.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of the job.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_job_permissions",
            description="Get permissions of a job.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of the job.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_run",
            description="Retrieve the metadata of a run.",
            parameters={
                "run_id": ParameterDef(
                    type="string",
                    description="Identifier of the run.",
                    required=True,
                ),
                "include_history": ParameterDef(
                    type="boolean",
                    description="Whether to include the repair history in the response.",
                ),
                "include_resolved_values": ParameterDef(
                    type="boolean",
                    description="Whether to include resolved parameter values in the response.",
                ),
            },
        ),
        ActionDefinition(
            name="get_run_output",
            description="Retrieve the output and metadata of a single task run.",
            parameters={
                "run_id": ParameterDef(
                    type="string",
                    description="Identifier of the run.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_sql_warehouse",
            description="Retrieve details for a specific SQL Warehouse.",
            parameters={
                "warehouse_id": ParameterDef(
                    type="string",
                    description="The ID of the SQL Warehouse.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_sql_warehouse_config",
            description="Retrieve the global configuration for SQL Warehouses.",
            parameters={},
        ),
        ActionDefinition(
            name="get_sql_warehouse_permissions",
            description="Retrieve the permissions for a specific SQL Warehouse.",
            parameters={
                "warehouse_id": ParameterDef(
                    type="string",
                    description="The ID of the SQL Warehouse.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_vector_search_index",
            description="Retrieve details about a specific vector search index.",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the vector search index.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_endpoints",
            description="List all vector search endpoints.",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of endpoints to return.",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_jobs",
            description="List all jobs using automatic pagination.",
            parameters={
                "expand_tasks": ParameterDef(
                    type="boolean",
                    description="Whether to include task and cluster details in the response.",
                ),
                "name": ParameterDef(
                    type="string",
                    description="Optional name to filter on.",
                ),
                "max_requests": ParameterDef(
                    type="integer",
                    description="Maximum number of API page requests to make (1-10).",
                ),
            },
        ),
        ActionDefinition(
            name="list_runs",
            description="List all runs available to the user.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of a job to filter runs.",
                ),
                "active_only": ParameterDef(
                    type="boolean",
                    description="Set to true to return only active runs.",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of runs to return.",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_sql_warehouses",
            description="List all SQL Warehouses available in the workspace.",
            parameters={},
        ),
        ActionDefinition(
            name="list_vector_search_indexes",
            description="List all vector search indexes for a given endpoint.",
            parameters={
                "endpoint_name": ParameterDef(
                    type="string",
                    description="The name of the vector search endpoint.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="query_vector_search_index",
            description="Query a specific vector search index.",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the vector search index.",
                    required=True,
                ),
                "columns": ParameterDef(
                    type="string",
                    description="JSON array of column names to include in the response.",
                    required=True,
                ),
                "query_text": ParameterDef(
                    type="string",
                    description="Free-text query for semantic search.",
                ),
                "query_vector": ParameterDef(
                    type="string",
                    description="JSON array of floats representing the embedding vector.",
                ),
                "filters_json": ParameterDef(
                    type="string",
                    description="JSON string representing query filters.",
                ),
                "num_results": ParameterDef(
                    type="integer",
                    description="Number of results to return.",
                    default=10,
                ),
                "include_embeddings": ParameterDef(
                    type="boolean",
                    description="Whether to include embedding vectors in the results.",
                ),
            },
        ),
        ActionDefinition(
            name="repair_run",
            description="Re-run one or more tasks.",
            parameters={
                "run_id": ParameterDef(
                    type="string",
                    description="Identifier of the run to repair.",
                    required=True,
                ),
                "rerun_tasks": ParameterDef(
                    type="string",
                    description="JSON array of task keys to repair.",
                ),
                "rerun_all_failed_tasks": ParameterDef(
                    type="boolean",
                    description="If true, repair all failed tasks.",
                ),
                "pipeline_params_full_refresh": ParameterDef(
                    type="boolean",
                    description="Controls whether the pipeline should perform a full refresh.",
                ),
            },
        ),
        ActionDefinition(
            name="reset_job",
            description="Overwrite all settings for a job.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of the job.",
                    required=True,
                ),
                "new_settings": ParameterDef(
                    type="string",
                    description="JSON string of the new settings that fully replaces all existing job settings.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="run_job_now",
            description="Run a job now and return the ID of the triggered run.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of the job to run.",
                    required=True,
                ),
                "jar_params": ParameterDef(
                    type="string",
                    description="JSON array of parameters for jobs with JAR tasks.",
                ),
                "notebook_params": ParameterDef(
                    type="string",
                    description="JSON object of key-value pairs for notebook tasks.",
                ),
                "python_params": ParameterDef(
                    type="string",
                    description="JSON array of parameters for Python tasks.",
                ),
                "spark_submit_params": ParameterDef(
                    type="string",
                    description="JSON array of parameters for spark submit tasks.",
                ),
            },
        ),
        ActionDefinition(
            name="scan_vector_search_index",
            description="Scan a vector search index and return entries after a given primary key.",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the vector search index.",
                    required=True,
                ),
                "last_primary_key": ParameterDef(
                    type="string",
                    description="Primary key of the last entry returned in the previous scan. Leave empty to start from the beginning.",
                ),
                "num_results": ParameterDef(
                    type="integer",
                    description="Number of results to return.",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="set_job_permissions",
            description="Set permissions on a job.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of the job.",
                    required=True,
                ),
                "access_control_list": ParameterDef(
                    type="string",
                    description="JSON string of permission objects with user_name/group_name/service_principal_name and permission_level.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="set_sql_warehouse_config",
            description="Update the global configuration for SQL Warehouses.",
            parameters={
                "instance_profile_arn": ParameterDef(
                    type="string",
                    description="Instance profile ARN for IAM role (AWS).",
                ),
                "google_service_account": ParameterDef(
                    type="string",
                    description="Service account email for GCP workspaces.",
                ),
                "security_policy": ParameterDef(
                    type="string",
                    description="Security policy: NONE or DATA_ACCESS_CONTROL.",
                ),
                "channel": ParameterDef(
                    type="string",
                    description="JSON string of channel details.",
                ),
                "enabled_warehouse_types": ParameterDef(
                    type="string",
                    description="JSON array of enabled warehouse type objects.",
                ),
                "config_param": ParameterDef(
                    type="string",
                    description="JSON array of general config key/value pairs.",
                ),
                "global_param": ParameterDef(
                    type="string",
                    description="JSON array of global parameter key/value pairs.",
                ),
            },
        ),
        ActionDefinition(
            name="set_sql_warehouse_permissions",
            description="Update the permissions for a specific SQL Warehouse.",
            parameters={
                "warehouse_id": ParameterDef(
                    type="string",
                    description="The ID of the SQL Warehouse.",
                    required=True,
                ),
                "access_control_list": ParameterDef(
                    type="string",
                    description="JSON string of access control entries with user_name/group_name/service_principal_name and permission_level.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="start_sql_warehouse",
            description="Start a SQL Warehouse by ID.",
            parameters={
                "warehouse_id": ParameterDef(
                    type="string",
                    description="The ID of the SQL Warehouse to start.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="stop_sql_warehouse",
            description="Stop a SQL Warehouse by ID.",
            parameters={
                "warehouse_id": ParameterDef(
                    type="string",
                    description="The ID of the SQL Warehouse to stop.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="sync_vector_search_index",
            description="Synchronize a Delta Sync vector search index.",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the vector search index to synchronize.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_job",
            description="Update an existing job. Only the fields provided will be updated.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="Identifier of the job to update.",
                    required=True,
                ),
                "new_settings": ParameterDef(
                    type="string",
                    description="JSON string of updated job settings (only fields to change).",
                    required=True,
                ),
                "fields_to_remove": ParameterDef(
                    type="string",
                    description="JSON array of field paths to remove from the job settings.",
                ),
            },
        ),
        ActionDefinition(
            name="upsert_vector_search_index_data",
            description="Upsert data into an existing vector search index.",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the vector search index.",
                    required=True,
                ),
                "inputs_json": ParameterDef(
                    type="string",
                    description="JSON array of row objects to upsert.",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Databricks Personal Access Token",
            description="Authenticate using your Databricks workspace domain and a personal access token.",
            setup_environment_variables=[
                EnvVar(
                    name="DATABRICKS_DOMAIN",
                    display_name="Workspace Domain",
                    description="Your Databricks workspace subdomain (the part before .cloud.databricks.com).",
                    required=True,
                    sensitive=False,
                    sample_format="my-workspace",
                    about_url="https://docs.databricks.com/en/workspace/workspace-details.html",
                ),
                EnvVar(
                    name="DATABRICKS_ACCESS_TOKEN",
                    display_name="Access Token",
                    description="A Databricks personal access token.",
                    required=True,
                    sensitive=True,
                    sample_format="dapi0123456789abcdef0123456789abcdef",
                    about_url="https://docs.databricks.com/en/dev-tools/auth/pat.html",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://{DATABRICKS_DOMAIN}.cloud.databricks.com/api/2.0/preview/scim/v2/Me",
                method="GET",
                headers={
                    "Authorization": "Bearer {DATABRICKS_ACCESS_TOKEN}",
                    "Accept": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["id"]
                ),
                cost_level="free",
                description=(
                    "Validates the PAT and workspace domain by fetching the "
                    "current user via SCIM on the configured Databricks "
                    "workspace"
                ),
            ),
        ),
    ],
)
