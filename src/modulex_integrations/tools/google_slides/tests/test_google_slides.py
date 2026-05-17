"""Happy-path tests for every google_slides @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_slides import (
    TOOLS,
    create_image,
    create_page_element,
    create_presentation,
    create_slide,
    create_table,
    delete_page_element,
    delete_slide,
    delete_table_column,
    delete_table_row,
    find_presentation,
    insert_table_columns,
    insert_table_rows,
    insert_text,
    insert_text_into_table,
    manifest,
    merge_data,
    refresh_chart,
    replace_all_text,
)
from modulex_integrations.tools.google_slides.outputs import (
    CreateImageOutput,
    CreatePageElementOutput,
    CreatePresentationOutput,
    CreateSlideOutput,
    CreateTableOutput,
    DeletePageElementOutput,
    DeleteSlideOutput,
    DeleteTableColumnOutput,
    DeleteTableRowOutput,
    FindPresentationOutput,
    InsertTableColumnsOutput,
    InsertTableRowsOutput,
    InsertTextIntoTableOutput,
    InsertTextOutput,
    MergeDataOutput,
    RefreshChartOutput,
    ReplaceAllTextOutput,
)

SLIDES_API = "https://slides.googleapis.com/v1"
DRIVE_API = "https://www.googleapis.com/drive/v3"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_17_actions(self) -> None:
        assert len(manifest.actions) == 17

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_image(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{"createImage": {"objectId": "IMG_OBJ_1"}}],
            "writeControl": {"requiredRevisionId": "rev_1"},
        },
    )

    result_dict = await create_image.ainvoke(
        _args(
            presentation_id="PRESID",
            slide_id="SLIDE_1",
            url="https://example.com/img.png",
            height=100,
            width=200,
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateImageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.image_object_id == "IMG_OBJ_1"


@pytest.mark.asyncio
async def test_create_page_element(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{"createShape": {"objectId": "SHAPE_OBJ_1"}}],
        },
    )

    result_dict = await create_page_element.ainvoke(
        _args(
            presentation_id="PRESID",
            slide_id="SLIDE_1",
            type="TEXT_BOX",
            height=80,
            width=160,
        )
    )

    result = CreatePageElementOutput.model_validate(result_dict)
    assert result.success is True
    assert result.shape_object_id == "SHAPE_OBJ_1"


@pytest.mark.asyncio
async def test_create_presentation_blank(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations",
        json={
            # TODO: fill in a representative Slides presentations.create response
            "presentationId": "NEW_PRESID",
            "title": "My Deck",
            "revisionId": "rev_1",
        },
    )

    result_dict = await create_presentation.ainvoke(_args(title="My Deck"))

    result = CreatePresentationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.presentation_id == "NEW_PRESID"


@pytest.mark.asyncio
async def test_create_presentation_copy(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DRIVE_API}/files/SRC_ID/copy?supportsAllDrives=true&fields=*",
        json={
            # TODO: fill in a representative Drive files.copy response
            "id": "COPIED_ID",
            "name": "My Deck Copy",
            "webViewLink": "https://docs.google.com/presentation/d/COPIED_ID/edit",
        },
    )

    result_dict = await create_presentation.ainvoke(
        _args(title="My Deck Copy", source_presentation_id="SRC_ID")
    )

    result = CreatePresentationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.presentation_id == "COPIED_ID"
    assert result.copied_from == "SRC_ID"


@pytest.mark.asyncio
async def test_create_slide(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{"createSlide": {"objectId": "NEW_SLIDE_1"}}],
        },
    )

    result_dict = await create_slide.ainvoke(
        _args(presentation_id="PRESID", layout_id="LAYOUT_1")
    )

    result = CreateSlideOutput.model_validate(result_dict)
    assert result.success is True
    assert result.slide_object_id == "NEW_SLIDE_1"


@pytest.mark.asyncio
async def test_create_table(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{"createTable": {"objectId": "TABLE_1"}}],
        },
    )

    result_dict = await create_table.ainvoke(
        _args(
            presentation_id="PRESID",
            slide_id="SLIDE_1",
            rows=3,
            columns=4,
            height=200,
            width=300,
        )
    )

    result = CreateTableOutput.model_validate(result_dict)
    assert result.success is True
    assert result.table_object_id == "TABLE_1"


@pytest.mark.asyncio
async def test_delete_page_element(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await delete_page_element.ainvoke(
        _args(presentation_id="PRESID", page_element_id="ELEMENT_1")
    )

    result = DeletePageElementOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted_object_id == "ELEMENT_1"


@pytest.mark.asyncio
async def test_delete_slide(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await delete_slide.ainvoke(
        _args(presentation_id="PRESID", slide_id="SLIDE_1")
    )

    result = DeleteSlideOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted_slide_id == "SLIDE_1"


@pytest.mark.asyncio
async def test_delete_table_column(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await delete_table_column.ainvoke(
        _args(presentation_id="PRESID", table_id="TABLE_1", column_index=2)
    )

    result = DeleteTableColumnOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_table_row(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await delete_table_row.ainvoke(
        _args(presentation_id="PRESID", table_id="TABLE_1", row_index=1)
    )

    result = DeleteTableRowOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_find_presentation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{SLIDES_API}/presentations/PRESID",
        json={
            # TODO: fill in a representative Slides presentations.get response
            "presentationId": "PRESID",
            "title": "My Deck",
            "revisionId": "rev_1",
            "locale": "en",
            "pageSize": {"width": {"magnitude": 9144000, "unit": "EMU"}},
            "slides": [{"objectId": "S1", "pageElements": []}],
            "layouts": [],
            "masters": [],
        },
    )

    result_dict = await find_presentation.ainvoke(_args(presentation_id="PRESID"))

    result = FindPresentationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "My Deck"


@pytest.mark.asyncio
async def test_insert_table_columns(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await insert_table_columns.ainvoke(
        _args(presentation_id="PRESID", table_id="TABLE_1", number=2)
    )

    result = InsertTableColumnsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_insert_table_rows(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await insert_table_rows.ainvoke(
        _args(presentation_id="PRESID", table_id="TABLE_1", number=3)
    )

    result = InsertTableRowsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_insert_text(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await insert_text.ainvoke(
        _args(presentation_id="PRESID", shape_id="SHAPE_1", text="Hello")
    )

    result = InsertTextOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_insert_text_into_table(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await insert_text_into_table.ainvoke(
        _args(
            presentation_id="PRESID",
            table_id="TABLE_1",
            text="cell text",
            row_index=0,
            column_index=1,
        )
    )

    result = InsertTextIntoTableOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_merge_data(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DRIVE_API}/files/SRC_ID/copy?supportsAllDrives=true&fields=*",
        json={
            # TODO: fill in a representative Drive files.copy response
            "id": "COPIED_ID",
            "name": "Merged Deck",
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/COPIED_ID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "COPIED_ID",
            "replies": [{}],
        },
    )

    result_dict = await merge_data.ainvoke(
        _args(
            source_presentation_id="SRC_ID",
            title="Merged Deck",
            placeholders_and_texts={"{{name}}": "Alice"},
        )
    )

    result = MergeDataOutput.model_validate(result_dict)
    assert result.success is True
    assert result.presentation_id == "COPIED_ID"


@pytest.mark.asyncio
async def test_refresh_chart(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{SLIDES_API}/presentations/PRESID",
        json={
            # TODO: fill in a representative Slides presentations.get response
            "presentationId": "PRESID",
            "slides": [
                {
                    "objectId": "S1",
                    "pageElements": [
                        {
                            "objectId": "CHART_1",
                            "sheetsChart": {"spreadsheetId": "SHEET_1"},
                        }
                    ],
                }
            ],
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{}],
        },
    )

    result_dict = await refresh_chart.ainvoke(_args(presentation_id="PRESID"))

    result = RefreshChartOutput.model_validate(result_dict)
    assert result.success is True
    assert result.refreshed_chart_count == 1
    assert result.refreshed_chart_ids == ["CHART_1"]


@pytest.mark.asyncio
async def test_replace_all_text(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{SLIDES_API}/presentations/PRESID:batchUpdate",
        json={
            # TODO: fill in a representative Slides batchUpdate response
            "presentationId": "PRESID",
            "replies": [{"replaceAllText": {"occurrencesChanged": 3}}],
        },
    )

    result_dict = await replace_all_text.ainvoke(
        _args(
            presentation_id="PRESID",
            text="old",
            replace_text="new",
        )
    )

    result = ReplaceAllTextOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_occurrences_changed == 3


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_create_image_missing_token() -> None:
    """create_image must fail fast when auth_data has no access_token."""
    result_dict = await create_image.ainvoke(
        {
            "auth_type": "oauth2",
            "auth_data": {},
            "presentation_id": "PRESID",
            "slide_id": "SLIDE_1",
            "url": "https://example.com/img.png",
            "height": 100,
            "width": 200,
        }
    )

    assert isinstance(result_dict, dict)
    result = CreateImageOutput.model_validate(result_dict)
    assert result.success is False
    assert "access token" in (result.error or "").lower()
