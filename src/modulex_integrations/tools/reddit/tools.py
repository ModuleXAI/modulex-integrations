"""Reddit LangChain ``@tool`` functions.

Pure HTTP integration against the Reddit Data API. Credentials arrive as
``auth_type, auth_data`` (first args); ``auth_data`` carries a registered
**script app** credential set — ``client_id`` / ``client_secret`` plus the
``bot_username`` / ``bot_password`` of the account the app runs as.

Every invocation first exchanges that credential set for a short-lived
bearer token (``POST https://www.reddit.com/api/v1/access_token`` with HTTP
Basic ``client_id:client_secret`` and ``grant_type=password``), then calls
``https://oauth.reddit.com`` with ``Authorization: bearer <token>``. Nothing
is cached between invocations, so every action is stateless — expect two HTTP
round trips per call. The password grant is user-bound, which is what makes
the write and moderator actions possible at all: a user-less token can only
read.

Reddit requires a descriptive, unique ``User-Agent`` and applies drastically
reduced rate limits to generic ones, so every request carries
``python:modulex.reddit:v1.0.0 (by /u/<account>)`` (overridable through the
credential's ``user_agent`` value).

Error model: nothing raises past the ``@tool`` boundary. Transport failures,
non-2xx responses, Reddit's ``api_type=json`` ``errors`` array (which arrives
inside an HTTP 200) and malformed bodies all fold into one ``success=False``
+ ``error`` envelope. Reddit's payloads are deeply wrapped and loosely typed,
so every response value is routed through the ``_as_*`` coercers before it
reaches a pydantic model.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.reddit.outputs import (
    DeleteOutput,
    EditedThing,
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
    PostedComment,
    RedditComment,
    RedditMessage,
    RedditPost,
    RedditRule,
    RedditSubreddit,
    RedditUser,
    ReplyOutput,
    ReportOutput,
    SaveOutput,
    SearchOutput,
    SearchSubredditsOutput,
    SendMessageOutput,
    SubmitPostOutput,
    SubmittedPost,
    SubscribeOutput,
    UnhideOutput,
    UnlockOutput,
    UnmarkNsfwOutput,
    UnsaveOutput,
    VoteOutput,
)

__all__ = [
    "delete",
    "edit",
    "get_comments",
    "get_controversial",
    "get_info",
    "get_me",
    "get_messages",
    "get_posts",
    "get_saved",
    "get_subreddit_info",
    "get_subreddit_rules",
    "get_user",
    "get_user_comments",
    "get_user_posts",
    "hide",
    "hot_posts",
    "list_my_subreddits",
    "lock",
    "mark_all_read",
    "mark_read",
    "marknsfw",
    "mod_approve",
    "mod_distinguish",
    "mod_remove",
    "mod_sticky",
    "reply",
    "report",
    "save",
    "search",
    "search_subreddits",
    "send_message",
    "submit_post",
    "subscribe",
    "unhide",
    "unlock",
    "unmarknsfw",
    "unsave",
    "vote",
]

# --- Constants --------------------------------------------------------------

_TIMEOUT = 30.0

# Two literal hosts, both compile-time constants: the token endpoint lives on
# www.reddit.com and every authenticated API call on oauth.reddit.com. No
# action parameter ever reaches the netloc.
_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_API_BASE = "https://oauth.reddit.com"
_WEB_BASE = "https://www.reddit.com"

# Hard ceiling on how deep the comment tree is walked. Reddit truncates deep
# threads with "more" placeholders rather than nesting forever, so this only
# ever bites on a pathological payload — where it keeps a RecursionError from
# escaping the tool boundary.
_MAX_REPLY_DEPTH = 32

_DEFAULT_USER_AGENT_APP = "python:modulex.reddit:v1.0.0"

# Path-segment shapes. Anything that lands in the URL path is matched against
# one of these first, so a crafted value cannot walk out of the path.
_SUBREDDIT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_]{1,50}$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,29}$")
_ID36_RE = re.compile(r"^[A-Za-z0-9]{1,20}$")

_POST_SORTS = ("hot", "new", "top", "rising", "controversial")
_TIME_FILTERS = ("hour", "day", "week", "month", "year", "all")
_COMMENT_SORTS = ("confidence", "top", "new", "controversial", "old", "random", "qa")
_SEARCH_SORTS = ("relevance", "hot", "top", "new", "comments")
_SEARCH_TYPES = ("link", "sr", "user")
_USER_SORTS = ("hot", "new", "top", "controversial")
_MESSAGE_FOLDERS = (
    "inbox",
    "unread",
    "sent",
    "messages",
    "comments",
    "selfreply",
    "mentions",
)
_SUBREDDIT_SEARCH_SORTS = ("relevance", "activity")
_SUBSCRIBE_ACTIONS = ("sub", "unsub")
_DISTINGUISH_HOW = ("yes", "no", "admin", "special")

_MISSING_CREDENTIALS = (
    "Reddit client ID, client secret, username and password are all required."
    " Add them to the credential from the script app you registered at"
    " https://www.reddit.com/prefs/apps."
)
_TIMED_OUT = "Request to Reddit timed out."


# --- Value coercion ---------------------------------------------------------
#
# Reddit's JSON is loosely typed: a field is routinely a string on one
# endpoint and a number on another, `edited` is either `false` or an epoch,
# and `replies` is either an object or an empty string. Model construction
# happens after the `except` clauses, so a wrong-typed field would raise
# `ValidationError` past the `@tool` boundary instead of returning the
# `success=False` envelope. Every parsed value goes through these.


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object value degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _as_list(payload: Any) -> list[Any]:
    """A non-array value degrades to empty rather than raising."""
    return payload if isinstance(payload, list) else []


def _as_str(value: Any) -> str | None:
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    return value if isinstance(value, str) else str(value)


def _as_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _as_float(value: Any) -> float | None:
    """Numbers only. ``edited: false`` and ``created_utc: null`` degrade to None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _as_str_list(value: Any) -> list[str]:
    return [item for item in _as_list(value) if isinstance(item, str)]


def _permalink(value: Any) -> str | None:
    """Expand Reddit's site-relative permalink into an absolute URL."""
    raw = _as_str(value)
    if not raw:
        return None
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return f"{_WEB_BASE}{raw}" if raw.startswith("/") else raw


# --- Input normalization ----------------------------------------------------


def _clamp(value: int | None, default: int, maximum: int = 100) -> int:
    """Reddit caps listing sizes at 100; clamp instead of letting it 400."""
    if value is None:
        return default
    return min(max(1, value), maximum)


def _strip_prefix(value: str, prefix: str) -> str:
    return value[len(prefix) :] if value.lower().startswith(prefix) else value


def _normalize_subreddit(subreddit: str) -> str | None:
    """Strip an ``r/`` prefix and validate; ``None`` when the name is unusable."""
    name = _strip_prefix((subreddit or "").strip().strip("/"), "r/").strip("/")
    return name if _SUBREDDIT_RE.match(name) else None


def _normalize_username(username: str) -> str | None:
    """Strip a ``u/`` prefix and validate; ``None`` when the name is unusable."""
    name = (username or "").strip().strip("/")
    name = _strip_prefix(_strip_prefix(name, "user/"), "u/").strip("/")
    return name if _USERNAME_RE.match(name) else None


def _normalize_post_id(post_id: str) -> str | None:
    """Accept either a bare id36 (``abc123``) or a ``t3_`` fullname."""
    value = _strip_prefix((post_id or "").strip(), "t3_")
    return value if _ID36_RE.match(value) else None


def _choice(
    value: str | None,
    allowed: tuple[str, ...],
    label: str,
) -> tuple[str | None, str | None]:
    """Validate an optional enum value; returns ``(normalized, error)``."""
    if value is None:
        return None, None
    normalized = value.strip().lower()
    if not normalized:
        return None, None
    if normalized not in allowed:
        return None, f"Invalid {label}: {value!r}. Allowed values: {', '.join(allowed)}."
    return normalized, None


def _bad_subreddit(subreddit: str) -> str:
    return (
        f"Invalid subreddit name: {subreddit!r}. Use the plain name without the"
        " r/ prefix (letters, digits and underscores)."
    )


def _bad_username(username: str) -> str:
    return (
        f"Invalid Reddit username: {username!r}. Use the plain name without the"
        " u/ prefix (letters, digits, underscores and hyphens)."
    )


# --- Credentials + token minting -------------------------------------------


def _credentials(auth_data: dict[str, Any]) -> tuple[str, str, str, str]:
    """The script-app credential set from ``auth_data``."""
    return (
        str(auth_data.get("client_id") or "").strip(),
        str(auth_data.get("client_secret") or "").strip(),
        str(auth_data.get("bot_username") or "").strip(),
        str(auth_data.get("bot_password") or ""),
    )


def _credential_error(auth_data: dict[str, Any]) -> str | None:
    """Short-circuit message when any half of the credential set is missing."""
    client_id, client_secret, username, password = _credentials(auth_data)
    if client_id and client_secret and username and password:
        return None
    return _MISSING_CREDENTIALS


