"""AWS LangChain @tool functions."""
from __future__ import annotations

import base64
import io
import json
import zipfile
from typing import Any

import boto3  # type: ignore[import-untyped]
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.aws.outputs import (
    CloudwatchLogsPutLogEventOutput,
    DynamodbCreateTableOutput,
    DynamodbExecuteStatementOutput,
    DynamodbGetItemOutput,
    DynamodbPutItemOutput,
    DynamodbQueryOutput,
    DynamodbScanOutput,
    DynamodbUpdateItemOutput,
    DynamodbUpdateTableOutput,
    EventbridgeSendEventOutput,
    LambdaCreateFunctionOutput,
    LambdaInvokeFunctionOutput,
    ListRegionOptionsOutput,
    RedshiftCreateRowsOutput,
    RedshiftDeleteRowsOutput,
    RedshiftQueryDatabaseOutput,
    RedshiftUpdateRowsOutput,
    RegionInfo,
    S3GeneratePresignedUrlOutput,
    S3UploadBase64AsFileOutput,
    SnsSendMessageOutput,
    SqsSendMessageOutput,
)

__all__ = [
    "cloudwatch_logs_put_log_event",
    "dynamodb_create_table",
    "dynamodb_execute_statement",
    "dynamodb_get_item",
    "dynamodb_put_item",
    "dynamodb_query",
    "dynamodb_scan",
    "dynamodb_update_item",
    "dynamodb_update_table",
    "eventbridge_send_event",
    "lambda_create_function",
    "lambda_invoke_function",
    "list_region_options",
    "redshift_create_rows",
    "redshift_delete_rows",
    "redshift_query_database",
    "redshift_update_rows",
    "s3_generate_presigned_url",
    "s3_upload_base64_as_file",
    "sns_send_message",
    "sqs_send_message",
]


def _get_boto3_client(
    service: str,
    auth_data: dict[str, Any],
    region: str = "us-east-1",
) -> Any:
    return boto3.client(
        service,
        aws_access_key_id=auth_data.get("access_key_id", ""),
        aws_secret_access_key=auth_data.get("secret_access_key", ""),
        region_name=region,
    )


# --- Input schemas ------------------------------------------------------------


class CloudwatchLogsPutLogEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    log_group_name: str = Field(description="Name of the CloudWatch log group")
    log_stream_name: str = Field(description="Name of the log stream")
    message: str = Field(description="The log event message")
    timestamp: int = Field(description="Unix timestamp in milliseconds")
    sequence_token: str | None = Field(default=None, description="Sequence token from a previous PutLogEvents call")


class DynamodbCreateTableInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    table_name: str = Field(description="Name of the table to create")
    key_primary_attribute_name: str = Field(description="Name of the partition key")
    key_primary_attribute_type: str = Field(description="Data type of the partition key: S, N, or B")
    key_secondary_attribute_name: str | None = Field(default=None, description="Name of the sort key")
    key_secondary_attribute_type: str | None = Field(default=None, description="Data type of the sort key: S, N, or B")
    billing_mode: str = Field(description="PROVISIONED or PAY_PER_REQUEST")
    read_capacity_units: int | None = Field(default=None, description="Read capacity units")
    write_capacity_units: int | None = Field(default=None, description="Write capacity units")
    stream_specification_enabled: bool | None = Field(default=None, description="Whether DynamoDB Streams is enabled")
    stream_specification_view_type: str | None = Field(default=None, description="Stream view type")


class DynamodbExecuteStatementInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    statement: str = Field(description="PartiQL statement")
    parameters: list[str] | None = Field(default=None, description="Parameter values for the statement")


class DynamodbGetItemInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    table_name: str = Field(description="Name of the DynamoDB table")
    key: dict[str, Any] = Field(description='Item key in DynamoDB JSON format')


class DynamodbPutItemInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    table_name: str = Field(description="Name of the DynamoDB table")
    item: dict[str, Any] = Field(description='Item in DynamoDB JSON format')


class DynamodbQueryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    table_name: str = Field(description="Name of the DynamoDB table")
    key_condition_expression: str = Field(description="Key condition expression")
    projection_expression: str | None = Field(default=None, description="Attributes to retrieve")
    expression_attribute_names: dict[str, str] | None = Field(default=None, description="Attribute name substitutions")
    expression_attribute_values: dict[str, Any] | None = Field(default=None, description="Attribute value substitutions in DynamoDB JSON format")


class DynamodbScanInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    table_name: str = Field(description="Name of the DynamoDB table")
    projection_expression: str | None = Field(default=None, description="Attributes to retrieve")
    filter_expression: str | None = Field(default=None, description="Filter expression")
    expression_attribute_names: dict[str, str] | None = Field(default=None, description="Attribute name substitutions")
    expression_attribute_values: dict[str, Any] | None = Field(default=None, description="Attribute value substitutions in DynamoDB JSON format")
    limit: int | None = Field(default=None, description="Maximum number of items to evaluate")


class DynamodbUpdateItemInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    table_name: str = Field(description="Name of the DynamoDB table")
    key: dict[str, Any] = Field(description='Item key in DynamoDB JSON format')
    update_expression: str | None = Field(default=None, description="Update expression, e.g. SET #n = :val")
    expression_attribute_names: dict[str, str] | None = Field(default=None, description="Attribute name substitutions")
    expression_attribute_values: dict[str, Any] | None = Field(default=None, description="Attribute value substitutions in DynamoDB JSON format")


class DynamodbUpdateTableInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    table_name: str = Field(description="Name of the DynamoDB table")
    billing_mode: str = Field(description="PROVISIONED or PAY_PER_REQUEST")
    read_capacity_units: int | None = Field(default=None, description="Read capacity units")
    write_capacity_units: int | None = Field(default=None, description="Write capacity units")
    stream_specification_enabled: bool | None = Field(default=None, description="Whether DynamoDB Streams is enabled")
    stream_specification_view_type: str | None = Field(default=None, description="Stream view type")


class EventbridgeSendEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    event_bus_name: str = Field(description="Name of the EventBridge event bus")
    event_data: dict[str, Any] = Field(description="JSON object for the event detail")
    detail_type: str = Field(default="modulex.event", description="Free-form event type string")


class LambdaCreateFunctionInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    function_name: str = Field(description="Name for the Lambda function")
    role: str = Field(description="IAM Role ARN for execution")
    code: str = Field(description="Function source code")
    runtime: str = Field(default="python3.12", description="Lambda runtime")
    handler: str = Field(default="lambda_function.lambda_handler", description="Handler entrypoint")


class LambdaInvokeFunctionInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    function_name: str = Field(description="Name or ARN of the Lambda function")
    event_data: dict[str, Any] | None = Field(default=None, description="Invocation payload")


class ListRegionOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class RedshiftCreateRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    workgroup_name: str = Field(description="Redshift Serverless workgroup name")
    database: str = Field(description="Database name")
    schema_name: str = Field(description="Schema name")
    table: str = Field(description="Table name")
    columns: list[str] = Field(description="Column names")
    rows: list[list[Any]] = Field(description="Row data as list of lists")


class RedshiftDeleteRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    workgroup_name: str = Field(description="Redshift Serverless workgroup name")
    database: str = Field(description="Database name")
    schema_name: str = Field(description="Schema name")
    table: str = Field(description="Table name")
    where: str = Field(description="WHERE clause with named parameters")
    sql_parameters: dict[str, Any] | None = Field(default=None, description="Named parameter values")


class RedshiftQueryDatabaseInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    workgroup_name: str = Field(description="Redshift Serverless workgroup name")
    database: str = Field(description="Database name")
    columns: list[str] | None = Field(default=None, description="Columns to retrieve")
    from_clause: str = Field(description="FROM clause, e.g. schema.table")
    where: str | None = Field(default=None, description="WHERE clause with named parameters")
    order_by: str | None = Field(default=None, description="ORDER BY clause")
    limit: int = Field(default=10, description="Max rows to return")
    sql_parameters: dict[str, Any] | None = Field(default=None, description="Named parameter values")


class RedshiftUpdateRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    workgroup_name: str = Field(description="Redshift Serverless workgroup name")
    database: str = Field(description="Database name")
    schema_name: str = Field(description="Schema name")
    table: str = Field(description="Table name")
    updates: dict[str, Any] = Field(description="Key-value pairs to update")
    where: str = Field(description="WHERE clause with named parameters")
    sql_parameters: dict[str, Any] | None = Field(default=None, description="Named parameter values")


