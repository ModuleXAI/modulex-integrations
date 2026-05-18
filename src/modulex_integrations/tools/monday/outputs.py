"""Pydantic response models for the monday integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ColumnValue",
    "CreateBoardOutput",
    "CreateColumnOutput",
    "CreateGroupOutput",
    "CreateItemOutput",
    "CreateSubitemOutput",
    "CreateUpdateOutput",
    "GetBoardItemsPageOutput",
    "GetColumnValuesOutput",
    "GetItemsByColumnValueOutput",
    "ItemSummary",
    "ListBoardsOutput",
    "ListWorkspacesOutput",
    "MondayBoard",
    "UpdateColumnValuesOutput",
    "UpdateItemNameOutput",
    "WorkspaceOption",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class ColumnValue(_Base):
    """A column value returned for an item."""

    id: str | None = None
    value: str | None = None
    text: str | None = None


class ItemSummary(_Base):
    """An item returned from a Monday.com board."""

    id: str | None = None
    name: str | None = None
    column_values: list[ColumnValue] = Field(default_factory=list)
    created_at: str | None = None
    creator_id: str | None = None
    email: str | None = None
    relative_link: str | None = None
    state: str | None = None
    updated_at: str | None = None
    url: str | None = None


class MondayBoard(_Base):
    """A board object from Monday.com."""

    id: str | None = None
    name: str | None = None
    state: str | None = None
    board_kind: str | None = None
    description: str | None = None
    workspace_id: str | None = None


class WorkspaceOption(_Base):
    """A workspace option with label and value."""

    label: str | None = None
    value: int | None = None


# --- Per-action output models ---------------------------------------------


class CreateBoardOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class CreateColumnOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class CreateGroupOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class CreateItemOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class CreateSubitemOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class CreateUpdateOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class GetBoardItemsPageOutput(_Base):
    success: bool
    error: str | None = None
    items: list[ItemSummary] = Field(default_factory=list)


class GetColumnValuesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[ItemSummary] = Field(default_factory=list)


class GetItemsByColumnValueOutput(_Base):
    success: bool
    error: str | None = None
    items: list[ItemSummary] = Field(default_factory=list)


class ListBoardsOutput(_Base):
    success: bool
    error: str | None = None
    boards: list[MondayBoard] = Field(default_factory=list)


class ListWorkspacesOutput(_Base):
    success: bool
    error: str | None = None
    workspaces: list[WorkspaceOption] = Field(default_factory=list)


class UpdateColumnValuesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[ItemSummary] = Field(default_factory=list)


class UpdateItemNameOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
