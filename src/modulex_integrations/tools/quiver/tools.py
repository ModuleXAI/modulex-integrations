"""Quiver LangChain ``@tool`` functions.

Three async tools wrapping the QuiverAI REST API (``api.quiver.ai/v1``)
for AI SVG generation and raster vectorization. The calling convention
is **key-based**: the modulex ``ToolExecutor`` injects an ``api_key: str``
directly (resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair.

Auth header: ``Authorization: Bearer <api_key>``.

Error model: every call is wrapped in try/except so non-2xx responses,
timeouts, and unexpected exceptions surface as ``success=False`` +
``error`` rather than raising.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.quiver.outputs import (
    ImageToSvgOutput,
    ListModelsOutput,
    ModelInfo,
    SvgArtifact,
    TextToSvgOutput,
    UsageInfo,
)

__all__ = ["image_to_svg", "list_models", "text_to_svg"]

_QUIVER_API_BASE = "https://api.quiver.ai/v1"
_GENERATE_TIMEOUT = 120.0
_VECTORIZE_TIMEOUT = 120.0
_MODELS_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# --- Parsing helpers -------------------------------------------------------


def _parse_artifacts(data: dict[str, Any]) -> list[SvgArtifact]:
    return [
        SvgArtifact(svg=item.get("svg"), mime_type=item.get("mime_type"))
        for item in data.get("data") or []
    ]


def _parse_usage(data: dict[str, Any]) -> UsageInfo | None:
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return None
    return UsageInfo(
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
        total_tokens=usage.get("total_tokens"),
    )


# --- Input schemas (args_schema for each @tool) ----------------------------


class TextToSvgInput(BaseModel):
    prompt: str = Field(description="A text description of the desired SVG")
    api_key: str = Field(description="QuiverAI API key (provided by credential system)")
    model: str = Field(
        default="arrow-1.1",
        description='The model to use for SVG generation (e.g. "arrow-1.1")',
    )
    instructions: str | None = Field(
        default=None, description="Style or formatting guidance for the SVG output"
    )
    references: list[str] | None = Field(
        default=None,
        description=(
            "Reference image URLs to guide SVG generation (up to 4 for arrow-1.1, "
            "16 for arrow-1.1-max)"
        ),
    )
    n: int | None = Field(default=None, description="Number of SVGs to generate (1-16, default 1)")
    temperature: float | None = Field(
        default=None, description="Sampling temperature (0-2, default 1)"
    )
    top_p: float | None = Field(
        default=None, description="Nucleus sampling probability (0-1, default 1)"
    )
    max_output_tokens: int | None = Field(
        default=None, description="Maximum output tokens (1-65536)"
    )
    presence_penalty: float | None = Field(
        default=None, description="Token penalty for prior output (-2 to 2, default 0)"
    )


class ImageToSvgInput(BaseModel):
    image: str = Field(description="URL of the raster image to vectorize into SVG")
    api_key: str = Field(description="QuiverAI API key (provided by credential system)")
    model: str = Field(
        default="arrow-1.1",
        description='The model to use for vectorization (e.g. "arrow-1.1")',
    )
    auto_crop: bool | None = Field(
        default=None, description="Automatically crop the image to its dominant subject"
    )
    target_size: int | None = Field(
        default=None, description="Square resize target in pixels (128-4096)"
    )
    temperature: float | None = Field(
        default=None, description="Sampling temperature (0-2, default 1)"
    )
    top_p: float | None = Field(
        default=None, description="Nucleus sampling probability (0-1, default 1)"
    )
    max_output_tokens: int | None = Field(
        default=None, description="Maximum output tokens (1-65536)"
    )
    presence_penalty: float | None = Field(
        default=None, description="Token penalty for prior output (-2 to 2, default 0)"
    )


class ListModelsInput(BaseModel):
    api_key: str = Field(description="QuiverAI API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=TextToSvgInput)
@serialize_pydantic_return
async def text_to_svg(
    prompt: str,
    api_key: str,
    model: str = "arrow-1.1",
    instructions: str | None = None,
    references: list[str] | None = None,
    n: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
    presence_penalty: float | None = None,
) -> TextToSvgOutput:
    """Generate SVG images from text prompts using QuiverAI."""
    if not api_key or not api_key.strip():
        return TextToSvgOutput(
            success=False,
            error="QuiverAI API key is empty. Please configure a valid Quiver credential.",
        )

    payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
    if instructions is not None:
        payload["instructions"] = instructions
    if references:
        # Quiver accepts reference images as objects with a `url` (or
        # `base64`) property. We expose URL references for stateless use.
        # TODO (unverified): base64 reference inputs are documented but not
        # exercised here per https://docs.quiver.ai/models/text-to-svg
        payload["references"] = [{"url": ref} for ref in references]
    if n is not None:
        payload["n"] = n
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if max_output_tokens is not None:
        payload["max_output_tokens"] = max_output_tokens
    if presence_penalty is not None:
        payload["presence_penalty"] = presence_penalty

    try:
        async with httpx.AsyncClient(timeout=_GENERATE_TIMEOUT) as client:
            response = await client.post(
                f"{_QUIVER_API_BASE}/svgs/generations",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return TextToSvgOutput(
                success=False,
                error=f"Quiver API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return TextToSvgOutput(
            success=False, error="Request timed out. Try reducing n or simplifying the prompt."
        )
    except Exception as exc:
        return TextToSvgOutput(success=False, error=f"SVG generation failed: {exc}")

    artifacts = _parse_artifacts(data)
    return TextToSvgOutput(
        success=True,
        id=data.get("id"),
        created=data.get("created"),
        svg_content=artifacts[0].svg if artifacts else None,
        artifacts=artifacts,
        credits=data.get("credits"),
        usage=_parse_usage(data),
    )


@tool(args_schema=ImageToSvgInput)
@serialize_pydantic_return
async def image_to_svg(
    image: str,
    api_key: str,
    model: str = "arrow-1.1",
    auto_crop: bool | None = None,
    target_size: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
    presence_penalty: float | None = None,
) -> ImageToSvgOutput:
    """Convert raster images into vector SVG format using QuiverAI."""
    if not api_key or not api_key.strip():
        return ImageToSvgOutput(
            success=False,
            error="QuiverAI API key is empty. Please configure a valid Quiver credential.",
        )
    if not image or not image.strip():
        return ImageToSvgOutput(success=False, error="No image URL provided.")

    # Quiver accepts the image as an object with a `url` (or `base64`)
    # property. We pass through the image URL for stateless vectorization.
    # TODO (unverified): base64 image inputs are documented but not
    # exercised here per https://docs.quiver.ai/models/image-to-svg
    payload: dict[str, Any] = {
        "model": model,
        "image": {"url": image},
        "stream": False,
    }
    if auto_crop is not None:
        payload["auto_crop"] = auto_crop
    if target_size is not None:
        payload["target_size"] = target_size
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if max_output_tokens is not None:
        payload["max_output_tokens"] = max_output_tokens
    if presence_penalty is not None:
        payload["presence_penalty"] = presence_penalty

    try:
        async with httpx.AsyncClient(timeout=_VECTORIZE_TIMEOUT) as client:
            response = await client.post(
                f"{_QUIVER_API_BASE}/svgs/vectorizations",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return ImageToSvgOutput(
                success=False,
                error=f"Quiver API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ImageToSvgOutput(
            success=False, error="Request timed out. Try a smaller target_size."
        )
    except Exception as exc:
        return ImageToSvgOutput(success=False, error=f"Image vectorization failed: {exc}")

    artifacts = _parse_artifacts(data)
    return ImageToSvgOutput(
        success=True,
        id=data.get("id"),
        created=data.get("created"),
        svg_content=artifacts[0].svg if artifacts else None,
        artifacts=artifacts,
        credits=data.get("credits"),
        usage=_parse_usage(data),
    )


@tool(args_schema=ListModelsInput)
@serialize_pydantic_return
async def list_models(api_key: str) -> ListModelsOutput:
    """List all available QuiverAI models."""
    if not api_key or not api_key.strip():
        return ListModelsOutput(
            success=False,
            error="QuiverAI API key is empty. Please configure a valid Quiver credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_MODELS_TIMEOUT) as client:
            response = await client.get(
                f"{_QUIVER_API_BASE}/models", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return ListModelsOutput(
                success=False,
                error=f"Quiver API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListModelsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListModelsOutput(success=False, error=f"List models failed: {exc}")

    models = [
        ModelInfo(
            id=model.get("id"),
            name=model.get("name"),
            description=model.get("description"),
            created=model.get("created"),
            owned_by=model.get("owned_by"),
            input_modalities=model.get("input_modalities") or [],
            output_modalities=model.get("output_modalities") or [],
            context_length=model.get("context_length"),
            max_output_length=model.get("max_output_length"),
            supported_operations=model.get("supported_operations") or [],
            supported_sampling_parameters=model.get("supported_sampling_parameters") or [],
        )
        for model in data.get("data") or []
    ]
    return ListModelsOutput(
        success=True,
        models=models,
        total_models=len(models),
    )