class S3GeneratePresignedUrlInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    bucket: str = Field(description="S3 bucket name")
    key: str = Field(description="Object key")


class S3UploadBase64AsFileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    bucket: str = Field(description="S3 bucket name")
    filename: str = Field(description="S3 object key (path + filename)")
    data: str = Field(description="Base64-encoded file content")


class SnsSendMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    topic: str = Field(description="ARN of the SNS topic")
    message: str = Field(description="Message to publish")


class SqsSendMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default="us-east-1", description="AWS region")
    queue_url: str = Field(description="URL of the SQS queue")
    event_data: dict[str, Any] = Field(description="JSON object for the message body")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=CloudwatchLogsPutLogEventInput)
@serialize_pydantic_return
async def cloudwatch_logs_put_log_event(
    auth_type: str,
    auth_data: dict[str, Any],
    log_group_name: str,
    log_stream_name: str,
    message: str,
    timestamp: int,
    region: str = "us-east-1",
    sequence_token: str | None = None,
) -> CloudwatchLogsPutLogEventOutput:
    """Upload a log event to a specified CloudWatch Logs log stream."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return CloudwatchLogsPutLogEventOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("logs", auth_data, region)
        params: dict[str, Any] = {
            "logGroupName": log_group_name,
            "logStreamName": log_stream_name,
            "logEvents": [{"timestamp": timestamp, "message": message}],
        }
        if sequence_token:
            params["sequenceToken"] = sequence_token
        resp = client.put_log_events(**params)
    except Exception as exc:
        return CloudwatchLogsPutLogEventOutput(success=False, error=str(exc))
    return CloudwatchLogsPutLogEventOutput(
        success=True,
        next_sequence_token=resp.get("nextSequenceToken"),
        rejected_log_events_info=resp.get("rejectedLogEventsInfo"),
    )


@tool(args_schema=DynamodbCreateTableInput)
@serialize_pydantic_return
async def dynamodb_create_table(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    key_primary_attribute_name: str,
    key_primary_attribute_type: str,
    billing_mode: str,
    region: str = "us-east-1",
    key_secondary_attribute_name: str | None = None,
    key_secondary_attribute_type: str | None = None,
    read_capacity_units: int | None = None,
    write_capacity_units: int | None = None,
    stream_specification_enabled: bool | None = None,
    stream_specification_view_type: str | None = None,
) -> DynamodbCreateTableOutput:
    """Create a new DynamoDB table with configurable key schema, billing mode, and optional streams."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return DynamodbCreateTableOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("dynamodb", auth_data, region)
        key_schema = [{"AttributeName": key_primary_attribute_name, "KeyType": "HASH"}]
        attr_defs = [{"AttributeName": key_primary_attribute_name, "AttributeType": key_primary_attribute_type}]
        if key_secondary_attribute_name and key_secondary_attribute_type:
            key_schema.append({"AttributeName": key_secondary_attribute_name, "KeyType": "RANGE"})
            attr_defs.append({"AttributeName": key_secondary_attribute_name, "AttributeType": key_secondary_attribute_type})
        params: dict[str, Any] = {
            "TableName": table_name,
            "KeySchema": key_schema,
            "AttributeDefinitions": attr_defs,
            "BillingMode": billing_mode,
        }
        if billing_mode == "PROVISIONED" and read_capacity_units and write_capacity_units:
            params["ProvisionedThroughput"] = {
                "ReadCapacityUnits": read_capacity_units,
                "WriteCapacityUnits": write_capacity_units,
            }
        if stream_specification_enabled is not None:
            stream_spec: dict[str, Any] = {"StreamEnabled": stream_specification_enabled}
            if stream_specification_view_type:
                stream_spec["StreamViewType"] = stream_specification_view_type
            params["StreamSpecification"] = stream_spec
        resp = client.create_table(**params)
    except Exception as exc:
        return DynamodbCreateTableOutput(success=False, error=str(exc))
    return DynamodbCreateTableOutput(
        success=True,
        table_description=resp.get("TableDescription"),
    )


