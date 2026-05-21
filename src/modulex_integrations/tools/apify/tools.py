"""Apify LangChain @tool functions."""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.apify.outputs import (
    GetDatasetItemsOutput,
    GetKvsRecordOutput,
    RunActorOutput,
    RunTaskOutput,
    RunTaskSynchronouslyOutput,
    ScrapeSingleUrlOutput,
    SetKeyValueStoreRecordOutput,
)

__all__ = [
    "get_dataset_items",
    "get_kvs_record",
    "run_actor",
    "run_task",
    "run_task_synchronously",
    "scrape_single_url",
    "set_key_value_store_record",
]

_BASE_URL = "https://api.apify.com/v2"
_TIMEOUT = 120.0
_WEB_CONTENT_CRAWLER_ID = "aYG0l9s7dbB7j3gbS"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Apify API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "bearer_token":
        token = auth_data.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


# --- Input schemas --------------------------------------------------------


class RunActorInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    actor_id: str = Field(description="The Actor ID or tilde-separated owner/name identifier")
    run_input: dict[str, Any] | None = Field(default=None, description="JSON object with the input for the Actor run")
    build_tag: str | None = Field(default=None, description="Specifies the Actor build to run")
    run_asynchronously: bool = Field(default=True, description="If true, returns immediately with run metadata")
    timeout: int | None = Field(default=None, description="Optional timeout for the run, in seconds")
    memory: int | None = Field(default=None, description="Memory limit for the run, in megabytes")
    max_items: int | None = Field(default=None, description="Maximum number of items the run should return")


class RunTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    task_id: str = Field(description="The ID of the task to run")
    override_input: str | None = Field(default=None, description="Optional JSON string to override default input")
    timeout: int | None = Field(default=None, description="Optional timeout for the run, in seconds")
    memory: int | None = Field(default=None, description="Memory limit for the run, in megabytes")
    build: str | None = Field(default=None, description="Specifies the Actor build to run")


class RunTaskSynchronouslyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    task_id: str = Field(description="The ID of the task to run")
    timeout: int | None = Field(default=None, description="Optional timeout for the run, in seconds")
    memory: int | None = Field(default=None, description="Memory limit for the run, in megabytes")
    build: str | None = Field(default=None, description="Specifies the Actor build to run")
    limit: int = Field(default=100, description="Maximum number of dataset items to return")


class GetDatasetItemsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    dataset_id: str = Field(description="The ID of the dataset to retrieve items from")
    offset: int = Field(default=0, description="Number of records to skip")
    limit: int = Field(default=100, description="Maximum number of items to return")
    clean: bool | None = Field(default=None, description="Return only non-empty items and skip hidden fields")
    fields: str | None = Field(default=None, description="Comma-separated list of field names to include")


class GetKvsRecordInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    key_value_store_id: str = Field(description="The ID of the key-value store")
    key: str = Field(description="The key of the record to retrieve")


class ScrapeSingleUrlInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    url: str = Field(description="The URL of the web page to scrape")
    crawler_type: str = Field(default="playwright:firefox", description="Crawling engine to use")


class SetKeyValueStoreRecordInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    key_value_store_id: str = Field(description="The ID of the key-value store")
    key: str = Field(description="The key of the record to create or update")
    value: str = Field(description="The value to store")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=RunActorInput)
@serialize_pydantic_return
async def run_actor(
    auth_type: str,
    auth_data: dict[str, Any],
    actor_id: str,
    run_input: dict[str, Any] | None = None,
    build_tag: str | None = None,
    run_asynchronously: bool = True,
    timeout: int | None = None,
    memory: int | None = None,
    max_items: int | None = None,
) -> RunActorOutput:
    """Run an Apify Actor and return the run metadata."""
    token = auth_data.get("token") if auth_data else None
    if not token or not token.strip():
        return RunActorOutput(success=False, error="Missing or empty API token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    params: dict[str, Any] = {}
    if build_tag:
        params["build"] = build_tag
    if timeout is not None:
        params["timeout"] = timeout
    if memory is not None:
        params["memory"] = memory
    if max_items is not None:
        params["maxItems"] = max_items

    if run_asynchronously:
        url = f"{_BASE_URL}/acts/{actor_id}/runs"
    else:
        url = f"{_BASE_URL}/acts/{actor_id}/run-sync-get-dataset-items"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                url,
                headers=headers,
                params=params,
                json=run_input or {},
            )
        if response.status_code not in (200, 201):
            return RunActorOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RunActorOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RunActorOutput(success=False, error=f"Call failed: {exc}")

    if run_asynchronously:
        run_data = data.get("data", data)
        return RunActorOutput(
            success=True,
            run_id=run_data.get("id"),
            act_id=run_data.get("actId"),
            status=run_data.get("status"),
            started_at=run_data.get("startedAt"),
            dataset_id=(run_data.get("defaultDatasetId")),
            key_value_store_id=run_data.get("defaultKeyValueStoreId"),
        )
    return RunActorOutput(
        success=True,
        data=data,
    )


