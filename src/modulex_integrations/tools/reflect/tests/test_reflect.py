"""Happy-path tests for every reflect @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.reflect import (
    TOOLS,
    append_daily_note,
    create_link,
    get_user,
    list_graph_id_options,
    list_links,
    manifest,
)
from modulex_integrations.tools.reflect.outputs import (
    AppendDailyNoteOutput,
    CreateLinkOutput,
    GetUserOutput,
    ListGraphIdOptionsOutput,
    ListLinksOutput,
)

API = "https://reflect.app/api"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_5_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_append_daily_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/graphs/graph123/daily-notes",
        json={},
        status_code=200,
    )

    result_dict = await append_daily_note.ainvoke(
        _args(graph_id="graph123", text="Hello world")
    )

    assert isinstance(result_dict, dict)
    result = AppendDailyNoteOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_link(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/graphs/graph123/links",
        json={
            "id": "link_abc123",
            # TODO: fill in additional response fields from upstream API docs
        },
        status_code=201,
    )

    result_dict = await create_link.ainvoke(
        _args(graph_id="graph123", url="https://example.com")
    )

    assert isinstance(result_dict, dict)
    result = CreateLinkOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "link_abc123"


@pytest.mark.asyncio
async def test_get_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me",
        json={
            "uid": "user_001",
            "graph_ids": ["graph_a", "graph_b"],
            # TODO: fill in additional response fields from upstream API docs
        },
    )

    result_dict = await get_user.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.uid == "user_001"
    assert result.graph_ids == ["graph_a", "graph_b"]


@pytest.mark.asyncio
async def test_list_graph_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me",
        json={
            "uid": "user_001",
            "graph_ids": ["graph_x", "graph_y"],
        },
    )

    result_dict = await list_graph_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListGraphIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.graph_ids == ["graph_x", "graph_y"]


@pytest.mark.asyncio
async def test_list_links(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/graphs/graph123/links",
        json=[
            {
                "id": "link_1",
                "url": "https://example.com",
                "title": "Example",
                "description": "An example link",
                "updated_at": "2024-01-15T10:00:00Z",
            },
            # TODO: fill in additional response items from upstream API docs
        ],
    )

    result_dict = await list_links.ainvoke(_args(graph_id="graph123"))

    assert isinstance(result_dict, dict)
    result = ListLinksOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.links) == 1
    assert result.links[0].id == "link_1"
    assert result.links[0].title == "Example"


# --- Failure-path tests -----------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_missing_token():  # type: ignore[no-untyped-def]
    """Empty credential should return success=False without hitting the wire."""
    result_dict = await get_user.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}}
    )

    assert isinstance(result_dict, dict)
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access token" in result.error.lower()
