"""Google Cloud integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_cloud.manifest import manifest
from modulex_integrations.tools.google_cloud.tools import (
    bigquery_insert_rows,
    create_bucket,
    create_scheduled_query,
    get_bucket,
    get_object,
    list_buckets,
    logging_write_log,
    run_query,
    search_objects,
    switch_instance_boot_status,
    upload_object,
)

TOOLS = (
    create_bucket,
    get_bucket,
    list_buckets,
    search_objects,
    get_object,
    upload_object,
    logging_write_log,
    run_query,
    bigquery_insert_rows,
    create_scheduled_query,
    switch_instance_boot_status,
)

__all__ = [
    "TOOLS",
    "bigquery_insert_rows",
    "create_bucket",
    "create_scheduled_query",
    "get_bucket",
    "get_object",
    "list_buckets",
    "logging_write_log",
    "manifest",
    "run_query",
    "search_objects",
    "switch_instance_boot_status",
    "upload_object",
]