@tool(args_schema=DynamodbExecuteStatementInput)
@serialize_pydantic_return
async def dynamodb_execute_statement(
    auth_type: str,
    auth_data: dict[str, Any],
    statement: str,
    region: str = "us-east-1",
    parameters: list[str] | None = None,
) -> DynamodbExecuteStatementOutput:
    """Execute a PartiQL statement against DynamoDB for reads or writes."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return DynamodbExecuteStatementOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("dynamodb", auth_data, region)
        params: dict[str, Any] = {"Statement": statement}
        if parameters:
            params["Parameters"] = [{"S": p} for p in parameters]
        all_items: list[dict[str, Any]] = []
        max_pages = 50
        pages_seen = 0
        while pages_seen < max_pages:
            pages_seen += 1
            resp = client.execute_statement(**params)
            all_items.extend(resp.get("Items", []))
            next_token = resp.get("NextToken")
            if not next_token:
                break
            params["NextToken"] = next_token
    except Exception as exc:
        return DynamodbExecuteStatementOutput(success=False, error=str(exc))
    return DynamodbExecuteStatementOutput(success=True, items=all_items)


@tool(args_schema=DynamodbGetItemInput)
@serialize_pydantic_return
async def dynamodb_get_item(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    key: dict[str, Any],
    region: str = "us-east-1",
) -> DynamodbGetItemOutput:
    """Retrieve an item from a DynamoDB table by its primary key."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return DynamodbGetItemOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("dynamodb", auth_data, region)
        resp = client.get_item(TableName=table_name, Key=key)
    except Exception as exc:
        return DynamodbGetItemOutput(success=False, error=str(exc))
    return DynamodbGetItemOutput(success=True, item=resp.get("Item"))


@tool(args_schema=DynamodbPutItemInput)
@serialize_pydantic_return
async def dynamodb_put_item(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    item: dict[str, Any],
    region: str = "us-east-1",
) -> DynamodbPutItemOutput:
    """Create or replace an item in a DynamoDB table."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return DynamodbPutItemOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("dynamodb", auth_data, region)
        resp = client.put_item(TableName=table_name, Item=item)
    except Exception as exc:
        return DynamodbPutItemOutput(success=False, error=str(exc))
    return DynamodbPutItemOutput(success=True, attributes=resp.get("Attributes"))


@tool(args_schema=DynamodbQueryInput)
@serialize_pydantic_return
async def dynamodb_query(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    key_condition_expression: str,
    region: str = "us-east-1",
    projection_expression: str | None = None,
    expression_attribute_names: dict[str, str] | None = None,
    expression_attribute_values: dict[str, Any] | None = None,
) -> DynamodbQueryOutput:
    """Query items from a DynamoDB table based on key conditions."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return DynamodbQueryOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("dynamodb", auth_data, region)
        params: dict[str, Any] = {
            "TableName": table_name,
            "KeyConditionExpression": key_condition_expression,
        }
        if projection_expression:
            params["ProjectionExpression"] = projection_expression
        if expression_attribute_names:
            params["ExpressionAttributeNames"] = expression_attribute_names
        if expression_attribute_values:
            params["ExpressionAttributeValues"] = expression_attribute_values
        all_items: list[dict[str, Any]] = []
        total_count = 0
        total_scanned = 0
        max_pages = 50
        pages_seen = 0
        while pages_seen < max_pages:
            pages_seen += 1
            resp = client.query(**params)
            all_items.extend(resp.get("Items", []))
            total_count += resp.get("Count", 0)
            total_scanned += resp.get("ScannedCount", 0)
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            params["ExclusiveStartKey"] = last_key
    except Exception as exc:
        return DynamodbQueryOutput(success=False, error=str(exc))
    return DynamodbQueryOutput(
        success=True,
        items=all_items,
        count=total_count,
        scanned_count=total_scanned,
    )


