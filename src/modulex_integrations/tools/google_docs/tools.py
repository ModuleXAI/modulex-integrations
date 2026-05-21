"""Google Docs LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_docs.outputs import (
    AppendImageOutput,
    AppendTextOutput,
    CreateDocumentFromTemplateOutput,
    CreateDocumentOutput,
    DocumentFile,
    FindDocumentOutput,
    GetDocumentOutput,
    GetTabContentOutput,
    InsertPageBreakOutput,
    InsertTableOutput,
    InsertTextOutput,
    ReplaceImageOutput,
    ReplaceTextOutput,
    TabContent,
)

__all__ = [
    "append_image",
    "append_text",
    "create_document",
    "create_document_from_template",
    "find_document",
    "get_document",
    "get_tab_content",
    "insert_page_break",
    "insert_table",
    "insert_text",
    "replace_image",
    "replace_text",
]

_DOCS_BASE_URL = "https://docs.googleapis.com/v1"
_DRIVE_BASE_URL = "https://www.googleapis.com/drive/v3"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class AppendImageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document to append the image to")
    image_uri: str = Field(description="The URL of the image to insert into the document")
    append_at_beginning: bool = Field(default=False, description="Whether to append at the beginning (true) or end (false) of the document")


class AppendTextInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document to append text to")
    text: str = Field(description="The text to append to the document")
    append_at_beginning: bool = Field(default=False, description="Whether to append at the beginning (true) or end (false) of the document")


class CreateDocumentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="Title of the new document")
    text: str | None = Field(default=None, description="Text content to insert into the document")
    folder_id: str | None = Field(default=None, description="ID of the Google Drive folder to place the document in")


class CreateDocumentFromTemplateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    template_id: str = Field(description="The ID of the template document containing {{placeholder}} variables")
    name: str = Field(description="Name for the new document")
    replace_values: dict[str, str] = Field(description="Key-value pairs to replace placeholders in the template (keys without curly braces)")
    folder_id: str | None = Field(default=None, description="ID of the Google Drive folder for the new document")


class FindDocumentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name_search_term: str | None = Field(default=None, description="Search for a document by name (equivalent to 'name contains' query)")
    search_query: str | None = Field(default=None, description="Custom Google Drive search query. If specified, name_search_term is ignored")


class GetDocumentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document to retrieve")
    include_tabs_content: bool = Field(default=False, description="Whether to populate the tabs field instead of the body field")


class GetTabContentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document")
    tab_ids: list[str] = Field(description="List of tab IDs to retrieve content for")


class InsertPageBreakInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document")
    index: int = Field(default=1, description="The index position to insert the page break at")
    tab_id: str | None = Field(default=None, description="The tab ID to insert the page break into")


class InsertTableInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document")
    rows: int = Field(description="The number of rows in the table")
    columns: int = Field(description="The number of columns in the table")
    index: int = Field(default=1, description="The index position to insert the table at")
    tab_id: str | None = Field(default=None, description="The tab ID to insert the table into")


class InsertTextInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document")
    text: str = Field(description="The text to insert")
    index: int = Field(default=1, description="The index position to insert the text at")
    tab_id: str | None = Field(default=None, description="The tab ID to insert the text into")


class ReplaceImageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document")
    image_id: str = Field(description="The ID of the image to be replaced (from the document's inlineObjects)")
    image_uri: str = Field(description="The URL of the new image to replace with")


class ReplaceTextInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    doc_id: str = Field(description="The ID of the document")
    text_to_replace: str = Field(description="The text to find and replace")
    new_text: str = Field(description="The replacement text")
    match_case: bool = Field(default=False, description="Whether the search is case-sensitive")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AppendImageInput)
@serialize_pydantic_return
async def append_image(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    image_uri: str,
    append_at_beginning: bool = False,
) -> AppendImageOutput:
    """Append an image to the end of a Google Docs document."""
    if not auth_data.get("access_token"):
        return AppendImageOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            doc_resp = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
            )
            if doc_resp.status_code != 200:
                return AppendImageOutput(
                    success=False,
                    error=f"Failed to get document ({doc_resp.status_code}): {doc_resp.text}",
                )
            doc_data = doc_resp.json()
            body_content = doc_data.get("body", {}).get("content", [])
            end_index = 1
            if body_content:
                last_element = body_content[-1]
                end_index = last_element.get("endIndex", 1) - 1

            insert_index = 1 if append_at_beginning else max(end_index, 1)

            requests_body: list[dict[str, Any]] = [
                {
                    "insertInlineImage": {
                        "uri": image_uri,
                        "location": {"index": insert_index},
                    }
                }
            ]

            response = await client.post(
                f"{_DOCS_BASE_URL}/documents/{doc_id}:batchUpdate",
                headers={**headers, "Content-Type": "application/json"},
                json={"requests": requests_body},
            )
            if response.status_code != 200:
                return AppendImageOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )
    except httpx.TimeoutException:
        return AppendImageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AppendImageOutput(success=False, error=f"Call failed: {exc}")

    return AppendImageOutput(
        success=True,
        document_id=doc_id,
        title=doc_data.get("title"),
    )


@tool(args_schema=AppendTextInput)
@serialize_pydantic_return
async def append_text(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    text: str,
    append_at_beginning: bool = False,
) -> AppendTextOutput:
    """Append text to an existing Google Docs document."""
    if not auth_data.get("access_token"):
        return AppendTextOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            doc_resp = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
            )
            if doc_resp.status_code != 200:
                return AppendTextOutput(
                    success=False,
                    error=f"Failed to get document ({doc_resp.status_code}): {doc_resp.text}",
                )
            doc_data = doc_resp.json()
            body_content = doc_data.get("body", {}).get("content", [])
            end_index = 1
            if body_content:
                last_element = body_content[-1]
                end_index = last_element.get("endIndex", 1) - 1

            insert_index = 1 if append_at_beginning else max(end_index, 1)

            requests_body: list[dict[str, Any]] = [
                {
                    "insertText": {
                        "text": text,
                        "location": {"index": insert_index},
                    }
                }
            ]

            response = await client.post(
                f"{_DOCS_BASE_URL}/documents/{doc_id}:batchUpdate",
                headers={**headers, "Content-Type": "application/json"},
                json={"requests": requests_body},
            )
            if response.status_code != 200:
                return AppendTextOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )
    except httpx.TimeoutException:
        return AppendTextOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AppendTextOutput(success=False, error=f"Call failed: {exc}")

    return AppendTextOutput(
        success=True,
        document_id=doc_id,
        title=doc_data.get("title"),
    )


@tool(args_schema=CreateDocumentInput)
@serialize_pydantic_return
async def create_document(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    text: str | None = None,
    folder_id: str | None = None,
) -> CreateDocumentOutput:
    """Create a new Google Docs document with optional text content."""
    if not auth_data.get("access_token"):
        return CreateDocumentOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            create_resp = await client.post(
                f"{_DOCS_BASE_URL}/documents",
                headers={**headers, "Content-Type": "application/json"},
                json={"title": title},
            )
            if create_resp.status_code != 200:
                return CreateDocumentOutput(
                    success=False,
                    error=f"Failed to create document ({create_resp.status_code}): {create_resp.text}",
                )
            doc_data = create_resp.json()
            document_id = doc_data.get("documentId")

            if text:
                insert_requests: list[dict[str, Any]] = [
                    {
                        "insertText": {
                            "text": text,
                            "location": {"index": 1},
                        }
                    }
                ]
                await client.post(
                    f"{_DOCS_BASE_URL}/documents/{document_id}:batchUpdate",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"requests": insert_requests},
                )

            if folder_id and document_id:
                get_file_resp = await client.get(
                    f"{_DRIVE_BASE_URL}/files/{document_id}",
                    headers=headers,
                    params={"fields": "parents"},
                )
                if get_file_resp.status_code == 200:
                    parents = get_file_resp.json().get("parents", [])
                    remove_parents = ",".join(parents) if parents else ""
                    await client.patch(
                        f"{_DRIVE_BASE_URL}/files/{document_id}",
                        headers=headers,
                        params={
                            "addParents": folder_id,
                            "removeParents": remove_parents,
                        },
                    )
    except httpx.TimeoutException:
        return CreateDocumentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDocumentOutput(success=False, error=f"Call failed: {exc}")

    return CreateDocumentOutput(
        success=True,
        document_id=document_id,
        title=title,
    )


@tool(args_schema=CreateDocumentFromTemplateInput)
@serialize_pydantic_return
async def create_document_from_template(
    auth_type: str,
    auth_data: dict[str, Any],
    template_id: str,
    name: str,
    replace_values: dict[str, str],
    folder_id: str | None = None,
) -> CreateDocumentFromTemplateOutput:
    """Create a new Google Docs document from a template with placeholder replacement."""
    if not auth_data.get("access_token"):
        return CreateDocumentFromTemplateOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            copy_resp = await client.post(
                f"{_DRIVE_BASE_URL}/files/{template_id}/copy",
                headers={**headers, "Content-Type": "application/json"},
                json={"name": name},
            )
            if copy_resp.status_code != 200:
                return CreateDocumentFromTemplateOutput(
                    success=False,
                    error=f"Failed to copy template ({copy_resp.status_code}): {copy_resp.text}",
                )
            copy_data = copy_resp.json()
            new_doc_id = copy_data.get("id")

            if replace_values and new_doc_id:
                replace_requests: list[dict[str, Any]] = [
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{" + key + "}}",
                                "matchCase": True,
                            },
                            "replaceText": value,
                        }
                    }
                    for key, value in replace_values.items()
                ]
                await client.post(
                    f"{_DOCS_BASE_URL}/documents/{new_doc_id}:batchUpdate",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"requests": replace_requests},
                )

            if folder_id and new_doc_id:
                get_file_resp = await client.get(
                    f"{_DRIVE_BASE_URL}/files/{new_doc_id}",
                    headers=headers,
                    params={"fields": "parents"},
                )
                if get_file_resp.status_code == 200:
                    parents = get_file_resp.json().get("parents", [])
                    remove_parents = ",".join(parents) if parents else ""
                    await client.patch(
                        f"{_DRIVE_BASE_URL}/files/{new_doc_id}",
                        headers=headers,
                        params={
                            "addParents": folder_id,
                            "removeParents": remove_parents,
                        },
                    )
    except httpx.TimeoutException:
        return CreateDocumentFromTemplateOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDocumentFromTemplateOutput(success=False, error=f"Call failed: {exc}")

    return CreateDocumentFromTemplateOutput(
        success=True,
        google_doc_id=new_doc_id,
        name=name,
    )


@tool(args_schema=FindDocumentInput)
@serialize_pydantic_return
async def find_document(
    auth_type: str,
    auth_data: dict[str, Any],
    name_search_term: str | None = None,
    search_query: str | None = None,
) -> FindDocumentOutput:
    """Search for Google Docs documents by name or query using Google Drive search."""
    if not auth_data.get("access_token"):
        return FindDocumentOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        if search_query:
            q = search_query
        elif name_search_term:
            q = f"name contains '{name_search_term}' and mimeType = 'application/vnd.google-apps.document'"
        else:
            q = "mimeType = 'application/vnd.google-apps.document'"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_DRIVE_BASE_URL}/files",
                headers=headers,
                params={
                    "q": q,
                    "fields": "files(id,name,mimeType)",
                },
            )
            if response.status_code != 200:
                return FindDocumentOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )
            data = response.json()
    except httpx.TimeoutException:
        return FindDocumentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindDocumentOutput(success=False, error=f"Call failed: {exc}")

    files = [
        DocumentFile(
            id=f.get("id"),
            name=f.get("name"),
            mime_type=f.get("mimeType"),
        )
        for f in data.get("files", [])
    ]
    return FindDocumentOutput(success=True, files=files)


@tool(args_schema=GetDocumentInput)
@serialize_pydantic_return
async def get_document(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    include_tabs_content: bool = False,
) -> GetDocumentOutput:
    """Get the contents of a Google Docs document."""
    if not auth_data.get("access_token"):
        return GetDocumentOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        params: dict[str, str] = {}
        if include_tabs_content:
            params["includeTabsContent"] = "true"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
                params=params,
            )
            if response.status_code != 200:
                return GetDocumentOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )
            data = response.json()
    except httpx.TimeoutException:
        return GetDocumentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDocumentOutput(success=False, error=f"Call failed: {exc}")

    return GetDocumentOutput(
        success=True,
        document_id=data.get("documentId"),
        title=data.get("title"),
        body=data.get("body"),
    )


@tool(args_schema=GetTabContentInput)
@serialize_pydantic_return
async def get_tab_content(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    tab_ids: list[str],
) -> GetTabContentOutput:
    """Get the content of specific tabs in a Google Docs document."""
    if not auth_data.get("access_token"):
        return GetTabContentOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
                params={"includeTabsContent": "true"},
            )
            if response.status_code != 200:
                return GetTabContentOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )
            data = response.json()
    except httpx.TimeoutException:
        return GetTabContentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTabContentOutput(success=False, error=f"Call failed: {exc}")

    tabs_result: list[TabContent] = []
    for tab in data.get("tabs", []):
        tab_props = tab.get("tabProperties", {})
        tab_id = tab_props.get("tabId")
        if tab_id in tab_ids:
            tabs_result.append(
                TabContent(
                    tab_id=tab_id,
                    title=tab_props.get("title"),
                    body=tab.get("documentTab", {}).get("body"),
                )
            )

    return GetTabContentOutput(success=True, tabs=tabs_result)


@tool(args_schema=InsertPageBreakInput)
@serialize_pydantic_return
async def insert_page_break(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    index: int = 1,
    tab_id: str | None = None,
) -> InsertPageBreakOutput:
    """Insert a page break into a Google Docs document at a specified index."""
    if not auth_data.get("access_token"):
        return InsertPageBreakOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        location: dict[str, Any] = {"index": index}
        if tab_id:
            location["tabId"] = tab_id

        requests_body: list[dict[str, Any]] = [
            {"insertPageBreak": {"location": location}}
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_DOCS_BASE_URL}/documents/{doc_id}:batchUpdate",
                headers={**headers, "Content-Type": "application/json"},
                json={"requests": requests_body},
            )
            if response.status_code != 200:
                return InsertPageBreakOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )

            doc_resp = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
            )
            doc_data = doc_resp.json() if doc_resp.status_code == 200 else {}
    except httpx.TimeoutException:
        return InsertPageBreakOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertPageBreakOutput(success=False, error=f"Call failed: {exc}")

    return InsertPageBreakOutput(
        success=True,
        document_id=doc_id,
        title=doc_data.get("title"),
    )


@tool(args_schema=InsertTableInput)
@serialize_pydantic_return
async def insert_table(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    rows: int,
    columns: int,
    index: int = 1,
    tab_id: str | None = None,
) -> InsertTableOutput:
    """Insert a table into a Google Docs document at a specified index."""
    if not auth_data.get("access_token"):
        return InsertTableOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        location: dict[str, Any] = {"index": index}
        if tab_id:
            location["tabId"] = tab_id

        requests_body: list[dict[str, Any]] = [
            {
                "insertTable": {
                    "rows": rows,
                    "columns": columns,
                    "location": location,
                }
            }
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_DOCS_BASE_URL}/documents/{doc_id}:batchUpdate",
                headers={**headers, "Content-Type": "application/json"},
                json={"requests": requests_body},
            )
            if response.status_code != 200:
                return InsertTableOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )

            doc_resp = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
            )
            doc_data = doc_resp.json() if doc_resp.status_code == 200 else {}
    except httpx.TimeoutException:
        return InsertTableOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertTableOutput(success=False, error=f"Call failed: {exc}")

    return InsertTableOutput(
        success=True,
        document_id=doc_id,
        title=doc_data.get("title"),
    )


@tool(args_schema=InsertTextInput)
@serialize_pydantic_return
async def insert_text(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    text: str,
    index: int = 1,
    tab_id: str | None = None,
) -> InsertTextOutput:
    """Insert text into a Google Docs document at a specified index."""
    if not auth_data.get("access_token"):
        return InsertTextOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        location: dict[str, Any] = {"index": index}
        if tab_id:
            location["tabId"] = tab_id

        requests_body: list[dict[str, Any]] = [
            {"insertText": {"text": text, "location": location}}
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_DOCS_BASE_URL}/documents/{doc_id}:batchUpdate",
                headers={**headers, "Content-Type": "application/json"},
                json={"requests": requests_body},
            )
            if response.status_code != 200:
                return InsertTextOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )

            doc_resp = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
            )
            doc_data = doc_resp.json() if doc_resp.status_code == 200 else {}
    except httpx.TimeoutException:
        return InsertTextOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertTextOutput(success=False, error=f"Call failed: {exc}")

    return InsertTextOutput(
        success=True,
        document_id=doc_id,
        title=doc_data.get("title"),
    )


@tool(args_schema=ReplaceImageInput)
@serialize_pydantic_return
async def replace_image(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    image_id: str,
    image_uri: str,
) -> ReplaceImageOutput:
    """Replace an existing image in a Google Docs document with a new one."""
    if not auth_data.get("access_token"):
        return ReplaceImageOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        requests_body: list[dict[str, Any]] = [
            {
                "replaceImage": {
                    "imageObjectId": image_id,
                    "uri": image_uri,
                }
            }
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_DOCS_BASE_URL}/documents/{doc_id}:batchUpdate",
                headers={**headers, "Content-Type": "application/json"},
                json={"requests": requests_body},
            )
            if response.status_code != 200:
                return ReplaceImageOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )

            doc_resp = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
            )
            doc_data = doc_resp.json() if doc_resp.status_code == 200 else {}
    except httpx.TimeoutException:
        return ReplaceImageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ReplaceImageOutput(success=False, error=f"Call failed: {exc}")

    return ReplaceImageOutput(
        success=True,
        document_id=doc_id,
        title=doc_data.get("title"),
    )


@tool(args_schema=ReplaceTextInput)
@serialize_pydantic_return
async def replace_text(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_id: str,
    text_to_replace: str,
    new_text: str,
    match_case: bool = False,
) -> ReplaceTextOutput:
    """Replace all instances of matched text in a Google Docs document."""
    if not auth_data.get("access_token"):
        return ReplaceTextOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        requests_body: list[dict[str, Any]] = [
            {
                "replaceAllText": {
                    "containsText": {
                        "text": text_to_replace,
                        "matchCase": match_case,
                    },
                    "replaceText": new_text,
                }
            }
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_DOCS_BASE_URL}/documents/{doc_id}:batchUpdate",
                headers={**headers, "Content-Type": "application/json"},
                json={"requests": requests_body},
            )
            if response.status_code != 200:
                return ReplaceTextOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )

            doc_resp = await client.get(
                f"{_DOCS_BASE_URL}/documents/{doc_id}",
                headers=headers,
            )
            doc_data = doc_resp.json() if doc_resp.status_code == 200 else {}
    except httpx.TimeoutException:
        return ReplaceTextOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ReplaceTextOutput(success=False, error=f"Call failed: {exc}")

    return ReplaceTextOutput(
        success=True,
        document_id=doc_id,
        title=doc_data.get("title"),
    )
