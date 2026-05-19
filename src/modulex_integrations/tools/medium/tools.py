"""Medium LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.medium.outputs import CreatePostOutput

__all__ = [
    "create_post",
]

_BASE_URL = "https://api.medium.com/v1"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Medium API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


class CreatePostInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="The title of the post. Used for SEO and listing display.")
    content_format: str = Field(description="The format of the content field. Valid values are 'html' and 'markdown'.")
    content: str = Field(description="The body of the post, in valid semantic HTML or Markdown.")
    tags: list[str] | None = Field(default=None, description="Tags to classify the post (array of strings). Only the first three are used.")
    canonical_url: str | None = Field(default=None, description="The original home of this content, if it was originally published elsewhere.")
    publish_status: str | None = Field(default=None, description="The status of the post. Valid values are 'public', 'draft', or 'unlisted'.")
    license: str | None = Field(default=None, description="The license of the post. Valid values are 'all-rights-reserved', 'cc-40-by', 'cc-40-by-sa', 'cc-40-by-nd', 'cc-40-by-nc', 'cc-40-by-nc-nd', 'cc-40-by-nc-sa', 'cc-40-zero', 'public-domain'.")
    notify_followers: bool | None = Field(default=None, description="Whether to notify followers that the user has published.")


@tool(args_schema=CreatePostInput)
@serialize_pydantic_return
async def create_post(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    content_format: str,
    content: str,
    tags: list[str] | None = None,
    canonical_url: str | None = None,
    publish_status: str | None = None,
    license: str | None = None,
    notify_followers: bool | None = None,
) -> CreatePostOutput:
    """Create a new Medium post."""
    access_token = auth_data.get("access_token", "")
    if not access_token or not access_token.strip():
        return CreatePostOutput(
            success=False,
            error="Missing or empty access_token in auth_data.",
        )
    headers = _get_auth_headers(auth_type, auth_data)
    oauth_uid = auth_data.get("oauth_uid", "")
    if not oauth_uid:
        return CreatePostOutput(
            success=False,
            error="Missing oauth_uid in auth_data. Medium requires the authenticated user ID to create posts.",
        )

    body: dict[str, Any] = {
        "title": title,
        "contentFormat": content_format,
        "content": content,
    }
    if tags is not None:
        body["tags"] = tags
    if canonical_url is not None:
        body["canonicalUrl"] = canonical_url
    if publish_status is not None:
        body["publishStatus"] = publish_status
    if license is not None:
        body["license"] = license
    if notify_followers is not None:
        body["notifyFollowers"] = notify_followers

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/users/{oauth_uid}/posts",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreatePostOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        result = response.json()
    except httpx.TimeoutException:
        return CreatePostOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreatePostOutput(success=False, error=f"Call failed: {exc}")

    data = result.get("data", {})
    return CreatePostOutput(
        success=True,
        id=data.get("id"),
        title=data.get("title"),
        author_id=data.get("authorId"),
        url=data.get("url"),
        canonical_url=data.get("canonicalUrl"),
        publish_status=data.get("publishStatus"),
        published_at=data.get("publishedAt"),
        license=data.get("license"),
        license_url=data.get("licenseUrl"),
        tags=data.get("tags") or [],
    )
