"""Pydantic response models for the figma integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CommentUser",
    "DeleteCommentOutput",
    "FigmaComment",
    "ListCommentsOutput",
    "PostACommentOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class CommentUser(_Base):
    """A Figma user who authored a comment."""

    handle: str | None = None
    img_url: str | None = None
    id: str | None = None


class FigmaComment(_Base):
    """A single comment on a Figma file."""

    id: str | None = None
    file_key: str | None = None
    parent_id: str | None = None
    user: CommentUser | None = None
    created_at: str | None = None
    resolved_at: str | None = None
    message: str | None = None
    order_id: str | None = None


# --- Per-action output models ---------------------------------------------


class ListCommentsOutput(_Base):
    success: bool
    error: str | None = None
    comments: list[FigmaComment] = Field(default_factory=list)


class DeleteCommentOutput(_Base):
    success: bool
    error: str | None = None


class PostACommentOutput(_Base):
    success: bool
    error: str | None = None
    comment: FigmaComment | None = None
