"""Gamma LangChain ``@tool`` functions.

Five async tools wrapping the Gamma REST API. The modulex
``ToolExecutor`` injects an ``api_key: str`` directly (resolved from the
user's ``api_key`` credential), which is sent on every request as the
``X-API-KEY`` header.

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
from modulex_integrations.tools.gamma.outputs import (
    CheckStatusOutput,
    FolderItem,
    GammaCredits,
    GammaError,
    GenerateFromTemplateOutput,
    GenerateOutput,
    ListFoldersOutput,
    ListThemesOutput,
    ThemeItem,
)

__all__ = [
    "check_status",
    "generate",
    "generate_from_template",
    "list_folders",
    "list_themes",
]

_BASE_URL = "https://public-api.gamma.app/v1.0"
_TIMEOUT = 60.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class GenerateInput(BaseModel):
    input_text: str = Field(
        description="Text and image URLs used to generate your gamma (1-100,000 tokens)"
    )
    text_mode: str = Field(
        description=(
            "How to handle input text: generate (AI expands), condense "
            "(AI summarizes), or preserve (keep as-is)"
        )
    )
    api_key: str = Field(description="Gamma API key (provided by credential system)")
    format: str | None = Field(
        default=None,
        description=(
            "Output format: presentation, document, webpage, or social "
            "(default: presentation)"
        ),
    )
    theme_id: str | None = Field(
        default=None,
        description="Custom Gamma workspace theme ID (use list_themes to find available themes)",
    )
    num_cards: int | None = Field(
        default=None,
        description=(
            "Number of cards/slides to generate "
            "(1-60 for Pro, 1-75 for Ultra; default: 10)"
        ),
    )
    card_split: str | None = Field(
        default=None,
        description="How to split content into cards: auto or inputTextBreaks (default: auto)",
    )
    card_dimensions: str | None = Field(
        default=None,
        description=(
            "Card aspect ratio. Presentation: fluid, 16x9, 4x3. Document: fluid, "
            "pageless, letter, a4. Social: 1x1, 4x5, 9x16"
        ),
    )
    additional_instructions: str | None = Field(
        default=None,
        description="Additional instructions for the AI generation (max 2000 chars)",
    )
    export_as: str | None = Field(
        default=None,
        description="Automatically export the generated gamma as pdf or pptx",
    )
    folder_ids: str | None = Field(
        default=None,
        description="Comma-separated folder IDs to store the generated gamma in",
    )
    text_amount: str | None = Field(
        default=None,
        description="Amount of text per card: brief, medium, detailed, or extensive",
    )
    text_tone: str | None = Field(
        default=None,
        description='Tone of the generated text, e.g. "professional", "casual" (max 500 chars)',
    )
    text_audience: str | None = Field(
        default=None,
        description='Target audience for the generated text, e.g. "executives" (max 500 chars)',
    )
    text_language: str | None = Field(
        default=None,
        description="Language code for the generated text (default: en)",
    )
    image_source: str | None = Field(
        default=None,
        description=(
            "Where to source images: aiGenerated, pictographic, unsplash, "
            "webAllImages, webFreeToUse, webFreeToUseCommercially, giphy, "
            "placeholder, or noImages"
        ),
    )
    image_model: str | None = Field(
        default=None,
        description="AI image generation model to use when image_source is aiGenerated",
    )
    image_style: str | None = Field(
        default=None,
        description='Style directive for AI-generated images, e.g. "watercolor" (max 500 chars)',
    )


class GenerateFromTemplateInput(BaseModel):
    gamma_id: str = Field(description="The ID of the template gamma to adapt")
    prompt: str = Field(
        description="Instructions for how to adapt the template (1-100,000 tokens)"
    )
    api_key: str = Field(description="Gamma API key (provided by credential system)")
    theme_id: str | None = Field(
        default=None, description="Custom Gamma workspace theme ID to apply"
    )
    export_as: str | None = Field(
        default=None,
        description="Automatically export the generated gamma as pdf or pptx",
    )
    folder_ids: str | None = Field(
        default=None,
        description="Comma-separated folder IDs to store the generated gamma in",
    )
    image_model: str | None = Field(
        default=None,
        description="AI image generation model to use when image_source is aiGenerated",
    )
    image_style: str | None = Field(
        default=None,
        description='Style directive for AI-generated images, e.g. "watercolor" (max 500 chars)',
    )


class CheckStatusInput(BaseModel):
    generation_id: str = Field(
        description="The generation ID returned by generate or generate_from_template"
    )
    api_key: str = Field(description="Gamma API key (provided by credential system)")


class ListThemesInput(BaseModel):
    api_key: str = Field(description="Gamma API key (provided by credential system)")
    query: str | None = Field(
        default=None,
        description="Search query to filter themes by name (case-insensitive)",
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of themes to return per page (max 50)",
    )
    after: str | None = Field(
        default=None,
        description="Pagination cursor from a previous response (next_cursor)",
    )


class ListFoldersInput(BaseModel):
    api_key: str = Field(description="Gamma API key (provided by credential system)")
    query: str | None = Field(
        default=None,
        description="Search query to filter folders by name (case-sensitive)",
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of folders to return per page (max 50)",
    )
    after: str | None = Field(
        default=None,
        description="Pagination cursor from a previous response (next_cursor)",
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=GenerateInput)
@serialize_pydantic_return
async def generate(
    input_text: str,
    text_mode: str,
    api_key: str,
    format: str | None = None,
    theme_id: str | None = None,
    num_cards: int | None = None,
    card_split: str | None = None,
    card_dimensions: str | None = None,
    additional_instructions: str | None = None,
    export_as: str | None = None,
    folder_ids: str | None = None,
    text_amount: str | None = None,
    text_tone: str | None = None,
    text_audience: str | None = None,
    text_language: str | None = None,
    image_source: str | None = None,
    image_model: str | None = None,
    image_style: str | None = None,
) -> GenerateOutput:
    """Generate a new Gamma presentation, document, webpage, or social post from text input."""
    if not api_key or not api_key.strip():
        return GenerateOutput(
            success=False,
            error="Gamma API key is empty. Please configure a valid Gamma credential.",
        )

    body: dict[str, Any] = {
        "inputText": input_text,
        "textMode": text_mode,
    }
    if format:
        body["format"] = format
    if theme_id:
        body["themeId"] = theme_id
    if num_cards is not None:
        body["numCards"] = num_cards
    if card_split:
        body["cardSplit"] = card_split
    if additional_instructions:
        body["additionalInstructions"] = additional_instructions
    if export_as:
        body["exportAs"] = export_as
    if folder_ids:
        body["folderIds"] = [fid.strip() for fid in folder_ids.split(",")]

    text_options: dict[str, Any] = {}
    if text_amount:
        text_options["amount"] = text_amount
    if text_tone:
        text_options["tone"] = text_tone
    if text_audience:
        text_options["audience"] = text_audience
    if text_language:
        text_options["language"] = text_language
    if text_options:
        body["textOptions"] = text_options

    image_options: dict[str, Any] = {}
    if image_source:
        image_options["source"] = image_source
    if image_model:
        image_options["model"] = image_model
    if image_style:
        image_options["style"] = image_style
    if image_options:
        body["imageOptions"] = image_options

    card_options: dict[str, Any] = {}
    if card_dimensions:
        card_options["dimensions"] = card_dimensions
    if card_options:
        body["cardOptions"] = card_options

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/generations", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return GenerateOutput(
                success=False,
                error=f"Gamma API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GenerateOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GenerateOutput(success=False, error=f"Generate failed: {exc}")

    return GenerateOutput(
        success=True,
        generation_id=data.get("generationId") or "",
        warnings=data.get("warnings"),
    )


@tool(args_schema=GenerateFromTemplateInput)
@serialize_pydantic_return
async def generate_from_template(
    gamma_id: str,
    prompt: str,
    api_key: str,
    theme_id: str | None = None,
    export_as: str | None = None,
    folder_ids: str | None = None,
    image_model: str | None = None,
    image_style: str | None = None,
) -> GenerateFromTemplateOutput:
    """Generate a new Gamma by adapting an existing template with a prompt."""
    if not api_key or not api_key.strip():
        return GenerateFromTemplateOutput(
            success=False,
            error="Gamma API key is empty. Please configure a valid Gamma credential.",
        )

    body: dict[str, Any] = {
        "gammaId": gamma_id,
        "prompt": prompt,
    }
    if theme_id:
        body["themeId"] = theme_id
    if export_as:
        body["exportAs"] = export_as
    if folder_ids:
        body["folderIds"] = [fid.strip() for fid in folder_ids.split(",")]

    image_options: dict[str, Any] = {}
    if image_model:
        image_options["model"] = image_model
    if image_style:
        image_options["style"] = image_style
    if image_options:
        body["imageOptions"] = image_options

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/generations/from-template",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return GenerateFromTemplateOutput(
                success=False,
                error=f"Gamma API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GenerateFromTemplateOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GenerateFromTemplateOutput(
            success=False, error=f"Generate from template failed: {exc}"
        )

    return GenerateFromTemplateOutput(
        success=True,
        generation_id=data.get("generationId") or "",
        warnings=data.get("warnings"),
    )


@tool(args_schema=CheckStatusInput)
@serialize_pydantic_return
async def check_status(
    generation_id: str,
    api_key: str,
) -> CheckStatusOutput:
    """Check the status of a Gamma generation job.

    Returns the gamma URL when completed, or error details if failed.
    """
    if not api_key or not api_key.strip():
        return CheckStatusOutput(
            success=False,
            error="Gamma API key is empty. Please configure a valid Gamma credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/generations/{generation_id}",
                headers={"X-API-KEY": api_key},
            )
        if response.status_code != 200:
            return CheckStatusOutput(
                success=False,
                error=f"Gamma API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CheckStatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CheckStatusOutput(success=False, error=f"Check status failed: {exc}")

    credits = None
    raw_credits = data.get("credits")
    if isinstance(raw_credits, dict):
        credits = GammaCredits(
            deducted=raw_credits.get("deducted"),
            remaining=raw_credits.get("remaining"),
        )

    generation_error = None
    raw_error = data.get("error")
    if isinstance(raw_error, dict):
        generation_error = GammaError(
            message=raw_error.get("message"),
            status_code=raw_error.get("statusCode"),
        )

    return CheckStatusOutput(
        success=True,
        generation_id=data.get("generationId") or "",
        status=data.get("status") or "pending",
        gamma_url=data.get("gammaUrl"),
        gamma_id=data.get("gammaId"),
        export_url=data.get("exportUrl"),
        credits=credits,
        generation_error=generation_error,
    )


@tool(args_schema=ListThemesInput)
@serialize_pydantic_return
async def list_themes(
    api_key: str,
    query: str | None = None,
    limit: int | None = None,
    after: str | None = None,
) -> ListThemesOutput:
    """List available themes in your Gamma workspace.

    Returns theme IDs, names, and keywords for styling.
    """
    if not api_key or not api_key.strip():
        return ListThemesOutput(
            success=False,
            error="Gamma API key is empty. Please configure a valid Gamma credential.",
        )

    params: dict[str, Any] = {}
    if query:
        params["query"] = query
    if limit is not None:
        params["limit"] = limit
    if after:
        params["after"] = after

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/themes",
                headers={"X-API-KEY": api_key},
                params=params,
            )
        if response.status_code != 200:
            return ListThemesOutput(
                success=False,
                error=f"Gamma API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListThemesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListThemesOutput(success=False, error=f"List themes failed: {exc}")

    if isinstance(data, dict):
        raw_items = data.get("data")
        if not isinstance(raw_items, list):
            raw_items = []
        has_more = data.get("hasMore")
        next_cursor = data.get("nextCursor")
    elif isinstance(data, list):
        raw_items = data
        has_more = False
        next_cursor = None
    else:
        raw_items = []
        has_more = False
        next_cursor = None

    return ListThemesOutput(
        success=True,
        themes=[
            ThemeItem(
                id=item.get("id") or "",
                name=item.get("name") or "",
                type=item.get("type") or "",
                color_keywords=item.get("colorKeywords") or [],
                tone_keywords=item.get("toneKeywords") or [],
            )
            for item in raw_items
            if isinstance(item, dict)
        ],
        has_more=has_more if has_more is not None else False,
        next_cursor=next_cursor,
    )


@tool(args_schema=ListFoldersInput)
@serialize_pydantic_return
async def list_folders(
    api_key: str,
    query: str | None = None,
    limit: int | None = None,
    after: str | None = None,
) -> ListFoldersOutput:
    """List available folders in your Gamma workspace.

    Returns folder IDs and names for organizing generated content.
    """
    if not api_key or not api_key.strip():
        return ListFoldersOutput(
            success=False,
            error="Gamma API key is empty. Please configure a valid Gamma credential.",
        )

    params: dict[str, Any] = {}
    if query:
        params["query"] = query
    if limit is not None:
        params["limit"] = limit
    if after:
        params["after"] = after

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/folders",
                headers={"X-API-KEY": api_key},
                params=params,
            )
        if response.status_code != 200:
            return ListFoldersOutput(
                success=False,
                error=f"Gamma API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFoldersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFoldersOutput(success=False, error=f"List folders failed: {exc}")

    if isinstance(data, dict):
        raw_items = data.get("data")
        if not isinstance(raw_items, list):
            raw_items = []
        has_more = data.get("hasMore")
        next_cursor = data.get("nextCursor")
    elif isinstance(data, list):
        raw_items = data
        has_more = False
        next_cursor = None
    else:
        raw_items = []
        has_more = False
        next_cursor = None

    return ListFoldersOutput(
        success=True,
        folders=[
            FolderItem(
                id=item.get("id") or "",
                name=item.get("name") or "",
            )
            for item in raw_items
            if isinstance(item, dict)
        ],
        has_more=has_more if has_more is not None else False,
        next_cursor=next_cursor,
    )
