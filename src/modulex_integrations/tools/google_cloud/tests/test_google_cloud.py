"""Happy-path tests for every google_cloud @tool, plus a manifest sanity check.

JWT signing is mocked out via ``unittest.mock.patch`` on the
``_get_access_token`` helper to avoid generating real RSA signatures in the
test path.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from modulex_integrations.tools.google_cloud import (
    TOOLS,
    bigquery_insert_rows,
    create_bucket,
    create_scheduled_query,
    get_bucket,
    get_object,
    list_buckets,
    logging_write_log,
    manifest,
    run_query,
    search_objects,
    switch_instance_boot_status,
    upload_object,
)
from modulex_integrations.tools.google_cloud.outputs import (
    BigqueryInsertRowsOutput,
    CreateBucketOutput,
    CreateScheduledQueryOutput,
    GetBucketOutput,
    GetObjectOutput,
    ListBucketsOutput,
    LoggingWriteLogOutput,
    RunQueryOutput,
    SearchObjectsOutput,
    SwitchInstanceBootStatusOutput,
    UploadObjectOutput,
)

_STORAGE_API = "https://storage.googleapis.com/storage/v1"
_STORAGE_UPLOAD_API = "https://storage.googleapis.com/upload/storage/v1"
_BIGQUERY_API = "https://bigquery.googleapis.com/bigquery/v2"
_LOGGING_API = "https://logging.googleapis.com/v2"
_COMPUTE_API = "https://compute.googleapis.com/compute/v1"
_DATA_TRANSFER_API = "https://bigquerydatatransfer.googleapis.com/v1"


def _patch_access_token() -> Any:
    """Patch _get_access_token so tests skip real JWT signing."""
    return patch(
        "modulex_integrations.tools.google_cloud.tools._get_access_token",
        new_callable=AsyncMock,
        return_value="fake-token",
    )

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "key_json": '{"type":"service_account","project_id":"test-project","client_email":"test@test.iam.gserviceaccount.com","private_key":"-----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEA2a2rwplBQLHgMHcPs0DTmEsDXAqG3bL0xL9ROcBqOq0J1JHm\\nFnjEIFMtYdVKwP/oLNP6HE9DYVhKCuakLePt9TjI8I0zFm2bPqlZOSkX8CZ7BQRZ\\nP3oquRfOdLCR8K7k82OjYPjpKMbp5ycVxGXDDmLVZHOaKxIzGklFwjF5g/JVBjBK\\nJFMM0a2p0lxU2ljk64MN6T9D1+CVD8t4+v7IW+3WRl8F1KN9TFJmcdJSKcQZJHRK\\nrPK0UGmH09v4v60J+eKzPH3TQ4Ouk+Nhw8NG9zN3MJKC1RGR2RIhzrdVoF3FO5T\\naqEkK+n/e72KcSzWV0OChSr4GIlaqm82n3fz/wIDAQABAoIBAC5RgZ+hBx7xHNaM\\npPgwGMb2llLlPjHRHHTBhuXylhBBZSz0FPNMivT/qMeeoUp8B7YlQ8BoG+6nMYBv\\nQHqJzjbLz5Nt7RNBh7xQOhJQf7Yj1Aq3XJxZ3Vkp3Nz9dJGCWkkv0YKn3D5rMQ1\\nVXbQC3kpe6QYQZ/TnKg3QXq0aZ2W3c9M/+J8FNPWAa1Abz4TeER9HGJHMnSvp6x\\nv/Bk4dq+tpe/7VE7G3h7kYDALGXAK11FOmHXfzgkkQoeLjR+MjjH7bsNU8djfRRb\\n5+M3cRcGEql+K8FpNQN0Nf/5/KVd5TNHbm4l5m3rPGOAKXB/9gHVfELAJafNRM2M\\ng2Go8WECgYEA8T/K19m9VdmFaaMN8LInaOBOjz7AS/EvAogJV5G2dCedS8uzq0U7\\nm6f/V9BEbb7r5xxfL3CVqf4LxfVZT3x4eOTlq+xjNkxf89SX5OjKn7C0Y1cVRPw\\nQ8L9Xxbz8bYQOE7Z0bGIiKGQJRaiqfn7aN2T7PEG/7IREZ+CTWxQmSECgYEA5ydK\\nwKzFER7YZpIxOGBBk+4s7L2Uw6q2GKzrGuf1ldHFqLBM8JjjHWuCfGo7djHGef4w\\n1fF8qWCkJTd6frf/RcZ2X9Pj7S8KF8lG3jyGJR8C1vx7GElJQs2gI6a1LJXPvaz3\\nxUVlq0laf2R5JkLn0IZ/HT7q/wRn1KQTNpAHh/8CgYBN+TfJWZwG2PYkdPd7M1Iv\\nVyrNSO2CxjJIrulT3y+jn7SD9mWXRu3P3nIBPn5h5oSu8OWC0tjn0O0/NZEfwJ+w\\nNB6kxVZ6CRot6J51d2W+6v7aFxIIaXC+Z0FYBJy0rZ6E0GuhxcXG+P+HvajsVe2j\\nwMIW/BIGkHVNWRj3U6lAAQKBgQCe/pu+9UUqCGXkJ4HKdkXS0P4cxfRJT1mZMg+C\\nqhVOtnKT+v3sh4C2D+vIYwHpJI+sOWfjt8h0VPBQ1+U3B9y9tH/fGPNYaexhl1nX\\n6x0BQf4KYFDsLjgLfPF1RCVK3cfjKIVXBIJDz5k6bp+vM3lVOqpVJurFJG3RJYQ+\\nzGHDzwKBgQCvnZ6HPwNlR2w6T+a9DGJ1XT5JlGBFp8bKZsYRRBpf8uZFgrvFVT23\\nYGEVL5JF+jQQ7wONn0iNbK+7Cy5YD/wZ7ATi3Nf+VVEpYi7DifBZc/xaJJ/IfIVy\\nfAnT05RHjs5ZiN3dnT5P1DrDYq4VV1dn8SqUx3MOojW8M/EyMKJh5A==\\n-----END RSA PRIVATE KEY-----\\n","private_key_id":"key1","client_id":"123","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token"}'
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a .ainvoke() input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_11_actions(self) -> None:
        assert len(manifest.actions) == 11

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_create_bucket(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_STORAGE_API}/b?project=test-project",
        json={
            "id": "test-bucket",
            "name": "test-bucket",
            "location": "US",
            "storageClass": "STANDARD",
            "timeCreated": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z",
            "projectNumber": "123456",
        },
    )

    with _patch_access_token():
        result_dict = await create_bucket.ainvoke(_args(bucket_name="test-bucket"))

    assert isinstance(result_dict, dict)
    result = CreateBucketOutput.model_validate(result_dict)
    assert result.success is True
    assert result.bucket is not None
    assert result.bucket.name == "test-bucket"


@pytest.mark.asyncio
async def test_get_bucket(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_STORAGE_API}/b/my-bucket",
        json={
            "id": "my-bucket",
            "name": "my-bucket",
            "location": "US",
            "storageClass": "STANDARD",
            "timeCreated": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z",
        },
    )

    with _patch_access_token():
        result_dict = await get_bucket.ainvoke(_args(bucket_name="my-bucket"))

    assert isinstance(result_dict, dict)
    result = GetBucketOutput.model_validate(result_dict)
    assert result.success is True
    assert result.bucket is not None
    assert result.bucket.name == "my-bucket"


@pytest.mark.asyncio
async def test_list_buckets(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_STORAGE_API}/b?project=test-project",
        json={
            "items": [
                {"id": "b1", "name": "bucket-1", "location": "US"},
                {"id": "b2", "name": "bucket-2", "location": "EU"},
            ]
        },
    )

    with _patch_access_token():
        result_dict = await list_buckets.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListBucketsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.buckets) == 2


@pytest.mark.asyncio
async def test_search_objects(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_STORAGE_API}/b/my-bucket/o?prefix=docs%2F",
        json={
            "items": [
                {"name": "docs/file1.txt", "bucket": "my-bucket", "size": "1024"},
            ]
        },
    )

    with _patch_access_token():
        result_dict = await search_objects.ainvoke(_args(bucket_name="my-bucket", prefix="docs/"))

    assert isinstance(result_dict, dict)
    result = SearchObjectsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.objects) >= 1


@pytest.mark.asyncio
async def test_get_object(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{_STORAGE_API}/b/my-bucket/o/path%2Fto%2Ffile.txt",
        json={
            "name": "path/to/file.txt",
            "bucket": "my-bucket",
            "size": "2048",
            "contentType": "text/plain",
        },
    )

    with _patch_access_token():
        result_dict = await get_object.ainvoke(_args(bucket_name="my-bucket", object_name="path/to/file.txt"))

    assert isinstance(result_dict, dict)
    result = GetObjectOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None
    assert result.metadata.name == "path/to/file.txt"


@pytest.mark.asyncio
async def test_upload_object(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_STORAGE_UPLOAD_API}/b/my-bucket/o?uploadType=media&name=hello.txt",
        json={
            "name": "hello.txt",
            "bucket": "my-bucket",
        },
    )

    with _patch_access_token():
        result_dict = await upload_object.ainvoke(
            _args(bucket_name="my-bucket", object_name="hello.txt", content="Hello, world!")
        )

    assert isinstance(result_dict, dict)
    result = UploadObjectOutput.model_validate(result_dict)
    assert result.success is True
    assert result.object_name == "hello.txt"


@pytest.mark.asyncio
async def test_logging_write_log(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_LOGGING_API}/entries:write",
        json={},
    )

    with _patch_access_token():
        result_dict = await logging_write_log.ainvoke(
            _args(log_name="my-log", text="Hello from test", severity="INFO")
        )

    assert isinstance(result_dict, dict)
    result = LoggingWriteLogOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_run_query(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_BIGQUERY_API}/projects/test-project/queries",
        json={
            "schema": {"fields": [{"name": "col1"}, {"name": "col2"}]},
            "rows": [{"f": [{"v": "val1"}, {"v": "val2"}]}],
            "totalRows": "1",
        },
    )

    with _patch_access_token():
        result_dict = await run_query.ainvoke(_args(query="SELECT 1"))

    assert isinstance(result_dict, dict)
    result = RunQueryOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.rows) == 1


@pytest.mark.asyncio
async def test_bigquery_insert_rows(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_BIGQUERY_API}/projects/test-project/datasets/my_dataset/tables/my_table/insertAll",
        json={},
    )

    with _patch_access_token():
        result_dict = await bigquery_insert_rows.ainvoke(
            _args(dataset_id="my_dataset", table_id="my_table", rows=[{"name": "test", "value": 42}])
        )

    assert isinstance(result_dict, dict)
    result = BigqueryInsertRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.inserted_count == 1


@pytest.mark.asyncio
async def test_create_scheduled_query(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_DATA_TRANSFER_API}/projects/test-project/locations/us/transferConfigs",
        json={
            "name": "projects/test-project/locations/us/transferConfigs/123",
            "displayName": "My Query",
            "dataSourceId": "scheduled_query",
            "schedule": "every 24 hours",
            "state": "PENDING",
            "destinationDatasetId": "my_dataset",
        },
    )

    with _patch_access_token():
        result_dict = await create_scheduled_query.ainvoke(
            _args(
                destination_dataset_id="my_dataset",
                display_name="My Query",
                query="SELECT * FROM table",
                schedule="every 24 hours",
            )
        )

    assert isinstance(result_dict, dict)
    result = CreateScheduledQueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.transfer_config is not None
    assert result.transfer_config.display_name == "My Query"


@pytest.mark.asyncio
async def test_switch_instance_boot_status(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_COMPUTE_API}/projects/test-project/zones/us-central1-a/instances/my-vm/start",
        json={
            "name": "operation-12345",
            "status": "RUNNING",
        },
    )

    with _patch_access_token():
        result_dict = await switch_instance_boot_status.ainvoke(
            _args(zone="us-central1-a", instance_name="my-vm", action="start")
        )

    assert isinstance(result_dict, dict)
    result = SwitchInstanceBootStatusOutput.model_validate(result_dict)
    assert result.success is True
    assert result.operation_name == "operation-12345"


# --- Failure-path tests -------------------------------------------------------


@pytest.mark.asyncio
async def test_create_bucket_invalid_credentials() -> None:
    """Passing empty key_json must return success=False with a credential error."""
    result_dict = await create_bucket.ainvoke(
        {"auth_type": "custom", "auth_data": {"key_json": ""}, "bucket_name": "x"}
    )

    assert isinstance(result_dict, dict)
    result = CreateBucketOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "credentials" in result.error.lower() or "key_json" in result.error.lower()
