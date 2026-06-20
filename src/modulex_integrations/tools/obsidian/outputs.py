"""Pydantic response models for the Obsidian integration's @tool functions.

Each action returns a typed output carrying ``success: bool`` +
``error: str | None`` plus the action-specific data fields. Fields are
permissive (``| None`` / ``default_factory=list``) because the upstream
Local REST API responses are parsed defensively with ``.get()``.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AppendActiveOutput",
    "AppendNoteOutput",
    "AppendPeriodicNoteOutput",
    "CommandItem",
    "CreateNoteOutput",
    "DeleteNoteOutput",
    "ExecuteCommandOutput",
    "FileEntry",
    "GetActiveOutput",
    "GetNoteOutput",
    "GetPeriodicNoteOutput",
    "ListCommandsOutput",
    "ListFilesOutput",
    "OpenFileOutput",
    "PatchActiveOutput",
    "PatchNoteOutput",
    "SearchMatch",
    "SearchOutput",
    "SearchResultItem",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class FileEntry(_Base):
    """A single file or directory entry in ``list_files``."""

    path: str | None = None
    type: str | None = None


class SearchMatch(_Base):
    """A single matching context snippet within a search result."""

    context: str | None = None


class SearchResultItem(_Base):
    """A single result row in ``search``."""

    filename: str | None = None
    score: float | None = None
    matches: list[SearchMatch] = Field(default_factory=list)


class CommandItem(_Base):
    """A single available command in ``list_commands``."""

    id: str | None = None
    name: str | None = None


# --- Per-action output models ----------------------------------------------


class ListFilesOutput(_Base):
    success: bool
    error: str | None = None
    files: list[FileEntry] = Field(default_factory=list)


class GetNoteOutput(_Base):
    success: bool
    error: str | None = None
    content: str | None = None
    filename: str | None = None


class CreateNoteOutput(_Base):
    success: bool
    error: str | None = None
    filename: str | None = None
    created: bool | None = None


class AppendNoteOutput(_Base):
    success: bool
    error: str | None = None
    filename: str | None = None
    appended: bool | None = None


class PatchNoteOutput(_Base):
    success: bool
    error: str | None = None
    filename: str | None = None
    patched: bool | None = None


class DeleteNoteOutput(_Base):
    success: bool
    error: str | None = None
    filename: str | None = None
    deleted: bool | None = None


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    results: list[SearchResultItem] = Field(default_factory=list)


class GetActiveOutput(_Base):
    success: bool
    error: str | None = None
    content: str | None = None
    filename: str | None = None


class AppendActiveOutput(_Base):
    success: bool
    error: str | None = None
    appended: bool | None = None


class PatchActiveOutput(_Base):
    success: bool
    error: str | None = None
    patched: bool | None = None


class ListCommandsOutput(_Base):
    success: bool
    error: str | None = None
    commands: list[CommandItem] = Field(default_factory=list)


class ExecuteCommandOutput(_Base):
    success: bool
    error: str | None = None
    command_id: str | None = None
    executed: bool | None = None


class OpenFileOutput(_Base):
    success: bool
    error: str | None = None
    filename: str | None = None
    opened: bool | None = None


class GetPeriodicNoteOutput(_Base):
    success: bool
    error: str | None = None
    content: str | None = None
    period: str | None = None


class AppendPeriodicNoteOutput(_Base):
    success: bool
    error: str | None = None
    period: str | None = None
    appended: bool | None = None
