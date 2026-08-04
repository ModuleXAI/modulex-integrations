"""Buffer LangChain ``@tool`` functions.

Ten async tools wrapping the Buffer GraphQL API. Buffer serves its whole
public surface from one endpoint — ``POST https://api.buffer.com`` — so every
action here posts a ``{"query": ..., "variables": ...}`` document and reads
its result out of the ``data`` envelope.

Calling convention is the modulex *api_key* one: the ``ToolExecutor`` injects
``api_key: str`` directly (resolved from the user's ``api_key`` credential),
not an ``auth_type``/``auth_data`` pair. The key travels as
``Authorization: Bearer <api_key>``.

Error model: GraphQL answers HTTP 200 for nearly everything, so three failure
shapes are folded into one ``success=False`` + ``error`` envelope —
transport/non-200 failures, a top-level ``errors`` array, and typed mutation
errors (``MutationError`` implementors such as ``UnauthorizedError``,
``NotFoundError``, ``LimitReachedError``). Nothing raises past the ``@tool``
boundary.

Media is attached by public URL: Buffer downloads the asset itself at publish
time, so ``media_url`` must point at a publicly reachable image or video.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.buffer.outputs import (
    BufferAccount,
    BufferAsset,
    BufferChannel,
    BufferIdea,
    BufferIdeaGroup,
    BufferOrganization,
    BufferPageInfo,
    BufferPost,
    BufferPostError,
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

__all__ = [
    "create_idea",
    "create_post",
    "delete_post",
    "edit_post",
    "get_account",
    "get_channels",
    "get_idea_groups",
    "get_ideas",
    "get_post",
    "get_posts",
]

# The single GraphQL endpoint. Nothing in an action parameter ever reaches the
# host, so the credential can only ever be sent to this compile-time constant.
_BUFFER_API_URL = "https://api.buffer.com"
_TIMEOUT = 30.0
_DEFAULT_LIMIT = 20

_EMPTY_KEY_ERROR = "Buffer API key is empty. Please configure a valid Buffer credential."

# Closed enum value sets, mirroring the API's ShareMode, SchedulingType,
# PostStatus, PostSortableKey and SortDirection enums. Sending a value outside
# these produces a GraphQL validation error, so they are checked locally first.
_SHARE_MODES = ("addToQueue", "shareNext", "shareNow", "customScheduled")
_SCHEDULING_TYPES = ("automatic", "notification")
_POST_STATUSES = ("draft", "needs_approval", "scheduled", "sending", "sent", "error")
_SORT_FIELDS = ("dueAt", "createdAt")
_SORT_DIRECTIONS = ("asc", "desc")
_MEDIA_TYPES = ("auto", "image", "video")
_VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v", ".webm", ".avi", ".mpeg", ".mpg", ".3gp")


# --- GraphQL documents -----------------------------------------------------

_POST_SELECTION = """
  id
  text
  status
  via
  channelId
  channelService
  schedulingType
  shareMode
  isCustomScheduled
  sharedNow
  createdAt
  updatedAt
  dueAt
  sentAt
  externalLink
  error {
    message
    supportUrl
    rawError
  }
  assets {
    id
    type
    mimeType
    source
    thumbnail
  }
"""

_IDEA_SELECTION = """
  id
  organizationId
  groupId
  content {
    title
    text
  }
"""

_CREATE_POST_MUTATION = f"""
  mutation CreatePost($input: CreatePostInput!) {{
    createPost(input: $input) {{
      __typename
      ... on PostActionSuccess {{
        post {{
          {_POST_SELECTION}
        }}
      }}
      ... on MutationError {{
        message
      }}
    }}
  }}
"""

_EDIT_POST_MUTATION = f"""
  mutation EditPost($input: EditPostInput!) {{
    editPost(input: $input) {{
      __typename
      ... on PostActionSuccess {{
        post {{
          {_POST_SELECTION}
        }}
      }}
      ... on MutationError {{
        message
      }}
    }}
  }}
"""

_DELETE_POST_MUTATION = """
  mutation DeletePost($input: DeletePostInput!) {
    deletePost(input: $input) {
      __typename
      ... on DeletePostSuccess {
        id
      }
      ... on MutationError {
        message
      }
    }
  }
