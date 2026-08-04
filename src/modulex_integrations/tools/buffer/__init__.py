"""Buffer integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.buffer.manifest import manifest
from modulex_integrations.tools.buffer.tools import (
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
)

TOOLS = (
    create_post,
    edit_post,
    get_post,
    get_posts,
    delete_post,
    get_channels,
    get_account,
    create_idea,
    get_ideas,
    get_idea_groups,
)

__all__ = [
    "TOOLS",
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
    "manifest",
]
