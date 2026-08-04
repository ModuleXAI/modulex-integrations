"""Happy-path tests per action, plus the failure paths that matter for a
GraphQL API that answers HTTP 200 for everything: a top-level ``errors``
array, a typed mutation error, a non-200 response, a non-object body, and an
empty credential."""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.buffer import (
    TOOLS,
    create_idea,
    create_post,
    delete_post,
    edit_post,
    get_account,
    get_channels,
    get_idea_groups,
    get_ideas,
    get_post,
    get_posts,
    manifest,
)
from modulex_integrations.tools.buffer.outputs import (
    CreateIdeaOutput,
    CreatePostOutput,
    DeletePostOutput,
    EditPostOutput,
    GetAccountOutput,
    GetChannelsOutput,
    GetIdeaGroupsOutput,
    GetIdeasOutput,
    GetPostOutput,
    GetPostsOutput,
)

API = "https://api.buffer.com"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _sent_variables(httpx_mock: Any, index: int = 0) -> dict[str, Any]:
    body = json.loads(httpx_mock.get_requests()[index].content)
    variables = body.get("variables")
    return variables if isinstance(variables, dict) else {}


_POST_NODE: dict[str, Any] = {
    "id": "post_1",
    "text": "Hello world",
    "status": "scheduled",
    "via": "api",
    "channelId": "chan_1",
    "channelService": "linkedin",
    "schedulingType": "automatic",
    "shareMode": "addToQueue",
    "isCustomScheduled": False,
    "sharedNow": False,
    "createdAt": "2026-08-01T10:00:00Z",
    "updatedAt": "2026-08-01T10:00:00Z",
    "dueAt": "2026-08-02T15:00:00Z",
    "sentAt": None,
    "externalLink": None,
    "error": None,
    "assets": [
        {
            "id": "asset_1",
            "type": "image",
            "mimeType": "image/png",
            "source": "https://cdn.example.com/a.png",
            "thumbnail": "https://cdn.example.com/a-thumb.png",
        }
    ],
}

_IDEA_NODE: dict[str, Any] = {
    "id": "idea_1",
    "organizationId": "org_1",
    "groupId": "group_1",
    "content": {"title": "Launch teaser", "text": "Tease the launch"},
}


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_10_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_create_post(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "createPost": {"__typename": "PostActionSuccess", "post": _POST_NODE}
            }
        },
    )

    result_dict = await create_post.ainvoke(
        _args(channel_id="chan_1", text="Hello world", mode="addToQueue")
    )
    assert isinstance(result_dict, dict)
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is True
    assert result.post is not None
    assert result.post.id == "post_1"
    assert result.post.channel_service == "linkedin"
    assert result.post.assets[0].mime_type == "image/png"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    post_input = _sent_variables(httpx_mock)["input"]
    assert post_input["channelId"] == "chan_1"
    assert post_input["mode"] == "addToQueue"
    assert post_input["schedulingType"] == "automatic"
    assert "assets" not in post_input


@pytest.mark.asyncio
async def test_create_post_with_image_url_and_alt_text(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "createPost": {"__typename": "PostActionSuccess", "post": _POST_NODE}
            }
        },
    )

    result_dict = await create_post.ainvoke(
        _args(
            channel_id="chan_1",
            text="Look at this",
            media_url="https://cdn.example.com/a.png",
            media_alt_text="A screenshot",
        )
    )
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is True

    assets = _sent_variables(httpx_mock)["input"]["assets"]
    assert assets == [
        {
            "image": {
                "url": "https://cdn.example.com/a.png",
                "metadata": {"altText": "A screenshot"},
            }
        }
    ]


@pytest.mark.asyncio
async def test_create_post_detects_video_url(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "createPost": {"__typename": "PostActionSuccess", "post": _POST_NODE}
            }
        },
    )

    result_dict = await create_post.ainvoke(
        _args(channel_id="chan_1", media_url="https://cdn.example.com/clip.mp4?v=2")
    )
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is True

    assets = _sent_variables(httpx_mock)["input"]["assets"]
    assert assets == [{"video": {"url": "https://cdn.example.com/clip.mp4?v=2"}}]


