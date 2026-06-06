"""Notion integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _page_size_param() -> ParameterDef:
    return ParameterDef(
        type="integer", description="Number of results (max 100)", default=100
    )


def _start_cursor_param() -> ParameterDef:
    return ParameterDef(type="string", description="Pagination cursor")


def _test_endpoint(placeholder: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://api.notion.com/v1/users/me",
        method="GET",
        headers={
            "Authorization": f"Bearer {{{placeholder}}}",
            "Notion-Version": "2022-06-28",
        },
        success_indicators=SuccessIndicators(status_codes=[200]),
        cost_level="free",
        description="Validates token by fetching the bot user",
    )


manifest = IntegrationManifest(
    name="notion",
    display_name="Notion",
    description=(
        "Notion workspace integration: pages, databases, blocks, users, "
        "comments, and search."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:notion-icon",
    app_url="https://www.notion.so",
    categories=[
        "Productivity & Collaboration",
        "Productivity",
        "Knowledge Management",
        "Documentation",
    ],
    actions=[
        ActionDefinition(
            name="search",
            description="Search across Notion pages and databases",
            parameters={
                "query": ParameterDef(type="string", description="Search query text"),
                "filter": ParameterDef(
                    type="object",
                    description="Filter (e.g. {'property': 'object', 'value': 'page'})",
                ),
                "sort": ParameterDef(
                    type="object",
                    description="Sort options",
                ),
                "start_cursor": _start_cursor_param(),
                "page_size": _page_size_param(),
            },
        ),
        ActionDefinition(
            name="create_page",
            description="Create a new page in a database or under a parent page",
            parameters={
                "parent_type": ParameterDef(
                    type="string",
                    description="'database' or 'page'",
                    required=True,
                ),
                "parent_id": ParameterDef(
                    type="string",
                    description="Parent page/database ID",
                    required=True,
                ),
                "title": ParameterDef(type="string", description="Page title"),
                "content": ParameterDef(
                    type="string",
                    description="Markdown content (converted to paragraph blocks)",
                ),
                "children": ParameterDef(
                    type="array",
                    description="Direct Notion block array (overrides content)",
                ),
                "properties": ParameterDef(
                    type="object",
                    description="Database properties (required for database parents)",
                ),
            },
        ),
        ActionDefinition(
            name="get_page",
            description="Retrieve a Notion page (optionally with child blocks)",
            parameters={
                "page_id": ParameterDef(
                    type="string",
                    description="Page ID to retrieve",
                    required=True,
                ),
                "include_content": ParameterDef(
                    type="boolean",
                    description="Include page child blocks (N+1 fetch)",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_page",
            description="Update page properties / archive status",
            parameters={
                "page_id": ParameterDef(
                    type="string", description="Page ID", required=True
                ),
                "title": ParameterDef(type="string", description="New title"),
                "properties": ParameterDef(
                    type="object", description="Updated properties"
                ),
                "archived": ParameterDef(
                    type="boolean", description="Archive (true) / unarchive (false)"
                ),
            },
        ),
        ActionDefinition(
            name="query_database",
            description="Query a database with filters and sorts",
            parameters={
                "database_id": ParameterDef(
                    type="string", description="Database ID", required=True
                ),
                "filter": ParameterDef(
                    type="object", description="Filter conditions"
                ),
                "sorts": ParameterDef(type="array", description="Sort options"),
                "start_cursor": _start_cursor_param(),
                "page_size": _page_size_param(),
            },
        ),
        ActionDefinition(
            name="get_database",
            description="Retrieve database metadata + property schema",
            parameters={
                "database_id": ParameterDef(
                    type="string", description="Database ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="create_database",
            description="Create a new database under a parent page",
            parameters={
                "parent_page_id": ParameterDef(
                    type="string",
                    description="Parent page ID",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Database title",
                    required=True,
                ),
                "properties": ParameterDef(
                    type="object",
                    description="Property schema definitions",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_database",
            description="Update database title / description / schema",
            parameters={
                "database_id": ParameterDef(
                    type="string", description="Database ID", required=True
                ),
                "title": ParameterDef(type="string", description="New title"),
                "description": ParameterDef(
                    type="string", description="New description"
                ),
                "properties": ParameterDef(
                    type="object", description="Updated property schema"
                ),
            },
        ),
        ActionDefinition(
            name="create_database_item",
            description="Create a new page inside a database",
            parameters={
                "database_id": ParameterDef(
                    type="string", description="Database ID", required=True
                ),
                "properties": ParameterDef(
                    type="object",
                    description="Item properties matching database schema",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_block",
            description="Retrieve a single block by ID",
            parameters={
                "block_id": ParameterDef(
                    type="string", description="Block ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="get_block_children",
            description="Retrieve a block's / page's child blocks",
            parameters={
                "block_id": ParameterDef(
                    type="string",
                    description="Parent block or page ID",
                    required=True,
                ),
                "start_cursor": _start_cursor_param(),
                "page_size": _page_size_param(),
            },
        ),
        ActionDefinition(
            name="append_blocks",
            description="Append blocks to a page or block",
            parameters={
                "block_id": ParameterDef(
                    type="string",
                    description="Block / page ID to append into",
                    required=True,
                ),
                "children": ParameterDef(
                    type="array",
                    description="Notion block objects to append",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_block",
            description="Update an existing block",
            parameters={
                "block_id": ParameterDef(
                    type="string", description="Block ID", required=True
                ),
                "block": ParameterDef(
                    type="object",
                    description="Block object with updated content",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_block",
            description="Archive (delete) a block",
            parameters={
                "block_id": ParameterDef(
                    type="string", description="Block ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_users",
            description="List all workspace users (people + bots)",
            parameters={
                "start_cursor": _start_cursor_param(),
                "page_size": _page_size_param(),
            },
        ),
        ActionDefinition(
            name="get_user",
            description="Retrieve a specific user by ID",
            parameters={
                "user_id": ParameterDef(
                    type="string", description="User ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="get_bot_user",
            description="Retrieve the integration's bot user (GET /users/me)",
            parameters={},
        ),
        ActionDefinition(
            name="create_comment",
            description="Create a comment on a page or discussion",
            parameters={
                "rich_text": ParameterDef(
                    type="array",
                    description="Rich text array for the comment body",
                    required=True,
                ),
                "page_id": ParameterDef(
                    type="string",
                    description="Page ID (use this for new comments)",
                ),
                "discussion_id": ParameterDef(
                    type="string",
                    description="Discussion ID (use this for replies)",
                ),
            },
        ),
        ActionDefinition(
            name="get_comments",
            description="Retrieve comments on a block / page",
            parameters={
                "block_id": ParameterDef(
                    type="string",
                    description="Block / page ID",
                    required=True,
                ),
                "start_cursor": _start_cursor_param(),
                "page_size": _page_size_param(),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 (Recommended)",
            description="Connect using Notion OAuth — most secure option",
            setup_environment_variables=[
                EnvVar(
                    name="NOTION_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Notion OAuth integration Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://www.notion.so/my-integrations",
                ),
                EnvVar(
                    name="NOTION_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Notion OAuth integration Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://api.notion.com/v1/oauth/authorize",
                token_url="https://api.notion.com/v1/oauth/token",
                scopes=[],
                token_auth_method="basic",
            ),
            test_endpoint=_test_endpoint("access_token"),
        ),
        BearerTokenAuthSchema(
            display_name="Internal Integration",
            description="Connect using a Notion Internal Integration Token",
            setup_environment_variables=[
                EnvVar(
                    name="NOTION_ACCESS_TOKEN",
                    display_name="Internal Integration Token",
                    description="Notion Internal Integration secret",
                    required=True,
                    sensitive=True,
                    sample_format="secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.notion.so/my-integrations",
                ),
            ],
            test_endpoint=_test_endpoint("bearer_token"),
        ),
    ],
)
