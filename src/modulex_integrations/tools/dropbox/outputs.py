"""Pydantic response models for the dropbox integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateFolderOutput",
    "CreateOrAppendToTextFileOutput",
    "CreateTextFileOutput",
    "CreateUpdateShareLinkOutput",
    "DeleteFileFolderOutput",
    "FileMetadata",
    "GetSharedLinkMetadataOutput",
    "ListFileFoldersOutput",
    "ListFileRevisionsOutput",
    "ListSharedLinksOutput",
    "MoveFileFolderOutput",
    "RenameFileFolderOutput",
    "SearchFileFoldersOutput",
    "SearchMatch",
    "SharedLinkInfo",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --- Nested resource models -----------------------------------------------


class FileMetadata(_Base):
    """Metadata for a file or folder returned by the Dropbox API."""

    tag: str | None = Field(default=None, alias=".tag")
    name: str | None = None
    id: str | None = None
    path_display: str | None = None
    path_lower: str | None = None
    size: int | None = None
    rev: str | None = None
    content_hash: str | None = None
    server_modified: str | None = None
    client_modified: str | None = None
    is_downloadable: bool | None = None


class SearchMatch(_Base):
    """A single search result match."""

    match_type: str | None = None
    metadata: FileMetadata | None = None


class SharedLinkInfo(_Base):
    """Metadata for a shared link."""

    url: str | None = None
    name: str | None = None
    path_lower: str | None = None
    id: str | None = None
    expires: str | None = None
    link_permissions: dict[str, object] | None = None


# --- Per-action output models ---------------------------------------------


class CreateFolderOutput(_Base):
    success: bool
    error: str | None = None
    metadata: FileMetadata | None = None


class SearchFileFoldersOutput(_Base):
    success: bool
    error: str | None = None
    matches: list[SearchMatch] = Field(default_factory=list)
    has_more: bool | None = None


class ListFileFoldersOutput(_Base):
    success: bool
    error: str | None = None
    entries: list[FileMetadata] = Field(default_factory=list)
    has_more: bool | None = None


class DeleteFileFolderOutput(_Base):
    success: bool
    error: str | None = None
    metadata: FileMetadata | None = None


class MoveFileFolderOutput(_Base):
    success: bool
    error: str | None = None
    metadata: FileMetadata | None = None


class RenameFileFolderOutput(_Base):
    success: bool
    error: str | None = None
    metadata: FileMetadata | None = None


class CreateTextFileOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    id: str | None = None
    path_display: str | None = None
    size: int | None = None
    rev: str | None = None
    content_hash: str | None = None


class CreateOrAppendToTextFileOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    id: str | None = None
    path_display: str | None = None
    size: int | None = None
    rev: str | None = None
    content_hash: str | None = None


class CreateUpdateShareLinkOutput(_Base):
    success: bool
    error: str | None = None
    url: str | None = None
    name: str | None = None
    path_lower: str | None = None
    link_permissions: dict[str, object] | None = None


class ListSharedLinksOutput(_Base):
    success: bool
    error: str | None = None
    links: list[SharedLinkInfo] = Field(default_factory=list)


class GetSharedLinkMetadataOutput(_Base):
    success: bool
    error: str | None = None
    url: str | None = None
    name: str | None = None
    path_lower: str | None = None
    id: str | None = None
    link_permissions: dict[str, object] | None = None


class ListFileRevisionsOutput(_Base):
    success: bool
    error: str | None = None
    entries: list[FileMetadata] = Field(default_factory=list)
    is_deleted: bool | None = None
