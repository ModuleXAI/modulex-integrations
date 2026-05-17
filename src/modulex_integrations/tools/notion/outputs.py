"""Pydantic response models for the Notion integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AppendBlocksOutput",
    "CreateCommentOutput",
    "CreateDatabaseItemOutput",
    "CreateDatabaseOutput",
    "CreatePageOutput",
    "DeleteBlockOutput",
    "GetBlockChildrenOutput",
    "GetBlockOutput",
    "GetBotUserOutput",
    "GetCommentsOutput",
    "GetDatabaseOutput",
    "GetPageOutput",
    "GetUserOutput",
    "ListUsersOutput",
    "QueryDatabaseOutput",
    "SearchOutput",
    "UpdateBlockOutput",
    "UpdateDatabaseOutput",
    "UpdatePageOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class _ListBase(_Base):
    """Common pagination metadata for list responses."""

    total: int = 0
    has_more: bool = False
    next_cursor: str | None = None


class SearchOutput(_ListBase):
    results: list[dict[str, Any]] = Field(default_factory=list)


class CreatePageOutput(_Base):
    id: str | None = None
    url: str | None = None
    created_time: str | None = None
    title: str | None = None
    properties: dict[str, Any] | None = None
    parent: dict[str, Any] | None = None


class GetPageOutput(_Base):
    id: str | None = None
    url: str | None = None
    created_time: str | None = None
    last_edited_time: str | None = None
    created_by: dict[str, Any] | None = None
    last_edited_by: dict[str, Any] | None = None
    title: str | None = None
    properties: dict[str, Any] | None = None
    parent: dict[str, Any] | None = None
    archived: bool | None = None
    content: list[dict[str, Any]] | None = None


class UpdatePageOutput(_Base):
    id: str | None = None
    url: str | None = None
    last_edited_time: str | None = None
    title: str | None = None
    properties: dict[str, Any] | None = None
    archived: bool | None = None


class QueryDatabaseOutput(_ListBase):
    database_id: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)


class GetDatabaseOutput(_Base):
    id: str | None = None
    url: str | None = None
    created_time: str | None = None
    last_edited_time: str | None = None
    title: str | None = None
    description: str | None = None
    properties: dict[str, Any] | None = None
    parent: dict[str, Any] | None = None
    archived: bool | None = None
    is_inline: bool | None = None


class CreateDatabaseOutput(_Base):
    id: str | None = None
    url: str | None = None
    created_time: str | None = None
    title: str | None = None
    properties: dict[str, Any] | None = None
    parent: dict[str, Any] | None = None


class UpdateDatabaseOutput(_Base):
    id: str | None = None
    url: str | None = None
    last_edited_time: str | None = None
    title: str | None = None
    description: str | None = None
    properties: dict[str, Any] | None = None


class CreateDatabaseItemOutput(_Base):
    id: str | None = None
    url: str | None = None
    created_time: str | None = None
    title: str | None = None
    properties: dict[str, Any] | None = None


class GetBlockOutput(_Base):
    id: str | None = None
    type: str | None = None
    created_time: str | None = None
    last_edited_time: str | None = None
    has_children: bool | None = None
    archived: bool | None = None
    parent: dict[str, Any] | None = None
    content: dict[str, Any] | None = None


class GetBlockChildrenOutput(_ListBase):
    block_id: str | None = None
    children: list[dict[str, Any]] = Field(default_factory=list)


class AppendBlocksOutput(_Base):
    block_id: str | None = None
    appended_blocks: list[dict[str, Any]] = Field(default_factory=list)
    total_appended: int = 0


class UpdateBlockOutput(_Base):
    id: str | None = None
    type: str | None = None
    last_edited_time: str | None = None
    has_children: bool | None = None
    content: dict[str, Any] | None = None


class DeleteBlockOutput(_Base):
    id: str | None = None
    type: str | None = None
    archived: bool | None = None


class ListUsersOutput(_ListBase):
    users: list[dict[str, Any]] = Field(default_factory=list)


class GetUserOutput(_Base):
    id: str | None = None
    object: str | None = None
    type: str | None = None
    name: str | None = None
    avatar_url: str | None = None
    person: dict[str, Any] | None = None
    bot: dict[str, Any] | None = None


class GetBotUserOutput(_Base):
    id: str | None = None
    object: str | None = None
    type: str | None = None
    name: str | None = None
    avatar_url: str | None = None
    bot: dict[str, Any] | None = None


class CreateCommentOutput(_Base):
    id: str | None = None
    created_time: str | None = None
    discussion_id: str | None = None
    parent: dict[str, Any] | None = None
    rich_text: list[dict[str, Any]] | None = None
    created_by: dict[str, Any] | None = None


class GetCommentsOutput(_ListBase):
    block_id: str | None = None
    comments: list[dict[str, Any]] = Field(default_factory=list)