"""

_GET_POST_QUERY = f"""
  query GetPost($input: PostInput!) {{
    post(input: $input) {{
      {_POST_SELECTION}
    }}
  }}
"""

_GET_POSTS_QUERY = f"""
  query GetPosts($input: PostsInput!, $first: Int, $after: String) {{
    posts(input: $input, first: $first, after: $after) {{
      edges {{
        node {{
          {_POST_SELECTION}
        }}
      }}
      pageInfo {{
        hasNextPage
        endCursor
      }}
    }}
  }}
"""

_GET_CHANNELS_QUERY = """
  query GetChannels($input: ChannelsInput!) {
    channels(input: $input) {
      id
      name
      displayName
      service
      serviceId
      avatar
      timezone
      type
      isQueuePaused
      isDisconnected
      organizationId
    }
  }
"""

_GET_ACCOUNT_QUERY = """
  query GetAccount {
    account {
      id
      email
      name
      timezone
      organizations {
        id
        name
        channelCount
        ownerEmail
      }
    }
  }
"""

_CREATE_IDEA_MUTATION = f"""
  mutation CreateIdea($input: CreateIdeaInput!) {{
    createIdea(input: $input) {{
      __typename
      ... on Idea {{
        {_IDEA_SELECTION}
      }}
      ... on IdeaResponse {{
        idea {{
          {_IDEA_SELECTION}
        }}
      }}
      ... on MutationError {{
        message
      }}
    }}
  }}
"""

_GET_IDEAS_QUERY = f"""
  query GetIdeas($input: IdeasInput!, $first: Int, $after: String) {{
    ideas(input: $input, first: $first, after: $after) {{
      edges {{
        node {{
          {_IDEA_SELECTION}
        }}
      }}
      pageInfo {{
        hasNextPage
        endCursor
      }}
    }}
  }}
"""

_GET_IDEA_GROUPS_QUERY = """
  query GetIdeaGroups($input: IdeaGroupsInput!) {
    ideaGroups(input: $input) {
      id
      name
      isLocked
    }
  }
