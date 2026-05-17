"""Hacker News LangChain ``@tool`` functions.

Public integration (no API key). ``api_key`` is accepted on every input
schema for signature uniformity with the rest of the credential system
but is never used. Two backends are involved:

- ``hnrss.org`` for keyword search (RSS-XML feeds).
- ``hacker-news.firebaseio.com`` for the official JSON API.
"""
from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.hackernews.outputs import (
    GetItemOutput,
    GetStoriesOutput,
    GetUserOutput,
    HNRSSItem,
    SearchOutput,
)

__all__ = [
    "get_ask_stories",
    "get_best_stories",
    "get_item",
    "get_job_stories",
    "get_new_stories",
    "get_show_stories",
    "get_top_stories",
    "get_user",
    "search_comments",
    "search_stories",
]

_HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
_HNRSS_BASE = "https://hnrss.org"
_TIMEOUT = 30.0
_DC_CREATOR = "{http://purl.org/dc/elements/1.1/}creator"


async def _fetch_text(url: str) -> str:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def _fetch_json(url: str) -> Any:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def _parse_rss_items(xml_content: str, max_results: int) -> list[HNRSSItem]:
    items: list[HNRSSItem] = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return items

    channel = root.find("channel")
    if channel is None:
        return items

    for elem in channel.findall("item")[:max_results]:
        creator = elem.find(_DC_CREATOR)
        comments_elem = elem.find("comments")
        items.append(
            HNRSSItem(
                title=elem.findtext("title", ""),
                link=elem.findtext("link", ""),
                description=elem.findtext("description", ""),
                pub_date=elem.findtext("pubDate", ""),
                guid=elem.findtext("guid", ""),
                author=creator.text if creator is not None else None,
                comments_url=comments_elem.text if comments_elem is not None else None,
            )
        )
    return items


async def _fetch_story_details(story_ids: list[int], limit: int) -> list[dict[str, Any]]:
    async def _one(item_id: int) -> dict[str, Any] | None:
        try:
            result = await _fetch_json(f"{_HN_API_BASE}/item/{item_id}.json")
        except Exception:
            return None
        return result if isinstance(result, dict) else None

    results = await asyncio.gather(*[_one(i) for i in story_ids[:limit]])
    return [r for r in results if r is not None]


class _SearchStoriesInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    keyword: str = Field(default="", description="Keyword to search for")
    max_results: int = Field(default=10, description="Maximum number of stories (1-50)")
    points: int | None = Field(default=None, description="Minimum points threshold")
    comments: int | None = Field(default=None, description="Minimum comments threshold")


class _SearchCommentsInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    keyword: str = Field(default="", description="Keyword to search for")
    max_results: int = Field(default=10, description="Maximum number of comments (1-50)")


class _StoriesInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    limit: int = Field(default=10, description="Number of stories (1-100)")
    fetch_details: bool = Field(default=True, description="Fetch full details vs IDs only")


class _GetItemInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    item_id: int = Field(description="The ID of the item to fetch")


class _GetUserInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    username: str = Field(description="The HN username to look up")


@tool(args_schema=_SearchStoriesInput)
@serialize_pydantic_return
async def search_stories(
    keyword: str = "",
    max_results: int = 10,
    points: int | None = None,
    comments: int | None = None,
    api_key: str | None = None,
) -> SearchOutput:
    """Search Hacker News stories by keyword via hnrss.org."""
    params: list[str] = []
    if keyword:
        params.append(f"q={keyword}")
    if points:
        params.append(f"points={points}")
    if comments:
        params.append(f"comments={comments}")
    params.append(f"count={min(max_results, 50)}")
    url = f"{_HNRSS_BASE}/newest?{'&'.join(params)}"

    try:
        xml_content = await _fetch_text(url)
    except Exception as exc:
        return SearchOutput(
            success=False, error=f"Failed to search stories: {exc}", keyword=keyword
        )

    items = _parse_rss_items(xml_content, max_results)
    return SearchOutput(
        success=True, stories=items, count=len(items), keyword=keyword
    )