def _user_agent(auth_data: dict[str, Any]) -> str:
    """A descriptive, per-account User-Agent, as Reddit's API rules require.

    Reddit throttles generic agents hard, so the account name is folded into
    the default to keep it unique. A ``user_agent`` value on the credential
    overrides it wholesale.
    """
    override = str(auth_data.get("user_agent") or "").strip()
    if override:
        return override
    _, _, username, _ = _credentials(auth_data)
    account = username or "unknown"
    return f"{_DEFAULT_USER_AGENT_APP} (by /u/{account})"


def _json_body(response: httpx.Response) -> Any:
    """Parsed body, or ``{}`` for the empty/non-JSON bodies Reddit sends."""
    try:
        return response.json()
    except Exception:
        return {}


def _is_ok(response: httpx.Response) -> bool:
    return 200 <= response.status_code < 300


def _http_error(response: httpx.Response, payload: Any) -> str:
    """A readable message for a non-2xx Reddit response."""
    body = _as_dict(payload)
    for key in ("message", "error_description", "explanation", "reason"):
        text = _as_str(body.get(key))
        if text:
            return f"Reddit API error ({response.status_code}): {text}"
    detail = (response.text or "").strip()
    if len(detail) > 400:
        detail = f"{detail[:400]}..."
    if response.status_code == 429:
        return (
            "Reddit API error (429): rate limit exceeded. Reddit allows roughly"
            f" 100 requests per minute per client ID. {detail}".strip()
        )
    return f"Reddit API error ({response.status_code}): {detail}".strip()


