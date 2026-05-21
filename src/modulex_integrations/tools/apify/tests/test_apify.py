"""Happy-path tests for every apify @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.apify import (
    TOOLS,
    get_dataset_items,
    get_kvs_record,
    manifest,
    run_actor,
    run_task,
    run_task_synchronously,
    scrape_single_url,
    set_key_value_store_record,
)
from modulex_integrations.tools.apify.outputs import (
    GetDatasetItemsOutput,
    GetKvsRecordOutput,
    RunActorOutput,
    RunTaskOutput,
    RunTaskSynchronouslyOutput,
    ScrapeSingleUrlOutput,
    SetKeyValueStoreRecordOutput,
)

API = "https://api.apify.com/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "fake_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a .ainvoke() input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_7_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_bearer_token_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"bearer_token"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_run_actor(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/acts/apify~web-scraper/runs",
        json={
            "data": {
                "id": "run123",
                "actId": "actor456",
                "status": "RUNNING",
                "startedAt": "2026-01-01T00:00:00.000Z",
                "defaultDatasetId": "ds789",
                "defaultKeyValueStoreId": "kvs012",
            },
        },
        status_code=201,
    )

    result_dict = await run_actor.ainvoke(_args(actor_id="apify~web-scraper"))

    assert isinstance(result_dict, dict)
    result = RunActorOutput.model_validate(result_dict)
    assert result.success is True
    assert result.run_id == "run123"
    assert result.status == "RUNNING"


@pytest.mark.asyncio
async def test_run_task(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/actor-tasks/task123/runs",
        json={
            "data": {
                "id": "run456",
                "actId": "actor789",
                "actTaskId": "task123",
                "status": "RUNNING",
                "startedAt": "2026-01-01T00:00:00.000Z",
                "defaultDatasetId": "ds111",
                "defaultKeyValueStoreId": "kvs222",
            },
        },
        status_code=201,
    )

    result_dict = await run_task.ainvoke(_args(task_id="task123"))

    assert isinstance(result_dict, dict)
    result = RunTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.run_id == "run456"
    assert result.task_id == "task123"


@pytest.mark.asyncio
async def test_run_task_synchronously(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/actor-tasks/task123/run-sync",
        json={
            "data": {
                "id": "run789",
                "actId": "actor111",
                "status": "SUCCEEDED",
                "startedAt": "2026-01-01T00:00:00.000Z",
                "finishedAt": "2026-01-01T00:01:00.000Z",
                "defaultDatasetId": "ds333",
            },
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/datasets/ds333/items?limit=100",
        json=[{"title": "Item 1"}, {"title": "Item 2"}],
    )

    result_dict = await run_task_synchronously.ainvoke(_args(task_id="task123"))

    assert isinstance(result_dict, dict)
    result = RunTaskSynchronouslyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.run_id == "run789"
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_get_dataset_items(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/datasets/ds123/items?offset=0&limit=100",
        json=[{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}],
    )

    result_dict = await get_dataset_items.ainvoke(_args(dataset_id="ds123"))

    assert isinstance(result_dict, dict)
    result = GetDatasetItemsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 2


@pytest.mark.asyncio
async def test_get_kvs_record(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/key-value-stores/kvs123/records/my-key",
        json={"hello": "world"},
        headers={"content-type": "application/json"},
    )

    result_dict = await get_kvs_record.ainvoke(
        _args(key_value_store_id="kvs123", key="my-key")
    )

    assert isinstance(result_dict, dict)
    result = GetKvsRecordOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data == {"hello": "world"}


@pytest.mark.asyncio
async def test_scrape_single_url(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/acts/aYG0l9s7dbB7j3gbS/run-sync-get-dataset-items",
        json=[
            {
                "url": "https://example.com",
                "text": "Example page content",
                "html": "<html>...</html>",
                "markdown": "# Example",
            },
        ],
    )

    result_dict = await scrape_single_url.ainvoke(_args(url="https://example.com"))

    assert isinstance(result_dict, dict)
    result = ScrapeSingleUrlOutput.model_validate(result_dict)
    assert result.success is True
    assert result.url == "https://example.com"
    assert result.text == "Example page content"


@pytest.mark.asyncio
async def test_set_key_value_store_record(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/key-value-stores/kvs123/records/my-key",
        status_code=201,
    )

    result_dict = await set_key_value_store_record.ainvoke(
        _args(key_value_store_id="kvs123", key="my-key", value='{"foo": "bar"}')
    )

    assert isinstance(result_dict, dict)
    result = SetKeyValueStoreRecordOutput.model_validate(result_dict)
    assert result.success is True
    assert result.store_id == "kvs123"
    assert result.key == "my-key"
    assert result.content_type == "application/json"


@pytest.mark.asyncio
async def test_run_actor_empty_credential() -> None:
    """Failure path: empty token returns error without hitting the wire."""
    result_dict = await run_actor.ainvoke(
        _args(auth_data={"token": ""}, actor_id="apify~web-scraper")
    )
    assert isinstance(result_dict, dict)
    result = RunActorOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "token" in result.error.lower() or "missing" in result.error.lower()
