"""Happy-path tests for every Reddit @tool, plus the manifest trio and the
failure paths that matter for an API that wraps everything in Thing/Listing
envelopes and reports write failures inside an HTTP 200."""
from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs

import pytest

from modulex_integrations.tools.reddit import (
    TOOLS,
    delete,
    edit,
    get_comments,
    get_controversial,
    get_info,
    get_me,
    get_messages,
    get_posts,
    get_saved,
    get_subreddit_info,
    get_subreddit_rules,
    get_user,
    get_user_comments,
    get_user_posts,
    hide,
    hot_posts,
    list_my_subreddits,
    lock,
    manifest,
    mark_all_read,
    mark_read,
    marknsfw,
    mod_approve,
    mod_distinguish,
    mod_remove,
    mod_sticky,
    reply,
    report,
    save,
    search,
    search_subreddits,
    send_message,
    submit_post,
    subscribe,
    unhide,
    unlock,
    unmarknsfw,
    unsave,
    vote,
)
from modulex_integrations.tools.reddit.outputs import (
    DeleteOutput,
    EditOutput,
    GetCommentsOutput,
    GetControversialOutput,
    GetInfoOutput,
    GetMeOutput,
    GetMessagesOutput,
    GetPostsOutput,
    GetSavedOutput,
    GetSubredditInfoOutput,
    GetSubredditRulesOutput,
    GetUserCommentsOutput,
    GetUserOutput,
    GetUserPostsOutput,
    HideOutput,
    HotPostsOutput,
    ListMySubredditsOutput,
    LockOutput,
    MarkAllReadOutput,
    MarkNsfwOutput,
    MarkReadOutput,
    ModApproveOutput,
    ModDistinguishOutput,
    ModRemoveOutput,
    ModStickyOutput,
    ReplyOutput,
    ReportOutput,
    SaveOutput,
    SearchOutput,
    SearchSubredditsOutput,
    SendMessageOutput,
    SubmitPostOutput,
    SubscribeOutput,
    UnhideOutput,
    UnlockOutput,
    UnmarkNsfwOutput,
    UnsaveOutput,
    VoteOutput,
)

API = "https://oauth.reddit.com"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
ACCESS_TOKEN = "minted-access-token"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "client_id": "p-fakeClientId",
        "client_secret": "fake_client_secret",
        "bot_username": "modulex_bot",
        "bot_password": "hunter2",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


def _mock_token(httpx_mock: Any) -> None:
    """Register the password-grant token mint every action performs first."""
    httpx_mock.add_response(
        method="POST",
        url=TOKEN_URL,
        json={
            "access_token": ACCESS_TOKEN,
            "token_type": "bearer",
            "expires_in": 86400,
            "scope": "*",
        },
    )


def _form(request: Any) -> dict[str, list[str]]:
    return parse_qs(request.content.decode())


def _query(request: Any) -> dict[str, list[str]]:
    return parse_qs(request.url.query.decode())


def _action_request(httpx_mock: Any) -> Any:
    """The API call itself — index 0 is always the token mint."""
    return httpx_mock.get_requests()[1]


def _listing(
    children: list[dict[str, Any]],
    after: Any = None,
    before: Any = None,
) -> dict[str, Any]:
    return {
        "kind": "Listing",
        "data": {"children": children, "after": after, "before": before},
    }


_POST_DATA: dict[str, Any] = {
    "id": "abc123",
    "name": "t3_abc123",
    "title": "A post about Python",
    "author": "modulex_bot",
    "url": "https://example.com/article",
    "permalink": "/r/python/comments/abc123/a_post_about_python/",
    "created_utc": 1754308800.0,
    "score": 421,
    "upvote_ratio": 0.97,
    "num_comments": 33,
    "is_self": False,
    "selftext": "",
    "thumbnail": "https://b.thumbs.redditmedia.com/x.jpg",
    "subreddit": "python",
    "subreddit_id": "t5_2qh0y",
    "domain": "example.com",
    "over_18": False,
    "spoiler": False,
    "locked": False,
    "stickied": False,
    "edited": False,
    "distinguished": None,
    "ups": 421,
    "downs": 0,
    "link_flair_text": "Discussion",
}