@tool(args_schema=DynamodbScanInput)
@serialize_pydantic_return
async def dynamodb_scan(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    region: str = "us-east-1",
    projection_expression: str | None = None,
    filter_expression: str | None = None,
    expression_attribute_names: dict[str, str] | None = None,
    expression_attribute_values: dict[str, Any] | None = None,
    limit: int | None = None,
) -> DynamodbScanOutput:
    """Scan all items in a DynamoDB table with optional filtering."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return DynamodbScanOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("dynamodb", auth_data, region)
        params: dict[str, Any] = {"TableName": table_name}
        if projection_expression:
            params["ProjectionExpression"] = projection_expression
        if filter_expression:
            params["FilterExpression"] = filter_expression
        if expression_attribute_names:
            params["ExpressionAttributeNames"] = expression_attribute_names
        if expression_attribute_values:
            params["ExpressionAttributeValues"] = expression_attribute_values
        if limit is not None:
            params["Limit"] = limit
        all_items: list[dict[str, Any]] = []
        total_count = 0
        total_scanned = 0
        max_pages = 50
        pages_seen = 0
        while pages_seen < max_pages:
            pages_seen += 1
            resp = client.scan(**params)
            all_items.extend(resp.get("Items", []))
            total_count += resp.get("Count", 0)
            total_scanned += resp.get("ScannedCount", 0)
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            params["ExclusiveStartKey"] = last_key
    except Exception as exc:
        return DynamodbScanOutput(success=False, error=str(exc))
    return DynamodbScanOutput(
        success=True,
        items=all_items,
        count=total_count,
        scanned_count=total_scanned,
    )


@tool(args_schema=DynamodbUpdateItemInput)
@serialize_pydantic_return
async def dynamodb_update_item(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    key: dict[str, Any],
    region: str = "us-east-1",
    update_expression: str | None = None,
    expression_attribute_names: dict[str, str] | None = None,
    expression_attribute_values: dict[str, Any] | None = None,
) -> DynamodbUpdateItemOutput:
    """Update attributes of an existing item or add a new item in a DynamoDB table."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return DynamodbUpdateItemOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("dynamodb", auth_data, region)
        params: dict[str, Any] = {
            "TableName": table_name,
            "Key": key,
            "ReturnValues": "ALL_NEW",
        }
        if update_expression:
            params["UpdateExpression"] = update_expression
        if expression_attribute_names:
            params["ExpressionAttributeNames"] = expression_attribute_names
        if expression_attribute_values:
            params["ExpressionAttributeValues"] = expression_attribute_values
        resp = client.update_item(**params)
    except Exception as exc:
        return DynamodbUpdateItemOutput(success=False, error=str(exc))
    return DynamodbUpdateItemOutput(success=True, attributes=resp.get("Attributes"))


@tool(args_schema=DynamodbUpdateTableInput)
@serialize_pydantic_return
async def dynamodb_update_table(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    billing_mode: str,
    region: str = "us-east-1",
    read_capacity_units: int | None = None,
    write_capacity_units: int | None = None,
    stream_specification_enabled: bool | None = None,
    stream_specification_view_type: str | None = None,
) -> DynamodbUpdateTableOutput:
    """Modify settings for a DynamoDB table such as billing mode, capacity, or streams."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return DynamodbUpdateTableOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("dynamodb", auth_data, region)
        params: dict[str, Any] = {
            "TableName": table_name,
            "BillingMode": billing_mode,
        }
        if billing_mode == "PROVISIONED" and read_capacity_units and write_capacity_units:
            params["ProvisionedThroughput"] = {
                "ReadCapacityUnits": read_capacity_units,
                "WriteCapacityUnits": write_capacity_units,
            }
        if stream_specification_enabled is not None:
            stream_spec: dict[str, Any] = {"StreamEnabled": stream_specification_enabled}
            if stream_specification_view_type:
                stream_spec["StreamViewType"] = stream_specification_view_type
            params["StreamSpecification"] = stream_spec
        resp = client.update_table(**params)
    except Exception as exc:
        return DynamodbUpdateTableOutput(success=False, error=str(exc))
    return DynamodbUpdateTableOutput(
        success=True,
        table_description=resp.get("TableDescription"),
    )


@tool(args_schema=EventbridgeSendEventInput)
@serialize_pydantic_return
async def eventbridge_send_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_bus_name: str,
    event_data: dict[str, Any],
    region: str = "us-east-1",
    detail_type: str = "modulex.event",
) -> EventbridgeSendEventOutput:
    """Send an event to an Amazon EventBridge event bus."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return EventbridgeSendEventOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("events", auth_data, region)
        resp = client.put_events(
            Entries=[
                {
                    "Source": "modulex",
                    "DetailType": detail_type,
                    "Detail": json.dumps(event_data),
                    "EventBusName": event_bus_name,
                },
            ],
        )
    except Exception as exc:
        return EventbridgeSendEventOutput(success=False, error=str(exc))
    return EventbridgeSendEventOutput(
        success=True,
        failed_entry_count=resp.get("FailedEntryCount"),
        entries=resp.get("Entries", []),
    )


