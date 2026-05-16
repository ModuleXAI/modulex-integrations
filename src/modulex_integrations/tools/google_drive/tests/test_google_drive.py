"""Tests for the Google Drive / Docs / Sheets / Slides integration.

24 actions all share the same shape, so coverage is shape-
representative rather than exhaustive: one happy-path per API surface
plus the manifest sanity trio, an auth-validation test, and a few
multi-call workflow tests for the trickier shapes.
"""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.google_drive import (
    TOOLS,
    add_slide,
    append_to_google_doc,
    copy_file,
    create_folder,
    create_google_doc,
    create_google_sheet,
    create_google_slides,
    create_text_file,
    delete_item,
    format_sheet_cells,
    format_sheet_text,
    get_file_metadata,
    list_folder,
    manifest,
    move_item,
    read_file,
    read_google_doc,
    read_google_sheet,
    read_google_slides,
    rename_item,
    search_files,
    update_google_doc,
    update_google_sheet,
    update_slide_content,
    update_text_file,
)
from modulex_integrations.tools.google_drive.outputs import (
    AddSlideOutput,
    AppendToGoogleDocOutput,
    CopyFileOutput,
    CreateFolderOutput,
    CreateGoogleDocOutput,
    CreateGoogleSheetOutput,
    CreateGoogleSlidesOutput,
    CreateTextFileOutput,
    DeleteItemOutput,
    FormatSheetCellsOutput,
    FormatSheetTextOutput,
    GetFileMetadataOutput,
    ListFolderOutput,
    MoveItemOutput,
    ReadFileOutput,
    ReadGoogleDocOutput,
    ReadGoogleSheetOutput,
    ReadGoogleSlidesOutput,
    RenameItemOutput,
    SearchFilesOutput,
    UpdateGoogleDocOutput,
    UpdateGoogleSheetOutput,
    UpdateSlideContentOutput,
    UpdateTextFileOutput,
)
from modulex_integrations.tools.google_drive.tools import _a1_to_grid

DRIVE = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3"
DOCS = "https://docs.googleapis.com/v1"
SHEETS = "https://sheets.googleapis.com/v4"
SLIDES = "https://slides.googleapis.com/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "tok-123"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


class TestManifest:
    def test_manifest_exposes_24_actions(self) -> None:
        assert len(manifest.actions) == 24

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_paired_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}


def test_a1_to_grid() -> None:
    assert _a1_to_grid("A1:B5") == {
        "sheetId": 0,
        "startColumnIndex": 0,
        "startRowIndex": 0,
        "endColumnIndex": 2,
        "endRowIndex": 5,
    }
    assert _a1_to_grid("Sheet1!C2") == {
        "sheetId": 0,
        "startColumnIndex": 2,
        "startRowIndex": 1,
        "endColumnIndex": 3,
        "endRowIndex": 2,
    }


@pytest.mark.asyncio
async def test_search_files_missing_token() -> None:
    bad = {"auth_type": "oauth2", "auth_data": {}}
    result = SearchFilesOutput.model_validate(
        await search_files.ainvoke(dict(bad, query="foo"))
    )
    assert result.success is False
    assert result.error is not None and "token" in result.error


@pytest.mark.asyncio
async def test_search_files(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{DRIVE}/files\?.*"),
        json={"files": [{"id": "f1", "name": "doc.txt", "mimeType": "text/plain"}]},
    )
    result = SearchFilesOutput.model_validate(
        await search_files.ainvoke(_args(query="doc"))
    )
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_list_folder_splits_folders_and_files(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{DRIVE}/files\?.*"),
        json={
            "files": [
                {"id": "F1", "mimeType": "application/vnd.google-apps.folder"},
                {"id": "f1", "mimeType": "text/plain"},
            ]
        },
    )
    result = ListFolderOutput.model_validate(
        await list_folder.ainvoke(_args())
    )
    assert result.success is True
    assert len(result.folders) == 1
    assert len(result.files) == 1


