"""Google Cloud LangChain @tool functions."""
from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_cloud.outputs import (
    BigqueryInsertRowsOutput,
    BucketMetadata,
    CreateBucketOutput,
    CreateScheduledQueryOutput,
    GetBucketOutput,
    GetObjectOutput,
    ListBucketsOutput,
    LoggingWriteLogOutput,
    ObjectMetadata,
    RunQueryOutput,
    SearchObjectsOutput,
    SwitchInstanceBootStatusOutput,
    TransferConfig,
    UploadObjectOutput,
)

__all__ = [
    "bigquery_insert_rows",
    "create_bucket",
    "create_scheduled_query",
    "get_bucket",
    "get_object",
    "list_buckets",
    "logging_write_log",
    "run_query",
    "search_objects",
    "switch_instance_boot_status",
    "upload_object",
]

_STORAGE_BASE = "https://storage.googleapis.com/storage/v1"
_STORAGE_UPLOAD_BASE = "https://storage.googleapis.com/upload/storage/v1"
_BIGQUERY_BASE = "https://bigquery.googleapis.com/bigquery/v2"
_LOGGING_BASE = "https://logging.googleapis.com/v2"
_COMPUTE_BASE = "https://compute.googleapis.com/compute/v1"
_DATA_TRANSFER_BASE = "https://bigquerydatatransfer.googleapis.com/v1"

_TIMEOUT = 60.0
_SCOPES = "https://www.googleapis.com/auth/cloud-platform"


def _parse_key_json(auth_data: dict[str, Any]) -> tuple[str, str, str]:
    """Extract project_id, client_email, and private_key from key_json in auth_data."""
    key_json_raw = auth_data.get("key_json", "")
    if not key_json_raw:
        raise ValueError("key_json is empty")
    if isinstance(key_json_raw, str):
        key_data = json.loads(key_json_raw)
    else:
        key_data = key_json_raw
    project_id = key_data.get("project_id", "")
    client_email = key_data.get("client_email", "")
    private_key = key_data.get("private_key", "")
    if not project_id or not client_email or not private_key:
        raise ValueError("key_json must contain project_id, client_email, and private_key")
    return project_id, client_email, private_key


def _create_jwt(client_email: str, private_key: str) -> str:
    """Create a signed JWT for Google API authentication."""
    import base64

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": client_email,
        "scope": _SCOPES,
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }

    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()

    loaded_key = serialization.load_pem_private_key(private_key.encode(), password=None)
    if not isinstance(loaded_key, RSAPrivateKey):
        raise ValueError("Only RSA private keys are supported for GCP JWT signing")
    signature = loaded_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    signature_b64 = _b64url(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


async def _get_access_token(client_email: str, private_key: str, http_client: httpx.AsyncClient) -> str:
    """Exchange a self-signed JWT for a Google OAuth2 access token."""
    jwt = _create_jwt(client_email, private_key)
    response = await http_client.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt,
        },
    )
    response.raise_for_status()
    token: str = response.json()["access_token"]
    return token


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


# --- Input schemas ------------------------------------------------------------


class CreateBucketInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    bucket_name: str = Field(description="Globally unique bucket name")
    location: str = Field(default="US", description="Bucket location")
    storage_class: str = Field(default="STANDARD", description="Storage class: STANDARD, NEARLINE, COLDLINE, or ARCHIVE")


class GetBucketInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    bucket_name: str = Field(description="Name of the bucket")


class ListBucketsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class SearchObjectsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    bucket_name: str = Field(description="Name of the bucket to search")
    prefix: str = Field(description="Object name prefix to filter by")
    delimiter: str | None = Field(default=None, description="Delimiter for directory-like listing")


class GetObjectInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    bucket_name: str = Field(description="Name of the bucket")
    object_name: str = Field(description="Full path/name of the object")


class UploadObjectInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    bucket_name: str = Field(description="Destination bucket name")
    object_name: str = Field(description="Destination path/name in the bucket")
    content: str = Field(description="Text content to upload")
    content_type: str = Field(default="text/plain", description="MIME type of the content")


class LoggingWriteLogInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    log_name: str = Field(description="Name of the log to write to")
    text: str = Field(description="Log message text")
    severity: str = Field(default="DEFAULT", description="Log severity level")


class RunQueryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(description="GoogleSQL query to execute")
    location: str = Field(default="US", description="Dataset location")


class BigqueryInsertRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    dataset_id: str = Field(description="BigQuery dataset ID")
    table_id: str = Field(description="BigQuery table ID")
    rows: list[dict[str, Any]] = Field(description="Array of row objects to insert")


class CreateScheduledQueryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    destination_dataset_id: str = Field(description="Destination dataset ID")
    display_name: str = Field(description="Human-readable name for the scheduled query")
    query: str = Field(description="GoogleSQL query to schedule")
    dataset_region: str = Field(default="us", description="Geographic location of the dataset")
    schedule: str | None = Field(default=None, description="Schedule in cron-like format")
    write_disposition: str = Field(default="WRITE_TRUNCATE", description="Write behavior: WRITE_TRUNCATE or WRITE_APPEND")
    destination_table_name_template: str = Field(default="logs", description="Destination table name template")


class SwitchInstanceBootStatusInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    zone: str = Field(description="Compute Engine zone")
    instance_name: str = Field(description="Name of the VM instance")
    action: str = Field(description="Action to perform: start or stop")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=CreateBucketInput)
@serialize_pydantic_return
async def create_bucket(
    auth_type: str,
    auth_data: dict[str, Any],
    bucket_name: str,
    location: str = "US",
    storage_class: str = "STANDARD",
) -> CreateBucketOutput:
    """Create a new Google Cloud Storage bucket."""
    try:
        project_id, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return CreateBucketOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.post(
                f"{_STORAGE_BASE}/b",
                headers=_auth_headers(access_token),
                params={"project": project_id},
                json={
                    "name": bucket_name,
                    "location": location,
                    "storageClass": storage_class,
                },
            )
        if response.status_code not in (200, 201):
            return CreateBucketOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateBucketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateBucketOutput(success=False, error=f"Call failed: {exc}")

    return CreateBucketOutput(
        success=True,
        bucket=BucketMetadata(
            id=data.get("id"),
            name=data.get("name"),
            location=data.get("location"),
            storage_class=data.get("storageClass"),
            time_created=data.get("timeCreated"),
            updated=data.get("updated"),
            project_number=data.get("projectNumber"),
        ),
    )


@tool(args_schema=GetBucketInput)
@serialize_pydantic_return
async def get_bucket(
    auth_type: str,
    auth_data: dict[str, Any],
    bucket_name: str,
) -> GetBucketOutput:
    """Get metadata for a Google Cloud Storage bucket."""
    try:
        _, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return GetBucketOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.get(
                f"{_STORAGE_BASE}/b/{quote(bucket_name, safe='')}",
                headers=_auth_headers(access_token),
            )
        if response.status_code != 200:
            return GetBucketOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetBucketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBucketOutput(success=False, error=f"Call failed: {exc}")

    return GetBucketOutput(
        success=True,
        bucket=BucketMetadata(
            id=data.get("id"),
            name=data.get("name"),
            location=data.get("location"),
            storage_class=data.get("storageClass"),
            time_created=data.get("timeCreated"),
            updated=data.get("updated"),
            project_number=data.get("projectNumber"),
        ),
    )


