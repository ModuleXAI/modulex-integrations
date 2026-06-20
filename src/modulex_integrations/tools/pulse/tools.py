"""Pulse LangChain ``@tool`` functions.

One async tool wrapping the Pulse OCR REST API (``api.runpulse.com``).
The modulex ``ToolExecutor`` injects an ``api_key: str`` directly
(resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.pulse.outputs import ParserOutput, PlanInfo

__all__ = ["parser"]

_PULSE_API_BASE = "https://api.runpulse.com"
_PARSE_TIMEOUT = 120.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class ParserInput(BaseModel):
    file_url: str = Field(
        description="Public HTTP(S) URL to a document to process (PDF, image, or Office file)"
    )
    api_key: str = Field(description="Pulse API key (provided by credential system)")
    pages: str | None = Field(
        default=None,
        description='Page range to process, 1-indexed (e.g. "1-2,5"). Omit for all pages.',
    )
    chunking: str | None = Field(
        default=None,
        description="Chunking strategies (comma-separated: semantic, header, page, recursive)",
    )
    chunk_size: int | None = Field(
        default=None,
        description="Maximum characters per chunk when chunking is enabled",
    )
    return_html: bool | None = Field(
        default=None, description="Whether to include HTML in the response"
    )
    extract_figure: bool | None = Field(
        default=None, description="Whether to extract figures from the document"
    )
    figure_description: bool | None = Field(
        default=None, description="Whether to generate descriptions/captions for extracted figures"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ParserInput)
@serialize_pydantic_return
async def parser(
    file_url: str,
    api_key: str,
    pages: str | None = None,
    chunking: str | None = None,
    chunk_size: int | None = None,
    return_html: bool | None = None,
    extract_figure: bool | None = None,
    figure_description: bool | None = None,
) -> ParserOutput:
    """Parse a document (PDF, image, or Office file) from a URL using Pulse OCR."""
    if not api_key or not api_key.strip():
        return ParserOutput(
            success=False,
            error="Pulse API key is empty. Please configure a valid Pulse credential.",
        )
    if not file_url or not file_url.strip():
        return ParserOutput(success=False, error="No document URL provided.")

    payload: dict[str, Any] = {"file_url": file_url.strip()}
    if pages and pages.strip():
        payload["pages"] = pages.strip()
    if chunking and chunking.strip():
        payload["chunking"] = chunking.strip()
    if chunk_size is not None and chunk_size > 0:
        payload["chunk_size"] = chunk_size
    if return_html is not None:
        payload["return_html"] = return_html
    if extract_figure is not None:
        payload["extract_figure"] = extract_figure
    if figure_description is not None:
        payload["figure_description"] = figure_description

    try:
        async with httpx.AsyncClient(timeout=_PARSE_TIMEOUT) as client:
            response = await client.post(
                f"{_PULSE_API_BASE}/extract", headers=_headers(api_key), json=payload
            )
        if response.status_code != 200:
            return ParserOutput(
                success=False,
                error=f"Pulse API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ParserOutput(
            success=False,
            error="Request timed out. Try a smaller page range or a smaller document.",
        )
    except Exception as exc:
        return ParserOutput(success=False, error=f"Document parsing failed: {exc}")

    if not isinstance(data, dict):
        return ParserOutput(success=False, error="Invalid response format from Pulse API.")

    # Some responses nest the extraction under "output"; flatten if present.
    nested = data.get("output")
    parsed: dict[str, Any] = nested if isinstance(nested, dict) else data

    # "plan-info" is the deprecated hyphenated alias of "plan_info"; read both.
    raw_plan = parsed.get("plan_info")
    if not isinstance(raw_plan, dict):
        raw_plan = parsed.get("plan-info")
    plan_info: PlanInfo | None = None
    if isinstance(raw_plan, dict):
        plan_info = PlanInfo(
            pages_used=raw_plan.get("pages_used"),
            tier=raw_plan.get("tier"),
            note=raw_plan.get("note"),
        )

    return ParserOutput(
        success=True,
        markdown=parsed.get("markdown"),
        page_count=parsed.get("page_count"),
        job_id=parsed.get("job_id") or parsed.get("extraction_id"),
        plan_info=plan_info,
        bounding_boxes=parsed.get("bounding_boxes"),
        extraction_url=parsed.get("extraction_url") or parsed.get("url"),
        html=parsed.get("html"),
        structured_output=parsed.get("structured_output"),
        chunks=parsed.get("chunks") or [],
        figures=parsed.get("figures") or [],
    )
