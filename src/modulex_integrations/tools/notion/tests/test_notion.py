"""Tests for the Notion integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.notion import (
    TOOLS,
    append_blocks,
    create_comment,
    create_database,
    create_database_item,
    create_page,
    delete_block,
    get_block,
    get_block_children,
    get_bot_user,
    get_comments,
    get_database,
    get_page,
    get_user,
    list_users,
    manifest,
    query_database,
    search,
    update_block,
    update_database,
    update_page,
)
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

API = "https://api.notion.com/v1"
_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "secret_xxxxxxxx"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


class TestManifest:
    def test_manifest_exposes_19_actions(self) -> None:
        assert len(manifest.actions) == 19

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_bearer_token_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}


@pytest.mark.asyncio
async def test_search(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={
            "results": [
                {
                    "id": "p1",
                    "object": "page",
                    "url": "https://notion.so/p1",
                    "properties": {
                        "Name": {"type": "title", "title": [{"plain_text": "Hello"}]}
                    },
                }
            ],
            "has_more": False,
        },
    )
    result = SearchOutput.model_validate(
        await search.ainvoke(_args(query="hello"))
    )
    assert result.success is True
    assert result.total == 1
    assert result.results[0]["title"] == "Hello"


@pytest.mark.asyncio
async def test_search_missing_token() -> None:
    bad = {"auth_type": "bearer_token", "auth_data": {}}
    result = SearchOutput.model_validate(await search.ainvoke(bad))
    assert result.success is False
    assert result.error is not None and "token" in result.error


@pytest.mark.asyncio
async def test_create_page_with_markdown(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured.update(_json.loads(request.content.decode()))
        return Response(200, json={"id": "new", "url": "https://notion.so/new"})

    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/pages")
    result = CreatePageOutput.model_validate(
        await create_page.ainvoke(
            _args(
                parent_type="page",
                parent_id="parent1",
                title="My Page",
                content="line1\nline2",
            )
        )
    )
    assert result.success is True
    assert captured["parent"] == {"page_id": "parent1"}
    assert len(captured["children"]) == 2  # 2 non-empty markdown lines


@pytest.mark.asyncio
async def test_get_page_with_content_does_n_plus_one(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/pages/page1",
        json={"id": "page1", "url": "u1"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/blocks/page1/children",
        json={"results": [{"id": "b1", "type": "paragraph"}]},
    )
    result = GetPageOutput.model_validate(
        await get_page.ainvoke(_args(page_id="page1"))
    )
    assert result.success is True
    assert result.content is not None and len(result.content) == 1


@pytest.mark.asyncio
async def test_get_page_no_content_skips_second_call(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/pages/page1",
        json={"id": "page1"},
    )
    result = GetPageOutput.model_validate(
        await get_page.ainvoke(_args(page_id="page1", include_content=False))
    )
    assert result.success is True
    assert result.content is None


@pytest.mark.asyncio
async def test_update_page(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH", url=f"{API}/pages/p1", json={"id": "p1", "archived": True}
    )
    result = UpdatePageOutput.model_validate(
        await update_page.ainvoke(_args(page_id="p1", archived=True))
    )
    assert result.success is True
    assert result.archived is True


@pytest.mark.asyncio
async def test_query_database(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/databases/db1/query",
        json={"results": [{"id": "row1"}], "has_more": False},
    )
    result = QueryDatabaseOutput.model_validate(
        await query_database.ainvoke(_args(database_id="db1"))
    )
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_get_database(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/databases/db1",
        json={
            "id": "db1",
            "title": [{"plain_text": "My DB"}],
            "description": [{"plain_text": "About"}],
        },
    )
    result = GetDatabaseOutput.model_validate(
        await get_database.ainvoke(_args(database_id="db1"))
    )
    assert result.success is True
    assert result.title == "My DB"
    assert result.description == "About"


@pytest.mark.asyncio
async def test_create_database(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/databases",
        json={"id": "db_new", "title": [{"plain_text": "X"}]},
    )
    result = CreateDatabaseOutput.model_validate(
        await create_database.ainvoke(
            _args(
                parent_page_id="page1",
                title="X",
                properties={"Name": {"title": {}}},
            )
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_database(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/databases/db1",
        json={"id": "db1", "title": [{"plain_text": "Renamed"}]},
    )
    result = UpdateDatabaseOutput.model_validate(
        await update_database.ainvoke(
            _args(database_id="db1", title="Renamed")
        )
    )
    assert result.success is True
    assert result.title == "Renamed"


@pytest.mark.asyncio
async def test_create_database_item(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{API}/pages", json={"id": "row1"}
    )
    result = CreateDatabaseItemOutput.model_validate(
        await create_database_item.ainvoke(
            _args(database_id="db1", properties={"Name": {}})
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_block(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/blocks/b1",
        json={
            "id": "b1",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"plain_text": "hi"}]},
        },
    )
    result = GetBlockOutput.model_validate(
        await get_block.ainvoke(_args(block_id="b1"))
    )
    assert result.success is True
    assert result.type == "paragraph"
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_block_children(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/blocks/b1/children?page_size=100",
        json={"results": [{"id": "b2", "type": "paragraph"}]},
    )
    result = GetBlockChildrenOutput.model_validate(
        await get_block_children.ainvoke(_args(block_id="b1"))
    )
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_append_blocks(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/blocks/b1/children",
        json={"results": [{"id": "new_b", "type": "paragraph"}]},
    )
    result = AppendBlocksOutput.model_validate(
        await append_blocks.ainvoke(
            _args(
                block_id="b1",
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": []},
                    }
                ],
            )
        )
    )
    assert result.success is True
    assert result.total_appended == 1


@pytest.mark.asyncio
async def test_update_block(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/blocks/b1",
        json={"id": "b1", "type": "paragraph", "paragraph": {"rich_text": []}},
    )
    result = UpdateBlockOutput.model_validate(
        await update_block.ainvoke(
            _args(block_id="b1", block={"paragraph": {"rich_text": []}})
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_block(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/blocks/b1",
        json={"id": "b1", "archived": True},
    )
    result = DeleteBlockOutput.model_validate(
        await delete_block.ainvoke(_args(block_id="b1"))
    )
    assert result.success is True
    assert result.archived is True


@pytest.mark.asyncio
async def test_list_users(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users?page_size=100",
        json={
            "results": [
                {"id": "u1", "type": "person", "person": {"email": "a@x.io"}}
            ]
        },
    )
    result = ListUsersOutput.model_validate(
        await list_users.ainvoke(_args())
    )
    assert result.success is True
    assert result.users[0]["person"] == {"email": "a@x.io"}


@pytest.mark.asyncio
async def test_get_user(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/users/u1", json={"id": "u1", "type": "bot"}
    )
    result = GetUserOutput.model_validate(
        await get_user.ainvoke(_args(user_id="u1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_bot_user(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me",
        json={"id": "bot1", "type": "bot", "bot": {"workspace_name": "WS"}},
    )
    result = GetBotUserOutput.model_validate(
        await get_bot_user.ainvoke(_args())
    )
    assert result.success is True
    assert result.bot == {"workspace_name": "WS"}


@pytest.mark.asyncio
async def test_create_comment_validates_target() -> None:
    result = CreateCommentOutput.model_validate(
        await create_comment.ainvoke(_args(rich_text=[]))
    )
    assert result.success is False
    assert result.error is not None and "page_id" in result.error


@pytest.mark.asyncio
async def test_create_comment(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/comments",
        json={"id": "c1", "discussion_id": "d1"},
    )
    result = CreateCommentOutput.model_validate(
        await create_comment.ainvoke(
            _args(
                rich_text=[{"type": "text", "text": {"content": "hi"}}],
                page_id="p1",
            )
        )
    )
    assert result.success is True
    assert result.discussion_id == "d1"


@pytest.mark.asyncio
async def test_get_comments(httpx_mock: Any) -> None:
    import re
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/comments\?.*"),
        json={"results": [{"id": "c1", "rich_text": []}]},
    )
    result = GetCommentsOutput.model_validate(
        await get_comments.ainvoke(_args(block_id="b1"))
    )
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_api_error_envelope(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{API}/search", status_code=401, text="unauthorized"
    )
    result = SearchOutput.model_validate(await search.ainvoke(_args()))
    assert result.success is False
    assert result.error is not None and "401" in result.error
