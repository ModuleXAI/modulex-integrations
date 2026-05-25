"""AWS integration manifest."""
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
    name="aws",
    display_name="Amazon Web Services",
    description="Interact with AWS services including DynamoDB, S3, Lambda, SNS, SQS, EventBridge, CloudWatch Logs, and Redshift.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:aws-themed",
    app_url="https://aws.amazon.com",
    categories=["Cloud Infrastructure", "Developer Tools & Infrastructure", "Data Storage"],
    actions=[
        ActionDefinition(
            name="cloudwatch_logs_put_log_event",
            description="Upload a log event to a specified CloudWatch Logs log stream.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "log_group_name": ParameterDef(
                    type="string",
                    description="Name of the CloudWatch log group",
                    required=True,
                ),
                "log_stream_name": ParameterDef(
                    type="string",
                    description="Name of the log stream within the log group",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="The log event message",
                    required=True,
                ),
                "timestamp": ParameterDef(
                    type="integer",
                    description="Unix timestamp in milliseconds for the event",
                    required=True,
                ),
                "sequence_token": ParameterDef(
                    type="string",
                    description="Sequence token from a previous PutLogEvents call (not needed for a new log stream)",
                ),
            },
        ),
        ActionDefinition(
            name="dynamodb_create_table",
            description="Create a new DynamoDB table with configurable key schema, billing mode, and optional streams.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the table to create",
                    required=True,
                ),
                "key_primary_attribute_name": ParameterDef(
                    type="string",
                    description="Name of the partition key attribute",
                    required=True,
                ),
                "key_primary_attribute_type": ParameterDef(
                    type="string",
                    description="Data type of the partition key: S (string), N (number), or B (binary)",
                    required=True,
                ),
                "key_secondary_attribute_name": ParameterDef(
                    type="string",
                    description="Name of the sort key attribute (optional)",
                ),
                "key_secondary_attribute_type": ParameterDef(
                    type="string",
                    description="Data type of the sort key: S (string), N (number), or B (binary)",
                ),
                "billing_mode": ParameterDef(
                    type="string",
                    description="Billing mode: PROVISIONED or PAY_PER_REQUEST",
                    required=True,
                ),
                "read_capacity_units": ParameterDef(
                    type="integer",
                    description="Read capacity units (required when billing_mode is PROVISIONED)",
                ),
                "write_capacity_units": ParameterDef(
                    type="integer",
                    description="Write capacity units (required when billing_mode is PROVISIONED)",
                ),
                "stream_specification_enabled": ParameterDef(
                    type="boolean",
                    description="Whether DynamoDB Streams is enabled",
                ),
                "stream_specification_view_type": ParameterDef(
                    type="string",
                    description="Stream view type: KEYS_ONLY, NEW_IMAGE, OLD_IMAGE, or NEW_AND_OLD_IMAGES",
                ),
            },
        ),
        ActionDefinition(
            name="dynamodb_execute_statement",
            description="Execute a PartiQL statement against DynamoDB for reads or writes.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "statement": ParameterDef(
                    type="string",
                    description="PartiQL statement to execute",
                    required=True,
                ),
                "parameters": ParameterDef(
                    type="array",
                    description="List of parameter values for the PartiQL statement (strings)",
                ),
            },
        ),
        ActionDefinition(
            name="dynamodb_get_item",
            description="Retrieve an item from a DynamoDB table by its primary key.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the DynamoDB table",
                    required=True,
                ),
                "key": ParameterDef(
                    type="object",
                    description='Item key in DynamoDB JSON format, e.g. {"id": {"S": "123"}}',
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="dynamodb_put_item",
            description="Create or replace an item in a DynamoDB table.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the DynamoDB table",
                    required=True,
                ),
                "item": ParameterDef(
                    type="object",
                    description='Item in DynamoDB JSON format, e.g. {"id": {"S": "123"}, "name": {"S": "foo"}}',
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="dynamodb_query",
            description="Query items from a DynamoDB table based on key conditions.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the DynamoDB table",
                    required=True,
                ),
                "key_condition_expression": ParameterDef(
                    type="string",
                    description="Key condition expression, e.g. partitionKey = :pk AND sortKey > :sk",
                    required=True,
                ),
                "projection_expression": ParameterDef(
                    type="string",
                    description="Comma-separated attribute names to retrieve",
                ),
                "expression_attribute_names": ParameterDef(
                    type="object",
                    description='Substitution tokens for attribute names, e.g. {"#n": "name"}',
                ),
                "expression_attribute_values": ParameterDef(
                    type="object",
                    description='Substitution values in DynamoDB JSON format, e.g. {":pk": {"S": "val"}}',
                ),
            },
        ),
        ActionDefinition(
            name="dynamodb_scan",
            description="Scan all items in a DynamoDB table with optional filtering.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the DynamoDB table",
                    required=True,
                ),
                "projection_expression": ParameterDef(
                    type="string",
                    description="Comma-separated attribute names to retrieve",
                ),
                "filter_expression": ParameterDef(
                    type="string",
                    description="Filter expression to apply after scanning",
                ),
                "expression_attribute_names": ParameterDef(
                    type="object",
                    description='Substitution tokens for attribute names, e.g. {"#n": "name"}',
                ),
                "expression_attribute_values": ParameterDef(
                    type="object",
                    description='Substitution values in DynamoDB JSON format, e.g. {":val": {"S": "x"}}',
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of items to evaluate",
                ),
            },
        ),
        ActionDefinition(
            name="dynamodb_update_item",
            description="Update attributes of an existing item or add a new item in a DynamoDB table.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the DynamoDB table",
                    required=True,
                ),
                "key": ParameterDef(
                    type="object",
                    description='Item key in DynamoDB JSON format, e.g. {"id": {"S": "123"}}',
                    required=True,
                ),
                "update_expression": ParameterDef(
                    type="string",
                    description='Update expression, e.g. SET #n = :val',
                ),
                "expression_attribute_names": ParameterDef(
                    type="object",
                    description='Substitution tokens for attribute names, e.g. {"#n": "name"}',
                ),
                "expression_attribute_values": ParameterDef(
                    type="object",
                    description='Substitution values in DynamoDB JSON format, e.g. {":val": {"S": "x"}}',
                ),
            },
        ),
        ActionDefinition(
            name="dynamodb_update_table",
            description="Modify settings for a DynamoDB table such as billing mode, capacity, or streams.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the DynamoDB table",
                    required=True,
                ),
                "billing_mode": ParameterDef(
                    type="string",
                    description="Billing mode: PROVISIONED or PAY_PER_REQUEST",
                    required=True,
                ),
                "read_capacity_units": ParameterDef(
                    type="integer",
                    description="Read capacity units (required when billing_mode is PROVISIONED)",
                ),
                "write_capacity_units": ParameterDef(
                    type="integer",
                    description="Write capacity units (required when billing_mode is PROVISIONED)",
                ),
                "stream_specification_enabled": ParameterDef(
                    type="boolean",
                    description="Whether DynamoDB Streams is enabled",
                ),
                "stream_specification_view_type": ParameterDef(
                    type="string",
                    description="Stream view type: KEYS_ONLY, NEW_IMAGE, OLD_IMAGE, or NEW_AND_OLD_IMAGES",
                ),
            },
        ),
        ActionDefinition(
            name="eventbridge_send_event",
            description="Send an event to an Amazon EventBridge event bus.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "event_bus_name": ParameterDef(
                    type="string",
                    description="Name of the EventBridge event bus",
                    required=True,
                ),
                "event_data": ParameterDef(
                    type="object",
                    description="JSON object to send as the event detail",
                    required=True,
                ),
                "detail_type": ParameterDef(
                    type="string",
                    description="Free-form string (max 128 chars) identifying the event type",
                    default="modulex.event",
                ),
            },
        ),
        ActionDefinition(
            name="lambda_create_function",
            description="Create a new AWS Lambda function from inline source code.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "function_name": ParameterDef(
                    type="string",
                    description="Name for the Lambda function",
                    required=True,
                ),
                "role": ParameterDef(
                    type="string",
                    description="IAM Role ARN for the function execution role",
                    required=True,
                ),
                "code": ParameterDef(
                    type="string",
                    description="Function source code (Python handler)",
                    required=True,
                ),
                "runtime": ParameterDef(
                    type="string",
                    description="Lambda runtime: python3.12, python3.11, nodejs20.x, etc.",
                    default="python3.12",
                ),
                "handler": ParameterDef(
                    type="string",
                    description="Handler entrypoint (e.g. lambda_function.lambda_handler)",
                    default="lambda_function.lambda_handler",
                ),
            },
        ),
        ActionDefinition(
            name="lambda_invoke_function",
            description="Invoke an AWS Lambda function synchronously and return its response.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "function_name": ParameterDef(
                    type="string",
                    description="Name or ARN of the Lambda function to invoke",
                    required=True,
                ),
                "event_data": ParameterDef(
                    type="object",
                    description="JSON object to send as the invocation payload",
                ),
            },
        ),
        ActionDefinition(
            name="list_region_options",
            description="List available AWS regions.",
            parameters={},
        ),
        ActionDefinition(
            name="redshift_create_rows",
            description="Insert rows into an Amazon Redshift Serverless table.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "workgroup_name": ParameterDef(
                    type="string",
                    description="Name of the Redshift Serverless workgroup",
                    required=True,
                ),
                "database": ParameterDef(
                    type="string",
                    description="Database name",
                    required=True,
                ),
                "schema_name": ParameterDef(
                    type="string",
                    description="Schema name",
                    required=True,
                ),
                "table": ParameterDef(
                    type="string",
                    description="Table name",
                    required=True,
                ),
                "columns": ParameterDef(
                    type="array",
                    description='List of column names (strings), e.g. ["id", "name"]',
                    required=True,
                ),
                "rows": ParameterDef(
                    type="array",
                    description='List of row arrays, e.g. [[1, "Alice"], [2, "Bob"]]',
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="redshift_delete_rows",
            description="Delete rows from an Amazon Redshift Serverless table.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "workgroup_name": ParameterDef(
                    type="string",
                    description="Name of the Redshift Serverless workgroup",
                    required=True,
                ),
                "database": ParameterDef(
                    type="string",
                    description="Database name",
                    required=True,
                ),
                "schema_name": ParameterDef(
                    type="string",
                    description="Schema name",
                    required=True,
                ),
                "table": ParameterDef(
                    type="string",
                    description="Table name",
                    required=True,
                ),
                "where": ParameterDef(
                    type="string",
                    description="WHERE clause with named parameters, e.g. id = :id",
                    required=True,
                ),
                "sql_parameters": ParameterDef(
                    type="object",
                    description='Named parameter values, e.g. {"id": 1}',
                ),
            },
        ),
        ActionDefinition(
            name="redshift_query_database",
            description="Run a SELECT query against an Amazon Redshift Serverless database.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "workgroup_name": ParameterDef(
                    type="string",
                    description="Name of the Redshift Serverless workgroup",
                    required=True,
                ),
                "database": ParameterDef(
                    type="string",
                    description="Database name",
                    required=True,
                ),
                "columns": ParameterDef(
                    type="array",
                    description='List of column names to retrieve (strings); omit for SELECT *',
                ),
                "from_clause": ParameterDef(
                    type="string",
                    description="FROM clause, e.g. schema_name.table_name",
                    required=True,
                ),
                "where": ParameterDef(
                    type="string",
                    description="WHERE clause with named parameters, e.g. id = :id",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="ORDER BY clause, e.g. column_name ASC",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of rows to return",
                    default=10,
                ),
                "sql_parameters": ParameterDef(
                    type="object",
                    description='Named parameter values, e.g. {"id": 1}',
                ),
            },
        ),
        ActionDefinition(
            name="redshift_update_rows",
            description="Update rows in an Amazon Redshift Serverless table.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "workgroup_name": ParameterDef(
                    type="string",
                    description="Name of the Redshift Serverless workgroup",
                    required=True,
                ),
                "database": ParameterDef(
                    type="string",
                    description="Database name",
                    required=True,
                ),
                "schema_name": ParameterDef(
                    type="string",
                    description="Schema name",
                    required=True,
                ),
                "table": ParameterDef(
                    type="string",
                    description="Table name",
                    required=True,
                ),
                "updates": ParameterDef(
                    type="object",
                    description='Key-value pairs to set, e.g. {"col1": "new_val"}',
                    required=True,
                ),
                "where": ParameterDef(
                    type="string",
                    description="WHERE clause with named parameters, e.g. id = :id",
                    required=True,
                ),
                "sql_parameters": ParameterDef(
                    type="object",
                    description='Named parameter values, e.g. {"id": 1}',
                ),
            },
        ),
        ActionDefinition(
            name="s3_generate_presigned_url",
            description="Generate a presigned URL to download an object from an S3 bucket.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "bucket": ParameterDef(
                    type="string",
                    description="S3 bucket name",
                    required=True,
                ),
                "key": ParameterDef(
                    type="string",
                    description="Object key (path) to generate the URL for",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="s3_upload_base64_as_file",
            description="Upload a base64-encoded string as a file to an S3 bucket.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "bucket": ParameterDef(
                    type="string",
                    description="S3 bucket name",
                    required=True,
                ),
                "filename": ParameterDef(
                    type="string",
                    description="S3 object key (path including filename and extension)",
                    required=True,
                ),
                "data": ParameterDef(
                    type="string",
                    description="Base64-encoded file content",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="sns_send_message",
            description="Publish a message to an Amazon SNS topic.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "topic": ParameterDef(
                    type="string",
                    description="ARN of the SNS topic",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="Message to publish",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="sqs_send_message",
            description="Send a message to an Amazon SQS queue.",
            parameters={
                "region": ParameterDef(
                    type="string",
                    description="AWS region (e.g. us-east-1, eu-west-1)",
                    default="us-east-1",
                ),
                "queue_url": ParameterDef(
                    type="string",
                    description="URL of the SQS queue",
                    required=True,
                ),
                "event_data": ParameterDef(
                    type="object",
                    description="JSON object to send as the message body",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="AWS Access Key",
            description="Authenticate using an AWS access key ID and secret access key.",
            setup_instructions=[
                "Sign in to the AWS Management Console.",
                "Go to IAM > Users > your user > Security credentials.",
                "Create an access key and save both the Access Key ID and Secret Access Key.",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="AWS_ACCESS_KEY_ID",
                    display_name="Access Key ID",
                    description="Your AWS Access Key ID",
                    required=True,
                    sensitive=False,
                    sample_format="AKIAIOSFODNN7EXAMPLE",
                    about_url="https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html",
                ),
                EnvVar(
                    name="AWS_SECRET_ACCESS_KEY",
                    display_name="Secret Access Key",
                    description="Your AWS Secret Access Key",
                    required=True,
                    sensitive=True,
                    sample_format="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15",
                method="GET",
                # AWS STS requires SigV4 signing — runtime cannot
                # synthesize the signature, so this request arrives
                # unsigned and STS returns 403 (or 400 if it can't
                # parse the request at all). We accept those as
                # success: they confirm STS is reachable and the
                # request was well-formed. True credential validation
                # happens at first-call time via boto3 in tools.py.
                success_indicators=SuccessIndicators(
                    status_codes=[200, 400, 403]
                ),
                cost_level="free",
                description=(
                    "Reachability check against AWS STS. Accepts 200 "
                    "(signed request, unlikely), 400 (malformed unsigned), "
                    "or 403 (missing/invalid signature — expected). True "
                    "credential validation runs via boto3 at first call."
                ),
            ),
        ),
    ],
)
