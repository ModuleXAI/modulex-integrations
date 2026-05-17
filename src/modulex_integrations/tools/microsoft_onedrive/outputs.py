"""Pydantic response models for the microsoft_onedrive integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateFolderOutput",
    "CreateFolderResult",
    "CreateLinkOutput",
    "CreateLinkResult",
    "DownloadFileOutput",
    "DownloadFileResult",
    "DriveItemSummary",
    "DriveSummary",
    "FindFileByNameOutput",
    "GetExcelTableOutput",
    "GetExcelTableResult",
    "GetFileByIdOutput",
    "ListFilesInFolderOutput",
    "ListMyDrivesOutput",
    "ListSharedFolderReferenceOptionsOutput",
    "SearchFilesOutput",
    "SharedFolderReferenceOption",
    "UploadFileOutput",
    "UploadFileResult",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ---------------------------------------------


class DriveItemSummary(_Base):
    """A DriveItem (file or folder) as returned by Microsoft Graph."""

    id: str | None = None
    name: str | None = None
    webUrl: str | None = None
    size: int | None = None
    createdDateTime: str | None = None
    lastModifiedDateTime: str | None = None
    file: dict[str, Any] | None = None
    folder: dict[str, Any] | None = None
    parentReference: dict[str, Any] | None = None


class DriveSummary(_Base):
    """A Drive object as returned by Microsoft Graph."""

    id: str | None = None
    name: str | None = None
    driveType: str | None = None
    owner: dict[str, Any] | None = None
    quota: dict[str, Any] | None = None


class SharedFolderReferenceOption(_Base):
    """A {label, value} option usable as create_folder.shared_folder_reference."""

    label: str | None = None
    value: str | None = None


class CreateFolderResult(_Base):
    """Microsoft Graph response for creating a folder."""

    id: str | None = None
    name: str | None = None
    webUrl: str | None = None
    parentReference: dict[str, Any] | None = None


class CreateLinkResult(_Base):
    """Microsoft Graph response for creating a sharing link (Permission resource)."""

    id: str | None = None
    link: dict[str, Any] | None = None


class DownloadFileResult(_Base):
    """Result envelope for download_file — file saved to /tmp + base64 content."""

    tmp_file_path: str | None = None
    file_name: str | None = None
    size_bytes: int | None = None
    content_base64: str | None = None


class GetExcelTableResult(_Base):
    """Result envelope for get_excel_table — table rows as list[list[str]]."""

    rows: list[list[str]] = Field(default_factory=list)
    row_count: int | None = None


class UploadFileResult(_Base):
    """Microsoft Graph response for an uploaded DriveItem (subset of fields)."""

    id: str | None = None
    name: str | None = None
    webUrl: str | None = None
    size: int | None = None


# --- Per-action output models -------------------------------------------


class CreateFolderOutput(_Base):
    success: bool
    error: str | None = None
    result: CreateFolderResult | None = None


class CreateLinkOutput(_Base):
    success: bool
    error: str | None = None
    result: CreateLinkResult | None = None


class DownloadFileOutput(_Base):
    success: bool
    error: str | None = None
    result: DownloadFileResult | None = None


class FindFileByNameOutput(_Base):
    success: bool
    error: str | None = None
    count: int | None = None
    items: list[DriveItemSummary] = Field(default_factory=list)


class GetExcelTableOutput(_Base):
    success: bool
    error: str | None = None
    result: GetExcelTableResult | None = None


class GetFileByIdOutput(_Base):
    success: bool
    error: str | None = None
    item: DriveItemSummary | None = None


class ListFilesInFolderOutput(_Base):
    success: bool
    error: str | None = None
    count: int | None = None
    items: list[DriveItemSummary] = Field(default_factory=list)


class ListMyDrivesOutput(_Base):
    success: bool
    error: str | None = None
    count: int | None = None
    drives: list[DriveSummary] = Field(default_factory=list)


class ListSharedFolderReferenceOptionsOutput(_Base):
    success: bool
    error: str | None = None
    count: int | None = None
    options: list[SharedFolderReferenceOption] = Field(default_factory=list)


class SearchFilesOutput(_Base):
    success: bool
    error: str | None = None
    count: int | None = None
    items: list[DriveItemSummary] = Field(default_factory=list)


class UploadFileOutput(_Base):
    success: bool
    error: str | None = None
    result: UploadFileResult | None = None
