"""Tests for the Hacker News integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.hackernews import (
    TOOLS,
    get_best_stories,
    get_item,
    get_job_stories,
    get_top_stories,
    get_user,
    manifest,
    search_comments,
    search_stories,
)
from modulex_integrations.tools.hackernews.outputs import (
    GetItemOutput,
    GetStoriesOutput,
    GetUserOutput,
    SearchOutput,
)

HN = "https://hacker-news.firebaseio.com/v0"
RSS = "https://hnrss.org"


_RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>HN</title>
    <item>
      <title>Some Rust thing</title>
      <link>https://example.com/rust</link>
      <description>desc</description>
      <pubDate>Fri, 16 May 2026 00:00:00 +0000</pubDate>
      <guid>https://news.ycombinator.com/item?id=1</guid>
      <dc:creator>alice</dc:creator>
      <comments>https://news.ycombinator.com/item?id=1</comments>
    </item>
    <item>
      <title>Show HN: thing two</title>
      <link>https://example.com/thing</link>
      <description>desc2</description>
      <pubDate>Fri, 16 May 2026 01:00:00 +0000</pubDate>
      <guid>https://news.ycombinator.com/item?id=2</guid>
      <dc:creator>bob</dc:creator>
      <comments>https://news.ycombinator.com/item?id=2</comments>
    </item>
  </channel>
</rss>
"""


class TestManifest:
    def test_manifest_exposes_ten_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_modulex_key_auth_with_reachability_test(self) -> None:
        auth = manifest.auth_schemas[0]
        assert auth.auth_type == "modulex_key"
        # Public API — reachability check against the public Firebase
        # endpoint so the credential-save flow has something to test.
        assert auth.test_endpoint is not None
        assert "hacker-news.firebaseio.com" in auth.test_endpoint.url


@pytest.mark.asyncio
async def test_search_stories(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{RSS}/newest?q=rust&count=5",
        text=_RSS_SAMPLE,
    )

    result_dict = await search_stories.ainvoke({"keyword": "rust", "max_results": 5})
    assert isinstance(result_dict, dict)
    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 2
    assert result.stories[0].title == "Some Rust thing"
    assert result.stories[0].author == "alice"


@pytest.mark.asyncio
async def test_search_comments(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{RSS}/newcomments?count=10&q=ai",
        text=_RSS_SAMPLE,
    )

    result_dict = await search_comments.ainvoke({"keyword": "ai"})
    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 2
    assert result.comments[0].title == "Some Rust thing"


@pytest.mark.asyncio
async def test_get_top_stories_fetch_details(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{HN}/topstories.json", json=[101, 102, 103]
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{HN}/item/101.json",
        json={"id": 101, "title": "Story 1", "by": "alice"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{HN}/item/102.json",
        json={"id": 102, "title": "Story 2", "by": "bob"},
    )

    result_dict = await get_top_stories.ainvoke({"limit": 2, "fetch_details": True})
    result = GetStoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.type == "top"
    assert result.count == 2
    assert {s["id"] for s in result.stories} == {101, 102}


@pytest.mark.asyncio
async def test_get_best_stories_ids_only(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{HN}/beststories.json", json=[1, 2, 3, 4]
    )
    result_dict = await get_best_stories.ainvoke({"limit": 3, "fetch_details": False})
    result = GetStoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.story_ids == [1, 2, 3]
    assert result.count == 3
    assert result.stories == []


@pytest.mark.asyncio
async def test_get_job_stories(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{HN}/jobstories.json", json=[7])
    httpx_mock.add_response(
        method="GET",
        url=f"{HN}/item/7.json",
        json={"id": 7, "title": "Hiring", "type": "job"},
    )
    result_dict = await get_job_stories.ainvoke({"limit": 5})
    result = GetStoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.type == "job"
    assert result.stories[0]["id"] == 7


@pytest.mark.asyncio
async def test_get_item_not_found(httpx_mock: Any) -> None:
    # Firebase returns the literal JSON value `null` for missing items,
    # not an empty body.
    httpx_mock.add_response(method="GET", url=f"{HN}/item/999.json", text="null")
    result_dict = await get_item.ainvoke({"item_id": 999})
    result = GetItemOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "999" in result.error


@pytest.mark.asyncio
async def test_get_item_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{HN}/item/42.json",
        json={"id": 42, "title": "The answer", "by": "alice"},
    )
    result_dict = await get_item.ainvoke({"item_id": 42})
    result = GetItemOutput.model_validate(result_dict)
    assert result.success is True
    assert result.item is not None
    assert result.item["title"] == "The answer"


@pytest.mark.asyncio
async def test_get_user(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{HN}/user/alice.json",
        json={"id": "alice", "karma": 42, "about": "hi"},
    )
    result_dict = await get_user.ainvoke({"username": "alice"})
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None and result.user["karma"] == 42


@pytest.mark.asyncio
async def test_get_user_not_found(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{HN}/user/ghost.json", text="null"
    )
    result_dict = await get_user.ainvoke({"username": "ghost"})
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "ghost" in result.error


@pytest.mark.asyncio
async def test_search_handles_upstream_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{RSS}/newest?count=10", status_code=503, text="boom"
    )
    result_dict = await search_stories.ainvoke({})
    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "Failed to search" in result.error
