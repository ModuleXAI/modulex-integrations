"""Happy-path tests per action + failure-path and empty-credential
tests for the non-2xx -> success=False branch (Mem0 tools don't raise)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.mem0 import (
    TOOLS,
    add_memories,
    get_memories,
    manifest,
    search_memories,
)
from modulex_integrations.tools.mem0.outputs import (
    AddMemoriesOutput,
    GetMemoriesOutput,
    SearchMemoriesOutput,
)

API = "https://api.mem0.ai"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:mem0"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_add_memories(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/memories/add/",
        json={
            "message": "Memory processing has been queued for background execution",
            "status": "PENDING",
            "event_id": "evt-123",
        },
    )

    result_dict = await add_memories.ainvoke(
        _args(
            user_id="user_1",
            messages=[{"role": "user", "content": "I love pizza"}],
        )
    )

    assert isinstance(result_dict, dict)

    result = AddMemoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "PENDING"
    assert result.event_id == "evt-123"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Token {_API_KEY}"


@pytest.mark.asyncio
async def test_add_memories_accepts_json_string(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/memories/add/",
        json={"message": "queued", "status": "PENDING", "event_id": "evt-9"},
    )

    result_dict = await add_memories.ainvoke(
        _args(
            user_id="user_1",
            messages='[{"role": "assistant", "content": "noted"}]',
        )
    )

    result = AddMemoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event_id == "evt-9"


@pytest.mark.asyncio
async def test_search_memories(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/memories/search/",
        json={
            "results": [
                {
                    "id": "mem-1",
                    "memory": "Likes pizza",
                    "user_id": "user_1",
                    "categories": ["food"],
                    "metadata": {"src": "chat"},
                    "created_at": "2024-01-01T00:00:00Z",
                    "score": 0.92,
                }
            ]
        },
    )

    result_dict = await search_memories.ainvoke(
        _args(user_id="user_1", query="what food do I like?")
    )

    assert isinstance(result_dict, dict)

    result = SearchMemoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.search_results[0].memory == "Likes pizza"
    assert result.search_results[0].score == 0.92
    assert result.search_results[0].categories == ["food"]
    assert result.ids == ["mem-1"]


@pytest.mark.asyncio
async def test_get_memories_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/memories/",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": "mem-2",
                    "memory": "Works at Acme",
                    "user_id": "user_1",
                    "created_at": "2024-02-01T00:00:00Z",
                    "updated_at": "2024-02-02T00:00:00Z",
                }
            ],
        },
    )

    result_dict = await get_memories.ainvoke(_args(user_id="user_1"))

    assert isinstance(result_dict, dict)

    result = GetMemoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.memories[0].memory == "Works at Acme"
    assert result.ids == ["mem-2"]
    assert result.count == 1
    assert result.next is None


@pytest.mark.asyncio
async def test_get_memories_by_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/memories/mem-3/",
        json={
            "id": "mem-3",
            "memory": "Prefers dark mode",
            "user_id": "user_1",
        },
    )

    result_dict = await get_memories.ainvoke(_args(user_id="user_1", memory_id="mem-3"))

    result = GetMemoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.memories[0].id == "mem-3"
    assert result.ids == ["mem-3"]


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/memories/search/",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await search_memories.ainvoke(_args(user_id="user_1", query="anything"))

    assert isinstance(result_dict, dict)

    result = SearchMemoriesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_add_memories_rejects_empty_messages() -> None:
    """A non-array / empty messages payload short-circuits before HTTP."""
    result_dict = await add_memories.ainvoke(_args(user_id="user_1", messages=[]))

    result = AddMemoriesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "non-empty" in result.error


# --- Empty-credential paths ------------------------------------------------


@pytest.mark.asyncio
async def test_add_memories_validates_empty_api_key() -> None:
    result_dict = await add_memories.ainvoke(
        {"user_id": "user_1", "messages": [{"role": "user", "content": "hi"}], "api_key": ""}
    )

    result = AddMemoriesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_search_validates_empty_api_key() -> None:
    result_dict = await search_memories.ainvoke(
        {"user_id": "user_1", "query": "x", "api_key": "  "}
    )

    result = SearchMemoriesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_get_memories_validates_empty_api_key() -> None:
    result_dict = await get_memories.ainvoke({"user_id": "user_1", "api_key": ""})

    result = GetMemoriesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
