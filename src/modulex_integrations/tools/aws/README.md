# Amazon Web Services

Interact with AWS services including DynamoDB, S3, Lambda, SNS, SQS,
EventBridge, CloudWatch Logs, and Redshift via the AWS SDK (`boto3`).

## Authentication

### AWS Access Key

- Sign in to the [AWS Management Console](https://console.aws.amazon.com/).
- Go to **IAM > Users > your user > Security credentials**.
- Create an access key and save both the Access Key ID and Secret Access Key.
- Required env vars:
  - `AWS_ACCESS_KEY_ID` (format: `AKIAIOSFODNN7EXAMPLE`)
  - `AWS_SECRET_ACCESS_KEY` (format: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
- The IAM user or role must have permissions for the specific AWS services
  being called (DynamoDB, S3, Lambda, SNS, SQS, EventBridge, CloudWatch Logs,
  Redshift Data API, EC2 DescribeRegions).

## Tools

| name | description | required params |
| --- | --- | --- |
| `cloudwatch_logs_put_log_event` | Upload a log event to a specified CloudWatch Logs log stream | `log_group_name`, `log_stream_name`, `message`, `timestamp` |
| `dynamodb_create_table` | Create a new DynamoDB table with configurable key schema, billing mode, and optional streams | `table_name`, `key_primary_attribute_name`, `key_primary_attribute_type`, `billing_mode` |
| `dynamodb_execute_statement` | Execute a PartiQL statement against DynamoDB for reads or writes | `statement` |
| `dynamodb_get_item` | Retrieve an item from a DynamoDB table by its primary key | `table_name`, `key` |
| `dynamodb_put_item` | Create or replace an item in a DynamoDB table | `table_name`, `item` |
| `dynamodb_query` | Query items from a DynamoDB table based on key conditions | `table_name`, `key_condition_expression` |
| `dynamodb_scan` | Scan all items in a DynamoDB table with optional filtering | `table_name` |
| `dynamodb_update_item` | Update attributes of an existing item or add a new item in a DynamoDB table | `table_name`, `key` |
| `dynamodb_update_table` | Modify settings for a DynamoDB table such as billing mode, capacity, or streams | `table_name`, `billing_mode` |
| `eventbridge_send_event` | Send an event to an Amazon EventBridge event bus | `event_bus_name`, `event_data` |
| `lambda_create_function` | Create a new AWS Lambda function from inline source code | `function_name`, `role`, `code` |
| `lambda_invoke_function` | Invoke an AWS Lambda function synchronously and return its response | `function_name` |
| `list_region_options` | List available AWS regions | (none) |
| `redshift_create_rows` | Insert rows into an Amazon Redshift Serverless table | `workgroup_name`, `database`, `schema_name`, `table`, `columns`, `rows` |
| `redshift_delete_rows` | Delete rows from an Amazon Redshift Serverless table | `workgroup_name`, `database`, `schema_name`, `table`, `where` |
| `redshift_query_database` | Run a SELECT query against an Amazon Redshift Serverless database | `workgroup_name`, `database`, `from_clause` |
| `redshift_update_rows` | Update rows in an Amazon Redshift Serverless table | `workgroup_name`, `database`, `schema_name`, `table`, `updates`, `where` |
| `s3_generate_presigned_url` | Generate a presigned URL to download an object from an S3 bucket | `bucket`, `key` |
| `s3_upload_base64_as_file` | Upload a base64-encoded string as a file to an S3 bucket | `bucket`, `filename`, `data` |
| `sns_send_message` | Publish a message to an Amazon SNS topic | `topic`, `message` |
| `sqs_send_message` | Send a message to an Amazon SQS queue | `queue_url`, `event_data` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved credential. The `region` parameter defaults to
`us-east-1` but can be overridden per call.

## Limits & Quotas

- AWS service limits vary by service, region, and account. See
  [AWS Service Quotas](https://docs.aws.amazon.com/general/latest/gr/aws-service-information.html)
  for per-service details.
- DynamoDB: default 40,000 RCU / 40,000 WCU per table (on-demand auto-scales).
- S3: no per-request limit; 3,500 PUT/s and 5,500 GET/s per prefix.
- Lambda: 1,000 concurrent executions (default, adjustable).
- SNS/SQS: region-dependent throughput limits.
- Redshift Data API: 200 active queries per cluster/workgroup.
- Error model: all AWS SDK exceptions are caught and returned as
  `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