async def _mint_access_token(
    client: httpx.AsyncClient,
    auth_data: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Exchange the script-app credential set for a bearer token.

    Returns ``(token, None)`` on success or ``(None, error)`` on failure, so
    callers short-circuit before touching the API. Reddit's bearer tokens are
    short-lived and are minted per invocation; nothing is cached.
    """
    client_id, client_secret, username, password = _credentials(auth_data)
    form = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    try:
        response = await client.post(
            _TOKEN_URL,
            data=form,
            auth=httpx.BasicAuth(client_id, client_secret),
            headers={
                "User-Agent": _user_agent(auth_data),
                "Accept": "application/json",
            },
        )
    except httpx.TimeoutException:
        return None, _TIMED_OUT
    except Exception as exc:
        return None, f"Failed to obtain a Reddit access token: {exc}"

    payload = _as_dict(_json_body(response))
    if not _is_ok(response):
        message = _as_str(payload.get("message")) or _as_str(payload.get("error"))
        detail = f": {message}" if message else ""
        return None, (
            f"Reddit rejected the credentials (HTTP {response.status_code}){detail}."
            " Check the client ID/secret, the account password, and that the"
            " account is a developer of the script app with two-factor"
            " authentication disabled."
        )
    # A rejected grant comes back as HTTP 200 with an `error` key.
    failure = _as_str(payload.get("error"))
    if failure:
        return None, f"Reddit rejected the credentials: {failure}."
    token = _as_str(payload.get("access_token"))
    if not token:
        return None, "Reddit token response did not contain an access_token."
    return token, None


# --- The single request chokepoint -----------------------------------------


async def _call(
    auth_data: dict[str, Any],
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
) -> tuple[Any, str | None]:
    """Mint a token, issue one authenticated request, return ``(payload, error)``.

    ``payload`` is the raw parsed JSON — callers decide its shape (Reddit's
    comment endpoint answers with a top-level array, everything else with an
    object). The credential guard lives here, so an unconfigured credential
    never reaches the network.
    """
    credential_error = _credential_error(auth_data)
    if credential_error:
        return {}, credential_error

    query: dict[str, Any] = {"raw_json": 1}
    if params:
        query.update(params)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(client, auth_data)
            if token is None:
                return {}, token_error
            headers = {
                "Authorization": f"bearer {token}",
                "User-Agent": _user_agent(auth_data),
                "Accept": "application/json",
            }
            if method == "GET":
                response = await client.get(
                    f"{_API_BASE}{path}", headers=headers, params=query
                )
            else:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                response = await client.post(
                    f"{_API_BASE}{path}",
                    headers=headers,
                    params=query,
                    data=data or {},
                )
    except httpx.TimeoutException:
        return {}, _TIMED_OUT
    except Exception as exc:
        return {}, f"Reddit request failed: {exc}"

    payload = _json_body(response)
    if not _is_ok(response):
        return {}, _http_error(response, payload)
    return payload, None


def _api_type_error(payload: Any) -> str | None:
    """Reddit reports write failures inside an HTTP 200 ``json.errors`` array.

    Each entry is ``[CODE, "human message", field]``; RATELIMIT, SUBREDDIT_NOEXIST
    and NO_TEXT all arrive this way.
    """
    errors = _as_list(_as_dict(_as_dict(payload).get("json")).get("errors"))
    if not errors:
        return None
    messages: list[str] = []
    for entry in errors:
        if isinstance(entry, list):
            parts = [text for text in (_as_str(item) for item in entry) if text]
            if parts:
                messages.append(": ".join(parts))
        else:
            text = _as_str(entry)
            if text:
                messages.append(text)
    return "; ".join(messages) if messages else "Reddit rejected the request."


# --- Listing + thing parsing ------------------------------------------------


def _listing(payload: Any) -> tuple[list[dict[str, Any]], str | None, str | None]:
    """Unwrap ``{"kind":"Listing","data":{"children":[...],"after":...}}``."""
    data = _as_dict(_as_dict(payload).get("data"))
    children = [child for child in _as_list(data.get("children")) if isinstance(child, dict)]
    return children, _as_str(data.get("after")), _as_str(data.get("before"))


def _thing(payload: Any) -> dict[str, Any]:
    """Unwrap a single ``{"kind":"tN","data":{...}}`` envelope.

    A few endpoints (``/api/v1/me``) answer with the bare object, so an
    envelope-less payload is returned as-is.
    """
    body = _as_dict(payload)
    inner = body.get("data")
    return _as_dict(inner) if isinstance(inner, dict) else body


def _children_of_kind(children: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [
        _as_dict(child.get("data")) for child in children if _as_str(child.get("kind")) == kind
    ]


def _parse_post(raw: Any) -> RedditPost:
    post = _as_dict(raw)
    return RedditPost(
        id=_as_str(post.get("id")),
        name=_as_str(post.get("name")),
        title=_as_str(post.get("title")),
        author=_as_str(post.get("author")),
        url=_as_str(post.get("url")),
        permalink=_permalink(post.get("permalink")),
        created_utc=_as_float(post.get("created_utc")),
        score=_as_int(post.get("score")),
        upvote_ratio=_as_float(post.get("upvote_ratio")),
        num_comments=_as_int(post.get("num_comments")),
        is_self=_as_bool(post.get("is_self")),
        selftext=_as_str(post.get("selftext")),
        thumbnail=_as_str(post.get("thumbnail")),
        subreddit=_as_str(post.get("subreddit")),
        subreddit_id=_as_str(post.get("subreddit_id")),
        domain=_as_str(post.get("domain")),
        over_18=_as_bool(post.get("over_18")),
        spoiler=_as_bool(post.get("spoiler")),
        locked=_as_bool(post.get("locked")),
        stickied=_as_bool(post.get("stickied")),
        hidden=_as_bool(post.get("hidden")),
        saved=_as_bool(post.get("saved")),
        edited=_as_float(post.get("edited")),
        distinguished=_as_str(post.get("distinguished")),
        ups=_as_int(post.get("ups")),
        downs=_as_int(post.get("downs")),
        link_flair_text=_as_str(post.get("link_flair_text")),
        author_flair_text=_as_str(post.get("author_flair_text")),
    )


def _parse_comment(raw: Any, remaining_depth: int = 0) -> RedditComment:
    comment = _as_dict(raw)
    replies: list[RedditComment] = []
    if remaining_depth > 0:
        # `replies` is an empty string when a comment has none, a Listing
        # otherwise; `_as_dict` absorbs both spellings.
        nested, _, _ = _listing(comment.get("replies"))
        replies = [
            _parse_comment(_as_dict(child.get("data")), remaining_depth - 1)
            for child in nested
            if _as_str(child.get("kind")) == "t1"
        ]
    return RedditComment(
        id=_as_str(comment.get("id")),
        name=_as_str(comment.get("name")),
        author=_as_str(comment.get("author")),
        body=_as_str(comment.get("body")),
        body_html=_as_str(comment.get("body_html")),
        created_utc=_as_float(comment.get("created_utc")),
        score=_as_int(comment.get("score")),
        permalink=_permalink(comment.get("permalink")),
        parent_id=_as_str(comment.get("parent_id")),
        link_id=_as_str(comment.get("link_id")),
        subreddit=_as_str(comment.get("subreddit")),
        subreddit_id=_as_str(comment.get("subreddit_id")),
        is_submitter=_as_bool(comment.get("is_submitter")),
        stickied=_as_bool(comment.get("stickied")),
        score_hidden=_as_bool(comment.get("score_hidden")),
        edited=_as_float(comment.get("edited")),
        distinguished=_as_str(comment.get("distinguished")),
        gilded=_as_int(comment.get("gilded")),
        ups=_as_int(comment.get("ups")),
        downs=_as_int(comment.get("downs")),
        author_flair_text=_as_str(comment.get("author_flair_text")),
        link_title=_as_str(comment.get("link_title")),
        link_author=_as_str(comment.get("link_author")),
        link_url=_as_str(comment.get("link_url")),
        replies=replies,
    )


def _parse_message(raw: Any) -> RedditMessage:
    message = _as_dict(raw)
    return RedditMessage(
        id=_as_str(message.get("id")),
        name=_as_str(message.get("name")),
        author=_as_str(message.get("author")),
        dest=_as_str(message.get("dest")),
        subject=_as_str(message.get("subject")),
        body=_as_str(message.get("body")),
        body_html=_as_str(message.get("body_html")),
        created_utc=_as_float(message.get("created_utc")),
        new=_as_bool(message.get("new")),
        was_comment=_as_bool(message.get("was_comment")),
        context=_as_str(message.get("context")),
        parent_id=_as_str(message.get("parent_id")),
        subreddit=_as_str(message.get("subreddit")),
        distinguished=_as_str(message.get("distinguished")),
    )


def _parse_subreddit(raw: Any) -> RedditSubreddit:
    sub = _as_dict(raw)
    active = sub.get("active_user_count")
    if active is None:
        active = sub.get("accounts_active")
    return RedditSubreddit(
        id=_as_str(sub.get("id")),
        name=_as_str(sub.get("name")),
        display_name=_as_str(sub.get("display_name")),
        display_name_prefixed=_as_str(sub.get("display_name_prefixed")),
        title=_as_str(sub.get("title")),
        description=_as_str(sub.get("description")),
        public_description=_as_str(sub.get("public_description")),
        subscribers=_as_int(sub.get("subscribers")),
        accounts_active=_as_int(active),
        created_utc=_as_float(sub.get("created_utc")),
        over18=_as_bool(sub.get("over18")),
        lang=_as_str(sub.get("lang")),
        subreddit_type=_as_str(sub.get("subreddit_type")),
        url=_as_str(sub.get("url")),
        icon_img=_as_str(sub.get("icon_img")),
        community_icon=_as_str(sub.get("community_icon")),
        banner_img=_as_str(sub.get("banner_img")),
    )


def _parse_user(raw: Any) -> RedditUser:
    user = _as_dict(raw)
    return RedditUser(
        id=_as_str(user.get("id")),
        name=_as_str(user.get("name")),
        created_utc=_as_float(user.get("created_utc")),
        link_karma=_as_int(user.get("link_karma")),
        comment_karma=_as_int(user.get("comment_karma")),
        total_karma=_as_int(user.get("total_karma")),
        awardee_karma=_as_int(user.get("awardee_karma")),
        awarder_karma=_as_int(user.get("awarder_karma")),
        is_gold=_as_bool(user.get("is_gold")),
        is_mod=_as_bool(user.get("is_mod")),
        is_employee=_as_bool(user.get("is_employee")),
        is_friend=_as_bool(user.get("is_friend")),
        has_verified_email=_as_bool(user.get("has_verified_email")),
        verified=_as_bool(user.get("verified")),
        over_18=_as_bool(user.get("over_18")),
        icon_img=_as_str(user.get("icon_img")),
    )


def _parse_rule(raw: Any) -> RedditRule:
    rule = _as_dict(raw)
    return RedditRule(
        short_name=_as_str(rule.get("short_name")),
        description=_as_str(rule.get("description")),
        description_html=_as_str(rule.get("description_html")),
        violation_reason=_as_str(rule.get("violation_reason")),
        kind=_as_str(rule.get("kind")),
        created_utc=_as_float(rule.get("created_utc")),
        priority=_as_int(rule.get("priority")),
    )


def _parse_posts(children: list[dict[str, Any]]) -> list[RedditPost]:
    return [_parse_post(_as_dict(child.get("data"))) for child in children]


def _parse_subreddits(children: list[dict[str, Any]]) -> list[RedditSubreddit]:
    return [_parse_subreddit(_as_dict(child.get("data"))) for child in children]


# --- Shared parameter descriptions -----------------------------------------

_D_SUBREDDIT = 'Subreddit name, without the r/ prefix (e.g. "technology")'
_D_USERNAME = 'Reddit username, without the u/ prefix (e.g. "spez")'
_D_AFTER = 'Fullname cursor for the next page (e.g. "t3_abc123"), taken from a previous response'
_D_BEFORE = 'Fullname cursor for the previous page (e.g. "t3_abc123")'
_D_COUNT = "Number of items already seen in this listing (affects numbering only)"
_D_SHOW = 'Set to "all" to include items your account filters would normally hide'
_D_SR_DETAIL = "Expand subreddit details on every item in the response"
_D_TIME = 'Time filter: "hour", "day", "week", "month", "year" or "all"'
_D_THING_ID = 'Thing fullname: "t3_abc123" for a post, "t1_def456" for a comment'


# --- Input schemas: subreddit reads ----------------------------------------


class GetPostsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)
    sort: str | None = Field(
        default=None,
        description='Sort: "hot" (default), "new", "top", "rising" or "controversial"',
    )
    time: str | None = Field(
        default=None,
        description=f'{_D_TIME}. Applies to the "top" and "controversial" sorts only',
    )
    limit: int | None = Field(
        default=None, description="Maximum posts to return (1-100, default 10)"
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    count: int | None = Field(default=None, description=_D_COUNT)
    show: str | None = Field(default=None, description=_D_SHOW)
    sr_detail: bool | None = Field(default=None, description=_D_SR_DETAIL)
    geo_filter: str | None = Field(
        default=None,
        description='Geographic filter for the "hot" sort (e.g. "GLOBAL", "US")',
    )


class HotPostsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)
    limit: int | None = Field(
        default=None, description="Maximum posts to return (1-100, default 10)"
    )


class GetControversialInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)
    time: str | None = Field(default=None, description=_D_TIME)
    limit: int | None = Field(
        default=None, description="Maximum posts to return (1-100, default 10)"
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    count: int | None = Field(default=None, description=_D_COUNT)
    show: str | None = Field(default=None, description=_D_SHOW)
    sr_detail: bool | None = Field(default=None, description=_D_SR_DETAIL)


class GetCommentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)
    post_id: str = Field(
        description='Post id36 (e.g. "abc123") or its "t3_abc123" fullname',
    )
    sort: str | None = Field(
        default=None,
        description=(
            'Comment sort: "confidence" (best, default), "top", "new",'
            ' "controversial", "old", "random" or "qa"'
        ),
    )
    limit: int | None = Field(
        default=None, description="Maximum comments to return (1-100, default 50)"
    )
    depth: int | None = Field(default=None, description="Maximum depth of nested reply subtrees")
    context: int | None = Field(
        default=None, description="Number of parent comments to include around a focused comment"
    )
    showedits: bool | None = Field(default=None, description="Include edit information")
    showmore: bool | None = Field(
        default=None, description='Include "load more comments" placeholders'
    )
    threaded: bool | None = Field(default=None, description="Return comments threaded (nested)")
    truncate: int | None = Field(
        default=None, description="Truncate the comment tree at this depth"
    )
    comment: str | None = Field(
        default=None, description="id36 of a single comment to focus the thread on"
    )


class SearchInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)
    query: str = Field(
        description=(
            "Search query. Supports field searches (title:, author:, selftext:,"
            " flair:, site:), boolean AND/OR/NOT in caps, parentheses and"
            ' "exact phrases"'
        )
    )
    sort: str | None = Field(
        default=None,
        description='Sort: "relevance" (default), "hot", "top", "new" or "comments"',
    )
    time: str | None = Field(default=None, description=_D_TIME)
    limit: int | None = Field(
        default=None, description="Maximum results to return (1-100, default 10)"
    )
    restrict_sr: bool | None = Field(
        default=None,
        description="Restrict the search to this subreddit (default true)",
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    count: int | None = Field(default=None, description=_D_COUNT)
    show: str | None = Field(default=None, description=_D_SHOW)
    result_type: str | None = Field(
        default=None,
        description='Result kind: "link" (posts, default), "sr" (subreddits) or "user"',
    )
    sr_detail: bool | None = Field(default=None, description=_D_SR_DETAIL)


class GetSubredditInfoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)


class GetSubredditRulesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)


# --- Input schemas: account + user reads -----------------------------------


class GetMeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class GetUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    username: str = Field(description=_D_USERNAME)


class GetUserPostsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    username: str = Field(description=_D_USERNAME)
    sort: str | None = Field(
        default=None,
        description='Sort: "new" (default), "hot", "top" or "controversial"',
    )
    time: str | None = Field(
        default=None,
        description=f'{_D_TIME}. Applies to the "top" and "controversial" sorts only',
    )
    limit: int | None = Field(
        default=None, description="Maximum posts to return (1-100, default 25)"
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    count: int | None = Field(default=None, description=_D_COUNT)
    show: str | None = Field(default=None, description=_D_SHOW)
    sr_detail: bool | None = Field(default=None, description=_D_SR_DETAIL)


class GetUserCommentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    username: str = Field(description=_D_USERNAME)
    sort: str | None = Field(
        default=None,
        description='Sort: "new" (default), "hot", "top" or "controversial"',
    )
    time: str | None = Field(
        default=None,
        description=f'{_D_TIME}. Applies to the "top" and "controversial" sorts only',
    )
    limit: int | None = Field(
        default=None, description="Maximum comments to return (1-100, default 25)"
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    count: int | None = Field(default=None, description=_D_COUNT)
    show: str | None = Field(default=None, description=_D_SHOW)
    sr_detail: bool | None = Field(default=None, description=_D_SR_DETAIL)


class GetSavedInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    username: str = Field(
        description=(
            "Your own Reddit username — Reddit only serves saved items for the"
            " authenticated account"
        )
    )
    limit: int | None = Field(
        default=None, description="Maximum items to return (1-100, default 25)"
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    count: int | None = Field(default=None, description=_D_COUNT)
    show: str | None = Field(default=None, description=_D_SHOW)
    sr_detail: bool | None = Field(default=None, description=_D_SR_DETAIL)


class GetInfoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_ids: str = Field(
        description=(
            'Comma-separated thing fullnames (e.g. "t3_abc123,t1_xyz789,t5_2qh33").'
            " Prefixes: t1_ comment, t3_ post, t5_ subreddit"
        )
    )


# --- Input schemas: subreddit discovery + messages -------------------------


class SearchSubredditsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(description="Text matched against subreddit names and descriptions")
    sort: str | None = Field(
        default=None, description='Sort: "relevance" (default) or "activity"'
    )
    limit: int | None = Field(
        default=None, description="Maximum subreddits to return (1-100, default 25)"
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    show_users: bool | None = Field(
        default=None, description="Also include matching user profiles"
    )
    sr_detail: bool | None = Field(default=None, description=_D_SR_DETAIL)


class ListMySubredditsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    limit: int | None = Field(
        default=None, description="Maximum subreddits to return (1-100, default 25)"
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    count: int | None = Field(default=None, description=_D_COUNT)
    show: str | None = Field(default=None, description=_D_SHOW)
    sr_detail: bool | None = Field(default=None, description=_D_SR_DETAIL)


class GetMessagesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    where: str | None = Field(
        default=None,
        description=(
            'Folder: "inbox" (default), "unread", "sent", "messages" (direct only),'
            ' "comments" (comment replies), "selfreply" or "mentions"'
        ),
    )
    limit: int | None = Field(
        default=None, description="Maximum messages to return (1-100, default 25)"
    )
    after: str | None = Field(default=None, description=_D_AFTER)
    before: str | None = Field(default=None, description=_D_BEFORE)
    mark: bool | None = Field(
        default=None, description="Mark the fetched messages as read"
    )
    count: int | None = Field(default=None, description=_D_COUNT)
    show: str | None = Field(default=None, description=_D_SHOW)


class SendMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    to: str = Field(description='Recipient username (e.g. "spez") or subreddit (e.g. "/r/python")')
    subject: str = Field(description="Message subject (max 100 characters)")
    text: str = Field(description="Message body in Reddit markdown")
    from_sr: str | None = Field(
        default=None,
        description="Send as modmail from this subreddit (requires mod mail permission)",
    )


class MarkReadInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_ids: str = Field(
        description='Comma-separated message fullnames (e.g. "t4_abc123,t4_def456")'
    )


class MarkAllReadInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- Input schemas: content writes -----------------------------------------


class SubmitPostInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)
    title: str = Field(description="Post title (max 300 characters)")
    text: str | None = Field(
        default=None,
        description="Body of a self post, in Reddit markdown. Mutually exclusive with url",
    )
    url: str | None = Field(
        default=None,
        description="Target of a link post. Mutually exclusive with text",
    )
    nsfw: bool | None = Field(default=None, description="Mark the post NSFW")
    spoiler: bool | None = Field(default=None, description="Mark the post a spoiler")
    send_replies: bool | None = Field(
        default=None, description="Send reply notifications to the inbox (default true)"
    )
    flair_id: str | None = Field(
        default=None, description="Flair template UUID (max 36 characters)"
    )
    flair_text: str | None = Field(default=None, description="Flair text (max 64 characters)")
    collection_id: str | None = Field(
        default=None, description="Collection UUID to add the new post to"
    )


class ReplyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    parent_id: str = Field(description=f"{_D_THING_ID} — the thing being replied to")
    text: str = Field(description="Reply body in Reddit markdown")
    return_rtjson: bool | None = Field(
        default=None, description="Return the reply as Rich Text JSON instead of markdown"
    )


class EditInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=f"{_D_THING_ID} — must be authored by this account")
    text: str = Field(description="Replacement body in Reddit markdown")


class DeleteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=f"{_D_THING_ID} — must be authored by this account")


class VoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)
    direction: int = Field(description="1 to upvote, 0 to clear the vote, -1 to downvote")


class SaveInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)
    category: str | None = Field(
        default=None, description="Saved-items category (a Reddit Premium feature)"
    )


class UnsaveInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)


class SubscribeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    subreddit: str = Field(description=_D_SUBREDDIT)
    action: str | None = Field(
        default=None, description='"sub" to subscribe (default) or "unsub" to unsubscribe'
    )


class ReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)
    reason: str | None = Field(
        default=None, description="Subreddit rule the content violates (max 100 characters)"
    )
    other_reason: str | None = Field(
        default=None, description="Free-form reason (max 100 characters)"
    )


class HideInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_ids: str = Field(
        description='Comma-separated post fullnames (e.g. "t3_abc123,t3_def456")'
    )


class UnhideInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_ids: str = Field(
        description='Comma-separated post fullnames (e.g. "t3_abc123,t3_def456")'
    )


class MarkNsfwInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description='Post fullname (e.g. "t3_abc123")')


class UnmarkNsfwInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description='Post fullname (e.g. "t3_abc123")')


# --- Input schemas: moderator actions --------------------------------------


class ModApproveInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)


class ModRemoveInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)
    spam: bool | None = Field(
        default=None, description="Also train the subreddit spam filter on this item"
    )


class ModDistinguishInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)
    how: str | None = Field(
        default=None,
        description=(
            '"yes" for a moderator badge (default), "no" to remove it, "admin"'
            ' or "special"'
        ),
    )
    sticky: bool | None = Field(
        default=None, description="Also sticky the comment to the top of the thread (comments only)"
    )


class LockInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)


class UnlockInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description=_D_THING_ID)


class ModStickyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    thing_id: str = Field(description='Post fullname (e.g. "t3_abc123")')
    state: bool | None = Field(
        default=None, description="True to sticky the post (default), false to unsticky it"
    )
    num: int | None = Field(
        default=None, description="Sticky slot 1-4 (1 is the top slot); only used when stickying"
    )


# --- Subreddit reads --------------------------------------------------------


@tool(args_schema=GetPostsInput)
@serialize_pydantic_return
async def get_posts(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
    sort: str | None = None,
    time: str | None = None,
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    count: int | None = None,
    show: str | None = None,
    sr_detail: bool | None = None,
    geo_filter: str | None = None,
) -> GetPostsOutput:
    """Fetch posts from a subreddit under a chosen sort (hot, new, top, rising,
    controversial)."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return GetPostsOutput(success=False, error=_bad_subreddit(subreddit))
    chosen_sort, sort_error = _choice(sort, _POST_SORTS, "sort")
    if sort_error:
        return GetPostsOutput(success=False, error=sort_error)
    chosen_sort = chosen_sort or "hot"
    chosen_time, time_error = _choice(time, _TIME_FILTERS, "time filter")
    if time_error:
        return GetPostsOutput(success=False, error=time_error)

    params: dict[str, Any] = {"limit": _clamp(limit, 10)}
    if chosen_time and chosen_sort in ("top", "controversial"):
        params["t"] = chosen_time
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if count is not None:
        params["count"] = count
    if show:
        params["show"] = show
    if sr_detail is not None:
        params["sr_detail"] = str(sr_detail).lower()
    if geo_filter:
        params["g"] = geo_filter

    payload, error = await _call(
        auth_data, "GET", f"/r/{quote(name, safe='')}/{chosen_sort}", params=params
    )
    if error:
        return GetPostsOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    posts = _parse_posts(children)
    resolved = posts[0].subreddit if posts and posts[0].subreddit else name
    return GetPostsOutput(
        success=True,
        subreddit=resolved,
        posts=posts,
        after=next_after,
        before=next_before,
    )


@tool(args_schema=HotPostsInput)
@serialize_pydantic_return
async def hot_posts(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
    limit: int | None = None,
) -> HotPostsOutput:
    """Fetch the most popular (hot) posts from a subreddit."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return HotPostsOutput(success=False, error=_bad_subreddit(subreddit))

    payload, error = await _call(
        auth_data,
        "GET",
        f"/r/{quote(name, safe='')}/hot",
        params={"limit": _clamp(limit, 10)},
    )
    if error:
        return HotPostsOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    posts = _parse_posts(children)
    resolved = posts[0].subreddit if posts and posts[0].subreddit else name
    return HotPostsOutput(
        success=True,
        subreddit=resolved,
        posts=posts,
        after=next_after,
        before=next_before,
    )


@tool(args_schema=GetControversialInput)
@serialize_pydantic_return
async def get_controversial(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
    time: str | None = None,
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    count: int | None = None,
    show: str | None = None,
    sr_detail: bool | None = None,
) -> GetControversialOutput:
    """Fetch the most controversial posts from a subreddit."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return GetControversialOutput(success=False, error=_bad_subreddit(subreddit))
    chosen_time, time_error = _choice(time, _TIME_FILTERS, "time filter")
    if time_error:
        return GetControversialOutput(success=False, error=time_error)

    params: dict[str, Any] = {"limit": _clamp(limit, 10)}
    if chosen_time:
        params["t"] = chosen_time
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if count is not None:
        params["count"] = count
    if show:
        params["show"] = show
    if sr_detail is not None:
        params["sr_detail"] = str(sr_detail).lower()

    payload, error = await _call(
        auth_data, "GET", f"/r/{quote(name, safe='')}/controversial", params=params
    )
    if error:
        return GetControversialOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    posts = _parse_posts(children)
    resolved = posts[0].subreddit if posts and posts[0].subreddit else name
    return GetControversialOutput(
        success=True,
        subreddit=resolved,
        posts=posts,
        after=next_after,
        before=next_before,
    )


@tool(args_schema=GetCommentsInput)
@serialize_pydantic_return
async def get_comments(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
    post_id: str,
    sort: str | None = None,
    limit: int | None = None,
    depth: int | None = None,
    context: int | None = None,
    showedits: bool | None = None,
    showmore: bool | None = None,
    threaded: bool | None = None,
    truncate: int | None = None,
    comment: str | None = None,
) -> GetCommentsOutput:
    """Fetch a post and its comment tree, with replies nested under each comment."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return GetCommentsOutput(success=False, error=_bad_subreddit(subreddit))
    identifier = _normalize_post_id(post_id)
    if not identifier:
        return GetCommentsOutput(
            success=False,
            error=f'Invalid post ID: {post_id!r}. Use the id36 (e.g. "abc123") or "t3_abc123".',
        )
    chosen_sort, sort_error = _choice(sort, _COMMENT_SORTS, "comment sort")
    if sort_error:
        return GetCommentsOutput(success=False, error=sort_error)

    params: dict[str, Any] = {
        "sort": chosen_sort or "confidence",
        "limit": _clamp(limit, 50),
    }
    if depth is not None:
        params["depth"] = depth
    if context is not None:
        params["context"] = context
    if showedits is not None:
        params["showedits"] = str(showedits).lower()
    if showmore is not None:
        params["showmore"] = str(showmore).lower()
    if threaded is not None:
        params["threaded"] = str(threaded).lower()
    if truncate is not None:
        params["truncate"] = truncate
    if comment:
        params["comment"] = comment

    payload, error = await _call(
        auth_data,
        "GET",
        f"/r/{quote(name, safe='')}/comments/{quote(identifier, safe='')}",
        params=params,
    )
    if error:
        return GetCommentsOutput(success=False, error=error)

    # This endpoint is the one that answers with a top-level array: element 0
    # is a Listing holding the post, element 1 a Listing holding the comments.
    parts = _as_list(payload)
    post_children, _, _ = _listing(parts[0] if len(parts) > 0 else {})
    comment_children, _, _ = _listing(parts[1] if len(parts) > 1 else {})

    post = _parse_post(_as_dict(post_children[0].get("data"))) if post_children else None
    comments = [
        _parse_comment(_as_dict(child.get("data")), _MAX_REPLY_DEPTH)
        for child in comment_children
        if _as_str(child.get("kind")) == "t1"
    ]
    return GetCommentsOutput(success=True, post=post, comments=comments)


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
    query: str,
    sort: str | None = None,
    time: str | None = None,
    limit: int | None = None,
    restrict_sr: bool | None = None,
    after: str | None = None,
    before: str | None = None,
    count: int | None = None,
    show: str | None = None,
    result_type: str | None = None,
    sr_detail: bool | None = None,
) -> SearchOutput:
    """Search for posts inside a subreddit."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return SearchOutput(success=False, error=_bad_subreddit(subreddit))
    if not (query or "").strip():
        return SearchOutput(success=False, error="A search query is required.")
    chosen_sort, sort_error = _choice(sort, _SEARCH_SORTS, "sort")
    if sort_error:
        return SearchOutput(success=False, error=sort_error)
    chosen_time, time_error = _choice(time, _TIME_FILTERS, "time filter")
    if time_error:
        return SearchOutput(success=False, error=time_error)
    chosen_type, type_error = _choice(result_type, _SEARCH_TYPES, "result type")
    if type_error:
        return SearchOutput(success=False, error=type_error)

    params: dict[str, Any] = {
        "q": query,
        "sort": chosen_sort or "relevance",
        "limit": _clamp(limit, 10),
        "restrict_sr": "false" if restrict_sr is False else "true",
    }
    if chosen_time:
        params["t"] = chosen_time
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if count is not None:
        params["count"] = count
    if show:
        params["show"] = show
    if chosen_type:
        params["type"] = chosen_type
    if sr_detail is not None:
        params["sr_detail"] = str(sr_detail).lower()

    payload, error = await _call(
        auth_data, "GET", f"/r/{quote(name, safe='')}/search", params=params
    )
    if error:
        return SearchOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    posts = _parse_posts(children)
    return SearchOutput(
        success=True,
        subreddit=name,
        posts=posts,
        after=next_after,
        before=next_before,
    )


@tool(args_schema=GetSubredditInfoInput)
@serialize_pydantic_return
async def get_subreddit_info(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
) -> GetSubredditInfoOutput:
    """Get metadata about a subreddit: title, description, subscriber count and type."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return GetSubredditInfoOutput(success=False, error=_bad_subreddit(subreddit))

    payload, error = await _call(auth_data, "GET", f"/r/{quote(name, safe='')}/about")
    if error:
        return GetSubredditInfoOutput(success=False, error=error)
    return GetSubredditInfoOutput(success=True, subreddit=_parse_subreddit(_thing(payload)))


@tool(args_schema=GetSubredditRulesInput)
@serialize_pydantic_return
async def get_subreddit_rules(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
) -> GetSubredditRulesOutput:
    """Get a subreddit's own rules plus the Reddit site-wide rules that apply to it."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return GetSubredditRulesOutput(success=False, error=_bad_subreddit(subreddit))

    payload, error = await _call(auth_data, "GET", f"/r/{quote(name, safe='')}/about/rules")
    if error:
        return GetSubredditRulesOutput(success=False, error=error)

    body = _as_dict(payload)
    return GetSubredditRulesOutput(
        success=True,
        rules=[_parse_rule(rule) for rule in _as_list(body.get("rules"))],
        site_rules=_as_str_list(body.get("site_rules")),
    )


# --- Account + user reads ---------------------------------------------------


@tool(args_schema=GetMeInput)
@serialize_pydantic_return
async def get_me(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetMeOutput:
    """Get the profile of the authenticated Reddit account."""
    payload, error = await _call(auth_data, "GET", "/api/v1/me")
    if error:
        return GetMeOutput(success=False, error=error)
    # /api/v1/me answers with the bare account object, not a Thing envelope.
    return GetMeOutput(success=True, user=_parse_user(_as_dict(payload)))


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(
    auth_type: str,
    auth_data: dict[str, Any],
    username: str,
) -> GetUserOutput:
    """Get the public profile of any Reddit user by username."""
    name = _normalize_username(username)
    if not name:
        return GetUserOutput(success=False, error=_bad_username(username))

    payload, error = await _call(auth_data, "GET", f"/user/{quote(name, safe='')}/about")
    if error:
        return GetUserOutput(success=False, error=error)
    return GetUserOutput(success=True, user=_parse_user(_thing(payload)))


@tool(args_schema=GetUserPostsInput)
@serialize_pydantic_return
async def get_user_posts(
    auth_type: str,
    auth_data: dict[str, Any],
    username: str,
    sort: str | None = None,
    time: str | None = None,
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    count: int | None = None,
    show: str | None = None,
    sr_detail: bool | None = None,
) -> GetUserPostsOutput:
    """Fetch the posts a Reddit user has submitted."""
    name = _normalize_username(username)
    if not name:
        return GetUserPostsOutput(success=False, error=_bad_username(username))
    chosen_sort, sort_error = _choice(sort, _USER_SORTS, "sort")
    if sort_error:
        return GetUserPostsOutput(success=False, error=sort_error)
    chosen_time, time_error = _choice(time, _TIME_FILTERS, "time filter")
    if time_error:
        return GetUserPostsOutput(success=False, error=time_error)

    params: dict[str, Any] = {"limit": _clamp(limit, 25)}
    if chosen_sort:
        params["sort"] = chosen_sort
        if chosen_time and chosen_sort in ("top", "controversial"):
            params["t"] = chosen_time
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if count is not None:
        params["count"] = count
    if show:
        params["show"] = show
    if sr_detail is not None:
        params["sr_detail"] = str(sr_detail).lower()

    payload, error = await _call(
        auth_data, "GET", f"/user/{quote(name, safe='')}/submitted", params=params
    )
    if error:
        return GetUserPostsOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    return GetUserPostsOutput(
        success=True,
        posts=_parse_posts(children),
        after=next_after,
        before=next_before,
    )


@tool(args_schema=GetUserCommentsInput)
@serialize_pydantic_return
async def get_user_comments(
    auth_type: str,
    auth_data: dict[str, Any],
    username: str,
    sort: str | None = None,
    time: str | None = None,
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    count: int | None = None,
    show: str | None = None,
    sr_detail: bool | None = None,
) -> GetUserCommentsOutput:
    """Fetch the comments a Reddit user has written."""
    name = _normalize_username(username)
    if not name:
        return GetUserCommentsOutput(success=False, error=_bad_username(username))
    chosen_sort, sort_error = _choice(sort, _USER_SORTS, "sort")
    if sort_error:
        return GetUserCommentsOutput(success=False, error=sort_error)
    chosen_time, time_error = _choice(time, _TIME_FILTERS, "time filter")
    if time_error:
        return GetUserCommentsOutput(success=False, error=time_error)

    params: dict[str, Any] = {"limit": _clamp(limit, 25)}
    if chosen_sort:
        params["sort"] = chosen_sort
        if chosen_time and chosen_sort in ("top", "controversial"):
            params["t"] = chosen_time
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if count is not None:
        params["count"] = count
    if show:
        params["show"] = show
    if sr_detail is not None:
        params["sr_detail"] = str(sr_detail).lower()

    payload, error = await _call(
        auth_data, "GET", f"/user/{quote(name, safe='')}/comments", params=params
    )
    if error:
        return GetUserCommentsOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    return GetUserCommentsOutput(
        success=True,
        comments=[_parse_comment(_as_dict(child.get("data"))) for child in children],
        after=next_after,
        before=next_before,
    )


@tool(args_schema=GetSavedInput)
@serialize_pydantic_return
async def get_saved(
    auth_type: str,
    auth_data: dict[str, Any],
    username: str,
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    count: int | None = None,
    show: str | None = None,
    sr_detail: bool | None = None,
) -> GetSavedOutput:
    """Fetch your own saved posts and comments, split by kind."""
    name = _normalize_username(username)
    if not name:
        return GetSavedOutput(success=False, error=_bad_username(username))

    params: dict[str, Any] = {"limit": _clamp(limit, 25)}
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if count is not None:
        params["count"] = count
    if show:
        params["show"] = show
    if sr_detail is not None:
        params["sr_detail"] = str(sr_detail).lower()

    payload, error = await _call(
        auth_data, "GET", f"/user/{quote(name, safe='')}/saved", params=params
    )
    if error:
        return GetSavedOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    return GetSavedOutput(
        success=True,
        posts=[_parse_post(item) for item in _children_of_kind(children, "t3")],
        comments=[_parse_comment(item) for item in _children_of_kind(children, "t1")],
        after=next_after,
        before=next_before,
    )


@tool(args_schema=GetInfoInput)
@serialize_pydantic_return
async def get_info(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_ids: str,
) -> GetInfoOutput:
    """Look up posts, comments and subreddits by their thing fullnames."""
    identifiers = (thing_ids or "").strip()
    if not identifiers:
        return GetInfoOutput(
            success=False,
            error='At least one thing fullname is required (e.g. "t3_abc123").',
        )

    payload, error = await _call(auth_data, "GET", "/api/info", params={"id": identifiers})
    if error:
        return GetInfoOutput(success=False, error=error)

    children, _, _ = _listing(payload)
    return GetInfoOutput(
        success=True,
        posts=[_parse_post(item) for item in _children_of_kind(children, "t3")],
        comments=[_parse_comment(item) for item in _children_of_kind(children, "t1")],
        subreddits=[_parse_subreddit(item) for item in _children_of_kind(children, "t5")],
    )


# --- Subreddit discovery ----------------------------------------------------


@tool(args_schema=SearchSubredditsInput)
@serialize_pydantic_return
async def search_subreddits(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    sort: str | None = None,
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    show_users: bool | None = None,
    sr_detail: bool | None = None,
) -> SearchSubredditsOutput:
    """Search for subreddits by name and description."""
    if not (query or "").strip():
        return SearchSubredditsOutput(success=False, error="A search query is required.")
    chosen_sort, sort_error = _choice(sort, _SUBREDDIT_SEARCH_SORTS, "sort")
    if sort_error:
        return SearchSubredditsOutput(success=False, error=sort_error)

    params: dict[str, Any] = {
        "q": query,
        "sort": chosen_sort or "relevance",
        "limit": _clamp(limit, 25),
    }
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if show_users is not None:
        params["show_users"] = str(show_users).lower()
    if sr_detail is not None:
        params["sr_detail"] = str(sr_detail).lower()

    payload, error = await _call(auth_data, "GET", "/subreddits/search", params=params)
    if error:
        return SearchSubredditsOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    return SearchSubredditsOutput(
        success=True,
        subreddits=_parse_subreddits(children),
        after=next_after,
        before=next_before,
    )


@tool(args_schema=ListMySubredditsInput)
@serialize_pydantic_return
async def list_my_subreddits(
    auth_type: str,
    auth_data: dict[str, Any],
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    count: int | None = None,
    show: str | None = None,
    sr_detail: bool | None = None,
) -> ListMySubredditsOutput:
    """List the subreddits the authenticated account subscribes to."""
    params: dict[str, Any] = {"limit": _clamp(limit, 25)}
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if count is not None:
        params["count"] = count
    if show:
        params["show"] = show
    if sr_detail is not None:
        params["sr_detail"] = str(sr_detail).lower()

    payload, error = await _call(
        auth_data, "GET", "/subreddits/mine/subscriber", params=params
    )
    if error:
        return ListMySubredditsOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    return ListMySubredditsOutput(
        success=True,
        subreddits=_parse_subreddits(children),
        after=next_after,
        before=next_before,
    )


# --- Messages ---------------------------------------------------------------


@tool(args_schema=GetMessagesInput)
@serialize_pydantic_return
async def get_messages(
    auth_type: str,
    auth_data: dict[str, Any],
    where: str | None = None,
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    mark: bool | None = None,
    count: int | None = None,
    show: str | None = None,
) -> GetMessagesOutput:
    """Retrieve items from the authenticated account's inbox."""
    folder, folder_error = _choice(where, _MESSAGE_FOLDERS, "message folder")
    if folder_error:
        return GetMessagesOutput(success=False, error=folder_error)
    folder = folder or "inbox"

    params: dict[str, Any] = {"limit": _clamp(limit, 25)}
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if mark is not None:
        params["mark"] = str(mark).lower()
    if count is not None:
        params["count"] = count
    if show:
        params["show"] = show

    payload, error = await _call(auth_data, "GET", f"/message/{folder}", params=params)
    if error:
        return GetMessagesOutput(success=False, error=error)

    children, next_after, next_before = _listing(payload)
    return GetMessagesOutput(
        success=True,
        messages=[_parse_message(_as_dict(child.get("data"))) for child in children],
        after=next_after,
        before=next_before,
    )


@tool(args_schema=SendMessageInput)
@serialize_pydantic_return
async def send_message(
    auth_type: str,
    auth_data: dict[str, Any],
    to: str,
    subject: str,
    text: str,
    from_sr: str | None = None,
) -> SendMessageOutput:
    """Send a private message to a Reddit user or subreddit."""
    recipient = (to or "").strip()
    if not recipient:
        return SendMessageOutput(success=False, error="A message recipient is required.")
    if not (subject or "").strip():
        return SendMessageOutput(success=False, error="A message subject is required.")

    form: dict[str, Any] = {
        "to": recipient,
        "subject": subject,
        "text": text,
        "api_type": "json",
    }
    if from_sr:
        sender = _normalize_subreddit(from_sr)
        if not sender:
            return SendMessageOutput(success=False, error=_bad_subreddit(from_sr))
        form["from_sr"] = sender

    payload, error = await _call(auth_data, "POST", "/api/compose", data=form)
    if error:
        return SendMessageOutput(success=False, error=error)
    rejection = _api_type_error(payload)
    if rejection:
        return SendMessageOutput(success=False, error=f"Failed to send message: {rejection}")
    return SendMessageOutput(success=True, message=f"Message sent to {recipient}.")


@tool(args_schema=MarkReadInput)
@serialize_pydantic_return
async def mark_read(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_ids: str,
) -> MarkReadOutput:
    """Mark one or more inbox messages as read."""
    identifiers = (thing_ids or "").strip()
    if not identifiers:
        return MarkReadOutput(
            success=False,
            error='At least one message fullname is required (e.g. "t4_abc123").',
        )

    _, error = await _call(auth_data, "POST", "/api/read_message", data={"id": identifiers})
    if error:
        return MarkReadOutput(success=False, error=error)
    return MarkReadOutput(success=True, message=f"Marked {identifiers} as read.")


@tool(args_schema=MarkAllReadInput)
@serialize_pydantic_return
async def mark_all_read(
    auth_type: str,
    auth_data: dict[str, Any],
) -> MarkAllReadOutput:
    """Mark every message in the inbox as read."""
    # This one answers with an empty body, so nothing is read from it — only
    # the status decides the outcome.
    _, error = await _call(auth_data, "POST", "/api/read_all_messages")
    if error:
        return MarkAllReadOutput(success=False, error=error)
    return MarkAllReadOutput(success=True, message="Marked all inbox messages as read.")


# --- Content writes ---------------------------------------------------------


@tool(args_schema=SubmitPostInput)
@serialize_pydantic_return
async def submit_post(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
    title: str,
    text: str | None = None,
    url: str | None = None,
    nsfw: bool | None = None,
    spoiler: bool | None = None,
    send_replies: bool | None = None,
    flair_id: str | None = None,
    flair_text: str | None = None,
    collection_id: str | None = None,
) -> SubmitPostOutput:
    """Submit a new text or link post to a subreddit."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return SubmitPostOutput(success=False, error=_bad_subreddit(subreddit))
    if not (title or "").strip():
        return SubmitPostOutput(success=False, error="A post title is required.")

    form: dict[str, Any] = {"sr": name, "title": title, "api_type": "json"}
    if text:
        form["kind"] = "self"
        form["text"] = text
    elif url:
        form["kind"] = "link"
        form["url"] = url
    else:
        # No body and no URL is a self post with an empty body, which Reddit
        # accepts (title-only posts are common).
        form["kind"] = "self"
        form["text"] = ""
    if nsfw is not None:
        form["nsfw"] = str(nsfw).lower()
    if spoiler is not None:
        form["spoiler"] = str(spoiler).lower()
    if send_replies is not None:
        form["sendreplies"] = str(send_replies).lower()
    if flair_id:
        form["flair_id"] = flair_id
    if flair_text:
        form["flair_text"] = flair_text
    if collection_id:
        form["collection_id"] = collection_id

    payload, error = await _call(auth_data, "POST", "/api/submit", data=form)
    if error:
        return SubmitPostOutput(success=False, error=error)
    rejection = _api_type_error(payload)
    if rejection:
        return SubmitPostOutput(success=False, error=f"Failed to submit post: {rejection}")

    data = _as_dict(_as_dict(_as_dict(payload).get("json")).get("data"))
    post_url = _as_str(data.get("url"))
    return SubmitPostOutput(
        success=True,
        message=f"Post submitted to r/{name}.",
        post=SubmittedPost(
            id=_as_str(data.get("id")),
            name=_as_str(data.get("name")),
            url=post_url,
            permalink=_permalink(data.get("permalink")) or post_url,
        ),
    )


@tool(args_schema=ReplyInput)
@serialize_pydantic_return
async def reply(
    auth_type: str,
    auth_data: dict[str, Any],
    parent_id: str,
    text: str,
    return_rtjson: bool | None = None,
) -> ReplyOutput:
    """Post a comment in reply to a Reddit post or comment."""
    parent = (parent_id or "").strip()
    if not parent:
        return ReplyOutput(success=False, error='A parent fullname is required (e.g. "t3_abc123").')
    if not (text or "").strip():
        return ReplyOutput(success=False, error="Reply text is required.")

    form: dict[str, Any] = {"thing_id": parent, "text": text, "api_type": "json"}
    if return_rtjson is not None:
        form["return_rtjson"] = str(return_rtjson).lower()

    payload, error = await _call(auth_data, "POST", "/api/comment", data=form)
    if error:
        return ReplyOutput(success=False, error=error)
    rejection = _api_type_error(payload)
    if rejection:
        return ReplyOutput(success=False, error=f"Failed to post reply: {rejection}")

    things = _as_list(_as_dict(_as_dict(_as_dict(payload).get("json")).get("data")).get("things"))
    created = _as_dict(_as_dict(things[0]).get("data")) if things else {}
    return ReplyOutput(
        success=True,
        message=f"Reply posted to {parent}.",
        comment=PostedComment(
            id=_as_str(created.get("id")),
            name=_as_str(created.get("name")),
            permalink=_permalink(created.get("permalink")),
            body=_as_str(created.get("body")),
        ),
    )


@tool(args_schema=EditInput)
@serialize_pydantic_return
async def edit(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
    text: str,
) -> EditOutput:
    """Replace the body of your own Reddit post or comment."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return EditOutput(success=False, error='A thing fullname is required (e.g. "t1_abc123").')

    payload, error = await _call(
        auth_data,
        "POST",
        "/api/editusertext",
        data={"thing_id": identifier, "text": text, "api_type": "json"},
    )
    if error:
        return EditOutput(success=False, error=error)
    rejection = _api_type_error(payload)
    if rejection:
        return EditOutput(success=False, error=f"Failed to edit {identifier}: {rejection}")

    things = _as_list(_as_dict(_as_dict(_as_dict(payload).get("json")).get("data")).get("things"))
    updated = _as_dict(_as_dict(things[0]).get("data")) if things else {}
    return EditOutput(
        success=True,
        message=f"Edited {identifier}.",
        thing=EditedThing(
            id=_as_str(updated.get("id")),
            name=_as_str(updated.get("name")),
            body=_as_str(updated.get("body")),
            selftext=_as_str(updated.get("selftext")),
        ),
    )


@tool(args_schema=DeleteInput)
@serialize_pydantic_return
async def delete(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
) -> DeleteOutput:
    """Delete your own Reddit post or comment."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return DeleteOutput(success=False, error='A thing fullname is required (e.g. "t3_abc123").')

    _, error = await _call(auth_data, "POST", "/api/del", data={"id": identifier})
    if error:
        return DeleteOutput(success=False, error=error)
    return DeleteOutput(success=True, message=f"Deleted {identifier}.")


@tool(args_schema=VoteInput)
@serialize_pydantic_return
async def vote(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
    direction: int,
) -> VoteOutput:
    """Upvote, downvote or clear your vote on a Reddit post or comment."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return VoteOutput(success=False, error='A thing fullname is required (e.g. "t3_abc123").')
    if direction not in (1, 0, -1):
        return VoteOutput(
            success=False,
            error="direction must be 1 (upvote), 0 (clear the vote) or -1 (downvote).",
        )

    _, error = await _call(
        auth_data, "POST", "/api/vote", data={"id": identifier, "dir": str(direction)}
    )
    if error:
        return VoteOutput(success=False, error=error)
    verb = {1: "Upvoted", 0: "Cleared the vote on", -1: "Downvoted"}[direction]
    return VoteOutput(success=True, message=f"{verb} {identifier}.")


@tool(args_schema=SaveInput)
@serialize_pydantic_return
async def save(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
    category: str | None = None,
) -> SaveOutput:
    """Save a Reddit post or comment to your saved items."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return SaveOutput(success=False, error='A thing fullname is required (e.g. "t3_abc123").')

    form: dict[str, Any] = {"id": identifier}
    if category:
        form["category"] = category

    _, error = await _call(auth_data, "POST", "/api/save", data=form)
    if error:
        return SaveOutput(success=False, error=error)
    return SaveOutput(success=True, message=f"Saved {identifier}.")


@tool(args_schema=UnsaveInput)
@serialize_pydantic_return
async def unsave(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
) -> UnsaveOutput:
    """Remove a Reddit post or comment from your saved items."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return UnsaveOutput(success=False, error='A thing fullname is required (e.g. "t3_abc123").')

    _, error = await _call(auth_data, "POST", "/api/unsave", data={"id": identifier})
    if error:
        return UnsaveOutput(success=False, error=error)
    return UnsaveOutput(success=True, message=f"Unsaved {identifier}.")


@tool(args_schema=SubscribeInput)
@serialize_pydantic_return
async def subscribe(
    auth_type: str,
    auth_data: dict[str, Any],
    subreddit: str,
    action: str | None = None,
) -> SubscribeOutput:
    """Subscribe to or unsubscribe from a subreddit."""
    name = _normalize_subreddit(subreddit)
    if not name:
        return SubscribeOutput(success=False, error=_bad_subreddit(subreddit))
    chosen, action_error = _choice(action, _SUBSCRIBE_ACTIONS, "action")
    if action_error:
        return SubscribeOutput(success=False, error=action_error)
    chosen = chosen or "sub"

    _, error = await _call(
        auth_data, "POST", "/api/subscribe", data={"action": chosen, "sr_name": name}
    )
    if error:
        return SubscribeOutput(success=False, error=error)
    verb = "Subscribed to" if chosen == "sub" else "Unsubscribed from"
    return SubscribeOutput(success=True, message=f"{verb} r/{name}.")


@tool(args_schema=ReportInput)
@serialize_pydantic_return
async def report(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
    reason: str | None = None,
    other_reason: str | None = None,
) -> ReportOutput:
    """Report a Reddit post or comment to the subreddit moderators."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return ReportOutput(success=False, error='A thing fullname is required (e.g. "t3_abc123").')

    form: dict[str, Any] = {"thing_id": identifier, "api_type": "json"}
    if reason:
        form["reason"] = reason
    if other_reason:
        form["other_reason"] = other_reason

    payload, error = await _call(auth_data, "POST", "/api/report", data=form)
    if error:
        return ReportOutput(success=False, error=error)
    rejection = _api_type_error(payload)
    if rejection:
        return ReportOutput(success=False, error=f"Failed to report {identifier}: {rejection}")
    return ReportOutput(success=True, message=f"Reported {identifier}.")


@tool(args_schema=HideInput)
@serialize_pydantic_return
async def hide(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_ids: str,
) -> HideOutput:
    """Hide one or more posts from your own listings."""
    identifiers = (thing_ids or "").strip()
    if not identifiers:
        return HideOutput(
            success=False, error='At least one post fullname is required (e.g. "t3_abc123").'
        )

    _, error = await _call(auth_data, "POST", "/api/hide", data={"id": identifiers})
    if error:
        return HideOutput(success=False, error=error)
    return HideOutput(success=True, message=f"Hid {identifiers}.")


@tool(args_schema=UnhideInput)
@serialize_pydantic_return
async def unhide(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_ids: str,
) -> UnhideOutput:
    """Unhide one or more previously hidden posts."""
    identifiers = (thing_ids or "").strip()
    if not identifiers:
        return UnhideOutput(
            success=False, error='At least one post fullname is required (e.g. "t3_abc123").'
        )

    _, error = await _call(auth_data, "POST", "/api/unhide", data={"id": identifiers})
    if error:
        return UnhideOutput(success=False, error=error)
    return UnhideOutput(success=True, message=f"Unhid {identifiers}.")


@tool(args_schema=MarkNsfwInput)
@serialize_pydantic_return
async def marknsfw(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
) -> MarkNsfwOutput:
    """Mark a post NSFW."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return MarkNsfwOutput(
            success=False, error='A post fullname is required (e.g. "t3_abc123").'
        )

    _, error = await _call(auth_data, "POST", "/api/marknsfw", data={"id": identifier})
    if error:
        return MarkNsfwOutput(success=False, error=error)
    return MarkNsfwOutput(success=True, message=f"Marked {identifier} NSFW.")


@tool(args_schema=UnmarkNsfwInput)
@serialize_pydantic_return
async def unmarknsfw(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
) -> UnmarkNsfwOutput:
    """Remove the NSFW mark from a post."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return UnmarkNsfwOutput(
            success=False, error='A post fullname is required (e.g. "t3_abc123").'
        )

    _, error = await _call(auth_data, "POST", "/api/unmarknsfw", data={"id": identifier})
    if error:
        return UnmarkNsfwOutput(success=False, error=error)
    return UnmarkNsfwOutput(success=True, message=f"Removed the NSFW mark from {identifier}.")


# --- Moderator actions ------------------------------------------------------


@tool(args_schema=ModApproveInput)
@serialize_pydantic_return
async def mod_approve(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
) -> ModApproveOutput:
    """Approve a reported or removed post or comment. Requires moderator rights."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return ModApproveOutput(
            success=False, error='A thing fullname is required (e.g. "t3_abc123").'
        )

    _, error = await _call(auth_data, "POST", "/api/approve", data={"id": identifier})
    if error:
        return ModApproveOutput(success=False, error=error)
    return ModApproveOutput(success=True, message=f"Approved {identifier}.")


