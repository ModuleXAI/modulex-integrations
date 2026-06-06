"""Happy-path tests for every google_docs @tool, plus a manifest sanity check."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.google_docs import (
    TOOLS,
    append_image,
    append_text,
    create_document,
    get_document,
    get_tab_content,
    insert_page_break,
    insert_table,
    insert_text,
    manifest,
    replace_image,
    replace_text,
)
from modulex_integrations.tools.google_docs.outputs import (
    AppendImageOutput,
    AppendTextOutput,
    CreateDocumentOutput,
    GetDocumentOutput,
    GetTabContentOutput,
    InsertPageBreakOutput,
    InsertTableOutput,
    InsertTextOutput,
    ReplaceImageOutput,
    ReplaceTextOutput,
)

DOCS_API = "https://docs.googleapis.com/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a .ainvoke() input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_10_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_append_image(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS_API}/documents/doc123",
        json={
            "documentId": "doc123",
            "title": "Test Doc",
            "body": {"content": [{"endIndex": 10}]},
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS_API}/documents/doc123:batchUpdate",
        json={"replies": []},
    )

    result_dict = await append_image.ainvoke(
        _args(doc_id="doc123", image_uri="https://example.com/img.png")
    )

    assert isinstance(result_dict, dict)
    result = AppendImageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "doc123"


@pytest.mark.asyncio
async def test_append_text(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS_API}/documents/doc123",
        json={
            "documentId": "doc123",
            "title": "Test Doc",
            "body": {"content": [{"endIndex": 10}]},
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS_API}/documents/doc123:batchUpdate",
        json={"replies": []},
    )

    result_dict = await append_text.ainvoke(
        _args(doc_id="doc123", text="Hello world")
    )

    assert isinstance(result_dict, dict)
    result = AppendTextOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "doc123"


@pytest.mark.asyncio
async def test_create_document(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS_API}/documents",
        json={"documentId": "new_doc_id", "title": "New Doc"},
    )

    result_dict = await create_document.ainvoke(_args(title="New Doc"))

    assert isinstance(result_dict, dict)
    result = CreateDocumentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "new_doc_id"
    assert result.title == "New Doc"


@pytest.mark.asyncio
async def test_get_document(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS_API}/documents/doc123",
        json={
            "documentId": "doc123",
            "title": "Test Doc",
            "body": {"content": [{"paragraph": {}}]},
        },
    )

    result_dict = await get_document.ainvoke(_args(doc_id="doc123"))

    assert isinstance(result_dict, dict)
    result = GetDocumentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "doc123"
    assert result.title == "Test Doc"


@pytest.mark.asyncio
async def test_get_tab_content(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(DOCS_API)}/documents/doc123\??.*"),
        json={
            "documentId": "doc123",
            "tabs": [
                {
                    "tabProperties": {"tabId": "tab1", "title": "Tab 1"},
                    "documentTab": {"body": {"content": []}},
                }
            ],
        },
    )

    result_dict = await get_tab_content.ainvoke(
        _args(doc_id="doc123", tab_ids=["tab1"])
    )

    assert isinstance(result_dict, dict)
    result = GetTabContentOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.tabs) == 1
    assert result.tabs[0].tab_id == "tab1"


@pytest.mark.asyncio
async def test_insert_page_break(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS_API}/documents/doc123:batchUpdate",
        json={"replies": []},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS_API}/documents/doc123",
        json={"documentId": "doc123", "title": "Test Doc"},
    )

    result_dict = await insert_page_break.ainvoke(_args(doc_id="doc123"))

    assert isinstance(result_dict, dict)
    result = InsertPageBreakOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "doc123"


@pytest.mark.asyncio
async def test_insert_table(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS_API}/documents/doc123:batchUpdate",
        json={"replies": []},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS_API}/documents/doc123",
        json={"documentId": "doc123", "title": "Test Doc"},
    )

    result_dict = await insert_table.ainvoke(
        _args(doc_id="doc123", rows=3, columns=4)
    )

    assert isinstance(result_dict, dict)
    result = InsertTableOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "doc123"


@pytest.mark.asyncio
async def test_insert_text(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS_API}/documents/doc123:batchUpdate",
        json={"replies": []},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS_API}/documents/doc123",
        json={"documentId": "doc123", "title": "Test Doc"},
    )

    result_dict = await insert_text.ainvoke(
        _args(doc_id="doc123", text="Inserted text")
    )

    assert isinstance(result_dict, dict)
    result = InsertTextOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "doc123"


@pytest.mark.asyncio
async def test_replace_image(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS_API}/documents/doc123:batchUpdate",
        json={"replies": []},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS_API}/documents/doc123",
        json={"documentId": "doc123", "title": "Test Doc"},
    )

    result_dict = await replace_image.ainvoke(
        _args(doc_id="doc123", image_id="img1", image_uri="https://example.com/new.png")
    )

    assert isinstance(result_dict, dict)
    result = ReplaceImageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "doc123"


@pytest.mark.asyncio
async def test_replace_text(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DOCS_API}/documents/doc123:batchUpdate",
        json={"replies": []},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{DOCS_API}/documents/doc123",
        json={"documentId": "doc123", "title": "Test Doc"},
    )

    result_dict = await replace_text.ainvoke(
        _args(doc_id="doc123", text_to_replace="old", new_text="new")
    )

    assert isinstance(result_dict, dict)
    result = ReplaceTextOutput.model_validate(result_dict)
    assert result.success is True
    assert result.document_id == "doc123"


@pytest.mark.asyncio
async def test_get_document_missing_credentials() -> None:
    """Failure-path: missing access_token returns inline error."""
    result_dict = await get_document.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}, "doc_id": "doc123"}
    )
    assert isinstance(result_dict, dict)
    result = GetDocumentOutput.model_validate(result_dict)
    assert result.success is False
    assert "access token" in (result.error or "").lower()
