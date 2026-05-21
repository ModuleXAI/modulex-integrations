# Google Cloud

Google Cloud Platform integration providing Cloud Storage bucket and object management, BigQuery query execution and streaming inserts, BigQuery Data Transfer scheduled queries, Compute Engine instance control, and Cloud Logging via the GCP REST APIs.

## Authentication

### Service Account Key

- Create a service account and download the JSON key file from the [GCP IAM Console](https://console.cloud.google.com/iam-admin/serviceaccounts).
- Required env var: `GOOGLE_CLOUD_KEY_JSON` (format: full JSON content of the service account key file).
- The service account must have appropriate IAM roles for the services you intend to use (e.g. Storage Admin, BigQuery Data Editor, Compute Instance Admin, Logging Writer).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_bucket` | Create a new Google Cloud Storage bucket | `bucket_name` |
| `get_bucket` | Get metadata for a Google Cloud Storage bucket | `bucket_name` |
| `list_buckets` | List all Google Cloud Storage buckets in the project | |
| `search_objects` | Search for objects in a bucket by prefix | `bucket_name`, `prefix` |
| `get_object` | Get metadata for a specific object in a Google Cloud Storage bucket | `bucket_name`, `object_name` |
| `upload_object` | Upload text content as an object to a Google Cloud Storage bucket | `bucket_name`, `object_name`, `content` |
| `logging_write_log` | Write a log entry to Google Cloud Logging | `log_name`, `text` |
| `run_query` | Run a SQL query in BigQuery and return the results | `query` |
| `bigquery_insert_rows` | Insert rows into a BigQuery table using streaming insert | `dataset_id`, `table_id`, `rows` |
| `create_scheduled_query` | Create a scheduled query in BigQuery Data Transfer Service | `destination_dataset_id`, `display_name`, `query` |
| `switch_instance_boot_status` | Start or stop a Google Compute Engine virtual machine instance | `zone`, `instance_name`, `action` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential (token-style injection for custom auth).

## Limits & Quotas

- **Cloud Storage**: 1,000 bucket creates per project per 2 seconds; 5,000 object mutations per bucket per second.
- **BigQuery**: 100 concurrent queries per project; streaming inserts limited to 50,000 rows per request and 10 MB per request.
- **Compute Engine**: API rate limits vary by method (typically 20 requests/second per project per region).
- **Cloud Logging**: 60 write requests per second per project.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