@tool(args_schema=ModRemoveInput)
@serialize_pydantic_return
async def mod_remove(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
    spam: bool | None = None,
) -> ModRemoveOutput:
    """Remove a post or comment, optionally as spam. Requires moderator rights."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return ModRemoveOutput(
            success=False, error='A thing fullname is required (e.g. "t3_abc123").'
        )

    _, error = await _call(
        auth_data,
        "POST",
        "/api/remove",
        data={"id": identifier, "spam": str(bool(spam)).lower()},
    )
    if error:
        return ModRemoveOutput(success=False, error=error)
    suffix = " as spam" if spam else ""
    return ModRemoveOutput(success=True, message=f"Removed {identifier}{suffix}.")


@tool(args_schema=ModDistinguishInput)
@serialize_pydantic_return
async def mod_distinguish(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
    how: str | None = None,
    sticky: bool | None = None,
) -> ModDistinguishOutput:
    """Add or remove a moderator/admin badge on a post or comment. Requires moderator
    rights."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return ModDistinguishOutput(
            success=False, error='A thing fullname is required (e.g. "t1_abc123").'
        )
    chosen, how_error = _choice(how, _DISTINGUISH_HOW, "distinguish type")
    if how_error:
        return ModDistinguishOutput(success=False, error=how_error)
    chosen = chosen or "yes"

    form: dict[str, Any] = {"id": identifier, "how": chosen, "api_type": "json"}
    if sticky is not None:
        form["sticky"] = str(sticky).lower()

    payload, error = await _call(auth_data, "POST", "/api/distinguish", data=form)
    if error:
        return ModDistinguishOutput(success=False, error=error)
    rejection = _api_type_error(payload)
    if rejection:
        return ModDistinguishOutput(
            success=False, error=f"Failed to distinguish {identifier}: {rejection}"
        )
    verb = "Removed the distinction from" if chosen == "no" else "Distinguished"
    return ModDistinguishOutput(success=True, message=f"{verb} {identifier}.")