_COMMENT_DATA: dict[str, Any] = {
    "id": "def456",
    "name": "t1_def456",
    "author": "someone",
    "body": "Nice write-up.",
    "body_html": "<p>Nice write-up.</p>",
    "created_utc": 1754309000.0,
    "score": 12,
    "permalink": "/r/python/comments/abc123/_/def456/",
    "parent_id": "t3_abc123",
    "link_id": "t3_abc123",
    "subreddit": "python",
    "is_submitter": False,
    "edited": False,
    "replies": "",
}

_SUBREDDIT_DATA: dict[str, Any] = {
    "id": "2qh0y",
    "name": "t5_2qh0y",
    "display_name": "python",
    "display_name_prefixed": "r/python",
    "title": "Python",
    "description": "News about Python.",
    "public_description": "News about the Python programming language.",
    "subscribers": 1300000,
    "active_user_count": 2100,
    "created_utc": 1201233135.0,
    "over18": False,
    "lang": "en",
    "subreddit_type": "public",
    "url": "/r/python/",
    "icon_img": "https://b.thumbs.redditmedia.com/icon.png",
    "banner_img": "",
}

_USER_DATA: dict[str, Any] = {
    "id": "1w72",
    "name": "spez",
    "created_utc": 1118030400.0,
    "link_karma": 150000,
    "comment_karma": 800000,
    "total_karma": 950000,
    "is_gold": True,
    "is_mod": True,
    "is_employee": True,
    "has_verified_email": True,
    "verified": True,
    "over_18": True,
    "icon_img": "https://styles.redditmedia.com/avatar.png",
}

_MESSAGE_DATA: dict[str, Any] = {
    "id": "msg1",
    "name": "t4_msg1",
    "author": "someone",
    "dest": "modulex_bot",
    "subject": "Hello",
    "body": "Hi there",
    "created_utc": 1754309100.0,
    "new": True,
    "was_comment": False,
    "context": "",
    "distinguished": None,
}

_OK_JSON: dict[str, Any] = {"json": {"errors": [], "data": {}}}


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_38_actions(self) -> None:
        assert len(manifest.actions) == 38

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Token mint -------------------------------------------------------------


@pytest.mark.asyncio
async def test_token_mint_uses_basic_auth_and_password_grant(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=_listing([]))

    await get_posts.ainvoke(_args(subreddit="python"))

    mint = httpx_mock.get_requests()[0]
    assert str(mint.url) == TOKEN_URL
    form = _form(mint)
    assert form["grant_type"] == ["password"]
    assert form["username"] == ["modulex_bot"]
    assert form["password"] == ["hunter2"]
    # HTTP Basic client_id:client_secret, per Reddit's script-app flow.
    assert mint.headers["Authorization"].startswith("Basic ")
    assert mint.headers["User-Agent"] == "python:modulex.reddit:v1.0.0 (by /u/modulex_bot)"

    call = _action_request(httpx_mock)
    assert call.headers["Authorization"] == f"bearer {ACCESS_TOKEN}"
    assert call.headers["User-Agent"] == "python:modulex.reddit:v1.0.0 (by /u/modulex_bot)"


@pytest.mark.asyncio
async def test_user_agent_override_from_credential(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=_listing([]))

    auth_data = dict(_AUTH["auth_data"], user_agent="python:acme-bot:v2 (by /u/acme)")
    await get_posts.ainvoke({"auth_type": "custom", "auth_data": auth_data, "subreddit": "python"})

    assert _action_request(httpx_mock).headers["User-Agent"] == "python:acme-bot:v2 (by /u/acme)"


@pytest.mark.asyncio
async def test_rejected_credentials_short_circuit(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=TOKEN_URL, status_code=401, json={"message": "Unauthorized"}
    )

    result = GetPostsOutput.model_validate(await get_posts.ainvoke(_args(subreddit="python")))
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_token_error_inside_http_200(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=TOKEN_URL, json={"error": "invalid_grant"})

    result = GetMeOutput.model_validate(await get_me.ainvoke(_args()))
    assert result.success is False
    assert result.error is not None
    assert "invalid_grant" in result.error


# --- Subreddit reads --------------------------------------------------------


