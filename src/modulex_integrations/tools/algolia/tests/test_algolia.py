"""Happy-path tests for every algolia @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.algolia import (
    TOOLS,
    browse_records,
    delete_records,
    list_index_name_options,
    manifest,
    save_records,
)
from modulex_integrations.tools.algolia.outputs import (
    BrowseRecordsOutput,
    DeleteRecordsOutput,
    ListIndexNameOptionsOutput,
    SaveRecordsOutput,
)

_APPLICATION_ID = "TESTAPPID"
_API_KEY = "fake-api-key"

API_READ = f"https://{_APPLICATION_ID}-dsn.algolia.net"
API_WRITE = f"https://{_APPLICATION_ID}.algolia.net"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(application_id=_APPLICATION_ID, api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_browse_records(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API_READ}/1/indexes/my_index/browse",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "hits": [{"objectID": "1", "name": "Test Record"}],
            "cursor": "next_cursor_value",
        },
    )

    result_dict = await browse_records.ainvoke(_args(index_name="my_index"))

    assert isinstance(result_dict, dict)
    result = BrowseRecordsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.hits) == 1
    assert result.cursor == "next_cursor_value"


@pytest.mark.asyncio
async def test_delete_records(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API_WRITE}/1/indexes/my_index/batch",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "taskID": 12345,
            "objectIDs": ["obj1", "obj2"],
        },
    )

    result_dict = await delete_records.ainvoke(
        _args(index_name="my_index", record_ids=["obj1", "obj2"])
    )

    assert isinstance(result_dict, dict)
    result = DeleteRecordsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task_id == 12345
    assert result.object_ids == ["obj1", "obj2"]


@pytest.mark.asyncio
async def test_list_index_name_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API_READ}/1/indexes",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "items": [
                {"name": "index_one"},
                {"name": "index_two"},
            ],
        },
    )

    result_dict = await list_index_name_options.ainvoke(
        _args()
    )

    assert isinstance(result_dict, dict)
    result = ListIndexNameOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.index_names == ["index_one", "index_two"]


@pytest.mark.asyncio
async def test_save_records(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API_WRITE}/1/indexes/my_index/batch",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "taskID": 67890,
            "objectIDs": ["rec1", "rec2"],
        },
    )

    result_dict = await save_records.ainvoke(
        _args(
            index_name="my_index",
            records=[
                {"objectID": "rec1", "title": "Record 1"},
                {"objectID": "rec2", "title": "Record 2"},
            ],
        )
    )

    assert isinstance(result_dict, dict)
    result = SaveRecordsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task_id == 67890
    assert result.object_ids == ["rec1", "rec2"]


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_browse_records_validates_empty_credentials() -> None:
    result_dict = await browse_records.ainvoke(
        {"index_name": "x", "application_id": "", "api_key": ""}
    )
    result = BrowseRecordsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "credentials" in result.error.lower()
