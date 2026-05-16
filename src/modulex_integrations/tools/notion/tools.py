"""Notion LangChain ``@tool`` functions.

Pure HTTP integration against the Notion v1 REST API. Token-based
runtime convention (``auth_type, auth_data`` first args) with paired
``oauth2 + bearer_token`` auth schemas.

19 actions across 6 surfaces (search / pages / databases / blocks /
users / comments). Every action wraps the body in try/except → unified
``success=False`` envelope (exa-style); HTTP errors surface as
``API error: <status> - <body>``.

``get_page`` does an **N+1 fetch** when ``include_content=True``: GET
the page, then GET its children block list. Preserved from legacy.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.notion.outputs import (
    AppendBlocksOutput,
    CreateCommentOutput,
    CreateDatabaseItemOutput,
    CreateDatabaseOutput,
    CreatePageOutput,
    DeleteBlockOutput,
    GetBlockChildrenOutput,
    GetBlockOutput,
    GetBotUserOutput,
    GetCommentsOutput,
    GetDatabaseOutput,
    GetPageOutput,
    GetUserOutput,
    ListUsersOutput,
    QueryDatabaseOutput,
    SearchOutput,
    UpdateBlockOutput,
    UpdateDatabaseOutput,
    UpdatePageOutput,
)

__all__ = [
    "append_blocks",
    "create_comment",
    "create_database",
    "create_database_item",
    "create_page",
    "delete_block",
    "get_block",
    "get_block_children",
    "get_bot_user",
    "get_comments",
    "get_database",
    "get_page",
    "get_user",
    "list_users",
    "query_database",
    "search",
    "update_block",
    "update_database",
    "update_page",
]

_API = "https://api.notion.com/v1"
_VERSION = "2022-06-28"
_TIMEOUT = 30.0


def _headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "Notion-Version": _VERSION}
    if auth_type == "oauth2":
        token = auth_data.get("access_token")
    elif auth_type == "bearer_token":
        token = auth_data.get("token") or auth_data.get("bearer_token")
    else:
        token = auth_data.get("access_token") or auth_data.get("token")
    if token:
        headers["Authorization"] = f"Bearer {str(token).strip()}"
    return headers


def _validate(auth_data: dict[str, Any], action: str) -> str | None:
    if not (
        auth_data.get("access_token")
        or auth_data.get("token")
        or auth_data.get("bearer_token")
    ):
        return f"Notion access token missing for {action}"
    return None


def _api_err(status: int, body: str) -> str:
    return f"API error: {status} - {body}"


def _extract_rich_text(rich_text_array: list[Any] | None) -> str:
    if not rich_text_array:
        return ""
    return "".join(item.get("plain_text", "") for item in rich_text_array)


def _extract_title(item: dict[str, Any]) -> str | None:
    """Pull a title string from a page/database item (Notion has 3 conventions)."""
    properties = item.get("properties") or {}
    for prop_value in properties.values():
        if prop_value.get("type") == "title":
            return _extract_rich_text(prop_value.get("title"))
    name_prop = properties.get("Name") or {}
    if name_prop.get("type") == "title":
        return _extract_rich_text(name_prop.get("title"))
    if isinstance(item.get("title"), list):
        return _extract_rich_text(item["title"])
    return None


def _markdown_to_blocks(markdown: str) -> list[dict[str, Any]]:
    """Trivial markdown→Notion blocks (one paragraph per non-empty line)."""
    if not markdown:
        return []
    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]},
        }
        for line in (s.strip() for s in markdown.split("\n"))
        if line
    ]


async def _call(
    method: str,
    path: str,
    auth_type: str,
    auth_data: dict[str, Any],
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Make one Notion API call and return (ok, error_msg, body_dict)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method,
                f"{_API}{path}",
                headers=_headers(auth_type, auth_data),
                json=json_body,
                params=params,
            )
        if response.status_code != 200:
            return False, _api_err(response.status_code, response.text), {}
        return True, None, response.json() or {}
    except Exception as exc:
        return False, str(exc), {}


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2 or bearer_token)")
    auth_data: dict[str, Any] = Field(description="Auth data carrying tokens")


class SearchInput(_AuthFields):
    query: str | None = None
    filter: dict[str, Any] | None = None
    sort: dict[str, Any] | None = None
    start_cursor: str | None = None
    page_size: int = 100


class CreatePageInput(_AuthFields):
    parent_type: str = Field(description="'database' or 'page'")
    parent_id: str = Field(description="Parent page/database ID")
    title: str | None = None
    content: str | None = None
    children: list[dict[str, Any]] | None = None
    properties: dict[str, Any] | None = None


class GetPageInput(_AuthFields):
    page_id: str = Field(description="Page ID")
    include_content: bool = Field(default=True)


class UpdatePageInput(_AuthFields):
    page_id: str = Field(description="Page ID")
    title: str | None = None
    properties: dict[str, Any] | None = None
    archived: bool | None = None


class QueryDatabaseInput(_AuthFields):
    database_id: str = Field(description="Database ID")
    filter: dict[str, Any] | None = None
    sorts: list[dict[str, Any]] | None = None
    start_cursor: str | None = None
    page_size: int = 100


class GetDatabaseInput(_AuthFields):
    database_id: str = Field(description="Database ID")


class CreateDatabaseInput(_AuthFields):
    parent_page_id: str = Field(description="Parent page ID")
    title: str = Field(description="Database title")
    properties: dict[str, Any] = Field(description="Property schema")


class UpdateDatabaseInput(_AuthFields):
    database_id: str = Field(description="Database ID")
    title: str | None = None
    description: str | None = None
    properties: dict[str, Any] | None = None


class CreateDatabaseItemInput(_AuthFields):
    database_id: str = Field(description="Database ID")
    properties: dict[str, Any] = Field(description="Item properties")


class GetBlockInput(_AuthFields):
    block_id: str = Field(description="Block ID")


class GetBlockChildrenInput(_AuthFields):
    block_id: str = Field(description="Parent block or page ID")
    start_cursor: str | None = None
    page_size: int = 100


class AppendBlocksInput(_AuthFields):
    block_id: str = Field(description="Block/page ID to append into")
    children: list[dict[str, Any]] = Field(description="Notion block objects")


class UpdateBlockInput(_AuthFields):
    block_id: str = Field(description="Block ID")
    block: dict[str, Any] = Field(description="Updated block content")


class DeleteBlockInput(_AuthFields):
    block_id: str = Field(description="Block ID")


class ListUsersInput(_AuthFields):
    start_cursor: str | None = None
    page_size: int = 100


class GetUserInput(_AuthFields):
    user_id: str = Field(description="User ID")


class GetBotUserInput(_AuthFields):
    pass


class CreateCommentInput(_AuthFields):
    rich_text: list[dict[str, Any]] = Field(description="Comment body as rich text")
    page_id: str | None = None
    discussion_id: str | None = None


class GetCommentsInput(_AuthFields):
    block_id: str = Field(description="Block/page ID")
    start_cursor: str | None = None
    page_size: int = 100


# --- Tools -----------------------------------------------------------------


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str | None = None,
    filter: dict[str, Any] | None = None,
    sort: dict[str, Any] | None = None,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> SearchOutput:
    """Search Notion pages and databases."""
    err = _validate(auth_data, "search")
    if err:
        return SearchOutput(success=False, error=err)
    payload: dict[str, Any] = {"page_size": min(page_size, 100)}
    if query:
        payload["query"] = query
    if filter:
        payload["filter"] = filter
    if sort:
        payload["sort"] = sort
    if start_cursor:
        payload["start_cursor"] = start_cursor

    ok, e, data = await _call("POST", "/search", auth_type, auth_data, json_body=payload)
    if not ok:
        return SearchOutput(success=False, error=e)
    raw_results = data.get("results") or []
    results = [
        {
            "id": item.get("id"),
            "object": item.get("object"),
            "url": item.get("url"),
            "created_time": item.get("created_time"),
            "last_edited_time": item.get("last_edited_time"),
            "title": _extract_title(item),
            "parent": item.get("parent"),
        }
        for item in raw_results
    ]
    return SearchOutput(
        success=True,
        results=results,
        total=len(results),
        has_more=data.get("has_more", False),
        next_cursor=data.get("next_cursor"),
    )


@tool(args_schema=CreatePageInput)
@serialize_pydantic_return
async def create_page(
    auth_type: str,
    auth_data: dict[str, Any],
    parent_type: str,
    parent_id: str,
    title: str | None = None,
    content: str | None = None,
    children: list[dict[str, Any]] | None = None,
    properties: dict[str, Any] | None = None,
) -> CreatePageOutput:
    """Create a new Notion page under a database or page parent."""
    err = _validate(auth_data, "create_page")
    if err:
        return CreatePageOutput(success=False, error=err)

    parent = (
        {"database_id": parent_id} if parent_type == "database" else {"page_id": parent_id}
    )
    payload: dict[str, Any] = {"parent": parent}
    if properties:
        payload["properties"] = properties
    elif title:
        payload["properties"] = {"title": {"title": [{"text": {"content": title}}]}}
    else:
        payload["properties"] = {}
    if children:
        payload["children"] = children
    elif content:
        payload["children"] = _markdown_to_blocks(content)

    ok, e, page = await _call("POST", "/pages", auth_type, auth_data, json_body=payload)
    if not ok:
        return CreatePageOutput(success=False, error=e)
    return CreatePageOutput(
        success=True,
        id=page.get("id"),
        url=page.get("url"),
        created_time=page.get("created_time"),
        title=_extract_title(page),
        properties=page.get("properties"),
        parent=page.get("parent"),
    )


@tool(args_schema=GetPageInput)
@serialize_pydantic_return
async def get_page(
    auth_type: str,
    auth_data: dict[str, Any],
    page_id: str,
    include_content: bool = True,
) -> GetPageOutput:
    """Retrieve a Notion page (optionally with child blocks via N+1 fetch)."""
    err = _validate(auth_data, "get_page")
    if err:
        return GetPageOutput(success=False, error=err)
    ok, e, page = await _call("GET", f"/pages/{page_id}", auth_type, auth_data)
    if not ok:
        return GetPageOutput(success=False, error=e)
    content: list[dict[str, Any]] | None = None
    if include_content:
        ok2, _e2, data = await _call(
            "GET", f"/blocks/{page_id}/children", auth_type, auth_data
        )
        if ok2:
            content = data.get("results") or []
    return GetPageOutput(
        success=True,
        id=page.get("id"),
        url=page.get("url"),
        created_time=page.get("created_time"),
        last_edited_time=page.get("last_edited_time"),
        created_by=page.get("created_by"),
        last_edited_by=page.get("last_edited_by"),
        title=_extract_title(page),
        properties=page.get("properties"),
        parent=page.get("parent"),
        archived=page.get("archived"),
        content=content,
    )


@tool(args_schema=UpdatePageInput)
@serialize_pydantic_return
async def update_page(
    auth_type: str,
    auth_data: dict[str, Any],
    page_id: str,
    title: str | None = None,
    properties: dict[str, Any] | None = None,
    archived: bool | None = None,
) -> UpdatePageOutput:
    """Update a page's properties / archive status."""
    err = _validate(auth_data, "update_page")
    if err:
        return UpdatePageOutput(success=False, error=err)
    payload: dict[str, Any] = {}
    if properties:
        payload["properties"] = properties
    elif title:
        payload["properties"] = {"title": {"title": [{"text": {"content": title}}]}}
    if archived is not None:
        payload["archived"] = archived

    ok, e, page = await _call(
        "PATCH", f"/pages/{page_id}", auth_type, auth_data, json_body=payload
    )
    if not ok:
        return UpdatePageOutput(success=False, error=e)
    return UpdatePageOutput(
        success=True,
        id=page.get("id"),
        url=page.get("url"),
        last_edited_time=page.get("last_edited_time"),
        title=_extract_title(page),
        properties=page.get("properties"),
        archived=page.get("archived"),
    )


