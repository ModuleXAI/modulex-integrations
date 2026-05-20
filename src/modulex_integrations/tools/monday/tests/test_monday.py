"""Happy-path tests for every monday @tool, plus manifest sanity checks.

Every tool takes ``auth_type`` + ``auth_data`` as the first two
arguments. The shared ``_AUTH`` dict uses the api_key flavour; an
extra OAuth2 happy-path test asserts the header switches to
``Authorization: Bearer …`` when the credential type changes.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.monday import (
    TOOLS,
    create_board,
    create_column,
    create_group,
    create_item,
    create_subitem,
    create_update,
    get_board_items_page,
    get_column_values,
    get_items_by_column_value,
    list_boards,
    list_workspaces,
    manifest,
    update_column_values,
    update_item_name,
)
from modulex_integrations.tools.monday.outputs import (
    CreateBoardOutput,
    CreateColumnOutput,
    CreateGroupOutput,
    CreateItemOutput,
    CreateSubitemOutput,
    CreateUpdateOutput,
    GetBoardItemsPageOutput,
    GetColumnValuesOutput,
    GetItemsByColumnValueOutput,
    ListBoardsOutput,
    ListWorkspacesOutput,
    UpdateColumnValuesOutput,
    UpdateItemNameOutput,
)

API = "https://api.monday.com/v2"

# Shared api-key credential used by the bulk of the tests.
# Annotated as ``dict[str, Any]`` to escape LangChain's typed
# ``StructuredTool.ainvoke`` overload.
_AUTH: dict[str, Any] = {
    "auth_type": "api_key",
    "auth_data": {"api_key": "fake-monday-api-token"},
}

_OAUTH_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake-oauth-access-token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: api-key auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_13_actions(self) -> None:
        assert len(manifest.actions) == 13

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2", "api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_board(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {"create_board": {"id": "12345"}},
        },
    )

    result_dict = await create_board.ainvoke(
        _args(board_name="Test Board", board_kind="public")
    )

    assert isinstance(result_dict, dict)
    result = CreateBoardOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "12345"
    # api_key credential reached the API as a raw Authorization header
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "fake-monday-api-token"


@pytest.mark.asyncio
async def test_create_board_oauth2(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """OAuth2 credentials should produce a ``Bearer …`` Authorization header."""
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"create_board": {"id": "oauth_board"}}},
    )

    result_dict = await create_board.ainvoke(
        dict(_OAUTH_AUTH, board_name="OAuth Board", board_kind="public")
    )

    result = CreateBoardOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "oauth_board"
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake-oauth-access-token"


@pytest.mark.asyncio
async def test_create_column(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {"create_column": {"id": "col_1"}},
        },
    )

    result_dict = await create_column.ainvoke(
        _args(board_id="123", title="Status", column_type="status")
    )

    assert isinstance(result_dict, dict)
    result = CreateColumnOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "col_1"


@pytest.mark.asyncio
async def test_create_group(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {"create_group": {"id": "new_group"}},
        },
    )

    result_dict = await create_group.ainvoke(
        _args(board_id="123", group_name="Sprint 1")
    )

    assert isinstance(result_dict, dict)
    result = CreateGroupOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "new_group"


@pytest.mark.asyncio
async def test_create_item(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {"create_item": {"id": "item_99"}},
        },
    )

    result_dict = await create_item.ainvoke(
        _args(board_id="123", item_name="New Task")
    )

    assert isinstance(result_dict, dict)
    result = CreateItemOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "item_99"


@pytest.mark.asyncio
async def test_create_subitem(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {"create_subitem": {"id": "sub_1"}},
        },
    )

    result_dict = await create_subitem.ainvoke(
        _args(board_id="123", parent_item_id="456", item_name="Sub Task")
    )

    assert isinstance(result_dict, dict)
    result = CreateSubitemOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "sub_1"


@pytest.mark.asyncio
async def test_create_update(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {"create_update": {"id": "upd_1"}},
        },
    )

    result_dict = await create_update.ainvoke(
        _args(board_id="123", item_id="456", update_body="Hello from test")
    )

    assert isinstance(result_dict, dict)
    result = CreateUpdateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "upd_1"


@pytest.mark.asyncio
async def test_get_board_items_page(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "boards": [
                    {
                        "items_page": {
                            "cursor": None,
                            "items": [
                                {
                                    "id": "1",
                                    "name": "Item 1",
                                    "column_values": [
                                        {"id": "status", "value": "{\"index\":0}", "text": "Done"},
                                    ],
                                },
                            ],
                        },
                    },
                ],
            },
        },
    )

    result_dict = await get_board_items_page.ainvoke(_args(board_id="123"))

    assert isinstance(result_dict, dict)
    result = GetBoardItemsPageOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1
    assert result.items[0].id == "1"


@pytest.mark.asyncio
async def test_get_column_values(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "items": [
                    {
                        "id": "456",
                        "name": "My Item",
                        "column_values": [
                            {"id": "status", "value": "{\"index\":1}", "text": "Working"},
                        ],
                    },
                ],
            },
        },
    )

    result_dict = await get_column_values.ainvoke(
        _args(board_id="123", item_id="456")
    )

    assert isinstance(result_dict, dict)
    result = GetColumnValuesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_get_items_by_column_value(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "items_page_by_column_values": {
                    "cursor": None,
                    "items": [
                        {
                            "id": "789",
                            "name": "Found Item",
                            "column_values": [
                                {"id": "email", "value": "test@example.com", "text": "test@example.com"},
                            ],
                        },
                    ],
                },
            },
        },
    )

    result_dict = await get_items_by_column_value.ainvoke(
        _args(board_id="123", column_id="email", value="test@example.com")
    )

    assert isinstance(result_dict, dict)
    result = GetItemsByColumnValueOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1
    assert result.items[0].name == "Found Item"


@pytest.mark.asyncio
async def test_list_boards(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "boards": [
                    {
                        "id": "111",
                        "name": "Project Board",
                        "state": "active",
                        "board_kind": "public",
                        "description": "A test board",
                        "workspace_id": 1,
                    },
                ],
            },
        },
    )

    result_dict = await list_boards.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListBoardsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.boards) == 1
    assert result.boards[0].name == "Project Board"


@pytest.mark.asyncio
async def test_list_workspaces(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "workspaces": [
                    {"id": "1", "name": "Main Workspace"},
                    {"id": "2", "name": "Dev Workspace"},
                ],
            },
        },
    )

    result_dict = await list_workspaces.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListWorkspacesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.workspaces) == 2
    assert result.workspaces[0].label == "Main Workspace"


@pytest.mark.asyncio
async def test_update_column_values(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "change_multiple_column_values": {
                    "id": "456",
                    "name": "Updated Item",
                    "column_values": [
                        {"id": "status", "value": "{\"index\":2}"},
                    ],
                },
            },
        },
    )

    result_dict = await update_column_values.ainvoke(
        _args(board_id="123", item_id="456", column_values='{"status": {"index": 2}}')
    )

    assert isinstance(result_dict, dict)
    result = UpdateColumnValuesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_update_item_name(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {"change_multiple_column_values": {"id": "456"}},
        },
    )

    result_dict = await update_item_name.ainvoke(
        _args(board_id="123", item_id="456", item_name="Renamed Item")
    )

    assert isinstance(result_dict, dict)
    result = UpdateItemNameOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "456"


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_create_board_validates_empty_api_key() -> None:
    result_dict = await create_board.ainvoke(
        {
            "auth_type": "api_key",
            "auth_data": {"api_key": ""},
            "board_name": "x",
            "board_kind": "public",
        }
    )
    result = CreateBoardOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")


@pytest.mark.asyncio
async def test_create_board_validates_empty_oauth_token() -> None:
    result_dict = await create_board.ainvoke(
        {
            "auth_type": "oauth2",
            "auth_data": {"access_token": ""},
            "board_name": "x",
            "board_kind": "public",
        }
    )
    result = CreateBoardOutput.model_validate(result_dict)
    assert result.success is False
    assert "access_token" in (result.error or "")