"""


# --- Transport helpers -----------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object payload degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _as_list(payload: Any) -> list[Any]:
    """A non-array payload degrades to empty rather than raising."""
    return payload if isinstance(payload, list) else []


def _as_str(value: Any) -> str | None:
    """Coerce a scalar to str; anything else degrades to None.

    The response models type every id/timestamp as ``str | None``, but model
    construction happens after the ``except`` clauses — so an upstream field
    arriving with the wrong type would raise ``ValidationError`` past the
    ``@tool`` boundary instead of returning the ``success=False`` envelope.
    """
    if value is None or isinstance(value, (dict, list)):
        return None
    return value if isinstance(value, str) else str(value)


def _as_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


async def _graphql(
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str | None]:
    """POST one GraphQL document and return ``(data, error)``.

    ``error`` is a ready-to-surface string for transport failures, non-200
    responses, and top-level GraphQL ``errors``; it is ``None`` when ``data``
    holds a usable object.
    """
    payload: dict[str, Any] = {"query": query}
    if variables is not None:
        payload["variables"] = variables

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _BUFFER_API_URL, headers=_headers(api_key), json=payload
            )
        if response.status_code != 200:
            return {}, f"Buffer API error ({response.status_code}): {response.text}"
        body = _as_dict(response.json())
    except httpx.TimeoutException:
        return {}, "Request to the Buffer API timed out."
    except Exception as exc:
        return {}, f"Buffer API request failed: {exc}"

    errors = _as_list(body.get("errors"))
    if errors:
        first = _as_dict(errors[0])
        message = first.get("message")
        code = _as_dict(first.get("extensions")).get("code")
        detail = message if isinstance(message, str) and message else "unknown error"
        if isinstance(code, str) and code:
            detail = f"{detail} ({code})"
        return {}, f"Buffer API error: {detail}"

    data = body.get("data")
    if not isinstance(data, dict):
        return {}, "Buffer API returned no data."
    return data, None


def _mutation_error(result: dict[str, Any], fallback: str) -> str:
    """Turn a typed ``MutationError`` payload into an error string."""
    message = result.get("message")
    if isinstance(message, str) and message.strip():
        return f"{fallback}: {message.strip()}"
    typename = result.get("__typename")
    if isinstance(typename, str) and typename:
        return f"{fallback} ({typename})"
    return fallback


# --- Parsing helpers -------------------------------------------------------


def _parse_asset(raw: dict[str, Any]) -> BufferAsset:
    return BufferAsset(
        id=_as_str(raw.get("id")),
        type=_as_str(raw.get("type")),
        mime_type=_as_str(raw.get("mimeType")),
        source=_as_str(raw.get("source")),
        thumbnail=_as_str(raw.get("thumbnail")),
    )


def _parse_post(raw: dict[str, Any]) -> BufferPost:
    error = _as_dict(raw.get("error")) if raw.get("error") else {}
    return BufferPost(
        id=_as_str(raw.get("id")),
        text=_as_str(raw.get("text")),
        status=_as_str(raw.get("status")),
        via=_as_str(raw.get("via")),
        channel_id=_as_str(raw.get("channelId")),
        channel_service=_as_str(raw.get("channelService")),
        scheduling_type=_as_str(raw.get("schedulingType")),
        share_mode=_as_str(raw.get("shareMode")),
        is_custom_scheduled=_as_bool(raw.get("isCustomScheduled")),
        shared_now=_as_bool(raw.get("sharedNow")),
        created_at=_as_str(raw.get("createdAt")),
        updated_at=_as_str(raw.get("updatedAt")),
        due_at=_as_str(raw.get("dueAt")),
        sent_at=_as_str(raw.get("sentAt")),
        external_link=_as_str(raw.get("externalLink")),
        error=(
            BufferPostError(
                message=_as_str(error.get("message")),
                support_url=_as_str(error.get("supportUrl")),
                raw_error=_as_str(error.get("rawError")),
            )
            if error
            else None
        ),
        assets=[_parse_asset(_as_dict(asset)) for asset in _as_list(raw.get("assets"))],
    )


def _parse_channel(raw: dict[str, Any]) -> BufferChannel:
    return BufferChannel(
        id=_as_str(raw.get("id")),
        name=_as_str(raw.get("name")),
        display_name=_as_str(raw.get("displayName")),
        service=_as_str(raw.get("service")),
        service_id=_as_str(raw.get("serviceId")),
        avatar=_as_str(raw.get("avatar")),
        timezone=_as_str(raw.get("timezone")),
        type=_as_str(raw.get("type")),
        is_queue_paused=_as_bool(raw.get("isQueuePaused")),
        is_disconnected=_as_bool(raw.get("isDisconnected")),
        organization_id=_as_str(raw.get("organizationId")),
    )


def _parse_account(raw: dict[str, Any]) -> BufferAccount:
    return BufferAccount(
        id=_as_str(raw.get("id")),
        email=_as_str(raw.get("email")),
        name=_as_str(raw.get("name")),
        timezone=_as_str(raw.get("timezone")),
        organizations=[
            BufferOrganization(
                id=_as_str(org.get("id")),
                name=_as_str(org.get("name")),
                channel_count=_as_int(org.get("channelCount")),
                owner_email=_as_str(org.get("ownerEmail")),
            )
            for org in (_as_dict(entry) for entry in _as_list(raw.get("organizations")))
        ],
    )


def _parse_idea(raw: dict[str, Any]) -> BufferIdea:
    content = _as_dict(raw.get("content"))
    return BufferIdea(
        id=_as_str(raw.get("id")),
        organization_id=_as_str(raw.get("organizationId")),
        group_id=_as_str(raw.get("groupId")),
        title=_as_str(content.get("title")),
        text=_as_str(content.get("text")),
    )


def _parse_idea_group(raw: dict[str, Any]) -> BufferIdeaGroup:
    return BufferIdeaGroup(
        id=_as_str(raw.get("id")),
        name=_as_str(raw.get("name")),
        is_locked=_as_bool(raw.get("isLocked")),
    )


def _parse_page_info(raw: dict[str, Any]) -> BufferPageInfo:
    return BufferPageInfo(
        has_next_page=_as_bool(raw.get("hasNextPage")),
        end_cursor=_as_str(raw.get("endCursor")),
    )


def _edge_nodes(connection: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a Relay ``edges { node { ... } }`` list into plain nodes."""
    return [
        _as_dict(_as_dict(edge).get("node")) for edge in _as_list(connection.get("edges"))
    ]