@pytest.mark.asyncio
async def test_create_post_custom_scheduled_sends_due_at(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "createPost": {"__typename": "PostActionSuccess", "post": _POST_NODE}
            }
        },
    )

    result_dict = await create_post.ainvoke(
        _args(
            channel_id="chan_1",
            text="Scheduled",
            mode="customScheduled",
            due_at="2026-08-02T15:00:00Z",
            save_to_draft=True,
        )
    )
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is True

    post_input = _sent_variables(httpx_mock)["input"]
    assert post_input["dueAt"] == "2026-08-02T15:00:00Z"
    assert post_input["saveToDraft"] is True


@pytest.mark.asyncio
async def test_edit_post(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {"editPost": {"__typename": "PostActionSuccess", "post": _POST_NODE}}
        },
    )

    result_dict = await edit_post.ainvoke(_args(post_id="post_1", text="Updated text"))
    assert isinstance(result_dict, dict)
    result = EditPostOutput.model_validate(result_dict)
    assert result.success is True
    assert result.post is not None
    assert result.post.id == "post_1"

    post_input = _sent_variables(httpx_mock)["input"]
    assert post_input["id"] == "post_1"
    assert post_input["text"] == "Updated text"
    # schedulingType is non-null upstream, so it is always sent; mode is
    # omitted when the caller makes no scheduling change.
    assert post_input["schedulingType"] == "automatic"
    assert "mode" not in post_input


@pytest.mark.asyncio
async def test_get_post(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", json={"data": {"post": _POST_NODE}})

    result_dict = await get_post.ainvoke(_args(post_id="post_1"))
    assert isinstance(result_dict, dict)
    result = GetPostOutput.model_validate(result_dict)
    assert result.success is True
    assert result.post is not None
    assert result.post.due_at == "2026-08-02T15:00:00Z"


@pytest.mark.asyncio
async def test_get_posts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "posts": {
                    "edges": [{"node": _POST_NODE}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor_1"},
                }
            }
        },
    )

    result_dict = await get_posts.ainvoke(
        _args(
            organization_id="org_1",
            channel_ids=["chan_1", "chan_2"],
            status=["scheduled", "sent"],
            limit=5,
            sort_by="createdAt",
            sort_direction="desc",
        )
    )
    assert isinstance(result_dict, dict)
    result = GetPostsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.posts) == 1
    assert result.posts[0].id == "post_1"
    assert result.page_info is not None
    assert result.page_info.has_next_page is True
    assert result.page_info.end_cursor == "cursor_1"

    variables = _sent_variables(httpx_mock)
    assert variables["first"] == 5
    assert variables["input"]["filter"]["channelIds"] == ["chan_1", "chan_2"]
    assert variables["input"]["filter"]["status"] == ["scheduled", "sent"]
    assert variables["input"]["sort"] == [{"field": "createdAt", "direction": "desc"}]


@pytest.mark.asyncio
async def test_delete_post(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={"data": {"deletePost": {"__typename": "DeletePostSuccess", "id": "post_1"}}},
    )

    result_dict = await delete_post.ainvoke(_args(post_id="post_1"))
    assert isinstance(result_dict, dict)
    result = DeletePostOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True
    assert result.id == "post_1"


@pytest.mark.asyncio
async def test_get_channels(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "channels": [
                    {
                        "id": "chan_1",
                        "name": "modulex",
                        "displayName": "ModuleX",
                        "service": "linkedin",
                        "serviceId": "urn:li:org:1",
                        "avatar": "https://cdn.example.com/avatar.png",
                        "timezone": "Europe/London",
                        "type": "page",
                        "isQueuePaused": False,
                        "isDisconnected": False,
                        "organizationId": "org_1",
                    }
                ]
            }
        },
    )

    result_dict = await get_channels.ainvoke(_args(organization_id="org_1"))
    assert isinstance(result_dict, dict)
    result = GetChannelsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.channels) == 1
    assert result.channels[0].service == "linkedin"
    assert result.channels[0].is_queue_paused is False


