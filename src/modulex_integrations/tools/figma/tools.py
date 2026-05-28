"""Figma LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.figma.outputs import (
    CommentUser,
    DeleteCommentOutput,
    FigmaComment,
    ListCommentsOutput,
    PostACommentOutput,
)

__all__ = [
    "delete_comment",
    "list_comments",
    "post_a_comment",
]

_BASE_URL = "https://api.figma.com"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Figma API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _parse_comment(c: dict[str, Any]) -> FigmaComment:
    """Parse a raw Figma comment dict into a FigmaComment model."""
    user_data = c.get("user") or {}
    return FigmaComment(
        id=c.get("id"),
        file_key=c.get("file_key"),
        parent_id=c.get("parent_id"),
        user=CommentUser(
            handle=user_data.get("handle"),
            img_url=user_data.get("img_url"),
            id=user_data.get("id"),
        ),
        created_at=c.get("created_at"),
        resolved_at=c.get("resolved_at"),
        message=c.get("message"),
        order_id=c.get("order_id"),
    )


# --- Input schemas --------------------------------------------------------


class ListCommentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    file_id: str = Field(description="The Figma file ID (found in the file URL after /file/)")


class DeleteCommentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    file_id: str = Field(description="The Figma file ID (found in the file URL after /file/)")
    comment_id: str = Field(description="The ID of the comment to delete")


class PostACommentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    file_id: str = Field(description="The Figma file ID (found in the file URL after /file/)")
    message: str = Field(description="The text contents of the comment to post")
    comment_id: str | None = Field(
        default=None,
        description="The ID of the comment to reply to (must be a root comment)",
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ListCommentsInput)
@serialize_pydantic_return
async def list_comments(
    auth_type: str,
    auth_data: dict[str, Any],
    file_id: str,
) -> ListCommentsOutput:
    """List all comments left on a Figma file."""
    if not auth_data.get("access_token"):
        return ListCommentsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/files/{file_id}/comments",
                headers=headers,
            )
        if response.status_code != 200:
            return ListCommentsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListCommentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCommentsOutput(success=False, error=f"Call failed: {exc}")

    raw_comments = data.get("comments", [])
    comments = [_parse_comment(c) for c in raw_comments]
    return ListCommentsOutput(success=True, comments=comments)


@tool(args_schema=DeleteCommentInput)
@serialize_pydantic_return
async def delete_comment(
    auth_type: str,
    auth_data: dict[str, Any],
    file_id: str,
    comment_id: str,
) -> DeleteCommentOutput:
    """Delete a comment from a Figma file."""
    if not auth_data.get("access_token"):
        return DeleteCommentOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{_BASE_URL}/v1/files/{file_id}/comments/{comment_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return DeleteCommentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteCommentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteCommentOutput(success=False, error=f"Call failed: {exc}")

    return DeleteCommentOutput(success=True)


@tool(args_schema=PostACommentInput)
@serialize_pydantic_return
async def post_a_comment(
    auth_type: str,
    auth_data: dict[str, Any],
    file_id: str,
    message: str,
    comment_id: str | None = None,
) -> PostACommentOutput:
    """Post a comment to a Figma file."""
    if not auth_data.get("access_token"):
        return PostACommentOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"message": message}
    if comment_id:
        payload["comment_id"] = comment_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/v1/files/{file_id}/comments",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return PostACommentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PostACommentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PostACommentOutput(success=False, error=f"Call failed: {exc}")

    return PostACommentOutput(success=True, comment=_parse_comment(data))