@tool(args_schema=LambdaCreateFunctionInput)
@serialize_pydantic_return
async def lambda_create_function(
    auth_type: str,
    auth_data: dict[str, Any],
    function_name: str,
    role: str,
    code: str,
    region: str = "us-east-1",
    runtime: str = "python3.12",
    handler: str = "lambda_function.lambda_handler",
) -> LambdaCreateFunctionOutput:
    """Create a new AWS Lambda function from inline source code."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return LambdaCreateFunctionOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            entry_file = handler.split(".")[0] + ".py" if "." in handler else "lambda_function.py"
            zf.writestr(entry_file, code)
        buf.seek(0)
        client = _get_boto3_client("lambda", auth_data, region)
        resp = client.create_function(
            FunctionName=function_name,
            Runtime=runtime,
            Role=role,
            Handler=handler,
            Code={"ZipFile": buf.read()},
        )
    except Exception as exc:
        return LambdaCreateFunctionOutput(success=False, error=str(exc))
    return LambdaCreateFunctionOutput(
        success=True,
        function_name=resp.get("FunctionName"),
        function_arn=resp.get("FunctionArn"),
        runtime=resp.get("Runtime"),
        role=resp.get("Role"),
        handler=resp.get("Handler"),
        code_size=resp.get("CodeSize"),
        last_modified=resp.get("LastModified"),
        state=resp.get("State"),
    )


@tool(args_schema=LambdaInvokeFunctionInput)
@serialize_pydantic_return
async def lambda_invoke_function(
    auth_type: str,
    auth_data: dict[str, Any],
    function_name: str,
    region: str = "us-east-1",
    event_data: dict[str, Any] | None = None,
) -> LambdaInvokeFunctionOutput:
    """Invoke an AWS Lambda function synchronously and return its response."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return LambdaInvokeFunctionOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("lambda", auth_data, region)
        params: dict[str, Any] = {
            "FunctionName": function_name,
            "InvocationType": "RequestResponse",
        }
        if event_data is not None:
            params["Payload"] = json.dumps(event_data)
        resp = client.invoke(**params)
        payload_bytes = resp.get("Payload")
        payload = None
        if payload_bytes:
            payload_str = payload_bytes.read().decode("utf-8")
            try:
                payload = json.loads(payload_str)
            except (json.JSONDecodeError, ValueError):
                payload = payload_str
    except Exception as exc:
        return LambdaInvokeFunctionOutput(success=False, error=str(exc))
    return LambdaInvokeFunctionOutput(
        success=True,
        status_code=resp.get("StatusCode"),
        payload=payload,
        function_error=resp.get("FunctionError"),
        executed_version=resp.get("ExecutedVersion"),
    )