@tool(args_schema=LockInput)
@serialize_pydantic_return
async def lock(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
) -> LockOutput:
    """Lock a post or comment so no new replies can be posted. Requires moderator rights."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return LockOutput(success=False, error='A thing fullname is required (e.g. "t3_abc123").')

    _, error = await _call(auth_data, "POST", "/api/lock", data={"id": identifier})
    if error:
        return LockOutput(success=False, error=error)
    return LockOutput(success=True, message=f"Locked {identifier}.")


@tool(args_schema=UnlockInput)
@serialize_pydantic_return
async def unlock(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
) -> UnlockOutput:
    """Unlock a previously locked post or comment. Requires moderator rights."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return UnlockOutput(success=False, error='A thing fullname is required (e.g. "t3_abc123").')

    _, error = await _call(auth_data, "POST", "/api/unlock", data={"id": identifier})
    if error:
        return UnlockOutput(success=False, error=error)
    return UnlockOutput(success=True, message=f"Unlocked {identifier}.")


@tool(args_schema=ModStickyInput)
@serialize_pydantic_return
async def mod_sticky(
    auth_type: str,
    auth_data: dict[str, Any],
    thing_id: str,
    state: bool | None = None,
    num: int | None = None,
) -> ModStickyOutput:
    """Sticky or unsticky a post at the top of a subreddit. Requires moderator rights."""
    identifier = (thing_id or "").strip()
    if not identifier:
        return ModStickyOutput(
            success=False, error='A post fullname is required (e.g. "t3_abc123").'
        )
    should_sticky = True if state is None else state
    if num is not None and not 1 <= num <= 4:
        return ModStickyOutput(success=False, error="num must be between 1 and 4.")

    form: dict[str, Any] = {
        "id": identifier,
        "state": str(should_sticky).lower(),
        "api_type": "json",
    }
    if num is not None and should_sticky:
        form["num"] = str(num)

    payload, error = await _call(
        auth_data, "POST", "/api/set_subreddit_sticky", data=form
    )
    if error:
        return ModStickyOutput(success=False, error=error)
    rejection = _api_type_error(payload)
    if rejection:
        return ModStickyOutput(
            success=False, error=f"Failed to set the sticky state of {identifier}: {rejection}"
        )
    verb = "Stickied" if should_sticky else "Unstickied"
    return ModStickyOutput(success=True, message=f"{verb} {identifier}.")