@tool(args_schema=ListBucketsInput)
@serialize_pydantic_return
async def list_buckets(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListBucketsOutput:
    """List all Google Cloud Storage buckets in the project."""
    try:
        project_id, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return ListBucketsOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.get(
                f"{_STORAGE_BASE}/b",
                headers=_auth_headers(access_token),
                params={"project": project_id},
            )
        if response.status_code != 200:
            return ListBucketsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListBucketsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListBucketsOutput(success=False, error=f"Call failed: {exc}")

    items = data.get("items", [])
    buckets = [
        BucketMetadata(
            id=b.get("id"),
            name=b.get("name"),
            location=b.get("location"),
            storage_class=b.get("storageClass"),
            time_created=b.get("timeCreated"),
            updated=b.get("updated"),
            project_number=b.get("projectNumber"),
        )
        for b in items
    ]
    return ListBucketsOutput(success=True, buckets=buckets)


@tool(args_schema=SearchObjectsInput)
@serialize_pydantic_return
async def search_objects(
    auth_type: str,
    auth_data: dict[str, Any],
    bucket_name: str,
    prefix: str,
    delimiter: str | None = None,
) -> SearchObjectsOutput:
    """Search for objects in a bucket by prefix."""
    try:
        _, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return SearchObjectsOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        params: dict[str, str] = {"prefix": prefix}
        if delimiter:
            params["delimiter"] = delimiter
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.get(
                f"{_STORAGE_BASE}/b/{quote(bucket_name, safe='')}/o",
                headers=_auth_headers(access_token),
                params=params,
            )
        if response.status_code != 200:
            return SearchObjectsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return SearchObjectsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchObjectsOutput(success=False, error=f"Call failed: {exc}")

    items = data.get("items", [])
    objects = [
        ObjectMetadata(
            name=o.get("name"),
            bucket=o.get("bucket"),
            size=o.get("size"),
            content_type=o.get("contentType"),
            time_created=o.get("timeCreated"),
            updated=o.get("updated"),
            md5_hash=o.get("md5Hash"),
        )
        for o in items
    ]
    return SearchObjectsOutput(success=True, objects=objects)


@tool(args_schema=GetObjectInput)
@serialize_pydantic_return
async def get_object(
    auth_type: str,
    auth_data: dict[str, Any],
    bucket_name: str,
    object_name: str,
) -> GetObjectOutput:
    """Get metadata for a specific object in a Google Cloud Storage bucket."""
    try:
        _, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return GetObjectOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.get(
                f"{_STORAGE_BASE}/b/{quote(bucket_name, safe='')}/o/{quote(object_name, safe='')}",
                headers=_auth_headers(access_token),
            )
        if response.status_code != 200:
            return GetObjectOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetObjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetObjectOutput(success=False, error=f"Call failed: {exc}")

    return GetObjectOutput(
        success=True,
        metadata=ObjectMetadata(
            name=data.get("name"),
            bucket=data.get("bucket"),
            size=data.get("size"),
            content_type=data.get("contentType"),
            time_created=data.get("timeCreated"),
            updated=data.get("updated"),
            md5_hash=data.get("md5Hash"),
        ),
    )


@tool(args_schema=UploadObjectInput)
@serialize_pydantic_return
async def upload_object(
    auth_type: str,
    auth_data: dict[str, Any],
    bucket_name: str,
    object_name: str,
    content: str,
    content_type: str = "text/plain",
) -> UploadObjectOutput:
    """Upload text content as an object to a Google Cloud Storage bucket."""
    try:
        _, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return UploadObjectOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.post(
                f"{_STORAGE_UPLOAD_BASE}/b/{quote(bucket_name, safe='')}/o",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": content_type,
                },
                params={"uploadType": "media", "name": object_name},
                content=content.encode(),
            )
        if response.status_code not in (200, 201):
            return UploadObjectOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UploadObjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UploadObjectOutput(success=False, error=f"Call failed: {exc}")

    return UploadObjectOutput(
        success=True,
        object_name=data.get("name"),
        bucket=data.get("bucket"),
    )


@tool(args_schema=LoggingWriteLogInput)
@serialize_pydantic_return
async def logging_write_log(
    auth_type: str,
    auth_data: dict[str, Any],
    log_name: str,
    text: str,
    severity: str = "DEFAULT",
) -> LoggingWriteLogOutput:
    """Write a log entry to Google Cloud Logging."""
    try:
        project_id, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return LoggingWriteLogOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.post(
                f"{_LOGGING_BASE}/entries:write",
                headers=_auth_headers(access_token),
                json={
                    "logName": f"projects/{project_id}/logs/{log_name}",
                    "resource": {"type": "global"},
                    "entries": [
                        {
                            "logName": f"projects/{project_id}/logs/{log_name}",
                            "resource": {"type": "global"},
                            "textPayload": text,
                            "severity": severity,
                        }
                    ],
                },
            )
        if response.status_code != 200:
            return LoggingWriteLogOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return LoggingWriteLogOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return LoggingWriteLogOutput(success=False, error=f"Call failed: {exc}")

    return LoggingWriteLogOutput(success=True)


@tool(args_schema=RunQueryInput)
@serialize_pydantic_return
async def run_query(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    location: str = "US",
) -> RunQueryOutput:
    """Run a SQL query in BigQuery and return the results."""
    try:
        project_id, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return RunQueryOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.post(
                f"{_BIGQUERY_BASE}/projects/{project_id}/queries",
                headers=_auth_headers(access_token),
                json={
                    "query": query,
                    "location": location,
                    "useLegacySql": False,
                },
            )
        if response.status_code != 200:
            return RunQueryOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return RunQueryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RunQueryOutput(success=False, error=f"Call failed: {exc}")

    schema_fields = [f.get("name", "") for f in data.get("schema", {}).get("fields", [])]
    raw_rows = data.get("rows", [])
    rows: list[dict[str, str | int | float | bool | None]] = []
    for row in raw_rows:
        cells = row.get("f", [])
        row_dict: dict[str, str | int | float | bool | None] = {}
        for i, cell in enumerate(cells):
            key = schema_fields[i] if i < len(schema_fields) else f"col_{i}"
            row_dict[key] = cell.get("v")
        rows.append(row_dict)

    return RunQueryOutput(
        success=True,
        rows=rows,
        total_rows=int(data.get("totalRows", 0)) if data.get("totalRows") else None,
    )