@pytest.mark.asyncio
async def test_get_account(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "account": {
                    "id": "acct_1",
                    "email": "owner@example.com",
                    "name": "Owner",
                    "timezone": "Europe/London",
                    "organizations": [
                        {
                            "id": "org_1",
                            "name": "ModuleX",
                            "channelCount": 3,
                            "ownerEmail": "owner@example.com",
                        }
                    ],
                }
            }
        },
    )

    result_dict = await get_account.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetAccountOutput.model_validate(result_dict)
    assert result.success is True
    assert result.account is not None
    assert result.account.organizations[0].id == "org_1"
    assert result.account.organizations[0].channel_count == 3


@pytest.mark.asyncio
async def test_create_idea(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={"data": {"createIdea": {"__typename": "Idea", **_IDEA_NODE}}},
    )

    result_dict = await create_idea.ainvoke(
        _args(
            organization_id="org_1",
            text="Tease the launch",
            title="Launch teaser",
            group_id="group_1",
        )
    )
    assert isinstance(result_dict, dict)
    result = CreateIdeaOutput.model_validate(result_dict)
    assert result.success is True
    assert result.idea is not None
    assert result.idea.id == "idea_1"
    assert result.idea.title == "Launch teaser"

    idea_input = _sent_variables(httpx_mock)["input"]
    assert idea_input["content"] == {"text": "Tease the launch", "title": "Launch teaser"}
    assert idea_input["group"] == {"groupId": "group_1"}


@pytest.mark.asyncio
async def test_create_idea_wrapped_in_idea_response(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "createIdea": {"__typename": "IdeaResponse", "idea": _IDEA_NODE}
            }
        },
    )

    result_dict = await create_idea.ainvoke(
        _args(organization_id="org_1", text="Tease the launch")
    )
    result = CreateIdeaOutput.model_validate(result_dict)
    assert result.success is True
    assert result.idea is not None
    assert result.idea.text == "Tease the launch"


@pytest.mark.asyncio
async def test_get_ideas(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "ideas": {
                    "edges": [{"node": _IDEA_NODE}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
    )

    result_dict = await get_ideas.ainvoke(_args(organization_id="org_1", limit=10))
    assert isinstance(result_dict, dict)
    result = GetIdeasOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.ideas) == 1
    assert result.ideas[0].group_id == "group_1"
    assert result.page_info is not None
    assert result.page_info.has_next_page is False

    assert _sent_variables(httpx_mock)["first"] == 10


@pytest.mark.asyncio
async def test_get_idea_groups(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "ideaGroups": [
                    {"id": "group_1", "name": "Drafts", "isLocked": False},
                    {"id": "group_2", "name": "Approved", "isLocked": True},
                ]
            }
        },
    )

    result_dict = await get_idea_groups.ainvoke(_args(organization_id="org_1"))
    assert isinstance(result_dict, dict)
    result = GetIdeaGroupsOutput.model_validate(result_dict)
    assert result.success is True
    assert [group.name for group in result.idea_groups] == ["Drafts", "Approved"]
    assert result.idea_groups[1].is_locked is True


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_top_level_graphql_errors_surface(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": None,
            "errors": [
                {"message": "Not authorized", "extensions": {"code": "UNAUTHORIZED"}}
            ],
        },
    )

    result_dict = await get_account.ainvoke(_args())
    result = GetAccountOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Not authorized" in result.error
    assert "UNAUTHORIZED" in result.error
    assert result.account is None


@pytest.mark.asyncio
async def test_typed_mutation_error_surfaces(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "createPost": {
                    "__typename": "LimitReachedError",
                    "message": "Daily posting limit reached",
                }
            }
        },
    )

    result_dict = await create_post.ainvoke(_args(channel_id="chan_1", text="Hello"))
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Daily posting limit reached" in result.error
    assert result.post is None


