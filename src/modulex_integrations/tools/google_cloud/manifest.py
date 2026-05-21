"""Google Cloud integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="google_cloud",
    display_name="Google Cloud",
    description="Google Cloud Platform services including Cloud Storage, BigQuery, Compute Engine, and Cloud Logging",
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-cloud",
    app_url="https://cloud.google.com",
    categories=["Cloud Infrastructure", "Data & Analytics", "Developer Tools & Infrastructure"],
    actions=[
        ActionDefinition(
            name="create_bucket",
            description="Create a new Google Cloud Storage bucket",
            parameters={
                "bucket_name": ParameterDef(
                    type="string",
                    description="Globally unique bucket name",
                    required=True,
                ),
                "location": ParameterDef(
                    type="string",
                    description="Bucket location (e.g. US, EU, us-central1). Defaults to US",
                    default="US",
                ),
                "storage_class": ParameterDef(
                    type="string",
                    description="Storage class: STANDARD, NEARLINE, COLDLINE, or ARCHIVE",
                    default="STANDARD",
                ),
            },
        ),
        ActionDefinition(
            name="get_bucket",
            description="Get metadata for a Google Cloud Storage bucket",
            parameters={
                "bucket_name": ParameterDef(
                    type="string",
                    description="Name of the bucket",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_buckets",
            description="List all Google Cloud Storage buckets in the project",
            parameters={},
        ),
        ActionDefinition(
            name="search_objects",
            description="Search for objects in a bucket by prefix",
            parameters={
                "bucket_name": ParameterDef(
                    type="string",
                    description="Name of the bucket to search",
                    required=True,
                ),
                "prefix": ParameterDef(
                    type="string",
                    description="Object name prefix to filter by",
                    required=True,
                ),
                "delimiter": ParameterDef(
                    type="string",
                    description="Delimiter for directory-like listing (commonly '/')",
                ),
            },
        ),
        ActionDefinition(
            name="get_object",
            description="Get metadata for a specific object in a Google Cloud Storage bucket",
            parameters={
                "bucket_name": ParameterDef(
                    type="string",
                    description="Name of the bucket containing the object",
                    required=True,
                ),
                "object_name": ParameterDef(
                    type="string",
                    description="Full path/name of the object in the bucket",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="upload_object",
            description="Upload text content as an object to a Google Cloud Storage bucket",
            parameters={
                "bucket_name": ParameterDef(
                    type="string",
                    description="Name of the destination bucket",
                    required=True,
                ),
                "object_name": ParameterDef(
                    type="string",
                    description="Destination path/name for the object in the bucket",
                    required=True,
                ),
                "content": ParameterDef(
                    type="string",
                    description="Text content to upload",
                    required=True,
                ),
                "content_type": ParameterDef(
                    type="string",
                    description="MIME type of the content (e.g. text/plain, application/json)",
                    default="text/plain",
                ),
            },
        ),
        ActionDefinition(
            name="logging_write_log",
            description="Write a log entry to Google Cloud Logging",
            parameters={
                "log_name": ParameterDef(
                    type="string",
                    description="Name of the log to write to",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Log message text",
                    required=True,
                ),
                "severity": ParameterDef(
                    type="string",
                    description="Log severity: DEFAULT, DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL, ALERT, or EMERGENCY",
                    default="DEFAULT",
                ),
            },
        ),
        ActionDefinition(
            name="run_query",
            description="Run a SQL query in BigQuery and return the results",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="GoogleSQL query to execute",
                    required=True,
                ),
                "location": ParameterDef(
                    type="string",
                    description="Dataset location (e.g. US, EU). Must match dataset location",
                    default="US",
                ),
            },
        ),
        ActionDefinition(
            name="bigquery_insert_rows",
            description="Insert rows into a BigQuery table using streaming insert",
            parameters={
                "dataset_id": ParameterDef(
                    type="string",
                    description="BigQuery dataset ID",
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description="BigQuery table ID",
                    required=True,
                ),
                "rows": ParameterDef(
                    type="array",
                    description="Array of row objects to insert, each with column names as keys",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_scheduled_query",
            description="Create a scheduled query in BigQuery Data Transfer Service",
            parameters={
                "destination_dataset_id": ParameterDef(
                    type="string",
                    description="Destination dataset ID for query results",
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="Human-readable name for the scheduled query",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="GoogleSQL query to schedule",
                    required=True,
                ),
                "dataset_region": ParameterDef(
                    type="string",
                    description="Geographic location of the dataset (e.g. us, eu)",
                    default="us",
                ),
                "schedule": ParameterDef(
                    type="string",
                    description="Schedule in cron-like format (e.g. 'every 24 hours', '1st monday of month 09:00')",
                ),
                "write_disposition": ParameterDef(
                    type="string",
                    description="Write behavior: WRITE_TRUNCATE or WRITE_APPEND",
                    default="WRITE_TRUNCATE",
                ),
                "destination_table_name_template": ParameterDef(
                    type="string",
                    description="Destination table name template, can use {run_date} or {run_time} variables",
                    default="logs",
                ),
            },
        ),
        ActionDefinition(
            name="switch_instance_boot_status",
            description="Start or stop a Google Compute Engine virtual machine instance",
            parameters={
                "zone": ParameterDef(
                    type="string",
                    description="Compute Engine zone (e.g. us-central1-a)",
                    required=True,
                ),
                "instance_name": ParameterDef(
                    type="string",
                    description="Name of the VM instance",
                    required=True,
                ),
                "action": ParameterDef(
                    type="string",
                    description="Action to perform: start or stop",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Service Account Key",
            description="Authenticate using a GCP service account JSON key file",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_CLOUD_KEY_JSON",
                    display_name="Service Account Key JSON",
                    description="The full JSON content of your GCP service account key file",
                    required=True,
                    sensitive=True,
                    sample_format='{"type":"service_account","project_id":"...","private_key":"...","client_email":"..."}',
                    about_url="https://cloud.google.com/iam/docs/keys-create-delete",
                ),
            ],
        ),
    ],
)