@tool(args_schema=ListRegionOptionsInput)
@serialize_pydantic_return
async def list_region_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListRegionOptionsOutput:
    """List available AWS regions."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return ListRegionOptionsOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("ec2", auth_data, "us-east-1")
        resp = client.describe_regions(AllRegions=True)
        regions = [
            RegionInfo(
                region_name=r.get("RegionName"),
                endpoint=r.get("Endpoint"),
                opt_in_status=r.get("OptInStatus"),
            )
            for r in resp.get("Regions", [])
        ]
    except Exception as exc:
        return ListRegionOptionsOutput(success=False, error=str(exc))
    return ListRegionOptionsOutput(success=True, regions=regions)


def _build_redshift_sql_params(sql_parameters: dict[str, Any] | None) -> list[dict[str, str]]:
    if not sql_parameters:
        return []
    result: list[dict[str, str]] = []
    for name, value in sql_parameters.items():
        result.append({"name": name, "value": str(value)})
    return result


def _execute_redshift_statement(
    auth_data: dict[str, Any],
    region: str,
    workgroup_name: str,
    database: str,
    sql: str,
    sql_parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    client = _get_boto3_client("redshift-data", auth_data, region)
    params: dict[str, Any] = {
        "WorkgroupName": workgroup_name,
        "Database": database,
        "Sql": sql,
    }
    rs_params = _build_redshift_sql_params(sql_parameters)
    if rs_params:
        params["Parameters"] = rs_params
    return client.execute_statement(**params)  # type: ignore[no-any-return]


@tool(args_schema=RedshiftCreateRowsInput)
@serialize_pydantic_return
async def redshift_create_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    workgroup_name: str,
    database: str,
    schema_name: str,
    table: str,
    columns: list[str],
    rows: list[list[Any]],
    region: str = "us-east-1",
) -> RedshiftCreateRowsOutput:
    """Insert rows into an Amazon Redshift Serverless table."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return RedshiftCreateRowsOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        col_list = ", ".join(columns)
        value_rows: list[str] = []
        for row in rows:
            vals = ", ".join(
                "NULL" if v is None else f"'{v}'" if isinstance(v, str) else str(v)
                for v in row
            )
            value_rows.append(f"({vals})")
        values_sql = ", ".join(value_rows)
        sql = f"INSERT INTO {schema_name}.{table} ({col_list}) VALUES {values_sql}"
        resp = _execute_redshift_statement(auth_data, region, workgroup_name, database, sql)
    except Exception as exc:
        return RedshiftCreateRowsOutput(success=False, error=str(exc))
    return RedshiftCreateRowsOutput(success=True, statement_id=resp.get("Id"))


@tool(args_schema=RedshiftDeleteRowsInput)
@serialize_pydantic_return
async def redshift_delete_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    workgroup_name: str,
    database: str,
    schema_name: str,
    table: str,
    where: str,
    region: str = "us-east-1",
    sql_parameters: dict[str, Any] | None = None,
) -> RedshiftDeleteRowsOutput:
    """Delete rows from an Amazon Redshift Serverless table."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return RedshiftDeleteRowsOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        sql = f"DELETE FROM {schema_name}.{table} WHERE {where}"
        resp = _execute_redshift_statement(
            auth_data, region, workgroup_name, database, sql, sql_parameters,
        )
    except Exception as exc:
        return RedshiftDeleteRowsOutput(success=False, error=str(exc))
    return RedshiftDeleteRowsOutput(success=True, statement_id=resp.get("Id"))


@tool(args_schema=RedshiftQueryDatabaseInput)
@serialize_pydantic_return
async def redshift_query_database(
    auth_type: str,
    auth_data: dict[str, Any],
    workgroup_name: str,
    database: str,
    from_clause: str,
    region: str = "us-east-1",
    columns: list[str] | None = None,
    where: str | None = None,
    order_by: str | None = None,
    limit: int = 10,
    sql_parameters: dict[str, Any] | None = None,
) -> RedshiftQueryDatabaseOutput:
    """Run a SELECT query against an Amazon Redshift Serverless database."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return RedshiftQueryDatabaseOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        col_list = ", ".join(columns) if columns else "*"
        sql = f"SELECT {col_list} FROM {from_clause}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        sql += f" LIMIT {limit}"
        resp = _execute_redshift_statement(
            auth_data, region, workgroup_name, database, sql, sql_parameters,
        )
        import time
        client = _get_boto3_client("redshift-data", auth_data, region)
        statement_id = resp["Id"]
        for _ in range(60):
            status_resp = client.describe_statement(Id=statement_id)
            status = status_resp.get("Status")
            if status in ("FINISHED", "FAILED", "ABORTED"):
                break
            time.sleep(1)
        if status != "FINISHED":
            return RedshiftQueryDatabaseOutput(
                success=False,
                error=f"Query did not finish: status={status}",
            )
        result_resp = client.get_statement_result(Id=statement_id)
    except Exception as exc:
        return RedshiftQueryDatabaseOutput(success=False, error=str(exc))
    return RedshiftQueryDatabaseOutput(
        success=True,
        records=result_resp.get("Records", []),
        total_num_rows=result_resp.get("TotalNumRows"),
        column_metadata=result_resp.get("ColumnMetadata", []),
    )