@pytest.mark.asyncio
async def test_delete_post_error_payload(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "deletePost": {"__typename": "VoidMutationError", "message": "Already sent"}
            }
        },
    )

    result_dict = await delete_post.ainvoke(_args(post_id="post_1"))
    result = DeletePostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.deleted is False
    assert result.error is not None
    assert "Already sent" in result.error


@pytest.mark.asyncio
async def test_get_post_missing_node(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", json={"data": {"post": None}})

    result_dict = await get_post.ainvoke(_args(post_id="missing"))
    result = GetPostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "missing" in result.error


@pytest.mark.asyncio
async def test_non_200_response(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", status_code=503, text="upstream unavailable")

    result_dict = await get_channels.ainvoke(_args(organization_id="org_1"))
    result = GetChannelsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "503" in result.error
    assert result.channels == []


@pytest.mark.asyncio
async def test_non_object_body_does_not_raise(httpx_mock):  # type: ignore[no-untyped-def]
    """A 200 carrying a bare JSON array must degrade to the error envelope."""
    httpx_mock.add_response(method="POST", json=["unexpected"])

    result_dict = await get_ideas.ainvoke(_args(organization_id="org_1"))
    assert isinstance(result_dict, dict)
    result = GetIdeasOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert result.ideas == []


# --- Local validation (no HTTP call is made) --------------------------------


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await get_account.ainvoke({"api_key": "   "})
    result = GetAccountOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_create_post_requires_text_or_media(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await create_post.ainvoke(_args(channel_id="chan_1"))
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "text" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_create_post_custom_scheduled_requires_due_at(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await create_post.ainvoke(
        _args(channel_id="chan_1", text="Hello", mode="customScheduled")
    )
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "due_at" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_create_post_rejects_unknown_mode(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await create_post.ainvoke(
        _args(channel_id="chan_1", text="Hello", mode="whenever")
    )
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "mode must be one of" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_create_post_rejects_non_http_media_url(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await create_post.ainvoke(
        _args(channel_id="chan_1", text="Hello", media_url="file:///etc/passwd")
    )
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "media_url" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_get_posts_rejects_unknown_status(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await get_posts.ainvoke(
        _args(organization_id="org_1", status=["published"])
    )
    result = GetPostsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "published" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_wrong_typed_scalar_degrades_instead_of_raising(httpx_mock):  # type: ignore[no-untyped-def]
    """A 200 whose field has the wrong TYPE must not escape the @tool boundary.

    Model construction happens after the `except` clauses, so an upstream
    scalar arriving as a number would raise `ValidationError` past the tool
    boundary rather than returning the `success=False` envelope. The `_as_*`
    coercers close that path.
    """
    httpx_mock.add_response(
        method="POST",
        json={"data": {"post": {"id": 12345, "text": "hi", "isCustomScheduled": "yes"}}},
    )

    result_dict = await get_post.ainvoke(_args(post_id="post_1"))
    assert isinstance(result_dict, dict)
    result = GetPostOutput.model_validate(result_dict)
    assert result.success is True
    assert result.post is not None
    assert result.post.id == "12345"
    # A non-bool in a bool field degrades to None rather than raising.
    assert result.post.is_custom_scheduled is None


@pytest.mark.asyncio
async def test_wrong_typed_nested_scalar_degrades(httpx_mock):  # type: ignore[no-untyped-def]
    """The same guarantee holds for nested objects and list members."""
    httpx_mock.add_response(
        method="POST",
        json={
            "data": {
                "account": {
                    "id": 999,
                    "email": "a@b.co",
                    "organizations": [{"id": 7, "name": 42, "channelCount": "many"}],
                }
            }
        },
    )

    result_dict = await get_account.ainvoke(_args())
    result = GetAccountOutput.model_validate(result_dict)
    assert result.success is True
    assert result.account is not None
    assert result.account.id == "999"
    assert result.account.organizations[0].id == "7"
    assert result.account.organizations[0].name == "42"
    # A non-int in an int field degrades to None.
    assert result.account.organizations[0].channel_count is None