@tool(args_schema=_SearchCommentsInput)
@serialize_pydantic_return
async def search_comments(
    keyword: str = "",
    max_results: int = 10,
    api_key: str | None = None,
) -> SearchOutput:
    """Search Hacker News comments by keyword via hnrss.org."""
    params: list[str] = [f"count={min(max_results, 50)}"]
    if keyword:
        params.append(f"q={keyword}")
    url = f"{_HNRSS_BASE}/newcomments?{'&'.join(params)}"

    try:
        xml_content = await _fetch_text(url)
    except Exception as exc:
        return SearchOutput(
            success=False, error=f"Failed to search comments: {exc}", keyword=keyword
        )

    items = _parse_rss_items(xml_content, max_results)
    return SearchOutput(
        success=True, comments=items, count=len(items), keyword=keyword
    )


async def _fetch_stories_helper(
    endpoint: str, kind: str, limit: int, fetch_details: bool
) -> GetStoriesOutput:
    try:
        ids = await _fetch_json(f"{_HN_API_BASE}/{endpoint}")
    except Exception as exc:
        return GetStoriesOutput(success=False, error=f"Failed to get {kind} stories: {exc}")

    if not isinstance(ids, list):
        return GetStoriesOutput(
            success=False, error=f"Unexpected response shape for {kind} stories"
        )

    if fetch_details:
        stories = await _fetch_story_details(ids, limit)
        return GetStoriesOutput(
            success=True, stories=stories, count=len(stories), type=kind
        )

    trimmed = list(ids[:limit])
    return GetStoriesOutput(
        success=True, story_ids=trimmed, count=len(trimmed), type=kind
    )


@tool(args_schema=_StoriesInput)
@serialize_pydantic_return
async def get_top_stories(
    limit: int = 10, fetch_details: bool = True, api_key: str | None = None
) -> GetStoriesOutput:
    """Get the current top stories from Hacker News."""
    return await _fetch_stories_helper("topstories.json", "top", limit, fetch_details)


@tool(args_schema=_StoriesInput)
@serialize_pydantic_return
async def get_new_stories(
    limit: int = 10, fetch_details: bool = True, api_key: str | None = None
) -> GetStoriesOutput:
    """Get the newest stories from Hacker News."""
    return await _fetch_stories_helper("newstories.json", "new", limit, fetch_details)


@tool(args_schema=_StoriesInput)
@serialize_pydantic_return
async def get_best_stories(
    limit: int = 10, fetch_details: bool = True, api_key: str | None = None
) -> GetStoriesOutput:
    """Get the highest-ranked stories from Hacker News."""
    return await _fetch_stories_helper("beststories.json", "best", limit, fetch_details)


@tool(args_schema=_StoriesInput)
@serialize_pydantic_return
async def get_ask_stories(
    limit: int = 10, fetch_details: bool = True, api_key: str | None = None
) -> GetStoriesOutput:
    """Get the latest Ask HN stories."""
    return await _fetch_stories_helper("askstories.json", "ask", limit, fetch_details)


@tool(args_schema=_StoriesInput)
@serialize_pydantic_return
async def get_show_stories(
    limit: int = 10, fetch_details: bool = True, api_key: str | None = None
) -> GetStoriesOutput:
    """Get the latest Show HN stories."""
    return await _fetch_stories_helper("showstories.json", "show", limit, fetch_details)


@tool(args_schema=_StoriesInput)
@serialize_pydantic_return
async def get_job_stories(
    limit: int = 10, fetch_details: bool = True, api_key: str | None = None
) -> GetStoriesOutput:
    """Get the latest job postings from Hacker News."""
    return await _fetch_stories_helper("jobstories.json", "job", limit, fetch_details)


@tool(args_schema=_GetItemInput)
@serialize_pydantic_return
async def get_item(item_id: int, api_key: str | None = None) -> GetItemOutput:
    """Get details of a specific Hacker News item by ID."""
    try:
        item = await _fetch_json(f"{_HN_API_BASE}/item/{item_id}.json")
    except Exception as exc:
        return GetItemOutput(success=False, error=f"Failed to get item: {exc}")

    if item is None:
        return GetItemOutput(success=False, error=f"Item {item_id} not found")

    return GetItemOutput(success=True, item=item, item_id=item_id)


@tool(args_schema=_GetUserInput)
@serialize_pydantic_return
async def get_user(username: str, api_key: str | None = None) -> GetUserOutput:
    """Get a Hacker News user's profile by username."""
    try:
        user = await _fetch_json(f"{_HN_API_BASE}/user/{username}.json")
    except Exception as exc:
        return GetUserOutput(success=False, error=f"Failed to get user: {exc}")

    if user is None:
        return GetUserOutput(success=False, error=f"User '{username}' not found")

    return GetUserOutput(success=True, user=user, username=username)