@tool(args_schema=RedshiftUpdateRowsInput)
@serialize_pydantic_return
async def redshift_update_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    workgroup_name: str,
    database: str,
    schema_name: str,
    table: str,
    updates: dict[str, Any],
    where: str,
    region: str = "us-east-1",
    sql_parameters: dict[str, Any] | None = None,
) -> RedshiftUpdateRowsOutput:
    """Update rows in an Amazon Redshift Serverless table."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return RedshiftUpdateRowsOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        set_clauses = ", ".join(
            f"{col} = '{val}'" if isinstance(val, str) else f"{col} = {val}"
            for col, val in updates.items()
        )
        sql = f"UPDATE {schema_name}.{table} SET {set_clauses} WHERE {where}"
        resp = _execute_redshift_statement(
            auth_data, region, workgroup_name, database, sql, sql_parameters,
        )
    except Exception as exc:
        return RedshiftUpdateRowsOutput(success=False, error=str(exc))
    return RedshiftUpdateRowsOutput(success=True, statement_id=resp.get("Id"))


@tool(args_schema=S3GeneratePresignedUrlInput)
@serialize_pydantic_return
async def s3_generate_presigned_url(
    auth_type: str,
    auth_data: dict[str, Any],
    bucket: str,
    key: str,
    region: str = "us-east-1",
) -> S3GeneratePresignedUrlOutput:
    """Generate a presigned URL to download an object from an S3 bucket."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return S3GeneratePresignedUrlOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("s3", auth_data, region)
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )
    except Exception as exc:
        return S3GeneratePresignedUrlOutput(success=False, error=str(exc))
    return S3GeneratePresignedUrlOutput(success=True, url=url)


@tool(args_schema=S3UploadBase64AsFileInput)
@serialize_pydantic_return
async def s3_upload_base64_as_file(
    auth_type: str,
    auth_data: dict[str, Any],
    bucket: str,
    filename: str,
    data: str,
    region: str = "us-east-1",
) -> S3UploadBase64AsFileOutput:
    """Upload a base64-encoded string as a file to an S3 bucket."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return S3UploadBase64AsFileOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        file_bytes = base64.b64decode(data)
        client = _get_boto3_client("s3", auth_data, region)
        client.put_object(Bucket=bucket, Key=filename, Body=file_bytes)
    except Exception as exc:
        return S3UploadBase64AsFileOutput(success=False, error=str(exc))
    return S3UploadBase64AsFileOutput(success=True, bucket=bucket, key=filename)


@tool(args_schema=SnsSendMessageInput)
@serialize_pydantic_return
async def sns_send_message(
    auth_type: str,
    auth_data: dict[str, Any],
    topic: str,
    message: str,
    region: str = "us-east-1",
) -> SnsSendMessageOutput:
    """Publish a message to an Amazon SNS topic."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return SnsSendMessageOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("sns", auth_data, region)
        resp = client.publish(TopicArn=topic, Message=message)
    except Exception as exc:
        return SnsSendMessageOutput(success=False, error=str(exc))
    return SnsSendMessageOutput(success=True, message_id=resp.get("MessageId"))


@tool(args_schema=SqsSendMessageInput)
@serialize_pydantic_return
async def sqs_send_message(
    auth_type: str,
    auth_data: dict[str, Any],
    queue_url: str,
    event_data: dict[str, Any],
    region: str = "us-east-1",
) -> SqsSendMessageOutput:
    """Send a message to an Amazon SQS queue."""
    if not auth_data.get("access_key_id") or not auth_data.get("secret_access_key"):
        return SqsSendMessageOutput(success=False, error="Missing AWS credentials (access_key_id / secret_access_key).")
    try:
        client = _get_boto3_client("sqs", auth_data, region)
        resp = client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event_data),
        )
    except Exception as exc:
        return SqsSendMessageOutput(success=False, error=str(exc))
    return SqsSendMessageOutput(
        success=True,
        message_id=resp.get("MessageId"),
        md5_of_message_body=resp.get("MD5OfMessageBody"),
        sequence_number=resp.get("SequenceNumber"),
    )