@tool(args_schema=BigqueryInsertRowsInput)
@serialize_pydantic_return
async def bigquery_insert_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    dataset_id: str,
    table_id: str,
    rows: list[dict[str, Any]],
) -> BigqueryInsertRowsOutput:
    """Insert rows into a BigQuery table using streaming insert."""
    try:
        project_id, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return BigqueryInsertRowsOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        insert_rows = [{"json": row} for row in rows]
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.post(
                f"{_BIGQUERY_BASE}/projects/{project_id}/datasets/{quote(dataset_id, safe='')}/tables/{quote(table_id, safe='')}/insertAll",
                headers=_auth_headers(access_token),
                json={"rows": insert_rows},
            )
        if response.status_code != 200:
            return BigqueryInsertRowsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return BigqueryInsertRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return BigqueryInsertRowsOutput(success=False, error=f"Call failed: {exc}")

    if data.get("insertErrors"):
        errors = data["insertErrors"]
        error_msg = "; ".join(
            e.get("errors", [{}])[0].get("message", "unknown")
            for e in errors[:3]
        )
        return BigqueryInsertRowsOutput(success=False, error=f"Insert errors: {error_msg}")

    return BigqueryInsertRowsOutput(success=True, inserted_count=len(rows))


@tool(args_schema=CreateScheduledQueryInput)
@serialize_pydantic_return
async def create_scheduled_query(
    auth_type: str,
    auth_data: dict[str, Any],
    destination_dataset_id: str,
    display_name: str,
    query: str,
    dataset_region: str = "us",
    schedule: str | None = None,
    write_disposition: str = "WRITE_TRUNCATE",
    destination_table_name_template: str = "logs",
) -> CreateScheduledQueryOutput:
    """Create a scheduled query in BigQuery Data Transfer Service."""
    try:
        project_id, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return CreateScheduledQueryOutput(success=False, error=f"Invalid credentials: {exc}")

    try:
        body: dict[str, Any] = {
            "displayName": display_name,
            "dataSourceId": "scheduled_query",
            "destinationDatasetId": destination_dataset_id,
            "params": {
                "query": query,
                "write_disposition": write_disposition,
                "destination_table_name_template": destination_table_name_template,
            },
        }
        if schedule:
            body["schedule"] = schedule

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.post(
                f"{_DATA_TRANSFER_BASE}/projects/{project_id}/locations/{quote(dataset_region, safe='')}/transferConfigs",
                headers=_auth_headers(access_token),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateScheduledQueryOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateScheduledQueryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateScheduledQueryOutput(success=False, error=f"Call failed: {exc}")

    return CreateScheduledQueryOutput(
        success=True,
        transfer_config=TransferConfig(
            name=data.get("name"),
            display_name=data.get("displayName"),
            data_source_id=data.get("dataSourceId"),
            schedule=data.get("schedule"),
            state=data.get("state"),
            destination_dataset_id=data.get("destinationDatasetId"),
        ),
    )


@tool(args_schema=SwitchInstanceBootStatusInput)
@serialize_pydantic_return
async def switch_instance_boot_status(
    auth_type: str,
    auth_data: dict[str, Any],
    zone: str,
    instance_name: str,
    action: str,
) -> SwitchInstanceBootStatusOutput:
    """Start or stop a Google Compute Engine virtual machine instance."""
    try:
        project_id, client_email, private_key = _parse_key_json(auth_data)
    except (ValueError, json.JSONDecodeError) as exc:
        return SwitchInstanceBootStatusOutput(success=False, error=f"Invalid credentials: {exc}")

    if action not in ("start", "stop"):
        return SwitchInstanceBootStatusOutput(success=False, error=f"Invalid action: {action}. Must be 'start' or 'stop'.")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            access_token = await _get_access_token(client_email, private_key, client)
            response = await client.post(
                f"{_COMPUTE_BASE}/projects/{project_id}/zones/{quote(zone, safe='')}/instances/{quote(instance_name, safe='')}/{quote(action, safe='')}",
                headers=_auth_headers(access_token),
            )
        if response.status_code != 200:
            return SwitchInstanceBootStatusOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return SwitchInstanceBootStatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SwitchInstanceBootStatusOutput(success=False, error=f"Call failed: {exc}")

    return SwitchInstanceBootStatusOutput(
        success=True,
        operation_name=data.get("name"),
        status=data.get("status"),
    )