@tool(args_schema=QueryDatabaseInput)
@serialize_pydantic_return
async def query_database(
    auth_type: str,
    auth_data: dict[str, Any],
    database_id: str,
    filter: dict[str, Any] | None = None,
    sorts: list[dict[str, Any]] | None = None,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> QueryDatabaseOutput:
    """Query a database with filters and sorts."""
    err = _validate(auth_data, "query_database")
    if err:
        return QueryDatabaseOutput(success=False, error=err)
    payload: dict[str, Any] = {"page_size": min(page_size, 100)}
    if filter:
        payload["filter"] = filter
    if sorts:
        payload["sorts"] = sorts
    if start_cursor:
        payload["start_cursor"] = start_cursor

    ok, e, data = await _call(
        "POST",
        f"/databases/{database_id}/query",
        auth_type,
        auth_data,
        json_body=payload,
    )
    if not ok:
        return QueryDatabaseOutput(success=False, error=e)
    raw_results = data.get("results") or []
    results = [
        {
            "id": item.get("id"),
            "url": item.get("url"),
            "created_time": item.get("created_time"),
            "last_edited_time": item.get("last_edited_time"),
            "title": _extract_title(item),
            "properties": item.get("properties"),
        }
        for item in raw_results
    ]
    return QueryDatabaseOutput(
        success=True,
        database_id=database_id,
        results=results,
        total=len(results),
        has_more=data.get("has_more", False),
        next_cursor=data.get("next_cursor"),
    )


@tool(args_schema=GetDatabaseInput)
@serialize_pydantic_return
async def get_database(
    auth_type: str, auth_data: dict[str, Any], database_id: str
) -> GetDatabaseOutput:
    """Retrieve database metadata + property schema."""
    err = _validate(auth_data, "get_database")
    if err:
        return GetDatabaseOutput(success=False, error=err)
    ok, e, db = await _call(
        "GET", f"/databases/{database_id}", auth_type, auth_data
    )
    if not ok:
        return GetDatabaseOutput(success=False, error=e)
    return GetDatabaseOutput(
        success=True,
        id=db.get("id"),
        url=db.get("url"),
        created_time=db.get("created_time"),
        last_edited_time=db.get("last_edited_time"),
        title=_extract_rich_text(db.get("title") or []),
        description=_extract_rich_text(db.get("description") or []),
        properties=db.get("properties"),
        parent=db.get("parent"),
        archived=db.get("archived"),
        is_inline=db.get("is_inline"),
    )


@tool(args_schema=CreateDatabaseInput)
@serialize_pydantic_return
async def create_database(
    auth_type: str,
    auth_data: dict[str, Any],
    parent_page_id: str,
    title: str,
    properties: dict[str, Any],
) -> CreateDatabaseOutput:
    """Create a new database under a parent page."""
    err = _validate(auth_data, "create_database")
    if err:
        return CreateDatabaseOutput(success=False, error=err)
    payload = {
        "parent": {"page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties,
    }
    ok, e, db = await _call(
        "POST", "/databases", auth_type, auth_data, json_body=payload
    )
    if not ok:
        return CreateDatabaseOutput(success=False, error=e)
    return CreateDatabaseOutput(
        success=True,
        id=db.get("id"),
        url=db.get("url"),
        created_time=db.get("created_time"),
        title=_extract_rich_text(db.get("title") or []),
        properties=db.get("properties"),
        parent=db.get("parent"),
    )


@tool(args_schema=UpdateDatabaseInput)
@serialize_pydantic_return
async def update_database(
    auth_type: str,
    auth_data: dict[str, Any],
    database_id: str,
    title: str | None = None,
    description: str | None = None,
    properties: dict[str, Any] | None = None,
) -> UpdateDatabaseOutput:
    """Update a database's title, description, or schema."""
    err = _validate(auth_data, "update_database")
    if err:
        return UpdateDatabaseOutput(success=False, error=err)
    payload: dict[str, Any] = {}
    if title:
        payload["title"] = [{"type": "text", "text": {"content": title}}]
    if description:
        payload["description"] = [{"type": "text", "text": {"content": description}}]
    if properties:
        payload["properties"] = properties

    ok, e, db = await _call(
        "PATCH",
        f"/databases/{database_id}",
        auth_type,
        auth_data,
        json_body=payload,
    )
    if not ok:
        return UpdateDatabaseOutput(success=False, error=e)
    return UpdateDatabaseOutput(
        success=True,
        id=db.get("id"),
        url=db.get("url"),
        last_edited_time=db.get("last_edited_time"),
        title=_extract_rich_text(db.get("title") or []),
        description=_extract_rich_text(db.get("description") or []),
        properties=db.get("properties"),
    )


@tool(args_schema=CreateDatabaseItemInput)
@serialize_pydantic_return
async def create_database_item(
    auth_type: str,
    auth_data: dict[str, Any],
    database_id: str,
    properties: dict[str, Any],
) -> CreateDatabaseItemOutput:
    """Create a new page inside a database."""
    err = _validate(auth_data, "create_database_item")
    if err:
        return CreateDatabaseItemOutput(success=False, error=err)
    payload = {"parent": {"database_id": database_id}, "properties": properties}
    ok, e, page = await _call(
        "POST", "/pages", auth_type, auth_data, json_body=payload
    )
    if not ok:
        return CreateDatabaseItemOutput(success=False, error=e)
    return CreateDatabaseItemOutput(
        success=True,
        id=page.get("id"),
        url=page.get("url"),
        created_time=page.get("created_time"),
        title=_extract_title(page),
        properties=page.get("properties"),
    )


@tool(args_schema=GetBlockInput)
@serialize_pydantic_return
async def get_block(
    auth_type: str, auth_data: dict[str, Any], block_id: str
) -> GetBlockOutput:
    """Retrieve a single block by ID."""
    err = _validate(auth_data, "get_block")
    if err:
        return GetBlockOutput(success=False, error=err)
    ok, e, block = await _call(
        "GET", f"/blocks/{block_id}", auth_type, auth_data
    )
    if not ok:
        return GetBlockOutput(success=False, error=e)
    block_type = block.get("type")
    return GetBlockOutput(
        success=True,
        id=block.get("id"),
        type=block_type,
        created_time=block.get("created_time"),
        last_edited_time=block.get("last_edited_time"),
        has_children=block.get("has_children"),
        archived=block.get("archived"),
        parent=block.get("parent"),
        content=block.get(block_type) if block_type else None,
    )


@tool(args_schema=GetBlockChildrenInput)
@serialize_pydantic_return
async def get_block_children(
    auth_type: str,
    auth_data: dict[str, Any],
    block_id: str,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> GetBlockChildrenOutput:
    """Retrieve a block's / page's child blocks."""
    err = _validate(auth_data, "get_block_children")
    if err:
        return GetBlockChildrenOutput(success=False, error=err)
    params: dict[str, Any] = {"page_size": min(page_size, 100)}
    if start_cursor:
        params["start_cursor"] = start_cursor
    ok, e, data = await _call(
        "GET",
        f"/blocks/{block_id}/children",
        auth_type,
        auth_data,
        params=params,
    )
    if not ok:
        return GetBlockChildrenOutput(success=False, error=e)
    raw_results = data.get("results") or []
    children = [
        {
            "id": block.get("id"),
            "type": block.get("type"),
            "has_children": block.get("has_children"),
            "content": block.get(block.get("type")) if block.get("type") else None,
        }
        for block in raw_results
    ]
    return GetBlockChildrenOutput(
        success=True,
        block_id=block_id,
        children=children,
        total=len(children),
        has_more=data.get("has_more", False),
        next_cursor=data.get("next_cursor"),
    )


@tool(args_schema=AppendBlocksInput)
@serialize_pydantic_return
async def append_blocks(
    auth_type: str,
    auth_data: dict[str, Any],
    block_id: str,
    children: list[dict[str, Any]],
) -> AppendBlocksOutput:
    """Append blocks to a page or block."""
    err = _validate(auth_data, "append_blocks")
    if err:
        return AppendBlocksOutput(success=False, error=err)
    ok, e, data = await _call(
        "PATCH",
        f"/blocks/{block_id}/children",
        auth_type,
        auth_data,
        json_body={"children": children},
    )
    if not ok:
        return AppendBlocksOutput(success=False, error=e)
    raw_results = data.get("results") or []
    appended = [
        {
            "id": block.get("id"),
            "type": block.get("type"),
            "has_children": block.get("has_children"),
        }
        for block in raw_results
    ]
    return AppendBlocksOutput(
        success=True,
        block_id=block_id,
        appended_blocks=appended,
        total_appended=len(appended),
    )


@tool(args_schema=UpdateBlockInput)
@serialize_pydantic_return
async def update_block(
    auth_type: str,
    auth_data: dict[str, Any],
    block_id: str,
    block: dict[str, Any],
) -> UpdateBlockOutput:
    """Update an existing block's content."""
    err = _validate(auth_data, "update_block")
    if err:
        return UpdateBlockOutput(success=False, error=err)
    ok, e, updated = await _call(
        "PATCH",
        f"/blocks/{block_id}",
        auth_type,
        auth_data,
        json_body=block,
    )
    if not ok:
        return UpdateBlockOutput(success=False, error=e)
    block_type = updated.get("type")
    return UpdateBlockOutput(
        success=True,
        id=updated.get("id"),
        type=block_type,
        last_edited_time=updated.get("last_edited_time"),
        has_children=updated.get("has_children"),
        content=updated.get(block_type) if block_type else None,
    )


@tool(args_schema=DeleteBlockInput)
@serialize_pydantic_return
async def delete_block(
    auth_type: str, auth_data: dict[str, Any], block_id: str
) -> DeleteBlockOutput:
    """Archive (delete) a block."""
    err = _validate(auth_data, "delete_block")
    if err:
        return DeleteBlockOutput(success=False, error=err)
    ok, e, block = await _call(
        "DELETE", f"/blocks/{block_id}", auth_type, auth_data
    )
    if not ok:
        return DeleteBlockOutput(success=False, error=e)
    return DeleteBlockOutput(
        success=True,
        id=block.get("id"),
        type=block.get("type"),
        archived=block.get("archived"),
    )


def _user_row(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user.get("id"),
        "object": user.get("object"),
        "type": user.get("type"),
        "name": user.get("name"),
        "avatar_url": user.get("avatar_url"),
        "person": user.get("person") if user.get("type") == "person" else None,
        "bot": user.get("bot") if user.get("type") == "bot" else None,
    }


@tool(args_schema=ListUsersInput)
@serialize_pydantic_return
async def list_users(
    auth_type: str,
    auth_data: dict[str, Any],
    start_cursor: str | None = None,
    page_size: int = 100,
) -> ListUsersOutput:
    """List all workspace users (people + bots)."""
    err = _validate(auth_data, "list_users")
    if err:
        return ListUsersOutput(success=False, error=err)
    params: dict[str, Any] = {"page_size": min(page_size, 100)}
    if start_cursor:
        params["start_cursor"] = start_cursor
    ok, e, data = await _call(
        "GET", "/users", auth_type, auth_data, params=params
    )
    if not ok:
        return ListUsersOutput(success=False, error=e)
    raw = data.get("results") or []
    users = [_user_row(u) for u in raw]
    return ListUsersOutput(
        success=True,
        users=users,
        total=len(users),
        has_more=data.get("has_more", False),
        next_cursor=data.get("next_cursor"),
    )


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(
    auth_type: str, auth_data: dict[str, Any], user_id: str
) -> GetUserOutput:
    """Retrieve a specific user by ID."""
    err = _validate(auth_data, "get_user")
    if err:
        return GetUserOutput(success=False, error=err)
    ok, e, user = await _call(
        "GET", f"/users/{user_id}", auth_type, auth_data
    )
    if not ok:
        return GetUserOutput(success=False, error=e)
    return GetUserOutput.model_validate({"success": True, **_user_row(user)})


@tool(args_schema=GetBotUserInput)
@serialize_pydantic_return
async def get_bot_user(
    auth_type: str, auth_data: dict[str, Any]
) -> GetBotUserOutput:
    """Retrieve the integration's bot user (GET /users/me)."""
    err = _validate(auth_data, "get_bot_user")
    if err:
        return GetBotUserOutput(success=False, error=err)
    ok, e, user = await _call(
        "GET", "/users/me", auth_type, auth_data
    )
    if not ok:
        return GetBotUserOutput(success=False, error=e)
    return GetBotUserOutput(
        success=True,
        id=user.get("id"),
        object=user.get("object"),
        type=user.get("type"),
        name=user.get("name"),
        avatar_url=user.get("avatar_url"),
        bot=user.get("bot"),
    )


@tool(args_schema=CreateCommentInput)
@serialize_pydantic_return
async def create_comment(
    auth_type: str,
    auth_data: dict[str, Any],
    rich_text: list[dict[str, Any]],
    page_id: str | None = None,
    discussion_id: str | None = None,
) -> CreateCommentOutput:
    """Create a comment on a page or discussion."""
    err = _validate(auth_data, "create_comment")
    if err:
        return CreateCommentOutput(success=False, error=err)
    if not page_id and not discussion_id:
        return CreateCommentOutput(
            success=False,
            error="Either page_id or discussion_id must be provided",
        )
    payload: dict[str, Any] = {"rich_text": rich_text}
    if page_id:
        payload["parent"] = {"page_id": page_id}
    if discussion_id:
        payload["discussion_id"] = discussion_id

    ok, e, comment = await _call(
        "POST", "/comments", auth_type, auth_data, json_body=payload
    )
    if not ok:
        return CreateCommentOutput(success=False, error=e)
    return CreateCommentOutput(
        success=True,
        id=comment.get("id"),
        created_time=comment.get("created_time"),
        discussion_id=comment.get("discussion_id"),
        parent=comment.get("parent"),
        rich_text=comment.get("rich_text"),
        created_by=comment.get("created_by"),
    )


@tool(args_schema=GetCommentsInput)
@serialize_pydantic_return
async def get_comments(
    auth_type: str,
    auth_data: dict[str, Any],
    block_id: str,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> GetCommentsOutput:
    """Retrieve comments on a block / page."""
    err = _validate(auth_data, "get_comments")
    if err:
        return GetCommentsOutput(success=False, error=err)
    params: dict[str, Any] = {
        "block_id": block_id,
        "page_size": min(page_size, 100),
    }
    if start_cursor:
        params["start_cursor"] = start_cursor
    ok, e, data = await _call(
        "GET", "/comments", auth_type, auth_data, params=params
    )
    if not ok:
        return GetCommentsOutput(success=False, error=e)
    raw = data.get("results") or []
    comments = [
        {
            "id": c.get("id"),
            "created_time": c.get("created_time"),
            "discussion_id": c.get("discussion_id"),
            "rich_text": c.get("rich_text"),
            "created_by": c.get("created_by"),
        }
        for c in raw
    ]
    return GetCommentsOutput(
        success=True,
        block_id=block_id,
        comments=comments,
        total=len(comments),
        has_more=data.get("has_more", False),
        next_cursor=data.get("next_cursor"),
    )