def _str_list(value: str | list[str] | None) -> list[str]:
    """Normalize an ID/status filter, tolerating a comma-separated string."""
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part).strip() for part in value if str(part).strip()]


def _looks_like_video(url: str) -> bool:
    return urlsplit(url).path.lower().endswith(_VIDEO_EXTENSIONS)


def _build_assets(
    media_url: str | None,
    media_type: str,
    media_alt_text: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Build the ``assets`` input from a public media URL.

    Returns ``(assets, error)``; ``assets`` is empty when no media was given.
    """
    if not media_url or not media_url.strip():
        return [], None

    url = media_url.strip()
    if not url.lower().startswith(("http://", "https://")):
        return [], "media_url must be a public http(s) URL pointing at an image or video."

    kind = (media_type or "auto").strip().lower()
    if kind not in _MEDIA_TYPES:
        return [], f"media_type must be one of: {', '.join(_MEDIA_TYPES)}."
    if kind == "auto":
        kind = "video" if _looks_like_video(url) else "image"

    if kind == "video":
        return [{"video": {"url": url}}], None

    image: dict[str, Any] = {"url": url}
    if media_alt_text and media_alt_text.strip():
        image["metadata"] = {"altText": media_alt_text.strip()}
    return [{"image": image}], None


# --- Input schemas (args_schema for each @tool) ----------------------------


class CreatePostInput(BaseModel):
    channel_id: str = Field(
        description="ID of the channel to create the post for (see get_channels)"
    )
    api_key: str = Field(description="Buffer API key (provided by credential system)")
    text: str | None = Field(
        default=None, description="Text content of the post (required unless media is attached)"
    )
    mode: str = Field(
        default="addToQueue",
        description=(
            "How to share the post: 'addToQueue', 'shareNext', 'shareNow', or "
            "'customScheduled' (requires due_at)"
        ),
    )
    scheduling_type: str = Field(
        default="automatic",
        description=(
            "How the post publishes: 'automatic' (Buffer publishes it) or "
            "'notification' (mobile reminder)"
        ),
    )
    due_at: str | None = Field(
        default=None,
        description="Publish time as an ISO 8601 timestamp (required when mode is customScheduled)",
    )
    save_to_draft: bool | None = Field(
        default=None, description="Save the post as a draft instead of scheduling it"
    )
    media_url: str | None = Field(
        default=None,
        description="Public http(s) URL of an image or video to attach; Buffer downloads it",
    )
    media_type: str = Field(
        default="auto",
        description="Attachment type: 'auto' (detect from the URL), 'image', or 'video'",
    )
    media_alt_text: str | None = Field(
        default=None, description="Alt text for an attached image (ignored for video)"
    )


class EditPostInput(BaseModel):
    post_id: str = Field(description="ID of the post to edit")
    api_key: str = Field(description="Buffer API key (provided by credential system)")
    text: str | None = Field(
        default=None, description="New text content; omit to keep the current text"
    )
    mode: str | None = Field(
        default=None,
        description=(
            "New share mode: 'addToQueue', 'shareNext', 'shareNow', or "
            "'customScheduled' (requires due_at). Omit to make no scheduling change"
        ),
    )
    scheduling_type: str | None = Field(
        default=None,
        description=(
            "How the post publishes: 'automatic' or 'notification'. Leave unset to keep "
            "the post's current setting; set it only to change how the post publishes"
        ),
    )
    due_at: str | None = Field(
        default=None,
        description=(
            "New publish time as an ISO 8601 timestamp (required when mode is customScheduled)"
        ),
    )
    save_to_draft: bool | None = Field(
        default=None, description="Save the post as a draft instead of keeping it scheduled"
    )
    media_url: str | None = Field(
        default=None,
        description=(
            "Public http(s) URL of an image or video to attach; replaces the existing attachments"
        ),
    )
    media_type: str = Field(
        default="auto",
        description="Attachment type: 'auto' (detect from the URL), 'image', or 'video'",
    )
    media_alt_text: str | None = Field(
        default=None, description="Alt text for an attached image (ignored for video)"
    )


class GetPostInput(BaseModel):
    post_id: str = Field(description="ID of the post to fetch")
    api_key: str = Field(description="Buffer API key (provided by credential system)")


class DeletePostInput(BaseModel):
    post_id: str = Field(description="ID of the post to delete")
    api_key: str = Field(description="Buffer API key (provided by credential system)")


class GetPostsInput(BaseModel):
    organization_id: str = Field(
        description="Buffer organization ID (see get_account)"
    )
    api_key: str = Field(description="Buffer API key (provided by credential system)")
    channel_ids: list[str] | None = Field(
        default=None, description="Channel IDs to filter by"
    )
    status: list[str] | None = Field(
        default=None,
        description=(
            "Statuses to filter by: draft, needs_approval, scheduled, sending, sent, error"
        ),
    )
    limit: int = Field(default=_DEFAULT_LIMIT, description="Maximum number of posts to return")
    after: str | None = Field(
        default=None, description="Pagination cursor from a previous page (page_info.end_cursor)"
    )
    sort_by: str = Field(default="dueAt", description="Field to sort by: 'dueAt' or 'createdAt'")
    sort_direction: str = Field(default="asc", description="Sort direction: 'asc' or 'desc'")


class GetChannelsInput(BaseModel):
    organization_id: str = Field(
        description="Buffer organization ID (see get_account)"
    )
    api_key: str = Field(description="Buffer API key (provided by credential system)")


class GetAccountInput(BaseModel):
    api_key: str = Field(description="Buffer API key (provided by credential system)")


class CreateIdeaInput(BaseModel):
    organization_id: str = Field(
        description="Buffer organization ID (see get_account)"
    )
    text: str = Field(description="Text content of the idea")
    api_key: str = Field(description="Buffer API key (provided by credential system)")
    title: str | None = Field(default=None, description="Optional title for the idea")
    group_id: str | None = Field(
        default=None, description="Optional idea group (board column) to place the idea in"
    )


class GetIdeasInput(BaseModel):
    organization_id: str = Field(
        description="Buffer organization ID (see get_account)"
    )
    api_key: str = Field(description="Buffer API key (provided by credential system)")
    limit: int = Field(default=_DEFAULT_LIMIT, description="Maximum number of ideas to return")
    after: str | None = Field(
        default=None, description="Pagination cursor from a previous page (page_info.end_cursor)"
    )


class GetIdeaGroupsInput(BaseModel):
    organization_id: str = Field(
        description="Buffer organization ID (see get_account)"
    )
    api_key: str = Field(description="Buffer API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=CreatePostInput)
@serialize_pydantic_return
async def create_post(
    channel_id: str,
    api_key: str,
    text: str | None = None,
    mode: str = "addToQueue",
    scheduling_type: str = "automatic",
    due_at: str | None = None,
    save_to_draft: bool | None = None,
    media_url: str | None = None,
    media_type: str = "auto",
    media_alt_text: str | None = None,
) -> CreatePostOutput:
    """Create a post for a channel — queue it, share it now, schedule it, or save it as a draft."""
    if not api_key or not api_key.strip():
        return CreatePostOutput(success=False, error=_EMPTY_KEY_ERROR)
    if mode not in _SHARE_MODES:
        return CreatePostOutput(
            success=False, error=f"mode must be one of: {', '.join(_SHARE_MODES)}."
        )
    if scheduling_type not in _SCHEDULING_TYPES:
        return CreatePostOutput(
            success=False,
            error=f"scheduling_type must be one of: {', '.join(_SCHEDULING_TYPES)}.",
        )
    if mode == "customScheduled" and not (due_at and due_at.strip()):
        return CreatePostOutput(
            success=False, error="due_at is required when mode is 'customScheduled'."
        )

    assets, asset_error = _build_assets(media_url, media_type, media_alt_text)
    if asset_error is not None:
        return CreatePostOutput(success=False, error=asset_error)
    if not (text and text.strip()) and not assets:
        return CreatePostOutput(
            success=False, error="Provide text, media_url, or both to create a post."
        )

    post_input: dict[str, Any] = {
        "channelId": channel_id,
        "mode": mode,
        "schedulingType": scheduling_type,
    }
    if text is not None:
        post_input["text"] = text
    if due_at and due_at.strip():
        post_input["dueAt"] = due_at.strip()
    if save_to_draft is not None:
        post_input["saveToDraft"] = save_to_draft
    if assets:
        post_input["assets"] = assets

    data, error = await _graphql(api_key, _CREATE_POST_MUTATION, {"input": post_input})
    if error is not None:
        return CreatePostOutput(success=False, error=error)

    result = _as_dict(data.get("createPost"))
    post = _as_dict(result.get("post"))
    if result.get("__typename") != "PostActionSuccess" or not post:
        return CreatePostOutput(
            success=False, error=_mutation_error(result, "Failed to create the post")
        )
    return CreatePostOutput(success=True, post=_parse_post(post))


@tool(args_schema=EditPostInput)
@serialize_pydantic_return
async def edit_post(
    post_id: str,
    api_key: str,
    text: str | None = None,
    mode: str | None = None,
    scheduling_type: str | None = None,
    due_at: str | None = None,
    save_to_draft: bool | None = None,
    media_url: str | None = None,
    media_type: str = "auto",
    media_alt_text: str | None = None,
) -> EditPostOutput:
    """Edit an existing post — update its text, schedule, or media (new media replaces the old)."""
    if not api_key or not api_key.strip():
        return EditPostOutput(success=False, error=_EMPTY_KEY_ERROR)
    if mode is not None and mode not in _SHARE_MODES:
        return EditPostOutput(
            success=False, error=f"mode must be one of: {', '.join(_SHARE_MODES)}."
        )
    if scheduling_type is not None and scheduling_type not in _SCHEDULING_TYPES:
        return EditPostOutput(
            success=False,
            error=f"scheduling_type must be one of: {', '.join(_SCHEDULING_TYPES)}.",
        )
    if mode == "customScheduled" and not (due_at and due_at.strip()):
        return EditPostOutput(
            success=False, error="due_at is required when mode is 'customScheduled'."
        )

    assets, asset_error = _build_assets(media_url, media_type, media_alt_text)
    if asset_error is not None:
        return EditPostOutput(success=False, error=asset_error)

    # schedulingType is non-null on the edit input, so a value must always be
    # sent. Defaulting it would silently convert a notification-published post
    # to automatic whenever the caller edits only the text, so an unspecified
    # value is read off the post instead. That costs one extra request only in
    # the ambiguous case — an explicit scheduling_type skips the lookup.
    resolved_scheduling_type = scheduling_type
    if resolved_scheduling_type is None:
        current, current_error = await _graphql(
            api_key, _GET_POST_QUERY, {"input": {"id": post_id}}
        )
        if current_error is not None:
            return EditPostOutput(success=False, error=current_error)
        current_post = _as_dict(current.get("post"))
        if not current_post:
            return EditPostOutput(
                success=False, error=f"Post '{post_id}' was not found."
            )
        resolved_scheduling_type = _as_str(current_post.get("schedulingType"))
        if resolved_scheduling_type not in _SCHEDULING_TYPES:
            return EditPostOutput(
                success=False,
                error=(
                    f"Post '{post_id}' reports an unrecognised scheduling type; "
                    "pass scheduling_type explicitly to edit it."
                ),
            )

    post_input: dict[str, Any] = {
        "id": post_id,
        "schedulingType": resolved_scheduling_type,
    }
    if text is not None:
        post_input["text"] = text
    if mode is not None:
        post_input["mode"] = mode
    if due_at and due_at.strip():
        post_input["dueAt"] = due_at.strip()
    if save_to_draft is not None:
        post_input["saveToDraft"] = save_to_draft
    if assets:
        post_input["assets"] = assets

    data, error = await _graphql(api_key, _EDIT_POST_MUTATION, {"input": post_input})
    if error is not None:
        return EditPostOutput(success=False, error=error)

    result = _as_dict(data.get("editPost"))
    post = _as_dict(result.get("post"))
    if result.get("__typename") != "PostActionSuccess" or not post:
        return EditPostOutput(
            success=False, error=_mutation_error(result, "Failed to edit the post")
        )
    return EditPostOutput(success=True, post=_parse_post(post))


@tool(args_schema=GetPostInput)
@serialize_pydantic_return
async def get_post(post_id: str, api_key: str) -> GetPostOutput:
    """Get a single post by ID, including its status, schedule, and media."""
    if not api_key or not api_key.strip():
        return GetPostOutput(success=False, error=_EMPTY_KEY_ERROR)

    data, error = await _graphql(api_key, _GET_POST_QUERY, {"input": {"id": post_id}})
    if error is not None:
        return GetPostOutput(success=False, error=error)

    post = _as_dict(data.get("post"))
    if not post:
        return GetPostOutput(success=False, error=f"Post '{post_id}' was not found.")
    return GetPostOutput(success=True, post=_parse_post(post))


@tool(args_schema=GetPostsInput)
@serialize_pydantic_return
async def get_posts(
    organization_id: str,
    api_key: str,
    channel_ids: list[str] | None = None,
    status: list[str] | None = None,
    limit: int = _DEFAULT_LIMIT,
    after: str | None = None,
    sort_by: str = "dueAt",
    sort_direction: str = "asc",
) -> GetPostsOutput:
    """List posts in an organization, optionally filtered by channel and status."""
    if not api_key or not api_key.strip():
        return GetPostsOutput(success=False, error=_EMPTY_KEY_ERROR)
    if sort_by not in _SORT_FIELDS:
        return GetPostsOutput(
            success=False, error=f"sort_by must be one of: {', '.join(_SORT_FIELDS)}."
        )
    if sort_direction not in _SORT_DIRECTIONS:
        return GetPostsOutput(
            success=False,
            error=f"sort_direction must be one of: {', '.join(_SORT_DIRECTIONS)}.",
        )

    statuses = _str_list(status)
    invalid = [entry for entry in statuses if entry not in _POST_STATUSES]
    if invalid:
        return GetPostsOutput(
            success=False,
            error=(
                f"Invalid post status '{invalid[0]}'. "
                f"Valid statuses: {', '.join(_POST_STATUSES)}."
            ),
        )

    posts_input: dict[str, Any] = {
        "organizationId": organization_id,
        "sort": [{"field": sort_by, "direction": sort_direction}],
    }
    post_filter: dict[str, Any] = {}
    channels = _str_list(channel_ids)
    if channels:
        post_filter["channelIds"] = channels
    if statuses:
        post_filter["status"] = statuses
    if post_filter:
        posts_input["filter"] = post_filter

    variables: dict[str, Any] = {
        "input": posts_input,
        "first": max(1, limit),
        "after": after or None,
    }
    data, error = await _graphql(api_key, _GET_POSTS_QUERY, variables)
    if error is not None:
        return GetPostsOutput(success=False, error=error)

    connection = _as_dict(data.get("posts"))
    return GetPostsOutput(
        success=True,
        posts=[_parse_post(node) for node in _edge_nodes(connection)],
        page_info=_parse_page_info(_as_dict(connection.get("pageInfo"))),
    )


@tool(args_schema=DeletePostInput)
@serialize_pydantic_return
async def delete_post(post_id: str, api_key: str) -> DeletePostOutput:
    """Delete a post by ID."""
    if not api_key or not api_key.strip():
        return DeletePostOutput(success=False, error=_EMPTY_KEY_ERROR)

    data, error = await _graphql(api_key, _DELETE_POST_MUTATION, {"input": {"id": post_id}})
    if error is not None:
        return DeletePostOutput(success=False, error=error)

    result = _as_dict(data.get("deletePost"))
    if result.get("__typename") != "DeletePostSuccess":
        return DeletePostOutput(
            success=False, error=_mutation_error(result, "Failed to delete the post")
        )
    return DeletePostOutput(success=True, deleted=True, id=result.get("id") or post_id)


@tool(args_schema=GetChannelsInput)
@serialize_pydantic_return
async def get_channels(organization_id: str, api_key: str) -> GetChannelsOutput:
    """List the social channels connected to an organization, including their channel IDs."""
    if not api_key or not api_key.strip():
        return GetChannelsOutput(success=False, error=_EMPTY_KEY_ERROR)

    variables: dict[str, Any] = {"input": {"organizationId": organization_id}}
    data, error = await _graphql(api_key, _GET_CHANNELS_QUERY, variables)
    if error is not None:
        return GetChannelsOutput(success=False, error=error)

    return GetChannelsOutput(
        success=True,
        channels=[
            _parse_channel(_as_dict(entry)) for entry in _as_list(data.get("channels"))
        ],
    )


@tool(args_schema=GetAccountInput)
@serialize_pydantic_return
async def get_account(api_key: str) -> GetAccountOutput:
    """Get the authenticated account, including its organizations and their IDs."""
    if not api_key or not api_key.strip():
        return GetAccountOutput(success=False, error=_EMPTY_KEY_ERROR)

    data, error = await _graphql(api_key, _GET_ACCOUNT_QUERY)
    if error is not None:
        return GetAccountOutput(success=False, error=error)

    account = _as_dict(data.get("account"))
    if not account:
        return GetAccountOutput(
            success=False, error="Account not found — check that the API key is valid."
        )
    return GetAccountOutput(success=True, account=_parse_account(account))


@tool(args_schema=CreateIdeaInput)
@serialize_pydantic_return
async def create_idea(
    organization_id: str,
    text: str,
    api_key: str,
    title: str | None = None,
    group_id: str | None = None,
) -> CreateIdeaOutput:
    """Save a content idea to an organization for later drafting and scheduling."""
    if not api_key or not api_key.strip():
        return CreateIdeaOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not text or not text.strip():
        return CreateIdeaOutput(success=False, error="text is required to create an idea.")

    content: dict[str, Any] = {"text": text}
    if title and title.strip():
        content["title"] = title.strip()
    idea_input: dict[str, Any] = {"organizationId": organization_id, "content": content}
    if group_id and group_id.strip():
        idea_input["group"] = {"groupId": group_id.strip()}

    data, error = await _graphql(api_key, _CREATE_IDEA_MUTATION, {"input": idea_input})
    if error is not None:
        return CreateIdeaOutput(success=False, error=error)

    result = _as_dict(data.get("createIdea"))
    typename = result.get("__typename")
    if typename == "Idea":
        node = result
    elif typename == "IdeaResponse":
        node = _as_dict(result.get("idea"))
    else:
        node = {}
    if not node.get("id"):
        return CreateIdeaOutput(
            success=False, error=_mutation_error(result, "Failed to create the idea")
        )
    return CreateIdeaOutput(success=True, idea=_parse_idea(node))


@tool(args_schema=GetIdeasInput)
@serialize_pydantic_return
async def get_ideas(
    organization_id: str,
    api_key: str,
    limit: int = _DEFAULT_LIMIT,
    after: str | None = None,
) -> GetIdeasOutput:
    """List content ideas saved in an organization."""
    if not api_key or not api_key.strip():
        return GetIdeasOutput(success=False, error=_EMPTY_KEY_ERROR)

    variables: dict[str, Any] = {
        "input": {"organizationId": organization_id},
        "first": max(1, limit),
        "after": after or None,
    }
    data, error = await _graphql(api_key, _GET_IDEAS_QUERY, variables)
    if error is not None:
        return GetIdeasOutput(success=False, error=error)

    connection = _as_dict(data.get("ideas"))
    return GetIdeasOutput(
        success=True,
        ideas=[_parse_idea(node) for node in _edge_nodes(connection)],
        page_info=_parse_page_info(_as_dict(connection.get("pageInfo"))),
    )


@tool(args_schema=GetIdeaGroupsInput)
@serialize_pydantic_return
async def get_idea_groups(organization_id: str, api_key: str) -> GetIdeaGroupsOutput:
    """List idea groups (board columns) in an organization, including their group IDs."""
    if not api_key or not api_key.strip():
        return GetIdeaGroupsOutput(success=False, error=_EMPTY_KEY_ERROR)

    variables: dict[str, Any] = {"input": {"organizationId": organization_id}}
    data, error = await _graphql(api_key, _GET_IDEA_GROUPS_QUERY, variables)
    if error is not None:
        return GetIdeaGroupsOutput(success=False, error=error)

    return GetIdeaGroupsOutput(
        success=True,
        idea_groups=[
            _parse_idea_group(_as_dict(entry)) for entry in _as_list(data.get("ideaGroups"))
        ],
    )