@pytest.mark.asyncio
async def test_get_posts(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        json=_listing([{"kind": "t3", "data": _POST_DATA}], after="t3_zzz"),
    )

    result_dict = await get_posts.ainvoke(
        _args(subreddit="r/python", sort="top", time="week", limit=5)
    )
    assert isinstance(result_dict, dict)
    result = GetPostsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.subreddit == "python"
    assert result.after == "t3_zzz"
    assert len(result.posts) == 1
    assert result.posts[0].id == "abc123"
    assert result.posts[0].permalink == (
        "https://www.reddit.com/r/python/comments/abc123/a_post_about_python/"
    )
    # `edited: false` is not a timestamp and must not become one.
    assert result.posts[0].edited is None

    call = _action_request(httpx_mock)
    assert call.url.path == "/r/python/top"
    query = _query(call)
    assert query["limit"] == ["5"]
    assert query["t"] == ["week"]
    assert query["raw_json"] == ["1"]


@pytest.mark.asyncio
async def test_get_posts_rejects_unknown_sort(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = GetPostsOutput.model_validate(
        await get_posts.ainvoke(_args(subreddit="python", sort="spicy"))
    )
    assert result.success is False
    assert result.error is not None
    assert "Invalid sort" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_get_posts_rejects_path_escaping_subreddit(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = GetPostsOutput.model_validate(
        await get_posts.ainvoke(_args(subreddit="../../api/v1/me"))
    )
    assert result.success is False
    assert result.error is not None
    assert "Invalid subreddit" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_hot_posts(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=_listing([{"kind": "t3", "data": _POST_DATA}]))

    result = HotPostsOutput.model_validate(
        await hot_posts.ainvoke(_args(subreddit="python", limit=200))
    )
    assert result.success is True
    assert result.posts[0].title == "A post about Python"

    call = _action_request(httpx_mock)
    assert call.url.path == "/r/python/hot"
    # Reddit caps listings at 100; an over-large limit is clamped, not rejected.
    assert _query(call)["limit"] == ["100"]


@pytest.mark.asyncio
async def test_get_controversial(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=_listing([{"kind": "t3", "data": _POST_DATA}]))

    result = GetControversialOutput.model_validate(
        await get_controversial.ainvoke(_args(subreddit="python", time="all"))
    )
    assert result.success is True
    assert result.posts[0].score == 421

    call = _action_request(httpx_mock)
    assert call.url.path == "/r/python/controversial"
    assert _query(call)["t"] == ["all"]


@pytest.mark.asyncio
async def test_get_comments_nests_replies(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    nested = dict(
        _COMMENT_DATA,
        id="ghi789",
        name="t1_ghi789",
        body="Thanks!",
        replies="",
    )
    parent = dict(
        _COMMENT_DATA,
        replies=_listing([{"kind": "t1", "data": nested}]),
    )
    httpx_mock.add_response(
        method="GET",
        json=[
            _listing([{"kind": "t3", "data": _POST_DATA}]),
            _listing([{"kind": "t1", "data": parent}, {"kind": "more", "data": {"id": "x"}}]),
        ],
    )

    result = GetCommentsOutput.model_validate(
        await get_comments.ainvoke(_args(subreddit="python", post_id="t3_abc123", sort="top"))
    )
    assert result.success is True
    assert result.post is not None
    assert result.post.name == "t3_abc123"
    # The "more" placeholder is not a comment and is dropped.
    assert len(result.comments) == 1
    assert result.comments[0].id == "def456"
    assert result.comments[0].replies[0].id == "ghi789"

    call = _action_request(httpx_mock)
    assert call.url.path == "/r/python/comments/abc123"
    assert _query(call)["sort"] == ["top"]


@pytest.mark.asyncio
async def test_get_comments_rejects_bad_post_id(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = GetCommentsOutput.model_validate(
        await get_comments.ainvoke(_args(subreddit="python", post_id="abc/../123"))
    )
    assert result.success is False
    assert result.error is not None
    assert "Invalid post ID" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_search(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=_listing([{"kind": "t3", "data": _POST_DATA}]))

    result = SearchOutput.model_validate(
        await search.ainvoke(
            _args(subreddit="python", query="title:asyncio", sort="new", restrict_sr=False)
        )
    )
    assert result.success is True
    assert result.posts[0].subreddit == "python"

    call = _action_request(httpx_mock)
    assert call.url.path == "/r/python/search"
    query = _query(call)
    assert query["q"] == ["title:asyncio"]
    assert query["sort"] == ["new"]
    assert query["restrict_sr"] == ["false"]


@pytest.mark.asyncio
async def test_get_subreddit_info(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json={"kind": "t5", "data": _SUBREDDIT_DATA})

    result = GetSubredditInfoOutput.model_validate(
        await get_subreddit_info.ainvoke(_args(subreddit="python"))
    )
    assert result.success is True
    assert result.subreddit is not None
    assert result.subreddit.display_name == "python"
    assert result.subreddit.subscribers == 1300000
    # `active_user_count` is the modern spelling of `accounts_active`.
    assert result.subreddit.accounts_active == 2100
    assert _action_request(httpx_mock).url.path == "/r/python/about"


@pytest.mark.asyncio
async def test_get_subreddit_rules(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        json={
            "rules": [
                {
                    "short_name": "Be nice",
                    "description": "No personal attacks.",
                    "description_html": "<p>No personal attacks.</p>",
                    "violation_reason": "Rudeness",
                    "kind": "all",
                    "created_utc": 1520000000.0,
                    "priority": 0,
                }
            ],
            "site_rules": ["Spam", "Personal and confidential information"],
            "site_rules_flow": [{"nextStepHeader": "..."}],
        },
    )

    result = GetSubredditRulesOutput.model_validate(
        await get_subreddit_rules.ainvoke(_args(subreddit="python"))
    )
    assert result.success is True
    assert result.rules[0].short_name == "Be nice"
    assert result.site_rules == ["Spam", "Personal and confidential information"]
    assert _action_request(httpx_mock).url.path == "/r/python/about/rules"


# --- Account + user reads ---------------------------------------------------


@pytest.mark.asyncio
async def test_get_me(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    # /api/v1/me answers with the bare account object, not a Thing envelope.
    httpx_mock.add_response(method="GET", json=_USER_DATA)

    result = GetMeOutput.model_validate(await get_me.ainvoke(_args()))
    assert result.success is True
    assert result.user is not None
    assert result.user.name == "spez"
    assert result.user.total_karma == 950000
    assert _action_request(httpx_mock).url.path == "/api/v1/me"


@pytest.mark.asyncio
async def test_get_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json={"kind": "t2", "data": _USER_DATA})

    result = GetUserOutput.model_validate(await get_user.ainvoke(_args(username="u/spez")))
    assert result.success is True
    assert result.user is not None
    assert result.user.id == "1w72"
    assert _action_request(httpx_mock).url.path == "/user/spez/about"


@pytest.mark.asyncio
async def test_get_user_rejects_bad_username(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = GetUserOutput.model_validate(await get_user.ainvoke(_args(username="a b/../c")))
    assert result.success is False
    assert result.error is not None
    assert "Invalid Reddit username" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_get_user_posts(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET", json=_listing([{"kind": "t3", "data": _POST_DATA}], after="t3_next")
    )

    result = GetUserPostsOutput.model_validate(
        await get_user_posts.ainvoke(_args(username="spez", sort="top", time="year"))
    )
    assert result.success is True
    assert result.posts[0].name == "t3_abc123"
    assert result.after == "t3_next"

    call = _action_request(httpx_mock)
    assert call.url.path == "/user/spez/submitted"
    assert _query(call)["t"] == ["year"]


@pytest.mark.asyncio
async def test_get_user_comments(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=_listing([{"kind": "t1", "data": _COMMENT_DATA}]))

    result = GetUserCommentsOutput.model_validate(
        await get_user_comments.ainvoke(_args(username="spez"))
    )
    assert result.success is True
    assert result.comments[0].body == "Nice write-up."
    assert result.comments[0].replies == []
    assert _action_request(httpx_mock).url.path == "/user/spez/comments"


@pytest.mark.asyncio
async def test_get_saved_splits_by_kind(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        json=_listing(
            [
                {"kind": "t3", "data": _POST_DATA},
                {"kind": "t1", "data": _COMMENT_DATA},
            ]
        ),
    )

    result = GetSavedOutput.model_validate(await get_saved.ainvoke(_args(username="modulex_bot")))
    assert result.success is True
    assert len(result.posts) == 1
    assert len(result.comments) == 1
    assert _action_request(httpx_mock).url.path == "/user/modulex_bot/saved"


@pytest.mark.asyncio
async def test_get_info(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        json=_listing(
            [
                {"kind": "t3", "data": _POST_DATA},
                {"kind": "t1", "data": _COMMENT_DATA},
                {"kind": "t5", "data": _SUBREDDIT_DATA},
            ]
        ),
    )

    result = GetInfoOutput.model_validate(
        await get_info.ainvoke(_args(thing_ids="t3_abc123,t1_def456,t5_2qh0y"))
    )
    assert result.success is True
    assert result.posts[0].id == "abc123"
    assert result.comments[0].id == "def456"
    assert result.subreddits[0].display_name == "python"

    call = _action_request(httpx_mock)
    assert call.url.path == "/api/info"
    assert _query(call)["id"] == ["t3_abc123,t1_def456,t5_2qh0y"]


@pytest.mark.asyncio
async def test_get_info_requires_ids(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = GetInfoOutput.model_validate(await get_info.ainvoke(_args(thing_ids="  ")))
    assert result.success is False
    assert httpx_mock.get_requests() == []


# --- Subreddit discovery ----------------------------------------------------


@pytest.mark.asyncio
async def test_search_subreddits(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=_listing([{"kind": "t5", "data": _SUBREDDIT_DATA}]))

    result = SearchSubredditsOutput.model_validate(
        await search_subreddits.ainvoke(_args(query="python", sort="activity"))
    )
    assert result.success is True
    assert result.subreddits[0].url == "/r/python/"

    call = _action_request(httpx_mock)
    assert call.url.path == "/subreddits/search"
    assert _query(call)["sort"] == ["activity"]


@pytest.mark.asyncio
async def test_list_my_subreddits(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        json=_listing([{"kind": "t5", "data": _SUBREDDIT_DATA}], after="t5_next"),
    )

    result = ListMySubredditsOutput.model_validate(await list_my_subreddits.ainvoke(_args()))
    assert result.success is True
    assert result.subreddits[0].display_name == "python"
    assert result.after == "t5_next"
    assert _action_request(httpx_mock).url.path == "/subreddits/mine/subscriber"


# --- Messages ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_messages(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=_listing([{"kind": "t4", "data": _MESSAGE_DATA}]))

    result = GetMessagesOutput.model_validate(
        await get_messages.ainvoke(_args(where="unread", mark=True))
    )
    assert result.success is True
    assert result.messages[0].subject == "Hello"
    assert result.messages[0].new is True

    call = _action_request(httpx_mock)
    assert call.url.path == "/message/unread"
    assert _query(call)["mark"] == ["true"]


@pytest.mark.asyncio
async def test_get_messages_rejects_unknown_folder(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = GetMessagesOutput.model_validate(await get_messages.ainvoke(_args(where="archive")))
    assert result.success is False
    assert result.error is not None
    assert "Invalid message folder" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_send_message(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/compose?raw_json=1", json=_OK_JSON)

    result = SendMessageOutput.model_validate(
        await send_message.ainvoke(
            _args(to="spez", subject="Hi", text="Hello there", from_sr="r/python")
        )
    )
    assert result.success is True
    assert result.message is not None

    form = _form(_action_request(httpx_mock))
    assert form["to"] == ["spez"]
    assert form["subject"] == ["Hi"]
    assert form["from_sr"] == ["python"]
    assert form["api_type"] == ["json"]


@pytest.mark.asyncio
async def test_send_message_surfaces_api_type_errors(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        json={"json": {"errors": [["USER_DOESNT_EXIST", "that user doesn't exist", "to"]]}},
    )

    result = SendMessageOutput.model_validate(
        await send_message.ainvoke(_args(to="nobody", subject="Hi", text="Hello"))
    )
    assert result.success is False
    assert result.error is not None
    assert "USER_DOESNT_EXIST" in result.error


@pytest.mark.asyncio
async def test_mark_read(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/read_message?raw_json=1", json={})

    result = MarkReadOutput.model_validate(
        await mark_read.ainvoke(_args(thing_ids="t4_msg1,t4_msg2"))
    )
    assert result.success is True
    assert _form(_action_request(httpx_mock))["id"] == ["t4_msg1,t4_msg2"]


@pytest.mark.asyncio
async def test_mark_all_read_accepts_empty_202_body(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    # Reddit queues this one: HTTP 202 with no body at all.
    httpx_mock.add_response(
        method="POST", url=f"{API}/api/read_all_messages?raw_json=1", status_code=202, content=b""
    )

    result = MarkAllReadOutput.model_validate(await mark_all_read.ainvoke(_args()))
    assert result.success is True
    assert result.error is None


# --- Content writes ---------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_post_self(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/submit?raw_json=1",
        json={
            "json": {
                "errors": [],
                "data": {
                    "id": "xyz789",
                    "name": "t3_xyz789",
                    "url": "https://www.reddit.com/r/python/comments/xyz789/hello/",
                    "drafts_count": 0,
                },
            }
        },
    )

    result = SubmitPostOutput.model_validate(
        await submit_post.ainvoke(
            _args(subreddit="python", title="Hello", text="**body**", nsfw=False, flair_text="Q")
        )
    )
    assert result.success is True
    assert result.post is not None
    assert result.post.name == "t3_xyz789"
    assert result.post.permalink == "https://www.reddit.com/r/python/comments/xyz789/hello/"

    form = _form(_action_request(httpx_mock))
    assert form["sr"] == ["python"]
    assert form["kind"] == ["self"]
    assert form["text"] == ["**body**"]
    assert form["nsfw"] == ["false"]
    assert form["flair_text"] == ["Q"]


@pytest.mark.asyncio
async def test_submit_post_link(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", json=_OK_JSON)

    result = SubmitPostOutput.model_validate(
        await submit_post.ainvoke(
            _args(subreddit="python", title="Article", url="https://example.com/a")
        )
    )
    assert result.success is True

    form = _form(_action_request(httpx_mock))
    assert form["kind"] == ["link"]
    assert form["url"] == ["https://example.com/a"]


@pytest.mark.asyncio
async def test_submit_post_surfaces_ratelimit_inside_http_200(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        json={"json": {"errors": [["RATELIMIT", "you are doing that too much", "ratelimit"]]}},
    )

    result = SubmitPostOutput.model_validate(
        await submit_post.ainvoke(_args(subreddit="python", title="Hello", text="hi"))
    )
    assert result.success is False
    assert result.error is not None
    assert "RATELIMIT" in result.error
    assert result.post is None


@pytest.mark.asyncio
async def test_reply(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/comment?raw_json=1",
        json={
            "json": {
                "errors": [],
                "data": {
                    "things": [
                        {
                            "kind": "t1",
                            "data": {
                                "id": "newc1",
                                "name": "t1_newc1",
                                "permalink": "/r/python/comments/abc123/_/newc1/",
                                "body": "Thanks!",
                            },
                        }
                    ]
                },
            }
        },
    )

    result = ReplyOutput.model_validate(
        await reply.ainvoke(_args(parent_id="t3_abc123", text="Thanks!"))
    )
    assert result.success is True
    assert result.comment is not None
    assert result.comment.name == "t1_newc1"
    assert result.comment.permalink == "https://www.reddit.com/r/python/comments/abc123/_/newc1/"

    form = _form(_action_request(httpx_mock))
    assert form["thing_id"] == ["t3_abc123"]
    assert form["text"] == ["Thanks!"]


@pytest.mark.asyncio
async def test_edit(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/editusertext?raw_json=1",
        json={
            "json": {
                "errors": [],
                "data": {
                    "things": [
                        {"kind": "t1", "data": {"id": "def456", "name": "t1_def456", "body": "v2"}}
                    ]
                },
            }
        },
    )

    result = EditOutput.model_validate(
        await edit.ainvoke(_args(thing_id="t1_def456", text="v2"))
    )
    assert result.success is True
    assert result.thing is not None
    assert result.thing.body == "v2"


@pytest.mark.asyncio
async def test_delete(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/del?raw_json=1", json={})

    result = DeleteOutput.model_validate(await delete.ainvoke(_args(thing_id="t3_abc123")))
    assert result.success is True
    assert _form(_action_request(httpx_mock))["id"] == ["t3_abc123"]


@pytest.mark.asyncio
async def test_vote(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/vote?raw_json=1", json={})

    result = VoteOutput.model_validate(
        await vote.ainvoke(_args(thing_id="t3_abc123", direction=-1))
    )
    assert result.success is True
    assert result.message is not None
    assert "Downvoted" in result.message
    assert _form(_action_request(httpx_mock))["dir"] == ["-1"]


@pytest.mark.asyncio
async def test_vote_rejects_bad_direction(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = VoteOutput.model_validate(
        await vote.ainvoke(_args(thing_id="t3_abc123", direction=7))
    )
    assert result.success is False
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_save(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/save?raw_json=1", json={})

    result = SaveOutput.model_validate(
        await save.ainvoke(_args(thing_id="t3_abc123", category="research"))
    )
    assert result.success is True
    assert _form(_action_request(httpx_mock))["category"] == ["research"]


@pytest.mark.asyncio
async def test_unsave(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/unsave?raw_json=1", json={})

    result = UnsaveOutput.model_validate(await unsave.ainvoke(_args(thing_id="t3_abc123")))
    assert result.success is True


@pytest.mark.asyncio
async def test_subscribe(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/subscribe?raw_json=1", json={})

    result = SubscribeOutput.model_validate(
        await subscribe.ainvoke(_args(subreddit="python", action="unsub"))
    )
    assert result.success is True
    assert result.message is not None
    assert "Unsubscribed" in result.message

    form = _form(_action_request(httpx_mock))
    assert form["action"] == ["unsub"]
    assert form["sr_name"] == ["python"]


@pytest.mark.asyncio
async def test_report(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/report?raw_json=1", json=_OK_JSON)

    result = ReportOutput.model_validate(
        await report.ainvoke(_args(thing_id="t3_abc123", reason="Spam"))
    )
    assert result.success is True
    assert _form(_action_request(httpx_mock))["reason"] == ["Spam"]


@pytest.mark.asyncio
async def test_hide(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/hide?raw_json=1", json={})

    result = HideOutput.model_validate(
        await hide.ainvoke(_args(thing_ids="t3_abc123,t3_def456"))
    )
    assert result.success is True
    assert _form(_action_request(httpx_mock))["id"] == ["t3_abc123,t3_def456"]


@pytest.mark.asyncio
async def test_unhide(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/unhide?raw_json=1", json={})

    result = UnhideOutput.model_validate(await unhide.ainvoke(_args(thing_ids="t3_abc123")))
    assert result.success is True


@pytest.mark.asyncio
async def test_marknsfw(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/marknsfw?raw_json=1", json={})

    result = MarkNsfwOutput.model_validate(await marknsfw.ainvoke(_args(thing_id="t3_abc123")))
    assert result.success is True


@pytest.mark.asyncio
async def test_unmarknsfw(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/unmarknsfw?raw_json=1", json={})

    result = UnmarkNsfwOutput.model_validate(await unmarknsfw.ainvoke(_args(thing_id="t3_abc123")))
    assert result.success is True


# --- Moderator actions ------------------------------------------------------


@pytest.mark.asyncio
async def test_mod_approve(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/approve?raw_json=1", json={})

    result = ModApproveOutput.model_validate(await mod_approve.ainvoke(_args(thing_id="t3_abc123")))
    assert result.success is True


@pytest.mark.asyncio
async def test_mod_remove_as_spam(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/remove?raw_json=1", json={})

    result = ModRemoveOutput.model_validate(
        await mod_remove.ainvoke(_args(thing_id="t3_abc123", spam=True))
    )
    assert result.success is True
    assert result.message is not None
    assert "as spam" in result.message
    assert _form(_action_request(httpx_mock))["spam"] == ["true"]


@pytest.mark.asyncio
async def test_mod_remove_without_moderator_rights_returns_403(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", status_code=403, text="Forbidden")

    result = ModRemoveOutput.model_validate(await mod_remove.ainvoke(_args(thing_id="t3_abc123")))
    assert result.success is False
    assert result.error is not None
    assert "403" in result.error


@pytest.mark.asyncio
async def test_mod_distinguish(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/distinguish?raw_json=1", json=_OK_JSON)

    result = ModDistinguishOutput.model_validate(
        await mod_distinguish.ainvoke(_args(thing_id="t1_def456", how="yes", sticky=True))
    )
    assert result.success is True

    form = _form(_action_request(httpx_mock))
    assert form["how"] == ["yes"]
    assert form["sticky"] == ["true"]


@pytest.mark.asyncio
async def test_lock(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/lock?raw_json=1", json={})

    result = LockOutput.model_validate(await lock.ainvoke(_args(thing_id="t3_abc123")))
    assert result.success is True


@pytest.mark.asyncio
async def test_unlock(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{API}/api/unlock?raw_json=1", json={})

    result = UnlockOutput.model_validate(await unlock.ainvoke(_args(thing_id="t3_abc123")))
    assert result.success is True


@pytest.mark.asyncio
async def test_mod_sticky(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{API}/api/set_subreddit_sticky?raw_json=1", json=_OK_JSON
    )

    result = ModStickyOutput.model_validate(
        await mod_sticky.ainvoke(_args(thing_id="t3_abc123", state=True, num=2))
    )
    assert result.success is True

    form = _form(_action_request(httpx_mock))
    assert form["state"] == ["true"]
    assert form["num"] == ["2"]


@pytest.mark.asyncio
async def test_mod_sticky_rejects_out_of_range_slot(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = ModStickyOutput.model_validate(
        await mod_sticky.ainvoke(_args(thing_id="t3_abc123", num=9))
    )
    assert result.success is False
    assert httpx_mock.get_requests() == []


# --- Envelope invariants ----------------------------------------------------


@pytest.mark.asyncio
async def test_empty_credentials_short_circuit(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result = GetMeOutput.model_validate(
        await get_me.ainvoke(
            {"auth_type": "custom", "auth_data": {"client_id": "  ", "client_secret": ""}}
        )
    )
    assert result.success is False
    assert result.error is not None
    assert "client ID" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_rate_limited_response(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", status_code=429, text="Too Many Requests")

    result = GetPostsOutput.model_validate(await get_posts.ainvoke(_args(subreddit="python")))
    assert result.success is False
    assert result.error is not None
    assert "rate limit" in result.error
    assert result.posts == []


@pytest.mark.asyncio
async def test_non_object_body_does_not_raise(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """A 200 carrying a bare JSON array must degrade, not raise."""
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json=["unexpected"])

    result = GetPostsOutput.model_validate(await get_posts.ainvoke(_args(subreddit="python")))
    assert result.success is True
    assert result.posts == []
    assert result.after is None


@pytest.mark.asyncio
async def test_wrong_typed_scalar_degrades_instead_of_raising(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """A 200 whose fields have the wrong TYPE must not escape the @tool boundary.

    Model construction happens after the `except` clauses, so an upstream
    scalar arriving as the wrong type would raise `ValidationError` past the
    tool boundary rather than returning an envelope. The `_as_*` coercers
    close that path.
    """
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        json=_listing(
            [
                {
                    "kind": "t3",
                    "data": {
                        "id": 12345,
                        "title": {"nested": "object"},
                        "score": "many",
                        "is_self": "yes",
                        "created_utc": "not-a-number",
                        "edited": False,
                    },
                }
            ],
            after=17,
        ),
    )

    result = GetPostsOutput.model_validate(await get_posts.ainvoke(_args(subreddit="python")))
    assert result.success is True
    post = result.posts[0]
    assert post.id == "12345"
    # A dict in a string field degrades to None rather than str(dict).
    assert post.title is None
    assert post.score is None
    assert post.is_self is None
    assert post.created_utc is None
    assert post.edited is None
    assert result.after == "17"


@pytest.mark.asyncio
async def test_wrong_typed_nested_scalar_degrades(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """The same guarantee holds for the nested reply tree."""
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        json=[
            _listing([{"kind": "t3", "data": {"id": "abc123"}}]),
            _listing(
                [
                    {
                        "kind": "t1",
                        "data": {
                            "id": 999,
                            "score": "lots",
                            "replies": _listing(
                                [{"kind": "t1", "data": {"id": 1000, "gilded": "two"}}]
                            ),
                        },
                    }
                ]
            ),
        ],
    )

    result = GetCommentsOutput.model_validate(
        await get_comments.ainvoke(_args(subreddit="python", post_id="abc123"))
    )
    assert result.success is True
    assert result.comments[0].id == "999"
    assert result.comments[0].score is None
    assert result.comments[0].replies[0].id == "1000"
    assert result.comments[0].replies[0].gilded is None


@pytest.mark.asyncio
async def test_malformed_thing_envelope_does_not_raise(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """A Thing whose `data` is a list, not an object."""
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", json={"kind": "t5", "data": ["oops"]})

    result = GetSubredditInfoOutput.model_validate(
        await get_subreddit_info.ainvoke(_args(subreddit="python"))
    )
    assert result.success is True
    assert result.subreddit is not None
    assert result.subreddit.display_name is None