@tool(args_schema=RunTaskInput)
@serialize_pydantic_return
async def run_task(
    auth_type: str,
    auth_data: dict[str, Any],
    task_id: str,
    override_input: str | None = None,
    timeout: int | None = None,
    memory: int | None = None,
    build: str | None = None,
) -> RunTaskOutput:
    """Start an Apify task and return its run metadata."""
    token = auth_data.get("token") if auth_data else None
    if not token or not token.strip():
        return RunTaskOutput(success=False, error="Missing or empty API token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    params: dict[str, Any] = {}
    if timeout is not None:
        params["timeout"] = timeout
    if memory is not None:
        params["memory"] = memory
    if build:
        params["build"] = build

    body: dict[str, Any] = {}
    if override_input:
        try:
            body = json.loads(override_input)
        except json.JSONDecodeError:
            return RunTaskOutput(success=False, error="override_input is not valid JSON")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/actor-tasks/{task_id}/runs",
                headers=headers,
                params=params,
                json=body,
            )
        if response.status_code not in (200, 201):
            return RunTaskOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RunTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RunTaskOutput(success=False, error=f"Call failed: {exc}")

    run_data = data.get("data", data)
    return RunTaskOutput(
        success=True,
        run_id=run_data.get("id"),
        act_id=run_data.get("actId"),
        task_id=run_data.get("actTaskId"),
        status=run_data.get("status"),
        started_at=run_data.get("startedAt"),
        dataset_id=run_data.get("defaultDatasetId"),
        key_value_store_id=run_data.get("defaultKeyValueStoreId"),
    )


