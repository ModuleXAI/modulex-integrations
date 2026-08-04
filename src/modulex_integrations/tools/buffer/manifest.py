"""Buffer integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_ORGANIZATION_ID = ParameterDef(
    type="string",
    description="Buffer organization ID (find it with the get_account action)",
    required=True,
)

_MEDIA_PARAMS = {
    "media_url": ParameterDef(
        type="string",
        description=(
            "Public http(s) URL of an image or video to attach. Buffer downloads the "
            "media itself, so the URL must stay reachable until the post publishes"
        ),
    ),
    "media_type": ParameterDef(
        type="string",
        description="Attachment type: 'auto' (detect from the URL), 'image', or 'video'",
        default="auto",
    ),
    "media_alt_text": ParameterDef(
        type="string",
        description="Alt text for an attached image (ignored for video attachments)",
    ),
}


manifest = IntegrationManifest(
    name="buffer",
    display_name="Buffer",
    description=(
        "Create, schedule, edit, and delete posts across connected social channels "
        "(Instagram, LinkedIn, X, Facebook, TikTok, and more), attach images or "
        "videos, browse channels, and capture content ideas using the Buffer API"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:buffer-themed",
    app_url="https://buffer.com",
    categories=["Social Media", "Marketing & Advertising", "Scheduling & Events"],
    actions=[
        ActionDefinition(
            name="create_post",
            description=(
                "Create a post for a channel — add it to the queue, share it immediately, "
                "schedule it for a specific time, or save it as a draft, optionally with "
                "an image or video attachment"
            ),
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description=(
                        "ID of the channel to create the post for (find it with the "
                        "get_channels action)"
                    ),
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text content of the post (required unless media is attached)",
                ),
                "mode": ParameterDef(
                    type="string",
                    description=(
                        "How to share the post: 'addToQueue', 'shareNext', 'shareNow', or "
                        "'customScheduled' (requires due_at)"
                    ),
                    default="addToQueue",
                ),
                "scheduling_type": ParameterDef(
                    type="string",
                    description=(
                        "How the post publishes: 'automatic' (Buffer publishes it) or "
                        "'notification' (a mobile reminder is sent instead)"
                    ),
                    default="automatic",
                ),
                "due_at": ParameterDef(
                    type="string",
                    description=(
                        "Publish time as an ISO 8601 timestamp, e.g. 2026-08-01T15:00:00Z "
                        "(required when mode is 'customScheduled')"
                    ),
                ),
                "save_to_draft": ParameterDef(
                    type="boolean",
                    description="Save the post as a draft instead of scheduling it",
                ),
                **_MEDIA_PARAMS,
            },
        ),
        ActionDefinition(
            name="edit_post",
            description=(
                "Edit an existing post — update its text, schedule, or media. Attaching "
                "new media replaces the existing attachments"
            ),
            parameters={
                "post_id": ParameterDef(
                    type="string",
                    description="ID of the post to edit",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="New text content of the post (omit to keep the current text)",
                ),
                "mode": ParameterDef(
                    type="string",
                    description=(
                        "New share mode: 'addToQueue', 'shareNext', 'shareNow', or "
                        "'customScheduled' (requires due_at). Omit to make no scheduling change"
                    ),
                ),
                "scheduling_type": ParameterDef(
                    type="string",
                    description=(
                        "How the post publishes: 'automatic' (Buffer publishes it) or "
                        "'notification' (a mobile reminder is sent instead). Buffer requires "
                        "this on every edit, so pass 'notification' when editing a post that "
                        "already publishes by notification"
                    ),
                    default="automatic",
                ),
                "due_at": ParameterDef(
                    type="string",
                    description=(
                        "New publish time as an ISO 8601 timestamp (required when mode is "
                        "'customScheduled')"
                    ),
                ),
                "save_to_draft": ParameterDef(
                    type="boolean",
                    description="Save the post as a draft instead of keeping it scheduled",
                ),
                **_MEDIA_PARAMS,
            },
        ),
        ActionDefinition(
            name="get_post",
            description="Get a single post by ID, including its status, schedule, and media",
            parameters={
                "post_id": ParameterDef(
                    type="string",
                    description="ID of the post to fetch",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_posts",
            description=(
                "List posts in an organization, optionally filtered by channel and status "
                "(draft, needs_approval, scheduled, sending, sent, error)"
            ),
            parameters={
                "organization_id": _ORGANIZATION_ID,
                "channel_ids": ParameterDef(
                    type="array",
                    description="Channel IDs to filter by",
                ),
                "status": ParameterDef(
                    type="array",
                    description=(
                        "Statuses to filter by: draft, needs_approval, scheduled, sending, "
                        "sent, error"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of posts to return",
                    default=20,
                ),
                "after": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous page (page_info.end_cursor)",
                ),
                "sort_by": ParameterDef(
                    type="string",
                    description="Field to sort by: 'dueAt' or 'createdAt'",
                    default="dueAt",
                ),
                "sort_direction": ParameterDef(
                    type="string",
                    description="Sort direction: 'asc' or 'desc'",
                    default="asc",
                ),
            },
        ),
        ActionDefinition(
            name="delete_post",
            description="Delete a post by ID",
            parameters={
                "post_id": ParameterDef(
                    type="string",
                    description="ID of the post to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_channels",
            description=(
                "List the social media channels connected to an organization, including "
                "the channel IDs needed to create posts"
            ),
            parameters={"organization_id": _ORGANIZATION_ID},
        ),
        ActionDefinition(
            name="get_account",
            description=(
                "Get the authenticated account, including its organizations and their IDs "
                "(needed for channel, post, and idea operations)"
            ),
            parameters={},
        ),
        ActionDefinition(
            name="create_idea",
            description="Save a content idea to an organization for later drafting and scheduling",
            parameters={
                "organization_id": _ORGANIZATION_ID,
                "text": ParameterDef(
                    type="string",
                    description="Text content of the idea",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Optional title for the idea",
                ),
                "group_id": ParameterDef(
                    type="string",
                    description=(
                        "Optional idea group (board column) to place the idea in (find it "
                        "with the get_idea_groups action)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_ideas",
            description="List content ideas saved in an organization",
            parameters={
                "organization_id": _ORGANIZATION_ID,
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of ideas to return",
                    default=20,
                ),
                "after": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous page (page_info.end_cursor)",
                ),
            },
        ),
        ActionDefinition(
            name="get_idea_groups",
            description=(
                "List idea groups (board columns) in an organization, including the group "
                "IDs used when creating ideas"
            ),
            parameters={"organization_id": _ORGANIZATION_ID},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Buffer API key",
            setup_instructions=[
                "Sign in to Buffer at https://publish.buffer.com",
                "Open API settings at https://publish.buffer.com/settings/api",
                "Create a new API key (it acts on your own Buffer account's data)",
                "Copy the key and paste it below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="BUFFER_API_KEY",
                    display_name="Buffer API Key",
                    description="Your Buffer API key from Buffer's API settings page",
                    required=True,
                    sensitive=True,
                    about_url="https://publish.buffer.com/settings/api",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.buffer.com",
                method="POST",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                body={"query": "query TestCredential { account { id } }"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data.account.id"],
                ),
                cost_level="free",
                description="Validates the API key by reading the authenticated account ID",
            ),
        ),
    ],
)
