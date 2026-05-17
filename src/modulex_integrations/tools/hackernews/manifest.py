"""Hacker News integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    IntegrationManifest,
    ModulexKeyAuthSchema,
    ParameterDef,
)

__all__ = ["manifest"]


def _stories_params() -> dict[str, ParameterDef]:
    return {
        "limit": ParameterDef(
            type="integer",
            description="Number of stories to return (1-100)",
            default=10,
        ),
        "fetch_details": ParameterDef(
            type="boolean",
            description="Whether to fetch full story details or just IDs",
            default=True,
        ),
    }


manifest = IntegrationManifest(
    name="hackernews",
    display_name="Hacker News",
    description=(
        "Access Hacker News content including top stories, new posts, "
        "Ask HN, Show HN, job postings, and search functionality for "
        "stories and comments."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:hackernews",
    app_url="https://news.ycombinator.com",
    categories=["news", "social", "technology", "community"],
    actions=[
        ActionDefinition(
            name="search_stories",
            description=(
                "Search Hacker News stories by keyword. Returns matching "
                "stories with titles, links, and metadata."
            ),
            parameters={
                "keyword": ParameterDef(
                    type="string",
                    description=(
                        "Keyword to search for in story titles. Leave empty "
                        "to get all new stories."
                    ),
                    default="",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of stories to return (1-50)",
                    default=10,
                ),
                "points": ParameterDef(
                    type="integer",
                    description="Minimum points threshold for stories",
                ),
                "comments": ParameterDef(
                    type="integer",
                    description="Minimum comments threshold for stories",
                ),
            },
        ),
        ActionDefinition(
            name="search_comments",
            description=(
                "Search Hacker News comments by keyword. Find discussions "
                "mentioning specific topics."
            ),
            parameters={
                "keyword": ParameterDef(
                    type="string",
                    description=(
                        "Keyword to search for in comments. Leave empty to "
                        "get all new comments."
                    ),
                    default="",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of comments to return (1-50)",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="get_top_stories",
            description="Get the current top stories from the Hacker News front page.",
            parameters=_stories_params(),
        ),
        ActionDefinition(
            name="get_new_stories",
            description="Get the newest stories submitted to Hacker News.",
            parameters=_stories_params(),
        ),
        ActionDefinition(
            name="get_best_stories",
            description="Get the highest-ranked stories from Hacker News.",
            parameters=_stories_params(),
        ),
        ActionDefinition(
            name="get_ask_stories",
            description="Get 'Ask HN' stories where users ask questions of the community.",
            parameters=_stories_params(),
        ),
        ActionDefinition(
            name="get_show_stories",
            description="Get 'Show HN' stories where users showcase projects and creations.",
            parameters=_stories_params(),
        ),
        ActionDefinition(
            name="get_job_stories",
            description="Get job postings from Hacker News.",
            parameters=_stories_params(),
        ),
        ActionDefinition(
            name="get_item",
            description=(
                "Get details of a specific Hacker News item by ID "
                "(story, comment, poll, etc.)."
            ),
            parameters={
                "item_id": ParameterDef(
                    type="integer",
                    description="The ID of the item to fetch",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_user",
            description=(
                "Get a Hacker News user's profile including karma, about "
                "text, and submitted items."
            ),
            parameters={
                "username": ParameterDef(
                    type="string",
                    description="The HN username to look up",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ModulexKeyAuthSchema(
            display_name="ModuleX Managed Key",
            description=(
                "Use ModuleX's managed access (Hacker News API is public, "
                "no authentication required)"
            ),
            # test_endpoint omitted — no credential to validate (public API).
        ),
    ],
)
