"""Tests for the ConvertAPI integration."""
from __future__ import annotations

import base64
from typing import Any

import pytest

from modulex_integrations.tools.convertapi import (
    TOOLS,
    convert_base64_file,
    convert_file,
    convert_web_url,
    get_supported_formats,
    manifest,
)
from modulex_integrations.tools.convertapi.outputs import (
    ConvertBase64FileOutput,
    ConvertFileOutput,
    ConvertWebUrlOutput,
    GetSupportedFormatsOutput,
)

API = "https://v2.convertapi.com"
_API_KEY = "convertapi-fake-secret"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_four_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]

    def test_test_endpoint_embeds_secret_in_url(self) -> None:
        # ``params`` placeholders are NOT substituted by the modulex runtime
        # — credentials must live in the URL/headers/body. We embed the
        # ``{api_key}`` placeholder directly in the URL query string.
        auth = manifest.auth_schemas[0]
        assert auth.test_endpoint is not None
        assert auth.test_endpoint.params == {}
        assert "Secret={api_key}" in auth.test_endpoint.url


@pytest.mark.asyncio
async def test_convert_file(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/convert/docx/to/pdf?Secret={_API_KEY}",
        json={
            "ConversionCost": 1,
            "Files": [
                {
                    "FileName": "out.pdf",
                    "FileSize": 12345,
                    "Url": "https://v2.convertapi.com/d/abc/out.pdf",
                    "FileData": None,
                }
            ],
        },
    )

    result_dict = await convert_file.ainvoke(
        _args(
            file_url="https://example.com/doc.docx",
            format_from="docx",
            format_to="pdf",
        )
    )
    result = ConvertFileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.conversion_cost == 1
    assert result.files[0].filename == "out.pdf"
    assert result.format_to == "pdf"


@pytest.mark.asyncio
async def test_convert_file_handles_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/convert/docx/to/pdf?Secret={_API_KEY}",
        status_code=401,
        text="invalid secret",
    )
    result_dict = await convert_file.ainvoke(
        _args(
            file_url="https://example.com/doc.docx",
            format_from="docx",
            format_to="pdf",
        )
    )
    result = ConvertFileOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "HTTP 401" in result.error


@pytest.mark.asyncio
async def test_convert_file_empty_files_returns_failure(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/convert/docx/to/pdf?Secret={_API_KEY}",
        json={"ConversionCost": 0, "Files": []},
    )
    result_dict = await convert_file.ainvoke(
        _args(
            file_url="https://example.com/doc.docx",
            format_from="docx",
            format_to="pdf",
        )
    )
    result = ConvertFileOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "No output files" in result.error


@pytest.mark.asyncio
async def test_convert_base64_file(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/convert/png/to/jpg?Secret={_API_KEY}",
        json={
            "ConversionCost": 1,
            "Files": [
                {
                    "FileName": "converted.jpg",
                    "FileSize": 2048,
                    "Url": "https://v2.convertapi.com/d/abc/converted.jpg",
                    "FileData": None,
                }
            ],
        },
    )

    encoded = base64.b64encode(b"some bytes").decode("ascii")
    result_dict = await convert_base64_file.ainvoke(
        _args(base64_string=encoded, format_from="png", format_to="jpg")
    )
    result = ConvertBase64FileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.files[0].filename == "converted.jpg"
    assert result.format_to == "jpg"


@pytest.mark.asyncio
async def test_convert_base64_file_rejects_invalid_b64() -> None:
    result_dict = await convert_base64_file.ainvoke(
        _args(base64_string="!!!not-base64!!!", format_from="png", format_to="jpg")
    )
    result = ConvertBase64FileOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "Invalid base64" in result.error


@pytest.mark.asyncio
async def test_convert_web_url(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/convert/web/to/pdf?Secret={_API_KEY}",
        json={
            "ConversionCost": 2,
            "Files": [
                {
                    "FileName": "page.pdf",
                    "FileSize": 67890,
                    "Url": "https://v2.convertapi.com/d/abc/page.pdf",
                    "FileData": None,
                }
            ],
        },
    )

    result_dict = await convert_web_url.ainvoke(
        _args(url="https://example.com", page_size="a4", page_orientation="portrait")
    )
    result = ConvertWebUrlOutput.model_validate(result_dict)
    assert result.success is True
    assert result.source_url == "https://example.com"
    assert result.files[0].filename == "page.pdf"


@pytest.mark.asyncio
async def test_convert_web_url_rejects_unsupported_format() -> None:
    result_dict = await convert_web_url.ainvoke(
        _args(url="https://example.com", format_to="docx")
    )
    result = ConvertWebUrlOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "docx" in result.error


@pytest.mark.asyncio
async def test_get_supported_formats(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/info/openapi/docx/to/*?Secret={_API_KEY}",
        json={
            "paths": {
                "/convert/docx/to/pdf": {},
                "/convert/docx/to/jpg": {},
                "/convert/docx/to/txt": {},
                "/convert/docx/to/*": {},  # should be skipped
            }
        },
    )

    result_dict = await get_supported_formats.ainvoke(_args(format_from="docx"))
    result = GetSupportedFormatsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 3
    assert result.supported_formats == ["jpg", "pdf", "txt"]


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result_dict = await convert_file.ainvoke(
        {
            "api_key": "",
            "file_url": "https://example.com/doc.docx",
            "format_from": "docx",
            "format_to": "pdf",
        }
    )
    result = ConvertFileOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "Secret key" in result.error
