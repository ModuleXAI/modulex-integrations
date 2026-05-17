"""Google Slides LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "create_image",
    "create_page_element",
    "create_presentation",
    "create_slide",
    "create_table",
    "delete_page_element",
    "delete_slide",
    "delete_table_column",
    "delete_table_row",
    "find_presentation",
    "insert_table_columns",
    "insert_table_rows",
    "insert_text",
    "insert_text_into_table",
    "merge_data",
    "refresh_chart",
    "replace_all_text",
]

_SLIDES_BASE_URL = "https://slides.googleapis.com/v1"
_DRIVE_BASE_URL = "https://www.googleapis.com/drive/v3"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build Authorization + Accept headers for Google REST endpoints."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


async def _batch_update(
    presentation_id: str,
    requests: list[dict[str, Any]],
    headers: dict[str, str],
) -> tuple[int, dict[str, Any], str]:
    """POST a Slides batchUpdate and return (status_code, json_or_empty, text)."""
    url = f"{_SLIDES_BASE_URL}/presentations/{presentation_id}:batchUpdate"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(url, headers=headers, json={"requests": requests})
    text = response.text
    try:
        data = response.json()
    except Exception:
        data = {}
    return response.status_code, data, text


# --- Input schemas --------------------------------------------------------


class CreateImageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    slide_id: str = Field(description="Object ID of the slide.")
    url: str = Field(description="Publicly accessible URL of the image.")
    height: int = Field(description="Height of the image in points (1/72 inch).")
    width: int = Field(description="Width of the image in points (1/72 inch).")
    scale_x: int = Field(default=1, description="Horizontal scale factor.")
    scale_y: int = Field(default=1, description="Vertical scale factor.")
    translate_x: int = Field(default=0, description="Horizontal translation in points.")
    translate_y: int = Field(default=0, description="Vertical translation in points.")


class CreatePageElementInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    slide_id: str = Field(description="Object ID of the slide.")
    type: str = Field(description="Shape type (e.g. TEXT_BOX, RECTANGLE).")
    height: int = Field(description="Height of the shape in points.")
    width: int = Field(description="Width of the shape in points.")
    scale_x: int = Field(default=1, description="Horizontal scale factor.")
    scale_y: int = Field(default=1, description="Vertical scale factor.")
    translate_x: int = Field(default=0, description="Horizontal translation in points.")
    translate_y: int = Field(default=0, description="Vertical translation in points.")


class CreatePresentationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="Title of the new presentation.")
    source_presentation_id: str | None = Field(
        default=None,
        description=(
            "Optional ID of an existing presentation to copy. When omitted, a "
            "blank presentation is created."
        ),
    )


class CreateSlideInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    layout_id: str = Field(description="Object ID of the slide layout.")
    insertion_index: int | None = Field(
        default=None,
        description="Optional 0-based index where the slide is inserted.",
    )


class CreateTableInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    slide_id: str = Field(description="Object ID of the slide.")
    rows: int = Field(description="Number of rows.")
    columns: int = Field(description="Number of columns.")
    height: int = Field(description="Height of the table in points.")
    width: int = Field(description="Width of the table in points.")
    translate_x: int | None = Field(
        default=None,
        description="Optional horizontal translation in points.",
    )
    translate_y: int | None = Field(
        default=None,
        description="Optional vertical translation in points.",
    )


class DeletePageElementInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    page_element_id: str = Field(description="Object ID of the page element to delete.")


class DeleteSlideInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    slide_id: str = Field(description="Object ID of the slide to delete.")


class DeleteTableColumnInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    table_id: str = Field(description="Object ID of the table to modify.")
    column_index: int = Field(description="0-based column index to delete.")


class DeleteTableRowInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    table_id: str = Field(description="Object ID of the table to modify.")
    row_index: int = Field(description="0-based row index to delete.")


class FindPresentationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the presentation to fetch.")


class InsertTableColumnsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    table_id: str = Field(description="Object ID of the table.")
    column_index: int | None = Field(
        default=None, description="Optional 0-based column index of the reference cell."
    )
    insert_right: bool | None = Field(
        default=None,
        description="Whether new columns are inserted to the right of the reference cell.",
    )
    number: int = Field(default=1, description="Number of columns to insert (max 20).")


class InsertTableRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    table_id: str = Field(description="Object ID of the table.")
    row_index: int | None = Field(
        default=None, description="Optional 0-based row index of the reference cell."
    )
    insert_below: bool | None = Field(
        default=None,
        description="Whether new rows are inserted below the reference cell.",
    )
    number: int = Field(default=1, description="Number of rows to insert (max 20).")


class InsertTextInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    shape_id: str = Field(description="Object ID of the target shape.")
    text: str = Field(description="Text content to insert.")
    insertion_index: int | None = Field(
        default=None,
        description="Optional 0-based character index at which to insert text.",
    )


class InsertTextIntoTableInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    table_id: str = Field(description="Object ID of the target table.")
    text: str = Field(description="Text content to insert into the cell.")
    row_index: int | None = Field(
        default=None, description="Optional 0-based row index of the target cell."
    )
    column_index: int | None = Field(
        default=None, description="Optional 0-based column index of the target cell."
    )
    insertion_index: int | None = Field(
        default=None,
        description="Optional 0-based character index within the cell.",
    )


class MergeDataInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    source_presentation_id: str = Field(
        description="ID of the template presentation to copy."
    )
    title: str = Field(description="Title of the new (copied) presentation.")
    placeholders_and_texts: dict[str, str] = Field(
        description="Mapping of placeholder text -> replacement string."
    )
    placeholders_and_image_urls: dict[str, str] | None = Field(
        default=None,
        description="Optional mapping of placeholder text -> image URL.",
    )


class RefreshChartInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")


class ReplaceAllTextInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    presentation_id: str = Field(description="ID of the target presentation.")
    text: str = Field(description="Text snippet to search for.")
    replace_text: str = Field(description="Replacement text inserted for every match.")
    slide_ids: list[str] | None = Field(
        default=None,
        description=(
            "Optional list of slide page object IDs to restrict the search to."
        ),
    )
    match_case: bool | None = Field(
        default=None, description="Whether the text match is case-sensitive."
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateImageInput)
@serialize_pydantic_return
async def create_image(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    slide_id: str,
    url: str,
    height: int,
    width: int,
    scale_x: int = 1,
    scale_y: int = 1,
    translate_x: int = 0,
    translate_y: int = 0,
) -> CreateImageOutput:
    """Insert an image (by URL) onto a slide in a presentation."""
    if not auth_data.get("access_token"):
        return CreateImageOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    requests_body: list[dict[str, Any]] = [
        {
            "createImage": {
                "url": url,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "height": {"magnitude": height, "unit": "PT"},
                        "width": {"magnitude": width, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": scale_x,
                        "scaleY": scale_y,
                        "translateX": translate_x,
                        "translateY": translate_y,
                        "unit": "PT",
                    },
                },
            }
        }
    ]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return CreateImageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateImageOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return CreateImageOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    replies = data.get("replies") or []
    image_object_id: str | None = None
    if replies:
        first = replies[0] or {}
        image_object_id = (first.get("createImage") or {}).get("objectId")
    return CreateImageOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        image_object_id=image_object_id,
        replies=replies,
        write_control=data.get("writeControl"),
    )


@tool(args_schema=CreatePageElementInput)
@serialize_pydantic_return
async def create_page_element(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    slide_id: str,
    type: str,
    height: int,
    width: int,
    scale_x: int = 1,
    scale_y: int = 1,
    translate_x: int = 0,
    translate_y: int = 0,
) -> CreatePageElementOutput:
    """Insert a new shape page element onto a slide."""
    if not auth_data.get("access_token"):
        return CreatePageElementOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    requests_body: list[dict[str, Any]] = [
        {
            "createShape": {
                "shapeType": type,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "height": {"magnitude": height, "unit": "PT"},
                        "width": {"magnitude": width, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": scale_x,
                        "scaleY": scale_y,
                        "translateX": translate_x,
                        "translateY": translate_y,
                        "unit": "PT",
                    },
                },
            }
        }
    ]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return CreatePageElementOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreatePageElementOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return CreatePageElementOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    replies = data.get("replies") or []
    shape_object_id: str | None = None
    if replies:
        first = replies[0] or {}
        shape_object_id = (first.get("createShape") or {}).get("objectId")
    return CreatePageElementOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        shape_object_id=shape_object_id,
        replies=replies,
        write_control=data.get("writeControl"),
    )


@tool(args_schema=CreatePresentationInput)
@serialize_pydantic_return
async def create_presentation(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    source_presentation_id: str | None = None,
) -> CreatePresentationOutput:
    """Create a blank presentation or duplicate an existing one."""
    if not auth_data.get("access_token"):
        return CreatePresentationOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            if source_presentation_id:
                # Copy via Drive API.
                url = f"{_DRIVE_BASE_URL}/files/{source_presentation_id}/copy"
                response = await client.post(
                    url,
                    headers=headers,
                    params={"supportsAllDrives": "true", "fields": "*"},
                    json={"name": title},
                )
            else:
                # Create blank via Slides API.
                url = f"{_SLIDES_BASE_URL}/presentations"
                response = await client.post(url, headers=headers, json={"title": title})
    except httpx.TimeoutException:
        return CreatePresentationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreatePresentationOutput(success=False, error=f"Call failed: {exc}")

    if response.status_code not in (200, 201):
        return CreatePresentationOutput(
            success=False,
            error=f"API error ({response.status_code}): {response.text}",
        )

    try:
        data = response.json()
    except Exception:
        data = {}

    if source_presentation_id:
        # Drive copy response.
        return CreatePresentationOutput(
            success=True,
            presentation_id=data.get("id"),
            title=data.get("name"),
            copied_from=source_presentation_id,
            file_id=data.get("id"),
            web_view_link=data.get("webViewLink"),
            raw=data,
        )
    return CreatePresentationOutput(
        success=True,
        presentation_id=data.get("presentationId"),
        title=data.get("title"),
        revision_id=data.get("revisionId"),
        raw=data,
    )


@tool(args_schema=CreateSlideInput)
@serialize_pydantic_return
async def create_slide(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    layout_id: str,
    insertion_index: int | None = None,
) -> CreateSlideOutput:
    """Create a new slide in a presentation."""
    if not auth_data.get("access_token"):
        return CreateSlideOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    create_slide_request: dict[str, Any] = {
        "slideLayoutReference": {"layoutId": layout_id},
    }
    if insertion_index is not None:
        create_slide_request["insertionIndex"] = insertion_index
    requests_body: list[dict[str, Any]] = [{"createSlide": create_slide_request}]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return CreateSlideOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSlideOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return CreateSlideOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    replies = data.get("replies") or []
    slide_object_id: str | None = None
    if replies:
        first = replies[0] or {}
        slide_object_id = (first.get("createSlide") or {}).get("objectId")
    return CreateSlideOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        slide_object_id=slide_object_id,
        replies=replies,
        write_control=data.get("writeControl"),
    )


@tool(args_schema=CreateTableInput)
@serialize_pydantic_return
async def create_table(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    slide_id: str,
    rows: int,
    columns: int,
    height: int,
    width: int,
    translate_x: int | None = None,
    translate_y: int | None = None,
) -> CreateTableOutput:
    """Create a new table on a slide."""
    if not auth_data.get("access_token"):
        return CreateTableOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    transform: dict[str, Any] = {
        "scaleX": 1,
        "scaleY": 1,
        "unit": "PT",
    }
    if translate_x is not None:
        transform["translateX"] = translate_x
    if translate_y is not None:
        transform["translateY"] = translate_y
    requests_body: list[dict[str, Any]] = [
        {
            "createTable": {
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "height": {"magnitude": height, "unit": "PT"},
                        "width": {"magnitude": width, "unit": "PT"},
                    },
                    "transform": transform,
                },
                "rows": rows,
                "columns": columns,
            }
        }
    ]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return CreateTableOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTableOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return CreateTableOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    replies = data.get("replies") or []
    table_object_id: str | None = None
    if replies:
        first = replies[0] or {}
        table_object_id = (first.get("createTable") or {}).get("objectId")
    return CreateTableOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        table_object_id=table_object_id,
        replies=replies,
        write_control=data.get("writeControl"),
    )


@tool(args_schema=DeletePageElementInput)
@serialize_pydantic_return
async def delete_page_element(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    page_element_id: str,
) -> DeletePageElementOutput:
    """Delete a page element from a slide."""
    if not auth_data.get("access_token"):
        return DeletePageElementOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    requests_body: list[dict[str, Any]] = [
        {"deleteObject": {"objectId": page_element_id}}
    ]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return DeletePageElementOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeletePageElementOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return DeletePageElementOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    return DeletePageElementOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        deleted_object_id=page_element_id,
        replies=data.get("replies") or [],
        write_control=data.get("writeControl"),
    )


@tool(args_schema=DeleteSlideInput)
@serialize_pydantic_return
async def delete_slide(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    slide_id: str,
) -> DeleteSlideOutput:
    """Delete a slide from a presentation."""
    if not auth_data.get("access_token"):
        return DeleteSlideOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    requests_body: list[dict[str, Any]] = [
        {"deleteObject": {"objectId": slide_id}}
    ]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return DeleteSlideOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteSlideOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return DeleteSlideOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    return DeleteSlideOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        deleted_slide_id=slide_id,
        replies=data.get("replies") or [],
        write_control=data.get("writeControl"),
    )


@tool(args_schema=DeleteTableColumnInput)
@serialize_pydantic_return
async def delete_table_column(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    table_id: str,
    column_index: int,
) -> DeleteTableColumnOutput:
    """Delete a column from a table."""
    if not auth_data.get("access_token"):
        return DeleteTableColumnOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    requests_body: list[dict[str, Any]] = [
        {
            "deleteTableColumn": {
                "tableObjectId": table_id,
                "cellLocation": {"columnIndex": column_index},
            }
        }
    ]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return DeleteTableColumnOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteTableColumnOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return DeleteTableColumnOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    return DeleteTableColumnOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        replies=data.get("replies") or [],
        write_control=data.get("writeControl"),
    )


@tool(args_schema=DeleteTableRowInput)
@serialize_pydantic_return
async def delete_table_row(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    table_id: str,
    row_index: int,
) -> DeleteTableRowOutput:
    """Delete a row from a table."""
    if not auth_data.get("access_token"):
        return DeleteTableRowOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    requests_body: list[dict[str, Any]] = [
        {
            "deleteTableRow": {
                "tableObjectId": table_id,
                "cellLocation": {"rowIndex": row_index},
            }
        }
    ]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return DeleteTableRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteTableRowOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return DeleteTableRowOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    return DeleteTableRowOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        replies=data.get("replies") or [],
        write_control=data.get("writeControl"),
    )


@tool(args_schema=FindPresentationInput)
@serialize_pydantic_return
async def find_presentation(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
) -> FindPresentationOutput:
    """Fetch full metadata about a Google Slides presentation."""
    if not auth_data.get("access_token"):
        return FindPresentationOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_SLIDES_BASE_URL}/presentations/{presentation_id}",
                headers=headers,
            )
    except httpx.TimeoutException:
        return FindPresentationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindPresentationOutput(success=False, error=f"Call failed: {exc}")

    if response.status_code != 200:
        return FindPresentationOutput(
            success=False,
            error=f"API error ({response.status_code}): {response.text}",
        )

    try:
        data = response.json()
    except Exception:
        data = {}

    return FindPresentationOutput(
        success=True,
        presentation_id=data.get("presentationId"),
        title=data.get("title"),
        locale=data.get("locale"),
        revision_id=data.get("revisionId"),
        page_size=data.get("pageSize"),
        slides=data.get("slides") or [],
        layouts=data.get("layouts") or [],
        masters=data.get("masters") or [],
        notes_master=data.get("notesMaster"),
        raw=data,
    )


@tool(args_schema=InsertTableColumnsInput)
@serialize_pydantic_return
async def insert_table_columns(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    table_id: str,
    column_index: int | None = None,
    insert_right: bool | None = None,
    number: int = 1,
) -> InsertTableColumnsOutput:
    """Insert new columns into a table."""
    if not auth_data.get("access_token"):
        return InsertTableColumnsOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    insert_req: dict[str, Any] = {
        "tableObjectId": table_id,
        "number": number,
    }
    if column_index is not None:
        insert_req["cellLocation"] = {"columnIndex": column_index}
    if insert_right is not None:
        insert_req["insertRight"] = insert_right
    requests_body: list[dict[str, Any]] = [{"insertTableColumns": insert_req}]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return InsertTableColumnsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertTableColumnsOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return InsertTableColumnsOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    return InsertTableColumnsOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        replies=data.get("replies") or [],
        write_control=data.get("writeControl"),
    )


@tool(args_schema=InsertTableRowsInput)
@serialize_pydantic_return
async def insert_table_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    table_id: str,
    row_index: int | None = None,
    insert_below: bool | None = None,
    number: int = 1,
) -> InsertTableRowsOutput:
    """Insert new rows into a table."""
    if not auth_data.get("access_token"):
        return InsertTableRowsOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    insert_req: dict[str, Any] = {
        "tableObjectId": table_id,
        "number": number,
    }
    if row_index is not None:
        insert_req["cellLocation"] = {"rowIndex": row_index}
    if insert_below is not None:
        insert_req["insertBelow"] = insert_below
    requests_body: list[dict[str, Any]] = [{"insertTableRows": insert_req}]
    try:
        status, data, text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return InsertTableRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertTableRowsOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return InsertTableRowsOutput(
            success=False,
            error=f"API error ({status}): {text}",
        )

    return InsertTableRowsOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        replies=data.get("replies") or [],
        write_control=data.get("writeControl"),
    )


@tool(args_schema=InsertTextInput)
@serialize_pydantic_return
async def insert_text(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    shape_id: str,
    text: str,
    insertion_index: int | None = None,
) -> InsertTextOutput:
    """Insert text into a shape on a slide."""
    if not auth_data.get("access_token"):
        return InsertTextOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    insert_req: dict[str, Any] = {
        "objectId": shape_id,
        "text": text,
    }
    if insertion_index is not None:
        insert_req["insertionIndex"] = insertion_index
    requests_body: list[dict[str, Any]] = [{"insertText": insert_req}]
    try:
        status, data, body_text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return InsertTextOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertTextOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return InsertTextOutput(
            success=False,
            error=f"API error ({status}): {body_text}",
        )

    return InsertTextOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        replies=data.get("replies") or [],
        write_control=data.get("writeControl"),
    )


@tool(args_schema=InsertTextIntoTableInput)
@serialize_pydantic_return
async def insert_text_into_table(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    table_id: str,
    text: str,
    row_index: int | None = None,
    column_index: int | None = None,
    insertion_index: int | None = None,
) -> InsertTextIntoTableOutput:
    """Insert text into a specific cell of a table."""
    if not auth_data.get("access_token"):
        return InsertTextIntoTableOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    cell_location: dict[str, Any] = {}
    if row_index is not None:
        cell_location["rowIndex"] = row_index
    if column_index is not None:
        cell_location["columnIndex"] = column_index
    insert_req: dict[str, Any] = {
        "objectId": table_id,
        "text": text,
        "cellLocation": cell_location,
    }
    if insertion_index is not None:
        insert_req["insertionIndex"] = insertion_index
    requests_body: list[dict[str, Any]] = [{"insertText": insert_req}]
    try:
        status, data, body_text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return InsertTextIntoTableOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertTextIntoTableOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return InsertTextIntoTableOutput(
            success=False,
            error=f"API error ({status}): {body_text}",
        )

    return InsertTextIntoTableOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        replies=data.get("replies") or [],
        write_control=data.get("writeControl"),
    )


@tool(args_schema=MergeDataInput)
@serialize_pydantic_return
async def merge_data(
    auth_type: str,
    auth_data: dict[str, Any],
    source_presentation_id: str,
    title: str,
    placeholders_and_texts: dict[str, str],
    placeholders_and_image_urls: dict[str, str] | None = None,
) -> MergeDataOutput:
    """Duplicate a template presentation and merge placeholder data into it."""
    if not auth_data.get("access_token"):
        return MergeDataOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Step 1: copy source via Drive.
            copy_response = await client.post(
                f"{_DRIVE_BASE_URL}/files/{source_presentation_id}/copy",
                headers=headers,
                params={"supportsAllDrives": "true", "fields": "*"},
                json={"name": title},
            )
            if copy_response.status_code not in (200, 201):
                return MergeDataOutput(
                    success=False,
                    error=(
                        f"Drive copy error ({copy_response.status_code}): "
                        f"{copy_response.text}"
                    ),
                )
            copy_data = copy_response.json()
            new_presentation_id = copy_data.get("id")
            if not new_presentation_id:
                return MergeDataOutput(
                    success=False,
                    error="Drive copy did not return a new file id.",
                )

            # Step 2: build batchUpdate requests.
            text_requests: list[dict[str, Any]] = [
                {
                    "replaceAllText": {
                        "containsText": {"text": k, "matchCase": True},
                        "replaceText": v,
                    }
                }
                for k, v in (placeholders_and_texts or {}).items()
            ]
            image_requests: list[dict[str, Any]] = [
                {
                    "replaceAllShapesWithImage": {
                        "imageUrl": v,
                        "replaceMethod": "CENTER_INSIDE",
                        "containsText": {"text": k, "matchCase": True},
                    }
                }
                for k, v in (placeholders_and_image_urls or {}).items()
            ]
            all_requests = text_requests + image_requests

            # Step 3: batchUpdate the new copy.
            bu_response = await client.post(
                f"{_SLIDES_BASE_URL}/presentations/{new_presentation_id}:batchUpdate",
                headers=headers,
                json={"requests": all_requests},
            )
    except httpx.TimeoutException:
        return MergeDataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return MergeDataOutput(success=False, error=f"Call failed: {exc}")

    if bu_response.status_code != 200:
        return MergeDataOutput(
            success=False,
            error=(
                f"batchUpdate error ({bu_response.status_code}): "
                f"{bu_response.text}"
            ),
        )

    try:
        bu_data = bu_response.json()
    except Exception:
        bu_data = {}

    return MergeDataOutput(
        success=True,
        presentation_id=bu_data.get("presentationId") or new_presentation_id,
        copied_from_id=source_presentation_id,
        new_presentation_title=title,
        replies=bu_data.get("replies") or [],
        write_control=bu_data.get("writeControl"),
    )


@tool(args_schema=RefreshChartInput)
@serialize_pydantic_return
async def refresh_chart(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
) -> RefreshChartOutput:
    """Refresh every Sheets chart embedded in a presentation."""
    if not auth_data.get("access_token"):
        return RefreshChartOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Step 1: fetch presentation to discover sheetsChart elements.
            get_response = await client.get(
                f"{_SLIDES_BASE_URL}/presentations/{presentation_id}",
                headers=headers,
            )
            if get_response.status_code != 200:
                return RefreshChartOutput(
                    success=False,
                    error=(
                        f"Slides get error ({get_response.status_code}): "
                        f"{get_response.text}"
                    ),
                )
            presentation = get_response.json()
            chart_ids: list[str] = []
            for slide in presentation.get("slides") or []:
                for element in slide.get("pageElements") or []:
                    sheets_chart = element.get("sheetsChart")
                    if sheets_chart and sheets_chart.get("spreadsheetId"):
                        obj_id = element.get("objectId")
                        if obj_id:
                            chart_ids.append(obj_id)

            if not chart_ids:
                return RefreshChartOutput(
                    success=True,
                    presentation_id=presentation_id,
                    refreshed_chart_count=0,
                    refreshed_chart_ids=[],
                )

            # Step 2: issue one batchUpdate per chart (mirrors pipedream loop).
            for chart_id in chart_ids:
                bu_response = await client.post(
                    f"{_SLIDES_BASE_URL}/presentations/{presentation_id}:batchUpdate",
                    headers=headers,
                    json={
                        "requests": [
                            {"refreshSheetsChart": {"objectId": chart_id}}
                        ]
                    },
                )
                if bu_response.status_code != 200:
                    return RefreshChartOutput(
                        success=False,
                        presentation_id=presentation_id,
                        error=(
                            f"refreshSheetsChart error for {chart_id} "
                            f"({bu_response.status_code}): {bu_response.text}"
                        ),
                        refreshed_chart_count=0,
                        refreshed_chart_ids=[],
                    )
    except httpx.TimeoutException:
        return RefreshChartOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RefreshChartOutput(success=False, error=f"Call failed: {exc}")

    return RefreshChartOutput(
        success=True,
        presentation_id=presentation_id,
        refreshed_chart_count=len(chart_ids),
        refreshed_chart_ids=chart_ids,
    )


@tool(args_schema=ReplaceAllTextInput)
@serialize_pydantic_return
async def replace_all_text(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    text: str,
    replace_text: str,
    slide_ids: list[str] | None = None,
    match_case: bool | None = None,
) -> ReplaceAllTextOutput:
    """Replace every occurrence of a given text in a presentation."""
    if not auth_data.get("access_token"):
        return ReplaceAllTextOutput(success=False, error="Missing access token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    contains_text: dict[str, Any] = {"text": text}
    if match_case is not None:
        contains_text["matchCase"] = match_case
    replace_req: dict[str, Any] = {
        "replaceText": replace_text,
        "containsText": contains_text,
    }
    if slide_ids:
        replace_req["pageObjectIds"] = slide_ids
    requests_body: list[dict[str, Any]] = [{"replaceAllText": replace_req}]
    try:
        status, data, body_text = await _batch_update(presentation_id, requests_body, headers)
    except httpx.TimeoutException:
        return ReplaceAllTextOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ReplaceAllTextOutput(success=False, error=f"Call failed: {exc}")

    if status != 200:
        return ReplaceAllTextOutput(
            success=False,
            error=f"API error ({status}): {body_text}",
        )

    replies = data.get("replies") or []
    total_changed: int | None = None
    if replies:
        first = replies[0] or {}
        replace_reply = first.get("replaceAllText") or {}
        if "occurrencesChanged" in replace_reply:
            total_changed = replace_reply.get("occurrencesChanged")
    return ReplaceAllTextOutput(
        success=True,
        presentation_id=data.get("presentationId") or presentation_id,
        total_occurrences_changed=total_changed,
        replies=replies,
        write_control=data.get("writeControl"),
    )
