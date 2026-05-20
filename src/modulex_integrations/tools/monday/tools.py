"""Monday.com LangChain ``@tool`` functions.

Every tool takes ``auth_type`` and ``auth_data`` as the first two
parameters; the modulex ``ToolExecutor`` injects them at call time so
the LLM never sees the credentials. Two auth flavours are supported:

- ``oauth2``: ``auth_data["access_token"]`` → ``Authorization: Bearer …``
- ``api_key``: ``auth_data["api_key"]`` → ``Authorization: <raw token>``

Monday.com's GraphQL API accepts both header shapes on the same
endpoint, so the difference lives entirely in ``_get_auth_headers``.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.monday.outputs import (
    ColumnValue,
    CreateBoardOutput,
    CreateColumnOutput,
    CreateGroupOutput,
    CreateItemOutput,
    CreateSubitemOutput,
    CreateUpdateOutput,
    GetBoardItemsPageOutput,
    GetColumnValuesOutput,
    GetItemsByColumnValueOutput,
    ItemSummary,
    ListBoardsOutput,
    ListWorkspacesOutput,
    MondayBoard,
    UpdateColumnValuesOutput,
    UpdateItemNameOutput,
    WorkspaceOption,
)

__all__ = [
    "create_board",
    "create_column",
    "create_group",
    "create_item",
    "create_subitem",
    "create_update",
    "get_board_items_page",
    "get_column_values",
    "get_items_by_column_value",
    "list_boards",
    "list_workspaces",
    "update_column_values",
    "update_item_name",
]

_BASE_URL = "https://api.monday.com/v2"
_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


class _AuthError(Exception):
    """Raised when the injected credential is missing or unusable."""


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build Monday.com API headers for the given credential.

    Raises ``_AuthError`` when the credential is empty so callers can
    surface a uniform ``success=False`` response.
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = (auth_data or {}).get("access_token")
        if not access_token or not str(access_token).strip():
            raise _AuthError(
                "OAuth access_token is empty. Please configure a valid credential."
            )
        headers["Authorization"] = f"Bearer {access_token}"
    elif auth_type == "api_key":
        api_key = (auth_data or {}).get("api_key")
        if not api_key or not str(api_key).strip():
            raise _AuthError(
                "API key is empty. Please configure a valid credential."
            )
        headers["Authorization"] = str(api_key)
    else:
        raise _AuthError(
            f"Unsupported auth_type {auth_type!r}; expected 'oauth2' or 'api_key'."
        )
    return headers


async def _graphql(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a GraphQL request against the Monday.com API."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(_BASE_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise httpx.HTTPStatusError(
            f"API error ({response.status_code}): {response.text}",
            request=response.request,
            response=response,
        )
    result: dict[str, Any] = response.json()
    return result


def _check_errors(data: dict[str, Any]) -> str | None:
    """Return an error string if the GraphQL response contains errors."""
    if data.get("errors"):
        return str(data["errors"])
    if data.get("error_message"):
        return str(data["error_message"])
    return None


# --- Input schemas --------------------------------------------------------


_AUTH_TYPE_FIELD = Field(description="Authentication type (oauth2, api_key)")
_AUTH_DATA_FIELD = Field(
    description="Authentication data: {access_token: ...} for oauth2, {api_key: ...} for api_key",
)


class CreateBoardInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_name: str = Field(description="The new board's name")
    board_kind: str = Field(description="The new board's kind: public, private, or share")
    workspace_id: int | None = Field(default=None, description="Workspace ID to create the board in")
    folder_id: int | None = Field(default=None, description="Folder ID to create the board in")
    template_id: int | None = Field(default=None, description="Template board ID to use")


class CreateColumnInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board to create the column in")
    title: str = Field(description="The title of the new column")
    column_type: str = Field(description="The type of column")
    defaults: str | None = Field(default=None, description="Custom labels JSON for status/dropdown columns")
    description: str | None = Field(default=None, description="Description of the new column")


class CreateGroupInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board to create the group in")
    group_name: str = Field(description="The name of the new group")


class CreateItemInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board to create the item in")
    item_name: str = Field(description="The new item's name")
    group_id: str | None = Field(default=None, description="Group ID to create the item in")
    create_labels: bool | None = Field(default=None, description="Create Status/Dropdown labels if missing")
    column_values: str | None = Field(default=None, description="JSON string of column values for the new item")


class CreateSubitemInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board containing the parent item")
    parent_item_id: str = Field(description="The ID of the parent item")
    item_name: str = Field(description="The new subitem's name")
    column_values: str | None = Field(default=None, description="JSON string of column values for the subitem")


class CreateUpdateInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board containing the item")
    item_id: str = Field(description="The ID of the item to add the update to")
    update_body: str = Field(description="The update text content")
    parent_id: str | None = Field(default=None, description="ID of a parent update to reply to")


class GetBoardItemsPageInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board to retrieve items from")
    query_params: str | None = Field(default=None, description="JSON object with filter/sort parameters")
    max_pages: int = Field(default=50, description="Maximum number of pages to fetch (default 50)")


class GetColumnValuesInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board")
    item_id: str = Field(description="The ID of the item to retrieve column values from")
    column_ids: list[str] | None = Field(default=None, description="List of column IDs to retrieve")


class GetItemsByColumnValueInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board to search in")
    column_id: str = Field(description="The ID of the column to search")
    value: str = Field(description="The value to search for")
    max_pages: int = Field(default=50, description="Maximum number of pages to fetch (default 50)")


class ListBoardsInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    ids: list[str] | None = Field(default=None, description="Filter to specific board IDs")
    workspace_ids: list[int] | None = Field(default=None, description="Filter to boards in specific workspace IDs")
    board_kind: str | None = Field(default=None, description="Filter by board kind: public, private, or share")
    state: str = Field(default="all", description="Filter by state: active, archived, deleted, or all")
    order_by: str = Field(default="created_at", description="Sort by: created_at or used_at")
    limit: int = Field(default=25, description="Maximum number of boards to return per page")
    page: int = Field(default=1, description="Page number to return")


class ListWorkspacesInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD


class UpdateColumnValuesInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board containing the item")
    item_id: str = Field(description="The ID of the item to update")
    column_values: str = Field(description="JSON string of column values to update")


class UpdateItemNameInput(BaseModel):
    auth_type: str = _AUTH_TYPE_FIELD
    auth_data: dict[str, Any] = _AUTH_DATA_FIELD
    board_id: str = Field(description="The ID of the board containing the item")
    item_id: str = Field(description="The ID of the item to rename")
    item_name: str = Field(description="The new item name")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateBoardInput)
@serialize_pydantic_return
async def create_board(
    auth_type: str,
    auth_data: dict[str, Any],
    board_name: str,
    board_kind: str,
    workspace_id: int | None = None,
    folder_id: int | None = None,
    template_id: int | None = None,
) -> CreateBoardOutput:
    """Creates a new board."""
    var_defs = ["$board_name: String!", "$board_kind: BoardKind!"]
    variables: dict[str, Any] = {"board_name": board_name, "board_kind": board_kind}
    args_parts = ["board_name: $board_name", "board_kind: $board_kind"]
    if workspace_id is not None:
        var_defs.append("$workspace_id: Int!")
        variables["workspace_id"] = workspace_id
        args_parts.append("workspace_id: $workspace_id")
    if folder_id is not None:
        var_defs.append("$folder_id: Int!")
        variables["folder_id"] = folder_id
        args_parts.append("folder_id: $folder_id")
    if template_id is not None:
        var_defs.append("$template_id: Int!")
        variables["template_id"] = template_id
        args_parts.append("template_id: $template_id")
    query = (
        f"mutation ({', '.join(var_defs)}) "
        f"{{ create_board ({', '.join(args_parts)}) {{ id }} }}"
    )
    try:
        result = await _graphql(auth_type, auth_data, query, variables)
    except _AuthError as exc:
        return CreateBoardOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return CreateBoardOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return CreateBoardOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateBoardOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return CreateBoardOutput(success=False, error=error)
    board_id = (result.get("data") or {}).get("create_board", {}).get("id")
    return CreateBoardOutput(success=True, id=board_id)


@tool(args_schema=CreateColumnInput)
@serialize_pydantic_return
async def create_column(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    title: str,
    column_type: str,
    defaults: str | None = None,
    description: str | None = None,
) -> CreateColumnOutput:
    """Creates a column in a board."""
    var_defs = ["$board_id: ID!", "$title: String!", "$column_type: ColumnType!"]
    variables: dict[str, Any] = {
        "board_id": board_id, "title": title, "column_type": column_type,
    }
    args_parts = ["board_id: $board_id", "title: $title", "column_type: $column_type"]
    if defaults is not None:
        var_defs.append("$defaults: JSON")
        variables["defaults"] = defaults
        args_parts.append("defaults: $defaults")
    if description is not None:
        var_defs.append("$description: String")
        variables["description"] = description
        args_parts.append("description: $description")
    query = (
        f"mutation ({', '.join(var_defs)}) "
        f"{{ create_column ({', '.join(args_parts)}) {{ id }} }}"
    )
    try:
        result = await _graphql(auth_type, auth_data, query, variables)
    except _AuthError as exc:
        return CreateColumnOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return CreateColumnOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return CreateColumnOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateColumnOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return CreateColumnOutput(success=False, error=error)
    col_id = (result.get("data") or {}).get("create_column", {}).get("id")
    return CreateColumnOutput(success=True, id=col_id)


@tool(args_schema=CreateGroupInput)
@serialize_pydantic_return
async def create_group(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    group_name: str,
) -> CreateGroupOutput:
    """Creates a new group in a specific board."""
    query = (
        "mutation ($board_id: ID!, $group_name: String!) "
        "{ create_group (board_id: $board_id, group_name: $group_name) { id } }"
    )
    variables: dict[str, Any] = {"board_id": board_id, "group_name": group_name}
    try:
        result = await _graphql(auth_type, auth_data, query, variables)
    except _AuthError as exc:
        return CreateGroupOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return CreateGroupOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return CreateGroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateGroupOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return CreateGroupOutput(success=False, error=error)
    group_id = (result.get("data") or {}).get("create_group", {}).get("id")
    return CreateGroupOutput(success=True, id=group_id)


@tool(args_schema=CreateItemInput)
@serialize_pydantic_return
async def create_item(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    item_name: str,
    group_id: str | None = None,
    create_labels: bool | None = None,
    column_values: str | None = None,
) -> CreateItemOutput:
    """Creates an item in a board."""
    var_defs = ["$board_id: ID!", "$item_name: String!"]
    variables: dict[str, Any] = {"board_id": board_id, "item_name": item_name}
    args_parts = ["board_id: $board_id", "item_name: $item_name"]
    if group_id is not None:
        var_defs.append("$group_id: String")
        variables["group_id"] = group_id
        args_parts.append("group_id: $group_id")
    if create_labels is not None:
        var_defs.append("$create_labels_if_missing: Boolean")
        variables["create_labels_if_missing"] = create_labels
        args_parts.append("create_labels_if_missing: $create_labels_if_missing")
    if column_values is not None:
        var_defs.append("$column_values: JSON")
        variables["column_values"] = column_values
        args_parts.append("column_values: $column_values")
    query = (
        f"mutation ({', '.join(var_defs)}) "
        f"{{ create_item ({', '.join(args_parts)}) {{ id }} }}"
    )
    try:
        result = await _graphql(auth_type, auth_data, query, variables)
    except _AuthError as exc:
        return CreateItemOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return CreateItemOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return CreateItemOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateItemOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return CreateItemOutput(success=False, error=error)
    item_id = (result.get("data") or {}).get("create_item", {}).get("id")
    return CreateItemOutput(success=True, id=item_id)


@tool(args_schema=CreateSubitemInput)
@serialize_pydantic_return
async def create_subitem(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    parent_item_id: str,
    item_name: str,
    column_values: str | None = None,
) -> CreateSubitemOutput:
    """Creates a subitem under a parent item."""
    var_defs = ["$parent_item_id: ID!", "$item_name: String!"]
    variables: dict[str, Any] = {"parent_item_id": parent_item_id, "item_name": item_name}
    args_parts = ["parent_item_id: $parent_item_id", "item_name: $item_name"]
    if column_values is not None:
        var_defs.append("$column_values: JSON")
        variables["column_values"] = column_values
        args_parts.append("column_values: $column_values")
    query = (
        f"mutation ({', '.join(var_defs)}) "
        f"{{ create_subitem ({', '.join(args_parts)}) {{ id }} }}"
    )
    try:
        result = await _graphql(auth_type, auth_data, query, variables)
    except _AuthError as exc:
        return CreateSubitemOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return CreateSubitemOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return CreateSubitemOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSubitemOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return CreateSubitemOutput(success=False, error=error)
    sub_id = (result.get("data") or {}).get("create_subitem", {}).get("id")
    return CreateSubitemOutput(success=True, id=sub_id)


@tool(args_schema=CreateUpdateInput)
@serialize_pydantic_return
async def create_update(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    item_id: str,
    update_body: str,
    parent_id: str | None = None,
) -> CreateUpdateOutput:
    """Creates a new update (comment) on an item."""
    var_defs = ["$item_id: ID!", "$body: String!"]
    variables: dict[str, Any] = {"item_id": item_id, "body": update_body}
    args_parts = ["item_id: $item_id", "body: $body"]
    if parent_id is not None:
        var_defs.append("$parent_id: ID")
        variables["parent_id"] = parent_id
        args_parts.append("parent_id: $parent_id")
    query = (
        f"mutation ({', '.join(var_defs)}) "
        f"{{ create_update ({', '.join(args_parts)}) {{ id }} }}"
    )
    try:
        result = await _graphql(auth_type, auth_data, query, variables)
    except _AuthError as exc:
        return CreateUpdateOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return CreateUpdateOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return CreateUpdateOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateUpdateOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return CreateUpdateOutput(success=False, error=error)
    update_id = (result.get("data") or {}).get("create_update", {}).get("id")
    return CreateUpdateOutput(success=True, id=update_id)


@tool(args_schema=GetBoardItemsPageInput)
@serialize_pydantic_return
async def get_board_items_page(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    query_params: str | None = None,
    max_pages: int = 50,
) -> GetBoardItemsPageOutput:
    """Retrieves items from a board with optional filtering."""
    query_args = ""
    if query_params:
        query_args = f", query_params: {json.dumps(query_params)}"
    safe_board_id = json.dumps(board_id)
    query = (
        f"{{ boards (ids: [{safe_board_id}]) {{ items_page (limit: 500{query_args}) "
        f"{{ cursor items {{ id name column_values {{ id value text }} }} }} }} }}"
    )
    try:
        all_items: list[dict[str, Any]] = []
        result = await _graphql(auth_type, auth_data, query)
        error = _check_errors(result)
        if error:
            return GetBoardItemsPageOutput(success=False, error=error)
        boards = (result.get("data") or {}).get("boards") or []
        if boards:
            page_data = boards[0].get("items_page") or {}
            all_items.extend(page_data.get("items") or [])
            cursor = page_data.get("cursor")
            pages_seen = 1
            while cursor and pages_seen < max_pages:
                next_query = (
                    f"{{ next_items_page (limit: 500, cursor: {json.dumps(cursor)}) "
                    f"{{ cursor items {{ id name column_values {{ id value text }} }} }} }}"
                )
                result = await _graphql(auth_type, auth_data, next_query)
                error = _check_errors(result)
                if error:
                    break
                next_data = (result.get("data") or {}).get("next_items_page") or {}
                all_items.extend(next_data.get("items") or [])
                cursor = next_data.get("cursor")
                pages_seen += 1
    except _AuthError as exc:
        return GetBoardItemsPageOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return GetBoardItemsPageOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return GetBoardItemsPageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBoardItemsPageOutput(success=False, error=f"Call failed: {exc}")
    items = [
        ItemSummary(
            id=i.get("id"),
            name=i.get("name"),
            column_values=[
                ColumnValue(id=cv.get("id"), value=cv.get("value"), text=cv.get("text"))
                for cv in (i.get("column_values") or [])
            ],
        )
        for i in all_items
    ]
    return GetBoardItemsPageOutput(success=True, items=items)


@tool(args_schema=GetColumnValuesInput)
@serialize_pydantic_return
async def get_column_values(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    item_id: str,
    column_ids: list[str] | None = None,
) -> GetColumnValuesOutput:
    """Returns values of specific columns for a board item."""
    col_filter = ""
    if column_ids:
        ids_str = ", ".join(json.dumps(c) for c in column_ids)
        col_filter = f"(ids: [{ids_str}])"
    safe_item_id = json.dumps(item_id)
    query = (
        f"{{ items (ids: [{safe_item_id}]) "
        f"{{ id name column_values{col_filter} {{ id value text }} }} }}"
    )
    try:
        result = await _graphql(auth_type, auth_data, query)
    except _AuthError as exc:
        return GetColumnValuesOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return GetColumnValuesOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return GetColumnValuesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetColumnValuesOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return GetColumnValuesOutput(success=False, error=error)
    raw_items = (result.get("data") or {}).get("items") or []
    items = [
        ItemSummary(
            id=i.get("id"),
            name=i.get("name"),
            column_values=[
                ColumnValue(id=cv.get("id"), value=cv.get("value"), text=cv.get("text"))
                for cv in (i.get("column_values") or [])
            ],
        )
        for i in raw_items
    ]
    return GetColumnValuesOutput(success=True, items=items)


@tool(args_schema=GetItemsByColumnValueInput)
@serialize_pydantic_return
async def get_items_by_column_value(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    column_id: str,
    value: str,
    max_pages: int = 50,
) -> GetItemsByColumnValueOutput:
    """Searches a column for items matching a specific value."""
    safe_board_id = json.dumps(board_id)
    safe_column_id = json.dumps(column_id)
    safe_value = json.dumps(value)
    query = (
        f"{{ items_page_by_column_values (board_id: {safe_board_id}, limit: 500, "
        f"columns: [{{column_id: {safe_column_id}, column_values: [{safe_value}]}}]) "
        f"{{ cursor items {{ id name column_values {{ id value text }} }} }} }}"
    )
    try:
        all_items: list[dict[str, Any]] = []
        result = await _graphql(auth_type, auth_data, query)
        error = _check_errors(result)
        if error:
            return GetItemsByColumnValueOutput(success=False, error=error)
        page_data = (result.get("data") or {}).get("items_page_by_column_values") or {}
        all_items.extend(page_data.get("items") or [])
        cursor = page_data.get("cursor")
        pages_seen = 1
        while cursor and pages_seen < max_pages:
            next_query = (
                f"{{ next_items_page (limit: 500, cursor: {json.dumps(cursor)}) "
                f"{{ cursor items {{ id name column_values {{ id value text }} }} }} }}"
            )
            result = await _graphql(auth_type, auth_data, next_query)
            error = _check_errors(result)
            if error:
                break
            next_data = (result.get("data") or {}).get("next_items_page") or {}
            all_items.extend(next_data.get("items") or [])
            cursor = next_data.get("cursor")
            pages_seen += 1
    except _AuthError as exc:
        return GetItemsByColumnValueOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return GetItemsByColumnValueOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return GetItemsByColumnValueOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetItemsByColumnValueOutput(success=False, error=f"Call failed: {exc}")
    items = [
        ItemSummary(
            id=i.get("id"),
            name=i.get("name"),
            column_values=[
                ColumnValue(id=cv.get("id"), value=cv.get("value"), text=cv.get("text"))
                for cv in (i.get("column_values") or [])
            ],
        )
        for i in all_items
    ]
    return GetItemsByColumnValueOutput(success=True, items=items)


@tool(args_schema=ListBoardsInput)
@serialize_pydantic_return
async def list_boards(
    auth_type: str,
    auth_data: dict[str, Any],
    ids: list[str] | None = None,
    workspace_ids: list[int] | None = None,
    board_kind: str | None = None,
    state: str = "all",
    order_by: str = "created_at",
    limit: int = 25,
    page: int = 1,
) -> ListBoardsOutput:
    """Lists boards with optional filters for kind, state, and workspace."""
    args_parts: list[str] = [f"limit: {json.dumps(limit)}", f"page: {json.dumps(page)}"]
    if ids:
        ids_str = ", ".join(json.dumps(i) for i in ids)
        args_parts.append(f"ids: [{ids_str}]")
    if workspace_ids:
        ws_str = ", ".join(json.dumps(w) for w in workspace_ids)
        args_parts.append(f"workspace_ids: [{ws_str}]")
    if board_kind:
        args_parts.append(f"board_kind: {json.dumps(board_kind)}")
    if state and state != "all":
        args_parts.append(f"state: {json.dumps(state)}")
    if order_by:
        args_parts.append(f"order_by: {json.dumps(order_by)}")
    args_str = ", ".join(args_parts)
    query = f"{{ boards ({args_str}) {{ id name state board_kind description workspace_id }} }}"
    try:
        result = await _graphql(auth_type, auth_data, query)
    except _AuthError as exc:
        return ListBoardsOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return ListBoardsOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return ListBoardsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListBoardsOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return ListBoardsOutput(success=False, error=error)
    raw_boards = (result.get("data") or {}).get("boards") or []
    boards = [
        MondayBoard(
            id=b.get("id"),
            name=b.get("name"),
            state=b.get("state"),
            board_kind=b.get("board_kind"),
            description=b.get("description"),
            workspace_id=str(b["workspace_id"]) if b.get("workspace_id") else None,
        )
        for b in raw_boards
    ]
    return ListBoardsOutput(success=True, boards=boards)


@tool(args_schema=ListWorkspacesInput)
@serialize_pydantic_return
async def list_workspaces(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListWorkspacesOutput:
    """Retrieves available workspaces with their IDs and names."""
    query = "{ workspaces { id name } }"
    try:
        result = await _graphql(auth_type, auth_data, query)
    except _AuthError as exc:
        return ListWorkspacesOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return ListWorkspacesOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return ListWorkspacesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWorkspacesOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return ListWorkspacesOutput(success=False, error=error)
    raw_workspaces = (result.get("data") or {}).get("workspaces") or []
    workspaces = [
        WorkspaceOption(
            label=w.get("name"),
            value=int(w["id"]) if w.get("id") else None,
        )
        for w in raw_workspaces
    ]
    return ListWorkspacesOutput(success=True, workspaces=workspaces)


@tool(args_schema=UpdateColumnValuesInput)
@serialize_pydantic_return
async def update_column_values(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    item_id: str,
    column_values: str,
) -> UpdateColumnValuesOutput:
    """Updates multiple column values for an item."""
    query = (
        "mutation ($board_id: ID!, $item_id: ID!, $column_values: JSON!) "
        "{ change_multiple_column_values "
        "(board_id: $board_id, item_id: $item_id, column_values: $column_values) "
        "{ id name column_values { id value } } }"
    )
    variables: dict[str, Any] = {
        "board_id": board_id, "item_id": item_id, "column_values": column_values,
    }
    try:
        result = await _graphql(auth_type, auth_data, query, variables)
    except _AuthError as exc:
        return UpdateColumnValuesOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return UpdateColumnValuesOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return UpdateColumnValuesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateColumnValuesOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return UpdateColumnValuesOutput(success=False, error=error)
    raw = (result.get("data") or {}).get("change_multiple_column_values")
    items: list[ItemSummary] = []
    if raw:
        items.append(
            ItemSummary(
                id=raw.get("id"),
                name=raw.get("name"),
                column_values=[
                    ColumnValue(id=cv.get("id"), value=cv.get("value"))
                    for cv in (raw.get("column_values") or [])
                ],
            )
        )
    return UpdateColumnValuesOutput(success=True, items=items)


@tool(args_schema=UpdateItemNameInput)
@serialize_pydantic_return
async def update_item_name(
    auth_type: str,
    auth_data: dict[str, Any],
    board_id: str,
    item_id: str,
    item_name: str,
) -> UpdateItemNameOutput:
    """Updates an item's name."""
    col_vals = json.dumps({"name": item_name})
    query = (
        "mutation ($board_id: ID!, $item_id: ID!, $column_values: JSON!) "
        "{ change_multiple_column_values "
        "(board_id: $board_id, item_id: $item_id, column_values: $column_values) "
        "{ id } }"
    )
    variables: dict[str, Any] = {
        "board_id": board_id, "item_id": item_id, "column_values": col_vals,
    }
    try:
        result = await _graphql(auth_type, auth_data, query, variables)
    except _AuthError as exc:
        return UpdateItemNameOutput(success=False, error=str(exc))
    except httpx.HTTPStatusError as exc:
        return UpdateItemNameOutput(success=False, error=str(exc))
    except httpx.TimeoutException:
        return UpdateItemNameOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateItemNameOutput(success=False, error=f"Call failed: {exc}")
    error = _check_errors(result)
    if error:
        return UpdateItemNameOutput(success=False, error=error)
    result_id = (result.get("data") or {}).get("change_multiple_column_values", {}).get("id")
    return UpdateItemNameOutput(success=True, id=result_id)
