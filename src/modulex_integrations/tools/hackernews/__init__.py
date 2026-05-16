"""Hacker News integration."""
from modulex_integrations.tools.hackernews.manifest import manifest
from modulex_integrations.tools.hackernews.tools import (
    get_ask_stories,
    get_best_stories,
    get_item,
    get_job_stories,
    get_new_stories,
    get_show_stories,
    get_top_stories,
    get_user,
    search_comments,
    search_stories,
)

TOOLS = (
    search_stories,
    search_comments,
    get_top_stories,
    get_new_stories,
    get_best_stories,
    get_ask_stories,
    get_show_stories,
    get_job_stories,
    get_item,
    get_user,
)

__all__ = [
    "TOOLS",
    "get_ask_stories",
    "get_best_stories",
    "get_item",
    "get_job_stories",
    "get_new_stories",
    "get_show_stories",
    "get_top_stories",
    "get_user",
    "manifest",
    "search_comments",
    "search_stories",
]
