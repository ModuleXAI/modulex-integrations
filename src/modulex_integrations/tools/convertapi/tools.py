"""ConvertAPI LangChain ``@tool`` functions."""
from __future__ import annotations

import base64
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.convertapi.outputs import (
    ConvertBase64FileOutput,
    ConvertedFile,
    ConvertFileOutput,
    ConvertWebUrlOutput,
    GetSupportedFormatsOutput,
)

__all__ = [
    "convert_base64_file",
    "convert_file",
    "convert_web_url",
    "get_supported_formats",
]

_BASE_URL = "https://v2.convertapi.com"
_WEB_FORMATS = ("pdf", "jpg")


def _auth_params(api_key: str) -> dict[str, str]:
    return {"Secret": api_key}


def _empty_key_error(name: str) -> str:
    return (
        f"ConvertAPI Secret key is empty for {name}. "
        "Please configure a valid credential."
    )


def _parse_files(payload: dict[str, Any]) -> list[ConvertedFile]:
    return [
        ConvertedFile(
            filename=f.get("FileName"),
            file_size=f.get("FileSize"),
            file_url=f.get("Url"),
            file_data_base64=f.get("FileData"),
        )
        for f in payload.get("Files", []) or []
    ]


class ConvertFileInput(BaseModel):
    api_key: str = Field(description="ConvertAPI Secret key (provided by credential system)")
    file_url: str = Field(description="URL of the file to convert")
    format_from: str = Field(description="Input file format")
    format_to: str = Field(description="Output file format")
    filename: str | None = Field(default=None, description="Output filename without extension")
    timeout: int | None = Field(default=300, description="Conversion timeout in seconds")


class ConvertBase64FileInput(BaseModel):
    api_key: str = Field(description="ConvertAPI Secret key (provided by credential system)")
    base64_string: str = Field(description="Base64-encoded file content")
    format_from: str = Field(description="Input file format")
    format_to: str = Field(description="Output file format")
    filename: str | None = Field(
        default="converted", description="Output filename without extension"
    )
    timeout: int | None = Field(default=300, description="Conversion timeout in seconds")


class ConvertWebUrlInput(BaseModel):
    api_key: str = Field(description="ConvertAPI Secret key (provided by credential system)")
    url: str = Field(description="Website URL to convert")
    format_to: str = Field(default="pdf", description="Output format ('pdf' or 'jpg')")
    filename: str | None = Field(default=None, description="Output filename without extension")
    timeout: int | None = Field(default=300, description="Conversion timeout in seconds")
    conversion_delay: int | None = Field(default=None, description="Page load delay (seconds)")
    page_orientation: str | None = Field(default=None, description="'portrait' or 'landscape'")
    page_size: str | None = Field(default=None, description="'a4', 'letter', 'legal', etc.")
    javascript: bool | None = Field(default=True, description="Allow JavaScript")
    ad_block: bool | None = Field(default=False, description="Block ads on the page")
    cookie_consent_block: bool | None = Field(
        default=False, description="Try to remove cookie consent popups"
    )


class GetSupportedFormatsInput(BaseModel):
    api_key: str = Field(description="ConvertAPI Secret key (provided by credential system)")
    format_from: str = Field(description="Input format to check available conversions for")


@tool(args_schema=ConvertFileInput)
@serialize_pydantic_return
async def convert_file(
    api_key: str,
    file_url: str,
    format_from: str,
    format_to: str,
    filename: str | None = None,
    timeout: int | None = 300,
) -> ConvertFileOutput:
    """Convert a file from a URL to another format using ConvertAPI."""
    if not api_key or not api_key.strip():
        return ConvertFileOutput(success=False, error=_empty_key_error("convert_file"))

    from_fmt = format_from.lower()
    to_fmt = format_to.lower()

    form: dict[str, Any] = {"File": file_url, "StoreFile": "true"}
    if filename:
        form["FileName"] = filename

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout or 300)) as client:
            response = await client.post(
                f"{_BASE_URL}/convert/{from_fmt}/to/{to_fmt}",
                params=_auth_params(api_key),
                data=form,
            )
        if response.status_code != 200:
            return ConvertFileOutput(
                success=False,
                error=f"ConvertAPI error (HTTP {response.status_code}): {response.text}",
            )
        body = response.json() or {}
    except Exception as exc:
        return ConvertFileOutput(success=False, error=f"File conversion failed: {exc}")

    files = _parse_files(body)
    if not files:
        return ConvertFileOutput(
            success=False, error="No output files returned from conversion"
        )

    return ConvertFileOutput(
        success=True,
        conversion_cost=body.get("ConversionCost"),
        files=files,
        format_from=from_fmt,
        format_to=to_fmt,
    )


