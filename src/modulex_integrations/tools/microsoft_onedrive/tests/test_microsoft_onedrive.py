"""Happy-path tests for every microsoft_onedrive @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.microsoft_onedrive import (
    TOOLS,
    create_folder,
    create_link,
    download_file,
    find_file_by_name,
    get_excel_table,
    get_file_by_id,
    list_files_in_folder,
    list_my_drives,
    list_shared_folder_reference_options,
    manifest,
    search_files,
    upload_file,
)
from modulex_integrations.tools.microsoft_onedrive.outputs import (
    CreateFolderOutput,
    CreateLinkOutput,
    DownloadFileOutput,
    FindFileByNameOutput,
    GetExcelTableOutput,
    GetFileByIdOutput,
    ListFilesInFolderOutput,
    ListMyDrivesOutput,
    ListSharedFolderReferenceOptionsOutput,
    SearchFilesOutput,
    UploadFileOutput,
)

API = "https://graph.microsoft.com/v1.0"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_11_actions(self) -> None:
        assert len(manifest.actions) == 11

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/drive/root/children",
        json={
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_post_children
        },
    )

    result_dict = await create_folder.ainvoke(_args(folder_name="New Folder"))

    assert isinstance(result_dict, dict)
    result = CreateFolderOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_create_link(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/drive/items/abc123/createLink",
        json={
            # TODO: fill in mock response from Microsoft Graph docs
            # https://docs.microsoft.com/en-us/graph/api/driveitem-createlink
        },
    )

    result_dict = await create_link.ainvoke(
        _args(drive_item_id="abc123", type="view")
    )

    assert isinstance(result_dict, dict)
    result = CreateLinkOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_download_file(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/abc123/content",
        content=b"fake-bytes",
        # TODO: fill in mock response from Microsoft Graph docs
        # https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_get_content
    )

    result_dict = await download_file.ainvoke(
        _args(file_id="abc123", new_file_name="downloaded.bin")
    )

    assert isinstance(result_dict, dict)
    result = DownloadFileOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_find_file_by_name(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/root/search(q='report')",
        json={
            "value": [],
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_search
        },
    )

    result_dict = await find_file_by_name.ainvoke(_args(name="report"))

    assert isinstance(result_dict, dict)
    result = FindFileByNameOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_get_excel_table(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/abc123/workbook/tables/Table1/range",
        json={
            "text": [],
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/graph/api/table-range
        },
    )

    result_dict = await get_excel_table.ainvoke(
        _args(item_id="abc123", table_name="Table1")
    )

    assert isinstance(result_dict, dict)
    result = GetExcelTableOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_get_file_by_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/abc123",
        json={
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_get
        },
    )

    result_dict = await get_file_by_id.ainvoke(_args(file_id="abc123"))

    assert isinstance(result_dict, dict)
    result = GetFileByIdOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_list_files_in_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/folder123/children",
        json={
            "value": [],
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_list_children
        },
    )

    result_dict = await list_files_in_folder.ainvoke(_args(folder_id="folder123"))

    assert isinstance(result_dict, dict)
    result = ListFilesInFolderOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_list_my_drives(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive?%24select=id%2Cname%2CdriveType%2Cowner%2Cquota",
        json={
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/graph/api/drive-get
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drives?%24select=id%2Cname%2CdriveType%2Cowner%2Cquota",
        json={
            "value": [],
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/graph/api/drive-list
        },
    )

    result_dict = await list_my_drives.ainvoke(_AUTH)

    assert isinstance(result_dict, dict)
    result = ListMyDrivesOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_list_shared_folder_reference_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/sharedWithMe",
        json={
            "value": [],
            # TODO: fill in mock response from Microsoft Graph docs
        },
    )

    result_dict = await list_shared_folder_reference_options.ainvoke(_AUTH)

    assert isinstance(result_dict, dict)
    result = ListSharedFolderReferenceOptionsOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_search_files(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/root/search(q='budget')",
        json={
            "value": [],
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/graph/api/driveitem-search
        },
    )

    result_dict = await search_files.ainvoke(_args(q="budget"))

    assert isinstance(result_dict, dict)
    result = SearchFilesOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_upload_file(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/source.bin",
        content=b"source-bytes",
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/me/drive/items/folder123:/uploaded.bin:/content",
        json={
            # TODO: fill in mock response from Microsoft Graph docs
            # https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_put_content
        },
    )

    result_dict = await upload_file.ainvoke(
        _args(
            upload_folder_id="folder123",
            file_url="https://example.com/source.bin",
            filename="uploaded.bin",
        )
    )

    assert isinstance(result_dict, dict)
    result = UploadFileOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_create_folder_missing_token() -> None:
    """Credential guard rejects empty auth_data."""
    result_dict = await create_folder.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}, "folder_name": "Test"}
    )
    assert isinstance(result_dict, dict)
    result = CreateFolderOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