@tool(args_schema=RunTaskSynchronouslyInput)
@serialize_pydantic_return
async def run_task_synchronously(
    auth_type: str,
    auth_data: dict[str, Any],
    task_id: str,
    timeout: int | None = None,
    memory: int | None = None,
    build: str | None = None,
    limit: int = 100,
) -> RunTaskSynchronouslyOutput:
    """Run an Apify task synchronously and return its dataset items."""
    token = auth_data.get("token") if auth_data else None
    if not token or not token.strip():
        return RunTaskSynchronouslyOutput(success=False, error="Missing or empty API token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    params: dict[str, Any] = {}
    if timeout is not None:
        params["timeout"] = timeout
    if memory is not None:
        params["memory"] = memory
    if build:
        params["build"] = build

    try:
        async with httpx.AsyncClient(timeout=max(_TIMEOUT, (timeout or 0) + 30)) as client:
            response = await client.post(
                f"{_BASE_URL}/actor-tasks/{task_id}/run-sync",
                headers=headers,
                params=params,
                json={},
            )
        if response.status_code != 200:
            return RunTaskSynchronouslyOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        run_data = response.json().get("data", response.json())
    except httpx.TimeoutException:
        return RunTaskSynchronouslyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RunTaskSynchronouslyOutput(success=False, error=f"Call failed: {exc}")

    dataset_id = run_data.get("defaultDatasetId")
    items: list[dict[str, Any]] = []
    if dataset_id:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                items_resp = await client.get(
                    f"{_BASE_URL}/datasets/{dataset_id}/items",
                    headers=_get_auth_headers(auth_type, auth_data),
                    params={"limit": limit},
                )
            if items_resp.status_code == 200:
                items = items_resp.json()
        except Exception:
            pass

    return RunTaskSynchronouslyOutput(
        success=True,
        run_id=run_data.get("id"),
        act_id=run_data.get("actId"),
        status=run_data.get("status"),
        started_at=run_data.get("startedAt"),
        finished_at=run_data.get("finishedAt"),
        dataset_id=dataset_id,
        items=items,
    )


@tool(args_schema=GetDatasetItemsInput)
@serialize_pydantic_return
async def get_dataset_items(
    auth_type: str,
    auth_data: dict[str, Any],
    dataset_id: str,
    offset: int = 0,
    limit: int = 100,
    clean: bool | None = None,
    fields: str | None = None,
) -> GetDatasetItemsOutput:
    """Retrieve items from an Apify dataset."""
    token = auth_data.get("token") if auth_data else None
    if not token or not token.strip():
        return GetDatasetItemsOutput(success=False, error="Missing or empty API token.")
    headers = _get_auth_headers(auth_type, auth_data)

    params: dict[str, Any] = {"offset": offset, "limit": limit}
    if clean is not None:
        params["clean"] = clean
    if fields:
        params["fields"] = fields

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/datasets/{dataset_id}/items",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return GetDatasetItemsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        items = response.json()
    except httpx.TimeoutException:
        return GetDatasetItemsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDatasetItemsOutput(success=False, error=f"Call failed: {exc}")

    return GetDatasetItemsOutput(
        success=True,
        items=items,
        count=len(items),
    )


@tool(args_schema=GetKvsRecordInput)
@serialize_pydantic_return
async def get_kvs_record(
    auth_type: str,
    auth_data: dict[str, Any],
    key_value_store_id: str,
    key: str,
) -> GetKvsRecordOutput:
    """Get a record from an Apify key-value store."""
    token = auth_data.get("token") if auth_data else None
    if not token or not token.strip():
        return GetKvsRecordOutput(success=False, error="Missing or empty API token.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/key-value-stores/{key_value_store_id}/records/{key}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetKvsRecordOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data = response.json()
        else:
            data = response.text
    except httpx.TimeoutException:
        return GetKvsRecordOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetKvsRecordOutput(success=False, error=f"Call failed: {exc}")

    return GetKvsRecordOutput(
        success=True,
        content_type=content_type,
        data=data,
    )


@tool(args_schema=ScrapeSingleUrlInput)
@serialize_pydantic_return
async def scrape_single_url(
    auth_type: str,
    auth_data: dict[str, Any],
    url: str,
    crawler_type: str = "playwright:firefox",
) -> ScrapeSingleUrlOutput:
    """Scrape a single URL using Apify's Web Content Crawler and return its content."""
    token = auth_data.get("token") if auth_data else None
    if not token or not token.strip():
        return ScrapeSingleUrlOutput(success=False, error="Missing or empty API token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    run_input = {
        "startUrls": [{"url": url}],
        "crawlerType": crawler_type,
        "maxCrawlDepth": 0,
        "maxCrawlPages": 1,
        "maxResults": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/acts/{_WEB_CONTENT_CRAWLER_ID}/run-sync-get-dataset-items",
                headers=headers,
                json=run_input,
            )
        if response.status_code != 200:
            return ScrapeSingleUrlOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        items = response.json()
    except httpx.TimeoutException:
        return ScrapeSingleUrlOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ScrapeSingleUrlOutput(success=False, error=f"Call failed: {exc}")

    if isinstance(items, list) and items:
        item = items[0]
        return ScrapeSingleUrlOutput(
            success=True,
            url=item.get("url"),
            text=item.get("text"),
            html=item.get("html"),
            markdown=item.get("markdown"),
        )
    return ScrapeSingleUrlOutput(success=True)


@tool(args_schema=SetKeyValueStoreRecordInput)
@serialize_pydantic_return
async def set_key_value_store_record(
    auth_type: str,
    auth_data: dict[str, Any],
    key_value_store_id: str,
    key: str,
    value: str,
) -> SetKeyValueStoreRecordOutput:
    """Create or update a record in an Apify key-value store."""
    token = auth_data.get("token") if auth_data else None
    if not token or not token.strip():
        return SetKeyValueStoreRecordOutput(success=False, error="Missing or empty API token.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        parsed = json.loads(value)
        content_type = "application/json"
        body = json.dumps(parsed).encode()
    except (json.JSONDecodeError, TypeError):
        content_type = "text/plain"
        body = value.encode()

    headers["Content-Type"] = content_type

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/key-value-stores/{key_value_store_id}/records/{key}",
                headers=headers,
                content=body,
            )
        if response.status_code not in (200, 201):
            return SetKeyValueStoreRecordOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return SetKeyValueStoreRecordOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SetKeyValueStoreRecordOutput(success=False, error=f"Call failed: {exc}")

    return SetKeyValueStoreRecordOutput(
        success=True,
        store_id=key_value_store_id,
        key=key,
        content_type=content_type,
    )