@tool(args_schema=ConvertBase64FileInput)
@serialize_pydantic_return
async def convert_base64_file(
    api_key: str,
    base64_string: str,
    format_from: str,
    format_to: str,
    filename: str | None = "converted",
    timeout: int | None = 300,
) -> ConvertBase64FileOutput:
    """Convert a base64-encoded file to another format using ConvertAPI."""
    if not api_key or not api_key.strip():
        return ConvertBase64FileOutput(
            success=False, error=_empty_key_error("convert_base64_file")
        )

    from_fmt = format_from.lower()
    to_fmt = format_to.lower()

    try:
        file_bytes = base64.b64decode(base64_string)
    except Exception as exc:
        return ConvertBase64FileOutput(
            success=False, error=f"Invalid base64 string: {exc}"
        )

    fname = filename or "converted"
    files_arg = {"File": (f"{fname}.{from_fmt}", file_bytes)}
    data_arg = {"StoreFile": "true"}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout or 300)) as client:
            response = await client.post(
                f"{_BASE_URL}/convert/{from_fmt}/to/{to_fmt}",
                params=_auth_params(api_key),
                files=files_arg,
                data=data_arg,
            )
        if response.status_code != 200:
            return ConvertBase64FileOutput(
                success=False,
                error=f"ConvertAPI error (HTTP {response.status_code}): {response.text}",
            )
        body = response.json() or {}
    except Exception as exc:
        return ConvertBase64FileOutput(
            success=False, error=f"Base64 file conversion failed: {exc}"
        )

    converted = _parse_files(body)
    if not converted:
        return ConvertBase64FileOutput(
            success=False, error="No output files returned from conversion"
        )

    return ConvertBase64FileOutput(
        success=True,
        conversion_cost=body.get("ConversionCost"),
        files=converted,
        format_from=from_fmt,
        format_to=to_fmt,
    )


@tool(args_schema=ConvertWebUrlInput)
@serialize_pydantic_return
async def convert_web_url(
    api_key: str,
    url: str,
    format_to: str = "pdf",
    filename: str | None = None,
    timeout: int | None = 300,
    conversion_delay: int | None = None,
    page_orientation: str | None = None,
    page_size: str | None = None,
    javascript: bool | None = True,
    ad_block: bool | None = False,
    cookie_consent_block: bool | None = False,
) -> ConvertWebUrlOutput:
    """Convert a web page URL to PDF or JPG using ConvertAPI."""
    if not api_key or not api_key.strip():
        return ConvertWebUrlOutput(
            success=False, error=_empty_key_error("convert_web_url")
        )

    to_fmt = format_to.lower()
    if to_fmt not in _WEB_FORMATS:
        return ConvertWebUrlOutput(
            success=False,
            error=(
                f"Invalid output format '{format_to}'. "
                f"Supported formats: {list(_WEB_FORMATS)}"
            ),
        )

    form: dict[str, Any] = {
        "Url": url,
        "StoreFile": "true",
        "JavaScript": str(bool(javascript)).lower(),
    }
    if filename:
        form["FileName"] = filename
    if conversion_delay:
        form["ConversionDelay"] = str(conversion_delay)
    if ad_block:
        form["AdBlock"] = "true"
    if cookie_consent_block:
        form["CookieConsentBlock"] = "true"
    if to_fmt == "pdf":
        if page_orientation:
            form["PageOrientation"] = page_orientation
        if page_size:
            form["PageSize"] = page_size

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout or 300)) as client:
            response = await client.post(
                f"{_BASE_URL}/convert/web/to/{to_fmt}",
                params=_auth_params(api_key),
                data=form,
            )
        if response.status_code != 200:
            return ConvertWebUrlOutput(
                success=False,
                error=f"ConvertAPI error (HTTP {response.status_code}): {response.text}",
            )
        body = response.json() or {}
    except Exception as exc:
        return ConvertWebUrlOutput(
            success=False, error=f"Web URL conversion failed: {exc}"
        )

    files = _parse_files(body)
    if not files:
        return ConvertWebUrlOutput(
            success=False, error="No output files returned from conversion"
        )

    return ConvertWebUrlOutput(
        success=True,
        conversion_cost=body.get("ConversionCost"),
        files=files,
        source_url=url,
        format_to=to_fmt,
    )


@tool(args_schema=GetSupportedFormatsInput)
@serialize_pydantic_return
async def get_supported_formats(
    api_key: str, format_from: str
) -> GetSupportedFormatsOutput:
    """Get the list of supported output formats for a given input format."""
    if not api_key or not api_key.strip():
        return GetSupportedFormatsOutput(
            success=False, error=_empty_key_error("get_supported_formats")
        )

    from_fmt = format_from.lower()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/info/openapi/{from_fmt}/to/*",
                params=_auth_params(api_key),
            )
        if response.status_code != 200:
            return GetSupportedFormatsOutput(
                success=False,
                error=f"Failed to get formats (HTTP {response.status_code})",
            )
        body = response.json() or {}
    except Exception as exc:
        return GetSupportedFormatsOutput(
            success=False, error=f"Failed to get supported formats: {exc}"
        )

    prefix = f"/convert/{from_fmt}/to/"
    formats: list[str] = []
    for path in (body.get("paths") or {}).keys():
        if path.startswith(prefix):
            name = path[len(prefix):]
            if name and name != "*":
                formats.append(name)
    formats.sort()

    return GetSupportedFormatsOutput(
        success=True,
        format_from=from_fmt,
        supported_formats=formats,
        count=len(formats),
    )
