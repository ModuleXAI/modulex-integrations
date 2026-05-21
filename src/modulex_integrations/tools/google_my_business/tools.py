"""Google My Business LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_my_business.outputs import (
    CreatePostOutput,
    CreateUpdateReplyToReviewOutput,
    GetReviewsMultipleLocationsOutput,
    GetSpecificReviewOutput,
    ListAllReviewsOutput,
    ListPostsOutput,
    LocalPost,
    LocationReview,
    Review,
    ReviewReply,
)

__all__ = [
    "create_post",
    "create_update_reply_to_review",
    "get_reviews_multiple_locations",
    "get_specific_review",
    "list_all_reviews",
    "list_posts",
]

_BASE_URL = "https://mybusiness.googleapis.com/v4"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google My Business API."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _parse_review(r: dict[str, Any]) -> Review:
    """Parse a review dict into a Review model."""
    reply_data = r.get("reviewReply")
    review_reply = None
    if reply_data:
        review_reply = ReviewReply(
            comment=reply_data.get("comment"),
            update_time=reply_data.get("updateTime"),
        )
    return Review(
        name=r.get("name"),
        review_id=r.get("reviewId"),
        reviewer_display_name=(r.get("reviewer") or {}).get("displayName"),
        star_rating=r.get("starRating"),
        comment=r.get("comment"),
        create_time=r.get("createTime"),
        update_time=r.get("updateTime"),
        review_reply=review_reply,
    )


def _parse_local_post(p: dict[str, Any]) -> LocalPost:
    """Parse a local post dict into a LocalPost model."""
    return LocalPost(
        name=p.get("name"),
        summary=p.get("summary"),
        topic_type=p.get("topicType"),
        state=p.get("state"),
        create_time=p.get("createTime"),
        update_time=p.get("updateTime"),
        search_url=p.get("searchUrl"),
        event=p.get("event"),
        offer=p.get("offer"),
        call_to_action=p.get("callToAction"),
    )


# --- Input schemas --------------------------------------------------------


class CreatePostInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="Account name/ID for the Google Business Profile account")
    location: str = Field(description="Location name/ID whose local posts will be created")
    topic_type: str = Field(description="Topic type of the local post: STANDARD, EVENT, OFFER, or ALERT")
    language_code: str | None = Field(default=None, description="Language of the local post (e.g. en-US)")
    summary: str | None = Field(default=None, description="Description/body of the local post")
    call_to_action: dict[str, Any] | None = Field(default=None, description="Action performed when user clicks through the post")
    event: dict[str, Any] | None = Field(default=None, description="Event information. Required for topic types EVENT and OFFER")
    media: list[dict[str, Any]] | None = Field(default=None, description="Media associated with the post. Array of objects with sourceUrl fields")
    media_format: str | None = Field(default=None, description="Format of the media items: PHOTO or VIDEO")
    alert_type: str | None = Field(default=None, description="Type of alert for ALERT topic type")
    offer: dict[str, Any] | None = Field(default=None, description="Additional data for offer posts (only for OFFER topic type)")


class CreateUpdateReplyToReviewInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="Account name/ID for the Google Business Profile account")
    location: str = Field(description="Location name/ID of the review")
    review: str = Field(description="Review name/ID to reply to")
    comment: str = Field(description="Body of the reply as plain text (max 4096 bytes)")


class GetReviewsMultipleLocationsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="Account name/ID for the Google Business Profile account")
    location_names: list[str] = Field(description="List of location name/ID strings to get reviews from")
    page_size: int = Field(default=50, description="Number of reviews to return per location (max 50)")
    order_by: str | None = Field(default=None, description="How to order reviews: 'createTime desc', 'createTime asc', 'updateTime desc', or 'updateTime asc'")
    ignore_rating_only_reviews: bool = Field(default=False, description="If true, only return reviews that have textual content")


class GetSpecificReviewInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="Account name/ID for the Google Business Profile account")
    location: str = Field(description="Location name/ID of the review")
    review: str = Field(description="Review name/ID to retrieve")


class ListAllReviewsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="Account name/ID for the Google Business Profile account")
    location: str = Field(description="Location name/ID whose reviews will be listed")


class ListPostsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="Account name/ID for the Google Business Profile account")
    location: str = Field(description="Location name/ID whose local posts will be listed")
    max_results: int = Field(default=100, description="Max number of posts to retrieve (max 1000)")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreatePostInput)
@serialize_pydantic_return
async def create_post(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    location: str,
    topic_type: str,
    language_code: str | None = None,
    summary: str | None = None,
    call_to_action: dict[str, Any] | None = None,
    event: dict[str, Any] | None = None,
    media: list[dict[str, Any]] | None = None,
    media_format: str | None = None,
    alert_type: str | None = None,
    offer: dict[str, Any] | None = None,
) -> CreatePostOutput:
    """Create a new local post associated with a location."""
    if not auth_data.get("access_token"):
        return CreatePostOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"topicType": topic_type}
    if language_code:
        body["languageCode"] = language_code
    if summary:
        body["summary"] = summary
    if call_to_action:
        body["callToAction"] = call_to_action
    if event:
        body["event"] = event
    if media and media_format:
        body["media"] = [
            {"sourceUrl": item.get("sourceUrl", item.get("source_url", "")), "mediaFormat": media_format}
            for item in media
        ]
    if alert_type:
        body["alertType"] = alert_type
    if offer:
        body["offer"] = offer
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/accounts/{account}/locations/{location}/localPosts",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreatePostOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreatePostOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreatePostOutput(success=False, error=f"Call failed: {exc}")
    return CreatePostOutput(success=True, post=_parse_local_post(data))


@tool(args_schema=CreateUpdateReplyToReviewInput)
@serialize_pydantic_return
async def create_update_reply_to_review(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    location: str,
    review: str,
    comment: str,
) -> CreateUpdateReplyToReviewOutput:
    """Create or update a reply to the specified review."""
    if not auth_data.get("access_token"):
        return CreateUpdateReplyToReviewOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/accounts/{account}/locations/{location}/reviews/{review}/reply",
                headers=headers,
                json={"comment": comment},
            )
        if response.status_code not in (200, 201):
            return CreateUpdateReplyToReviewOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateUpdateReplyToReviewOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateUpdateReplyToReviewOutput(success=False, error=f"Call failed: {exc}")
    return CreateUpdateReplyToReviewOutput(
        success=True,
        comment=data.get("comment"),
        update_time=data.get("updateTime"),
    )


@tool(args_schema=GetReviewsMultipleLocationsInput)
@serialize_pydantic_return
async def get_reviews_multiple_locations(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    location_names: list[str],
    page_size: int = 50,
    order_by: str | None = None,
    ignore_rating_only_reviews: bool = False,
) -> GetReviewsMultipleLocationsOutput:
    """Get reviews from multiple locations at once."""
    if not auth_data.get("access_token"):
        return GetReviewsMultipleLocationsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    full_location_names = [
        f"accounts/{account}/locations/{loc}" if not loc.startswith("accounts/") else loc
        for loc in location_names
    ]
    body: dict[str, Any] = {
        "locationNames": full_location_names,
        "pageSize": page_size,
        "ignoreRatingOnlyReviews": ignore_rating_only_reviews,
    }
    if order_by:
        body["orderBy"] = order_by
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/accounts/{account}/locations:batchGetReviews",
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return GetReviewsMultipleLocationsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetReviewsMultipleLocationsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetReviewsMultipleLocationsOutput(success=False, error=f"Call failed: {exc}")
    location_reviews: list[LocationReview] = []
    for loc_data in data.get("locationReviews", []):
        reviews = [_parse_review(r) for r in loc_data.get("reviews", [])]
        location_reviews.append(
            LocationReview(
                location_name=loc_data.get("locationName"),
                reviews=reviews,
            )
        )
    return GetReviewsMultipleLocationsOutput(success=True, location_reviews=location_reviews)


@tool(args_schema=GetSpecificReviewInput)
@serialize_pydantic_return
async def get_specific_review(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    location: str,
    review: str,
) -> GetSpecificReviewOutput:
    """Return a specific review by name."""
    if not auth_data.get("access_token"):
        return GetSpecificReviewOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/accounts/{account}/locations/{location}/reviews/{review}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetSpecificReviewOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSpecificReviewOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSpecificReviewOutput(success=False, error=f"Call failed: {exc}")
    return GetSpecificReviewOutput(success=True, review=_parse_review(data))


@tool(args_schema=ListAllReviewsInput)
@serialize_pydantic_return
async def list_all_reviews(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    location: str,
) -> ListAllReviewsOutput:
    """List all reviews of a location to audit reviews in bulk."""
    if not auth_data.get("access_token"):
        return ListAllReviewsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/accounts/{account}/locations/{location}/reviews",
                headers=headers,
            )
        if response.status_code != 200:
            return ListAllReviewsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAllReviewsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAllReviewsOutput(success=False, error=f"Call failed: {exc}")
    reviews = [_parse_review(r) for r in data.get("reviews", [])]
    return ListAllReviewsOutput(
        success=True,
        reviews=reviews,
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=ListPostsInput)
@serialize_pydantic_return
async def list_posts(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    location: str,
    max_results: int = 100,
) -> ListPostsOutput:
    """List local posts associated with a location."""
    if not auth_data.get("access_token"):
        return ListPostsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    all_posts: list[LocalPost] = []
    page_token: str | None = None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while len(all_posts) < max_results:
                params: dict[str, Any] = {"pageSize": min(100, max_results - len(all_posts))}
                if page_token:
                    params["pageToken"] = page_token
                response = await client.get(
                    f"{_BASE_URL}/accounts/{account}/locations/{location}/localPosts",
                    headers=headers,
                    params=params,
                )
                if response.status_code != 200:
                    return ListPostsOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                for p in data.get("localPosts", []):
                    all_posts.append(_parse_local_post(p))
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
    except httpx.TimeoutException:
        return ListPostsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListPostsOutput(success=False, error=f"Call failed: {exc}")
    return ListPostsOutput(success=True, posts=all_posts)
