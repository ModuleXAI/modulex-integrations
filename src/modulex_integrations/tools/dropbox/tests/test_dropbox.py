"""Happy-path tests for every dropbox @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.dropbox import (
    TOOLS,
    create_a_text_file,
    create_folder,
    create_or_append_to_a_text_file,
    create_update_share_link,
    delete_file_folder,
    get_shared_link_metadata,
    list_file_folders_in_a_folder,
    list_file_revisions,
    list_shared_links,
    manifest,
    move_file_folder,
    rename_file_folder,
    search_files_folders,
)
from modulex_integrations.tools.dropbox.outputs import (
    CreateFolderOutput,
    CreateOrAppendToTextFileOutput,
    CreateTextFileOutput,
    CreateUpdateShareLinkOutput,
    DeleteFileFolderOutput,
    GetSharedLinkMetadataOutput,
    ListFileFoldersOutput,
    ListFileRevisionsOutput,
    ListSharedLinksOutput,
    MoveFileFolderOutput,
    RenameFileFolderOutput,
    SearchFileFoldersOutput,
)

API = "https://api.dropboxapi.com/2"
CONTENT_API = "https://content.dropboxapi.com/2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_12_actions(self) -> None:
        assert len(manifest.actions) == 12

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/files/create_folder_v2",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "metadata": {
                "name": "NewFolder",
                "id": "id:abc123",
                "path_display": "/NewFolder",
                "path_lower": "/newfolder",
            },
        },
    )

    result_dict = await create_folder.ainvoke(_args(name="NewFolder"))

    assert isinstance(result_dict, dict)
    result = CreateFolderOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None
    assert result.metadata.name == "NewFolder"


@pytest.mark.asyncio
async def test_search_files_folders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/files/search_v2",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "matches": [
                {
                    "match_type": {".tag": "filename"},
                    "metadata": {
                        "metadata": {
                            ".tag": "file",
                            "name": "report.pdf",
                            "id": "id:xyz789",
                            "path_display": "/Documents/report.pdf",
                        },
                    },
                },
            ],
            "has_more": False,
        },
    )

    result_dict = await search_files_folders.ainvoke(_args(query="report"))

    assert isinstance(result_dict, dict)
    result = SearchFileFoldersOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.matches) == 1


@pytest.mark.asyncio
async def test_list_file_folders_in_a_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/files/list_folder",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "entries": [
                {
                    ".tag": "folder",
                    "name": "Documents",
                    "id": "id:folder1",
                    "path_display": "/Documents",
                    "path_lower": "/documents",
                },
            ],
            "has_more": False,
        },
    )

    result_dict = await list_file_folders_in_a_folder.ainvoke(_args(path=""))

    assert isinstance(result_dict, dict)
    result = ListFileFoldersOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.entries) == 1


@pytest.mark.asyncio
async def test_delete_file_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/files/delete_v2",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "metadata": {
                ".tag": "file",
                "name": "old.txt",
                "id": "id:del1",
                "path_display": "/old.txt",
            },
        },
    )

    result_dict = await delete_file_folder.ainvoke(_args(path="/old.txt"))

    assert isinstance(result_dict, dict)
    result = DeleteFileFolderOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_move_file_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/files/move_v2",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "metadata": {
                ".tag": "file",
                "name": "doc.txt",
                "id": "id:mv1",
                "path_display": "/Archive/doc.txt",
            },
        },
    )

    result_dict = await move_file_folder.ainvoke(_args(path_from="/doc.txt", path_to="/Archive"))

    assert isinstance(result_dict, dict)
    result = MoveFileFolderOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_rename_file_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/files/move_v2",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "metadata": {
                ".tag": "file",
                "name": "renamed.txt",
                "id": "id:rn1",
                "path_display": "/renamed.txt",
            },
        },
    )

    result_dict = await rename_file_folder.ainvoke(
        _args(path_from="/old_name.txt", new_name="renamed.txt")
    )

    assert isinstance(result_dict, dict)
    result = RenameFileFolderOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_a_text_file(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{CONTENT_API}/files/upload",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "name": "hello.txt",
            "id": "id:up1",
            "path_display": "/hello.txt",
            "size": 13,
            "rev": "015f11a45f3",
            "content_hash": "abc123hash",
        },
    )

    result_dict = await create_a_text_file.ainvoke(
        _args(name="hello.txt", content="Hello, World!")
    )

    assert isinstance(result_dict, dict)
    result = CreateTextFileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "hello.txt"


@pytest.mark.asyncio
async def test_create_or_append_to_a_text_file(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{CONTENT_API}/files/download",
        status_code=409,
        text="not_found",
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{CONTENT_API}/files/upload",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "name": "log.txt",
            "id": "id:ap1",
            "path_display": "/log.txt",
            "size": 20,
            "rev": "015f11a45f4",
            "content_hash": "def456hash",
        },
    )

    result_dict = await create_or_append_to_a_text_file.ainvoke(
        _args(name="log.txt", content="New log entry")
    )

    assert isinstance(result_dict, dict)
    result = CreateOrAppendToTextFileOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_update_share_link(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sharing/create_shared_link_with_settings",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "url": "https://www.dropbox.com/s/abc123/doc.txt?dl=0",
            "name": "doc.txt",
            "path_lower": "/doc.txt",
            "link_permissions": {"can_revoke": True},
        },
    )

    result_dict = await create_update_share_link.ainvoke(_args(path="/doc.txt"))

    assert isinstance(result_dict, dict)
    result = CreateUpdateShareLinkOutput.model_validate(result_dict)
    assert result.success is True
    assert result.url is not None


@pytest.mark.asyncio
async def test_list_shared_links(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sharing/list_shared_links",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "links": [
                {
                    "url": "https://www.dropbox.com/s/xyz/file.pdf?dl=0",
                    "name": "file.pdf",
                    "path_lower": "/file.pdf",
                },
            ],
        },
    )

    result_dict = await list_shared_links.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListSharedLinksOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.links) == 1


@pytest.mark.asyncio
async def test_get_shared_link_metadata(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sharing/get_shared_link_metadata",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "url": "https://www.dropbox.com/s/abc/doc.txt?dl=0",
            "name": "doc.txt",
            "path_lower": "/doc.txt",
            "id": "id:slm1",
            "link_permissions": {"can_revoke": True},
        },
    )

    result_dict = await get_shared_link_metadata.ainvoke(
        _args(shared_link_url="https://www.dropbox.com/s/abc/doc.txt?dl=0")
    )

    assert isinstance(result_dict, dict)
    result = GetSharedLinkMetadataOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "doc.txt"


@pytest.mark.asyncio
async def test_list_file_revisions(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/files/list_revisions",
        json={
            # TODO: fill in a representative response shape from the Dropbox API docs
            "entries": [
                {
                    ".tag": "file",
                    "name": "doc.txt",
                    "rev": "015f11a45f3",
                    "size": 100,
                    "server_modified": "2024-01-15T10:00:00Z",
                },
            ],
            "is_deleted": False,
        },
    )

    result_dict = await list_file_revisions.ainvoke(_args(path="/doc.txt"))

    assert isinstance(result_dict, dict)
    result = ListFileRevisionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.entries) == 1


@pytest.mark.asyncio
async def test_create_folder_api_error(httpx_mock):  # type: ignore[no-untyped-def]
    """Failure-path: non-2xx from Dropbox API returns success=False."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/files/create_folder_v2",
        status_code=409,
        json={"error_summary": "path/conflict/folder/.."},
    )

    result_dict = await create_folder.ainvoke(_args(name="Conflict"))

    assert isinstance(result_dict, dict)
    result = CreateFolderOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
