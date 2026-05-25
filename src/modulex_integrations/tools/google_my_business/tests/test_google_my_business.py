"""Happy-path tests for every google_my_business @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_my_business import (
    TOOLS,
    create_post,
    create_update_reply_to_review,
    get_reviews_multiple_locations,
    get_specific_review,
    list_all_reviews,
    list_posts,
    manifest,
)
from modulex_integrations.tools.google_my_business.outputs import (
    CreatePostOutput,
    CreateUpdateReplyToReviewOutput,
    GetReviewsMultipleLocationsOutput,
    GetSpecificReviewOutput,
    ListAllReviewsOutput,
    ListPostsOutput,
)

API = "https://mybusiness.googleapis.com/v4"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_post(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/accounts/123/locations/456/localPosts",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "name": "accounts/123/locations/456/localPosts/789",
            "summary": "Hello world",
            "topicType": "STANDARD",
            "state": "LIVE",
            "createTime": "2024-01-01T00:00:00Z",
            "updateTime": "2024-01-01T00:00:00Z",
        },
    )

    result_dict = await create_post.ainvoke(
        _args(account="123", location="456", topic_type="STANDARD", summary="Hello world")
    )

    assert isinstance(result_dict, dict)
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is True
    assert result.post is not None
    assert result.post.summary == "Hello world"


@pytest.mark.asyncio
async def test_create_update_reply_to_review(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/accounts/123/locations/456/reviews/789/reply",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "comment": "Thank you for your review!",
            "updateTime": "2024-01-01T00:00:00Z",
        },
    )

    result_dict = await create_update_reply_to_review.ainvoke(
        _args(account="123", location="456", review="789", comment="Thank you for your review!")
    )

    assert isinstance(result_dict, dict)
    result = CreateUpdateReplyToReviewOutput.model_validate(result_dict)
    assert result.success is True
    assert result.comment == "Thank you for your review!"


@pytest.mark.asyncio
async def test_get_reviews_multiple_locations(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/accounts/123/locations:batchGetReviews",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "locationReviews": [
                {
                    "locationName": "accounts/123/locations/456",
                    "reviews": [
                        {
                            "name": "accounts/123/locations/456/reviews/r1",
                            "reviewId": "r1",
                            "starRating": "FIVE",
                            "comment": "Great place!",
                            "createTime": "2024-01-01T00:00:00Z",
                        }
                    ],
                }
            ],
        },
    )

    result_dict = await get_reviews_multiple_locations.ainvoke(
        _args(account="123", location_names=["456"])
    )

    assert isinstance(result_dict, dict)
    result = GetReviewsMultipleLocationsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.location_reviews) == 1
    assert len(result.location_reviews[0].reviews) == 1


@pytest.mark.asyncio
async def test_get_specific_review(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/123/locations/456/reviews/789",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "name": "accounts/123/locations/456/reviews/789",
            "reviewId": "789",
            "starRating": "FOUR",
            "comment": "Nice experience",
            "createTime": "2024-01-01T00:00:00Z",
        },
    )

    result_dict = await get_specific_review.ainvoke(
        _args(account="123", location="456", review="789")
    )

    assert isinstance(result_dict, dict)
    result = GetSpecificReviewOutput.model_validate(result_dict)
    assert result.success is True
    assert result.review is not None
    assert result.review.review_id == "789"


@pytest.mark.asyncio
async def test_list_all_reviews(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/123/locations/456/reviews",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "reviews": [
                {
                    "name": "accounts/123/locations/456/reviews/r1",
                    "reviewId": "r1",
                    "starRating": "FIVE",
                    "comment": "Excellent!",
                    "createTime": "2024-01-01T00:00:00Z",
                }
            ],
            "nextPageToken": None,
        },
    )

    result_dict = await list_all_reviews.ainvoke(
        _args(account="123", location="456")
    )

    assert isinstance(result_dict, dict)
    result = ListAllReviewsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.reviews) == 1


@pytest.mark.asyncio
async def test_list_posts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/123/locations/456/localPosts?pageSize=100",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "localPosts": [
                {
                    "name": "accounts/123/locations/456/localPosts/p1",
                    "summary": "Check out our sale!",
                    "topicType": "OFFER",
                    "state": "LIVE",
                    "createTime": "2024-01-01T00:00:00Z",
                }
            ],
        },
    )

    result_dict = await list_posts.ainvoke(
        _args(account="123", location="456")
    )

    assert isinstance(result_dict, dict)
    result = ListPostsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.posts) == 1
    assert result.posts[0].topic_type == "OFFER"


# --- Failure-path test -----------------------------------------------------


@pytest.mark.asyncio
async def test_create_post_missing_credential():  # type: ignore[no-untyped-def]
    """Verify empty access_token returns success=False without hitting the wire."""
    result_dict = await create_post.ainvoke(
        _args(
            auth_data={},
            account="123",
            location="456",
            topic_type="STANDARD",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error
