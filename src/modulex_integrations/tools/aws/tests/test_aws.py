"""Happy-path tests for every aws @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from modulex_integrations.tools.aws import (
    TOOLS,
    cloudwatch_logs_put_log_event,
    dynamodb_create_table,
    dynamodb_execute_statement,
    dynamodb_get_item,
    dynamodb_put_item,
    dynamodb_query,
    dynamodb_scan,
    dynamodb_update_item,
    dynamodb_update_table,
    eventbridge_send_event,
    lambda_create_function,
    lambda_invoke_function,
    list_region_options,
    manifest,
    redshift_create_rows,
    redshift_delete_rows,
    redshift_query_database,
    redshift_update_rows,
    s3_generate_presigned_url,
    s3_upload_base64_as_file,
    sns_send_message,
    sqs_send_message,
)
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
    S3GeneratePresignedUrlOutput,
    S3UploadBase64AsFileOutput,
    SnsSendMessageOutput,
    SqsSendMessageOutput,
)

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


BOTO3_CLIENT = "modulex_integrations.tools.aws.tools._get_boto3_client"


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_21_actions(self) -> None:
        assert len(manifest.actions) == 21

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_cloudwatch_logs_put_log_event() -> None:
    mock_client = MagicMock()
    mock_client.put_log_events.return_value = {
        "nextSequenceToken": "seq-token-123",
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await cloudwatch_logs_put_log_event.ainvoke(
            _args(
                log_group_name="/aws/test",
                log_stream_name="stream-1",
                message="test log",
                timestamp=1700000000000,
            )
        )
    assert isinstance(result_dict, dict)
    result = CloudwatchLogsPutLogEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.next_sequence_token == "seq-token-123"


@pytest.mark.asyncio
async def test_dynamodb_create_table() -> None:
    mock_client = MagicMock()
    mock_client.create_table.return_value = {
        "TableDescription": {"TableName": "test-table", "TableStatus": "CREATING"},
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await dynamodb_create_table.ainvoke(
            _args(
                table_name="test-table",
                key_primary_attribute_name="id",
                key_primary_attribute_type="S",
                billing_mode="PAY_PER_REQUEST",
            )
        )
    assert isinstance(result_dict, dict)
    result = DynamodbCreateTableOutput.model_validate(result_dict)
    assert result.success is True
    assert result.table_description is not None


@pytest.mark.asyncio
async def test_dynamodb_execute_statement() -> None:
    mock_client = MagicMock()
    mock_client.execute_statement.return_value = {
        "Items": [{"id": {"S": "1"}, "name": {"S": "Alice"}}],
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await dynamodb_execute_statement.ainvoke(
            _args(statement="SELECT * FROM \"test-table\"")
        )
    assert isinstance(result_dict, dict)
    result = DynamodbExecuteStatementOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_dynamodb_get_item() -> None:
    mock_client = MagicMock()
    mock_client.get_item.return_value = {
        "Item": {"id": {"S": "123"}, "name": {"S": "test"}},
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await dynamodb_get_item.ainvoke(
            _args(table_name="test-table", key={"id": {"S": "123"}})
        )
    assert isinstance(result_dict, dict)
    result = DynamodbGetItemOutput.model_validate(result_dict)
    assert result.success is True
    assert result.item is not None


@pytest.mark.asyncio
async def test_dynamodb_put_item() -> None:
    mock_client = MagicMock()
    mock_client.put_item.return_value = {}
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await dynamodb_put_item.ainvoke(
            _args(
                table_name="test-table",
                item={"id": {"S": "123"}, "name": {"S": "test"}},
            )
        )
    assert isinstance(result_dict, dict)
    result = DynamodbPutItemOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_dynamodb_query() -> None:
    mock_client = MagicMock()
    mock_client.query.return_value = {
        "Items": [{"id": {"S": "1"}}],
        "Count": 1,
        "ScannedCount": 1,
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await dynamodb_query.ainvoke(
            _args(
                table_name="test-table",
                key_condition_expression="id = :id",
                expression_attribute_values={":id": {"S": "1"}},
            )
        )
    assert isinstance(result_dict, dict)
    result = DynamodbQueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_dynamodb_scan() -> None:
    mock_client = MagicMock()
    mock_client.scan.return_value = {
        "Items": [{"id": {"S": "1"}}, {"id": {"S": "2"}}],
        "Count": 2,
        "ScannedCount": 2,
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await dynamodb_scan.ainvoke(
            _args(table_name="test-table")
        )
    assert isinstance(result_dict, dict)
    result = DynamodbScanOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_dynamodb_update_item() -> None:
    mock_client = MagicMock()
    mock_client.update_item.return_value = {
        "Attributes": {"id": {"S": "123"}, "name": {"S": "updated"}},
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await dynamodb_update_item.ainvoke(
            _args(
                table_name="test-table",
                key={"id": {"S": "123"}},
                update_expression="SET #n = :val",
                expression_attribute_names={"#n": "name"},
                expression_attribute_values={":val": {"S": "updated"}},
            )
        )
    assert isinstance(result_dict, dict)
    result = DynamodbUpdateItemOutput.model_validate(result_dict)
    assert result.success is True
    assert result.attributes is not None


@pytest.mark.asyncio
async def test_dynamodb_update_table() -> None:
    mock_client = MagicMock()
    mock_client.update_table.return_value = {
        "TableDescription": {"TableName": "test-table", "TableStatus": "UPDATING"},
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await dynamodb_update_table.ainvoke(
            _args(
                table_name="test-table",
                billing_mode="PAY_PER_REQUEST",
            )
        )
    assert isinstance(result_dict, dict)
    result = DynamodbUpdateTableOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_eventbridge_send_event() -> None:
    mock_client = MagicMock()
    mock_client.put_events.return_value = {
        "FailedEntryCount": 0,
        "Entries": [{"EventId": "evt-123"}],
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await eventbridge_send_event.ainvoke(
            _args(
                event_bus_name="default",
                event_data={"key": "value"},
            )
        )
    assert isinstance(result_dict, dict)
    result = EventbridgeSendEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.failed_entry_count == 0


@pytest.mark.asyncio
async def test_lambda_create_function() -> None:
    mock_client = MagicMock()
    mock_client.create_function.return_value = {
        "FunctionName": "my-func",
        "FunctionArn": "arn:aws:lambda:us-east-1:123:function:my-func",
        "Runtime": "python3.12",
        "Role": "arn:aws:iam::123:role/my-role",
        "Handler": "lambda_function.lambda_handler",
        "CodeSize": 250,
        "State": "Active",
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await lambda_create_function.ainvoke(
            _args(
                function_name="my-func",
                role="arn:aws:iam::123:role/my-role",
                code="def lambda_handler(event, context): return {'statusCode': 200}",
            )
        )
    assert isinstance(result_dict, dict)
    result = LambdaCreateFunctionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.function_name == "my-func"


@pytest.mark.asyncio
async def test_lambda_invoke_function() -> None:
    mock_payload = MagicMock()
    mock_payload.read.return_value = b'{"statusCode": 200}'
    mock_client = MagicMock()
    mock_client.invoke.return_value = {
        "StatusCode": 200,
        "Payload": mock_payload,
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await lambda_invoke_function.ainvoke(
            _args(function_name="my-func", event_data={"test": True})
        )
    assert isinstance(result_dict, dict)
    result = LambdaInvokeFunctionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_list_region_options() -> None:
    mock_client = MagicMock()
    mock_client.describe_regions.return_value = {
        "Regions": [
            {"RegionName": "us-east-1", "Endpoint": "ec2.us-east-1.amazonaws.com", "OptInStatus": "opt-in-not-required"},
            {"RegionName": "eu-west-1", "Endpoint": "ec2.eu-west-1.amazonaws.com", "OptInStatus": "opt-in-not-required"},
        ],
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await list_region_options.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListRegionOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.regions) == 2


@pytest.mark.asyncio
async def test_redshift_create_rows() -> None:
    mock_client = MagicMock()
    mock_client.execute_statement.return_value = {"Id": "stmt-123"}
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await redshift_create_rows.ainvoke(
            _args(
                workgroup_name="default",
                database="dev",
                schema_name="public",
                table="users",
                columns=["id", "name"],
                rows=[[1, "Alice"], [2, "Bob"]],
            )
        )
    assert isinstance(result_dict, dict)
    result = RedshiftCreateRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.statement_id == "stmt-123"


@pytest.mark.asyncio
async def test_redshift_delete_rows() -> None:
    mock_client = MagicMock()
    mock_client.execute_statement.return_value = {"Id": "stmt-456"}
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await redshift_delete_rows.ainvoke(
            _args(
                workgroup_name="default",
                database="dev",
                schema_name="public",
                table="users",
                where="id = 1",
            )
        )
    assert isinstance(result_dict, dict)
    result = RedshiftDeleteRowsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_redshift_query_database() -> None:
    mock_client = MagicMock()
    mock_client.execute_statement.return_value = {"Id": "stmt-789"}
    mock_client.describe_statement.return_value = {"Status": "FINISHED"}
    mock_client.get_statement_result.return_value = {
        "Records": [[{"stringValue": "Alice"}]],
        "TotalNumRows": 1,
        "ColumnMetadata": [{"name": "name", "typeName": "varchar"}],
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await redshift_query_database.ainvoke(
            _args(
                workgroup_name="default",
                database="dev",
                from_clause="public.users",
            )
        )
    assert isinstance(result_dict, dict)
    result = RedshiftQueryDatabaseOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_num_rows == 1


@pytest.mark.asyncio
async def test_redshift_update_rows() -> None:
    mock_client = MagicMock()
    mock_client.execute_statement.return_value = {"Id": "stmt-abc"}
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await redshift_update_rows.ainvoke(
            _args(
                workgroup_name="default",
                database="dev",
                schema_name="public",
                table="users",
                updates={"name": "Updated"},
                where="id = 1",
            )
        )
    assert isinstance(result_dict, dict)
    result = RedshiftUpdateRowsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_s3_generate_presigned_url() -> None:
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/bucket/key?X-Amz-Signature=abc"
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await s3_generate_presigned_url.ainvoke(
            _args(bucket="my-bucket", key="my-file.txt")
        )
    assert isinstance(result_dict, dict)
    result = S3GeneratePresignedUrlOutput.model_validate(result_dict)
    assert result.success is True
    assert result.url is not None


@pytest.mark.asyncio
async def test_s3_upload_base64_as_file() -> None:
    mock_client = MagicMock()
    mock_client.put_object.return_value = {}
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await s3_upload_base64_as_file.ainvoke(
            _args(
                bucket="my-bucket",
                filename="test.txt",
                data="SGVsbG8gV29ybGQ=",
            )
        )
    assert isinstance(result_dict, dict)
    result = S3UploadBase64AsFileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.bucket == "my-bucket"
    assert result.key == "test.txt"


@pytest.mark.asyncio
async def test_sns_send_message() -> None:
    mock_client = MagicMock()
    mock_client.publish.return_value = {"MessageId": "msg-123"}
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await sns_send_message.ainvoke(
            _args(
                topic="arn:aws:sns:us-east-1:123:my-topic",
                message="Hello!",
            )
        )
    assert isinstance(result_dict, dict)
    result = SnsSendMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "msg-123"


@pytest.mark.asyncio
async def test_sqs_send_message() -> None:
    mock_client = MagicMock()
    mock_client.send_message.return_value = {
        "MessageId": "msg-456",
        "MD5OfMessageBody": "abc123",
    }
    with patch(BOTO3_CLIENT, return_value=mock_client):
        result_dict = await sqs_send_message.ainvoke(
            _args(
                queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue",
                event_data={"key": "value"},
            )
        )
    assert isinstance(result_dict, dict)
    result = SqsSendMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "msg-456"


@pytest.mark.asyncio
async def test_dynamodb_get_item_empty_credentials() -> None:
    """Failure-path test: empty credentials should short-circuit."""
    result_dict = await dynamodb_get_item.ainvoke(
        _args(
            auth_data={},
            table_name="test-table",
            key={"id": {"S": "123"}},
        )
    )
    assert isinstance(result_dict, dict)
    result = DynamodbGetItemOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
