"""Happy-path tests per action + a failure-path test for the
``{"error": {...}}`` envelope branch and an empty-credential test.

The YouTube Data API v3 passes its credential as a ``key=`` query
parameter and never raises on errors (it returns HTTP 200 with an error
envelope), so failures surface as ``success=False`` + ``error``.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.youtube import (
    TOOLS,
    channel_info,
    channel_playlists,
    channel_videos,
    comments,
    manifest,
    playlist_items,
    search,
    trending,
    video_categories,
    video_details,
)
from modulex_integrations.tools.youtube.outputs import (
    ChannelInfoOutput,
    ChannelPlaylistsOutput,
    ChannelVideosOutput,
    CommentsOutput,
    PlaylistItemsOutput,
    SearchOutput,
    TrendingOutput,
    VideoCategoriesOutput,
    VideoDetailsOutput,
)

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_9_actions(self) -> None:
        assert len(manifest.actions) == 9

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_logo(self) -> None:
        assert manifest.logo == "modulex:youtube"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {
                    "id": {"videoId": "vid123"},
                    "snippet": {
                        "title": "Intro to AI",
                        "description": "A primer.",
                        "thumbnails": {"default": {"url": "https://img/d.jpg"}},
                        "channelId": "UCabc",
                        "channelTitle": "AI Channel",
                        "publishedAt": "2025-01-01T00:00:00Z",
                        "liveBroadcastContent": "none",
                    },
                }
            ],
            "pageInfo": {"totalResults": 42},
            "nextPageToken": "TOKEN2",
        },
    )

    result_dict = await search.ainvoke(_args(query="ai"))
    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.items[0].video_id == "vid123"
    assert result.items[0].channel_title == "AI Channel"
    assert result.total_results == 42
    assert result.next_page_token == "TOKEN2"

    sent = httpx_mock.get_requests()[0]
    assert sent.url.params["key"] == _API_KEY
    assert sent.url.params["type"] == "video"


@pytest.mark.asyncio
async def test_trending(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {
                    "id": "trend1",
                    "snippet": {
                        "title": "Trending clip",
                        "thumbnails": {"high": {"url": "https://img/h.jpg"}},
                        "channelId": "UCx",
                        "channelTitle": "Popular",
                        "publishedAt": "2025-02-02T00:00:00Z",
                    },
                    "statistics": {
                        "viewCount": "1000",
                        "likeCount": "50",
                        "commentCount": "7",
                    },
                    "contentDetails": {"duration": "PT4M13S"},
                }
            ],
            "pageInfo": {"totalResults": 1},
        },
    )

    result_dict = await trending.ainvoke(_args(region_code="US"))
    assert isinstance(result_dict, dict)

    result = TrendingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.items[0].video_id == "trend1"
    assert result.items[0].view_count == 1000
    assert result.items[0].duration == "PT4M13S"


@pytest.mark.asyncio
async def test_video_details(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {
                    "id": "dQw4w9WgXcQ",
                    "snippet": {
                        "title": "A Video",
                        "description": "desc",
                        "channelId": "UCz",
                        "channelTitle": "Creator",
                        "publishedAt": "2009-10-25T00:00:00Z",
                        "thumbnails": {"high": {"url": "https://img/h.jpg"}},
                        "tags": ["music", "classic"],
                        "categoryId": "10",
                        "liveBroadcastContent": "none",
                    },
                    "statistics": {
                        "viewCount": "1500000000",
                        "likeCount": "15000000",
                        "commentCount": "2000000",
                        "favoriteCount": "0",
                    },
                    "contentDetails": {
                        "duration": "PT3M33S",
                        "definition": "hd",
                        "caption": "true",
                        "licensedContent": True,
                    },
                    "status": {"privacyStatus": "public"},
                }
            ]
        },
    )

    result_dict = await video_details.ainvoke(_args(video_id="dQw4w9WgXcQ"))
    assert isinstance(result_dict, dict)

    result = VideoDetailsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.video_id == "dQw4w9WgXcQ"
    assert result.view_count == 1500000000
    assert result.tags == ["music", "classic"]
    assert result.definition == "hd"
    assert result.is_live_content is False


@pytest.mark.asyncio
async def test_video_categories(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {"id": "1", "snippet": {"title": "Film & Animation", "assignable": True}},
                {"id": "10", "snippet": {"title": "Music", "assignable": True}},
                {"id": "99", "snippet": {"title": "Hidden", "assignable": False}},
            ]
        },
    )

    result_dict = await video_categories.ainvoke(_args(region_code="US"))
    assert isinstance(result_dict, dict)

    result = VideoCategoriesOutput.model_validate(result_dict)
    assert result.success is True
    # The non-assignable category is filtered out.
    assert result.total_results == 2
    assert {c.category_id for c in result.items} == {"1", "10"}


@pytest.mark.asyncio
async def test_channel_info(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {
                    "id": "UCchannel",
                    "snippet": {
                        "title": "My Channel",
                        "description": "About me",
                        "publishedAt": "2010-01-01T00:00:00Z",
                        "thumbnails": {"high": {"url": "https://img/h.jpg"}},
                        "customUrl": "@mychannel",
                        "country": "US",
                    },
                    "statistics": {
                        "subscriberCount": "12345",
                        "videoCount": "200",
                        "viewCount": "9999999",
                        "hiddenSubscriberCount": False,
                    },
                    "contentDetails": {"relatedPlaylists": {"uploads": "UUchannel"}},
                    "brandingSettings": {
                        "image": {"bannerExternalUrl": "https://img/banner.jpg"}
                    },
                }
            ]
        },
    )

    result_dict = await channel_info.ainvoke(_args(channel_id="UCchannel"))
    assert isinstance(result_dict, dict)

    result = ChannelInfoOutput.model_validate(result_dict)
    assert result.success is True
    assert result.channel_id == "UCchannel"
    assert result.subscriber_count == 12345
    assert result.uploads_playlist_id == "UUchannel"
    assert result.banner_image_url == "https://img/banner.jpg"


@pytest.mark.asyncio
async def test_channel_videos(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {
                    "id": {"videoId": "cv1"},
                    "snippet": {
                        "title": "Channel clip",
                        "description": "desc",
                        "thumbnails": {"medium": {"url": "https://img/m.jpg"}},
                        "publishedAt": "2025-03-03T00:00:00Z",
                        "channelTitle": "My Channel",
                    },
                }
            ],
            "pageInfo": {"totalResults": 1},
            "nextPageToken": "NEXT",
        },
    )

    result_dict = await channel_videos.ainvoke(_args(channel_id="UCchannel"))
    assert isinstance(result_dict, dict)

    result = ChannelVideosOutput.model_validate(result_dict)
    assert result.success is True
    assert result.items[0].video_id == "cv1"
    assert result.next_page_token == "NEXT"


@pytest.mark.asyncio
async def test_channel_playlists(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {
                    "id": "PLabc",
                    "snippet": {
                        "title": "Best Of",
                        "description": "compilation",
                        "thumbnails": {"medium": {"url": "https://img/m.jpg"}},
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "channelTitle": "My Channel",
                    },
                    "contentDetails": {"itemCount": 17},
                }
            ],
            "pageInfo": {"totalResults": 1},
        },
    )

    result_dict = await channel_playlists.ainvoke(_args(channel_id="UCchannel"))
    assert isinstance(result_dict, dict)

    result = ChannelPlaylistsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.items[0].playlist_id == "PLabc"
    assert result.items[0].item_count == 17


@pytest.mark.asyncio
async def test_playlist_items(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {
                    "snippet": {
                        "title": "Item one",
                        "description": "desc",
                        "thumbnails": {"medium": {"url": "https://img/m.jpg"}},
                        "publishedAt": "2024-05-05T00:00:00Z",
                        "channelTitle": "Owner",
                        "position": 0,
                        "resourceId": {"videoId": "snip-vid"},
                        "videoOwnerChannelId": "UCowner",
                        "videoOwnerChannelTitle": "Owner Channel",
                    },
                    "contentDetails": {"videoId": "pl-vid-1"},
                }
            ],
            "pageInfo": {"totalResults": 1},
        },
    )

    result_dict = await playlist_items.ainvoke(_args(playlist_id="PLabc"))
    assert isinstance(result_dict, dict)

    result = PlaylistItemsOutput.model_validate(result_dict)
    assert result.success is True
    # contentDetails.videoId takes precedence over resourceId.videoId.
    assert result.items[0].video_id == "pl-vid-1"
    assert result.items[0].position == 0
    assert result.items[0].video_owner_channel_title == "Owner Channel"


@pytest.mark.asyncio
async def test_comments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "items": [
                {
                    "id": "thread1",
                    "snippet": {
                        "totalReplyCount": 3,
                        "topLevelComment": {
                            "id": "comment1",
                            "snippet": {
                                "authorDisplayName": "Jane",
                                "authorChannelUrl": "https://youtube.com/jane",
                                "authorProfileImageUrl": "https://img/jane.jpg",
                                "textDisplay": "Great video!",
                                "textOriginal": "Great video!",
                                "likeCount": 12,
                                "publishedAt": "2025-04-04T00:00:00Z",
                                "updatedAt": "2025-04-04T00:00:00Z",
                            },
                        },
                    },
                }
            ],
            "pageInfo": {"totalResults": 1},
        },
    )

    result_dict = await comments.ainvoke(_args(video_id="dQw4w9WgXcQ"))
    assert isinstance(result_dict, dict)

    result = CommentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.items[0].comment_id == "comment1"
    assert result.items[0].author_display_name == "Jane"
    assert result.items[0].like_count == 12
    assert result.items[0].reply_count == 3


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_error_envelope(httpx_mock):  # type: ignore[no-untyped-def]
    """YouTube returns HTTP 200 with an ``error`` envelope on bad requests;
    the tool surfaces it as ``success=False`` + the upstream message."""
    httpx_mock.add_response(
        method="GET",
        json={"error": {"code": 403, "message": "The request cannot be completed."}},
    )

    result_dict = await search.ainvoke(_args(query="anything"))
    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "The request cannot be completed."


@pytest.mark.asyncio
async def test_video_details_not_found(httpx_mock):  # type: ignore[no-untyped-def]
    """An empty items array means the video does not exist."""
    httpx_mock.add_response(method="GET", json={"items": []})

    result_dict = await video_details.ainvoke(_args(video_id="missing"))
    assert isinstance(result_dict, dict)

    result = VideoDetailsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Video not found"


@pytest.mark.asyncio
async def test_search_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await search.ainvoke({"query": "x", "api_key": ""})
    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