@pytest.mark.asyncio
async def test_read_file_text(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{DRIVE}/files/f1?fields=id%2Cname%2CmimeType%2Csize%2CwebViewLink",
        json={"id": "f1", "name": "doc.txt", "mimeType": "text/plain"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{DRIVE}/files/f1?alt=media",
        text="hello world",
    )
    result = ReadFileOutput.model_validate(
        await read_file.ainvoke(_args(file_id="f1"))
    )
    assert result.success is True
    assert result.content == "hello world"


@pytest.mark.asyncio
async def test_read_file_google_doc_exports_text(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{DRIVE}/files/d1?fields=id%2Cname%2CmimeType%2Csize%2CwebViewLink",
        json={
            "id": "d1",
            "name": "My Doc",
            "mimeType": "application/vnd.google-apps.document",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{DRIVE}/files/d1/export?mimeType=text%2Fplain",
        text="document body",
    )
    result = ReadFileOutput.model_validate(
        await read_file.ainvoke(_args(file_id="d1"))
    )
    assert result.success is True
    assert result.content == "document body"


@pytest.mark.asyncio
async def test_read_file_binary_returns_link(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{DRIVE}/files/b1?fields=id%2Cname%2CmimeType%2Csize%2CwebViewLink",
        json={
            "id": "b1",
            "name": "image.png",
            "mimeType": "image/png",
            "webViewLink": "https://drive.google.com/file/d/b1/view",
        },
    )
    result = ReadFileOutput.model_validate(
        await read_file.ainvoke(_args(file_id="b1"))
    )
    assert result.success is True
    assert result.message is not None and "web_view_link" in result.message


@pytest.mark.asyncio
async def test_create_text_file_rejects_bad_extension() -> None:
    result = CreateTextFileOutput.model_validate(
        await create_text_file.ainvoke(
            _args(name="doc.docx", content="x")
        )
    )
    assert result.success is False
    assert result.error is not None and ".txt or .md" in result.error


@pytest.mark.asyncio
async def test_create_text_file_uploads_multipart(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        from httpx import Response

        captured["content"] = request.content
        captured["content_type"] = request.headers.get("content-type")
        return Response(
            201, json={"id": "f_new", "name": "x.md", "mimeType": "text/markdown"}
        )

    httpx_mock.add_callback(
        _capture,
        method="POST",
        url=re.compile(rf"{UPLOAD}/files\?.*"),
    )
    result = CreateTextFileOutput.model_validate(
        await create_text_file.ainvoke(
            _args(name="x.md", content="hi")
        )
    )
    assert result.success is True
    assert "multipart/related" in (captured["content_type"] or "")
    body = captured["content"].decode()
    assert "hi" in body and "text/markdown" in body


@pytest.mark.asyncio
async def test_update_text_file(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{DRIVE}/files/f1\?.*"),
        json={"mimeType": "text/plain", "name": "old.txt"},
    )
    httpx_mock.add_response(
        method="PATCH",
        url=re.compile(rf"{UPLOAD}/files/f1\?.*"),
        json={"id": "f1", "name": "new.txt", "mimeType": "text/plain"},
    )
    httpx_mock.add_response(
        method="PATCH", url=f"{DRIVE}/files/f1", json={"id": "f1"}
    )
    result = UpdateTextFileOutput.model_validate(
        await update_text_file.ainvoke(
            _args(file_id="f1", content="new", name="new.txt")
        )
    )
    assert result.success is True
    assert result.name == "new.txt"


@pytest.mark.asyncio
async def test_create_folder(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=re.compile(rf"{DRIVE}/files\?.*"),
        status_code=201,
        json={"id": "F_new", "name": "X"},
    )
    result = CreateFolderOutput.model_validate(
        await create_folder.ainvoke(_args(name="X"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_item(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=re.compile(rf"{DRIVE}/files/F1\?.*"),
        status_code=204,
    )
    result = DeleteItemOutput.model_validate(
        await delete_item.ainvoke(_args(item_id="F1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_rename_item(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=re.compile(rf"{DRIVE}/files/F1\?.*"),
        json={"id": "F1", "name": "Renamed"},
    )
    result = RenameItemOutput.model_validate(
        await rename_item.ainvoke(_args(item_id="F1", new_name="Renamed"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_move_item_reads_parents_first(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{DRIVE}/files/F1?fields=parents",
        json={"parents": ["P1", "P2"]},
    )
    httpx_mock.add_response(
        method="PATCH",
        url=re.compile(rf"{DRIVE}/files/F1\?.*"),
        json={"id": "F1", "name": "X"},
    )
    result = MoveItemOutput.model_validate(
        await move_item.ainvoke(_args(item_id="F1", destination_folder_id="Dest"))
    )
    assert result.success is True
    assert result.new_parent == "Dest"


@pytest.mark.asyncio
async def test_copy_file(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=re.compile(rf"{DRIVE}/files/F1/copy\?.*"),
        status_code=201,
        json={"id": "F_copy", "name": "Copy"},
    )
    result = CopyFileOutput.model_validate(
        await copy_file.ainvoke(_args(file_id="F1", new_name="Copy"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_file_metadata(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{DRIVE}/files/F1\?.*"),
        json={
            "id": "F1",
            "name": "X",
            "mimeType": "application/pdf",
            "size": "1024",
        },
    )
    result = GetFileMetadataOutput.model_validate(
        await get_file_metadata.ainvoke(_args(file_id="F1"))
    )
    assert result.success is True
    assert result.size == "1024"


@pytest.mark.asyncio
async def test_create_google_doc_with_content(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=re.compile(rf"{DRIVE}/files\?.*"),
        status_code=201,
        json={"id": "d1", "name": "My Doc"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS}/documents/d1:batchUpdate",
        json={"replies": []},
    )
    result = CreateGoogleDocOutput.model_validate(
        await create_google_doc.ainvoke(
            _args(name="My Doc", content="hello")
        )
    )
    assert result.success is True
    assert result.id == "d1"


@pytest.mark.asyncio
async def test_read_google_doc(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS}/documents/d1",
        json={
            "title": "My Doc",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "hello "}},
                                {"textRun": {"content": "world"}},
                            ]
                        }
                    }
                ]
            },
        },
    )
    result = ReadGoogleDocOutput.model_validate(
        await read_google_doc.ainvoke(_args(document_id="d1"))
    )
    assert result.success is True
    assert result.content == "hello world"


@pytest.mark.asyncio
async def test_update_google_doc(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS}/documents/d1",
        json={
            "title": "X",
            "body": {"content": [{"endIndex": 50}]},
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS}/documents/d1:batchUpdate",
        json={"replies": []},
    )
    result = UpdateGoogleDocOutput.model_validate(
        await update_google_doc.ainvoke(
            _args(document_id="d1", content="replaced")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_append_to_google_doc(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS}/documents/d1",
        json={"title": "X", "body": {"content": [{"endIndex": 10}]}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS}/documents/d1:batchUpdate",
        json={"replies": []},
    )
    result = AppendToGoogleDocOutput.model_validate(
        await append_to_google_doc.ainvoke(
            _args(document_id="d1", content="more")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_google_sheet(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=re.compile(rf"{SHEETS}/spreadsheets\?.*"),
        status_code=201,
        json={
            "spreadsheetId": "s1",
            "sheets": [{"properties": {"title": "Sheet1"}}],
        },
    )
    result = CreateGoogleSheetOutput.model_validate(
        await create_google_sheet.ainvoke(_args(name="Budget"))
    )
    assert result.success is True
    assert result.id == "s1"


@pytest.mark.asyncio
async def test_read_google_sheet_resolves_localized_name(httpx_mock: Any) -> None:
    # Sheet name resolution call: returns "Sayfa1" (Turkish for "Sheet1").
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{SHEETS}/spreadsheets/s1\?fields=.*"),
        json={"sheets": [{"properties": {"title": "Sayfa1"}}]},
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{SHEETS}/spreadsheets/s1/values/Sayfa1.*"),
        json={"range": "Sayfa1!A1:B2", "values": [["a", "b"], ["c", "d"]]},
    )
    result = ReadGoogleSheetOutput.model_validate(
        await read_google_sheet.ainvoke(
            _args(spreadsheet_id="s1", range="Sheet1!A1:B2")
        )
    )
    assert result.success is True
    assert result.row_count == 2


@pytest.mark.asyncio
async def test_update_google_sheet(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{SHEETS}/spreadsheets/s1\?.*"),
        json={"sheets": [{"properties": {"title": "Sheet1"}}]},
    )
    httpx_mock.add_response(
        method="PUT",
        url=re.compile(rf"{SHEETS}/spreadsheets/s1/values/.*"),
        json={"updatedRange": "Sheet1!A1:B2", "updatedCells": 4},
    )
    result = UpdateGoogleSheetOutput.model_validate(
        await update_google_sheet.ainvoke(
            _args(
                spreadsheet_id="s1",
                range="Sheet1!A1:B2",
                data=[["a", "b"], ["c", "d"]],
            )
        )
    )
    assert result.success is True
    assert result.updated_cells == 4


@pytest.mark.asyncio
async def test_format_sheet_cells_validates_format() -> None:
    result = FormatSheetCellsOutput.model_validate(
        await format_sheet_cells.ainvoke(
            _args(spreadsheet_id="s1", range="A1:B2")
        )
    )
    assert result.success is False
    assert result.error is not None and "No formatting" in result.error


@pytest.mark.asyncio
async def test_format_sheet_cells(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{SHEETS}/spreadsheets/s1:batchUpdate",
        json={"replies": []},
    )
    result = FormatSheetCellsOutput.model_validate(
        await format_sheet_cells.ainvoke(
            _args(
                spreadsheet_id="s1",
                range="A1:B2",
                background_color={"red": 1.0, "green": 0.0, "blue": 0.0},
                horizontal_alignment="CENTER",
            )
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_format_sheet_text(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{SHEETS}/spreadsheets/s1:batchUpdate",
        json={"replies": []},
    )
    result = FormatSheetTextOutput.model_validate(
        await format_sheet_text.ainvoke(
            _args(spreadsheet_id="s1", range="A1", bold=True, font_size=14)
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_google_slides(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES}/presentations",
        status_code=201,
        json={"presentationId": "p1"},
    )
    result = CreateGoogleSlidesOutput.model_validate(
        await create_google_slides.ainvoke(_args(name="Deck"))
    )
    assert result.success is True
    assert result.id == "p1"


@pytest.mark.asyncio
async def test_read_google_slides_extracts_text(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{SLIDES}/presentations/p1",
        json={
            "title": "Deck",
            "slides": [
                {
                    "objectId": "s1",
                    "pageElements": [
                        {
                            "objectId": "title_1",
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "placeholder": {"type": "TITLE"},
                                "text": {
                                    "textElements": [
                                        {"textRun": {"content": "Hello"}}
                                    ]
                                },
                            },
                        }
                    ],
                }
            ],
        },
    )
    result = ReadGoogleSlidesOutput.model_validate(
        await read_google_slides.ainvoke(_args(presentation_id="p1"))
    )
    assert result.success is True
    assert result.slide_count == 1
    assert result.slides[0]["text_content"] == "Hello"


@pytest.mark.asyncio
async def test_add_slide(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES}/presentations/p1:batchUpdate",
        json={"replies": []},
    )
    result = AddSlideOutput.model_validate(
        await add_slide.ainvoke(_args(presentation_id="p1", layout="TITLE"))
    )
    assert result.success is True
    assert result.layout == "TITLE"


@pytest.mark.asyncio
async def test_update_slide_content(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES}/presentations/p1:batchUpdate",
        json={"replies": []},
    )
    result = UpdateSlideContentOutput.model_validate(
        await update_slide_content.ainvoke(
            _args(
                presentation_id="p1",
                slide_id="s1",
                placeholder_id="ph1",
                text="New title",
            )
        )
    )
    assert result.success is True
