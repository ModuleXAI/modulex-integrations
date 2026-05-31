"""HeyGen LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.heygen.outputs import (
    CreateTalkingPhotoOutput,
    CreateVideoFromTemplateOutput,
    ListCustomEventsOptionsOutput,
    ListVoiceIdOptionsOutput,
    RetrieveVideoLinkOutput,
    VoiceInfo,
)

__all__ = [
    "create_talking_photo",
    "create_video_from_template",
    "list_custom_events_options",
    "list_voice_id_options",
    "retrieve_video_link",
]

_BASE_URL = "https://api.heygen.com"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class CreateTalkingPhotoInput(BaseModel):
    talking_photo_id: str = Field(description="Identifier of the talking photo to use")
    text: str = Field(description="The text that the character will speak")
    voice_id: str = Field(description="Identifier of the voice to use")
    api_key: str = Field(description="HeyGen API key")
    title: str | None = Field(default=None, description="Title of the video")
    test: bool | None = Field(default=None, description="Set to true to use test mode (no credits charged, watermark added)")
    caption: bool | None = Field(default=None, description="Set to true to create video with captions")
    scale: str | None = Field(default=None, description="Talking photo scale, value between 0 and 2.0 (default 1.0)")
    talking_photo_style: str | None = Field(default=None, description="Talking photo crop style: square, circle")
    talking_style: str | None = Field(default=None, description="Talking photo talking style: stable, expressive")
    expression: str | None = Field(default=None, description="Talking photo expression style: default, happy")
    super_resolution: bool | None = Field(default=None, description="Whether to enhance the photo image")
    matting: bool | None = Field(default=None, description="Whether to apply matting to the photo")


class CreateVideoFromTemplateInput(BaseModel):
    template_id: str = Field(description="Identifier of the template to use")
    api_key: str = Field(description="HeyGen API key")
    title: str | None = Field(default=None, description="Title of the video")
    test: bool | None = Field(default=None, description="Set to true to use test mode (no credits charged, watermark added)")
    caption: bool | None = Field(default=None, description="Set to true to create video with captions")
    variables: dict[str, Any] | None = Field(default=None, description="Template variable overrides as a JSON object where keys are variable names and values are objects with variable properties")


class ListCustomEventsOptionsInput(BaseModel):
    api_key: str = Field(description="HeyGen API key")


class ListVoiceIdOptionsInput(BaseModel):
    api_key: str = Field(description="HeyGen API key")


class RetrieveVideoLinkInput(BaseModel):
    video_id: str = Field(description="Identifier of the HeyGen video to retrieve")
    api_key: str = Field(description="HeyGen API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateTalkingPhotoInput)
@serialize_pydantic_return
async def create_talking_photo(
    talking_photo_id: str,
    text: str,
    voice_id: str,
    api_key: str,
    title: str | None = None,
    test: bool | None = None,
    caption: bool | None = None,
    scale: str | None = None,
    talking_photo_style: str | None = None,
    talking_style: str | None = None,
    expression: str | None = None,
    super_resolution: bool | None = None,
    matting: bool | None = None,
) -> CreateTalkingPhotoOutput:
    """Creates a talking photo video from a provided image, text, and voice"""
    if not api_key or not api_key.strip():
        return CreateTalkingPhotoOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    talking_photo_config: dict[str, Any] = {
        "type": "talking_photo",
        "talking_photo_id": talking_photo_id,
    }
    if talking_photo_style is not None:
        talking_photo_config["talking_photo_style"] = talking_photo_style
    if talking_style is not None:
        talking_photo_config["talking_style"] = talking_style
    if expression is not None:
        talking_photo_config["expression"] = expression
    if super_resolution is not None:
        talking_photo_config["super_resolution"] = super_resolution
    if matting is not None:
        talking_photo_config["matting"] = matting
    if scale is not None:
        talking_photo_config["scale"] = float(scale)

    voice_config: dict[str, Any] = {
        "type": "text",
        "voice_id": voice_id,
        "input_text": text,
    }

    video_input: dict[str, Any] = {
        "character": talking_photo_config,
        "voice": voice_config,
    }

    payload: dict[str, Any] = {
        "video_inputs": [video_input],
    }
    if title is not None:
        payload["title"] = title
    if test is not None:
        payload["test"] = test
    if caption is not None:
        payload["caption"] = caption

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v2/video/generate",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return CreateTalkingPhotoOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateTalkingPhotoOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTalkingPhotoOutput(success=False, error=f"Call failed: {exc}")

    video_data = data.get("data", {})
    return CreateTalkingPhotoOutput(
        success=True,
        video_id=video_data.get("video_id"),
        status=video_data.get("status"),
    )


@tool(args_schema=CreateVideoFromTemplateInput)
@serialize_pydantic_return
async def create_video_from_template(
    template_id: str,
    api_key: str,
    title: str | None = None,
    test: bool | None = None,
    caption: bool | None = None,
    variables: dict[str, Any] | None = None,
) -> CreateVideoFromTemplateOutput:
    """Generates a video from a selected template with optional variable overrides"""
    if not api_key or not api_key.strip():
        return CreateVideoFromTemplateOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if test is not None:
        payload["test"] = test
    if caption is not None:
        payload["caption"] = caption
    if variables is not None:
        payload["variables"] = variables

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v2/template/{template_id}/generate",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return CreateVideoFromTemplateOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateVideoFromTemplateOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateVideoFromTemplateOutput(success=False, error=f"Call failed: {exc}")

    video_data = data.get("data", {})
    return CreateVideoFromTemplateOutput(
        success=True,
        video_id=video_data.get("video_id"),
        status=video_data.get("status"),
    )


@tool(args_schema=ListCustomEventsOptionsInput)
@serialize_pydantic_return
async def list_custom_events_options(
    api_key: str,
) -> ListCustomEventsOptionsOutput:
    """Retrieves available options for webhook custom events"""
    if not api_key or not api_key.strip():
        return ListCustomEventsOptionsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/webhook/webhook.list",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return ListCustomEventsOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListCustomEventsOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCustomEventsOptionsOutput(success=False, error=f"Call failed: {exc}")

    events = data.get("data", [])
    if isinstance(events, list):
        return ListCustomEventsOptionsOutput(success=True, events=events)
    return ListCustomEventsOptionsOutput(success=True, events=[])


@tool(args_schema=ListVoiceIdOptionsInput)
@serialize_pydantic_return
async def list_voice_id_options(
    api_key: str,
) -> ListVoiceIdOptionsOutput:
    """Retrieves available voice options for video generation"""
    if not api_key or not api_key.strip():
        return ListVoiceIdOptionsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v2/voices",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return ListVoiceIdOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListVoiceIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListVoiceIdOptionsOutput(success=False, error=f"Call failed: {exc}")

    voices_data = data.get("data", {}).get("voices", [])
    voices = [
        VoiceInfo(voice_id=v.get("voice_id"), name=v.get("name"))
        for v in voices_data
        if isinstance(v, dict)
    ]
    return ListVoiceIdOptionsOutput(success=True, voices=voices)


@tool(args_schema=RetrieveVideoLinkInput)
@serialize_pydantic_return
async def retrieve_video_link(
    video_id: str,
    api_key: str,
) -> RetrieveVideoLinkOutput:
    """Fetches the status and download link for a specific HeyGen video"""
    if not api_key or not api_key.strip():
        return RetrieveVideoLinkOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/video_status.get",
                headers=_headers(api_key),
                params={"video_id": video_id},
            )
        if response.status_code != 200:
            return RetrieveVideoLinkOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RetrieveVideoLinkOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RetrieveVideoLinkOutput(success=False, error=f"Call failed: {exc}")

    video_data = data.get("data", {})
    return RetrieveVideoLinkOutput(
        success=True,
        video_id=video_data.get("video_id"),
        status=video_data.get("status"),
        video_url=video_data.get("video_url"),
        thumbnail_url=video_data.get("thumbnail_url"),
        duration=video_data.get("duration"),
        caption_url=video_data.get("caption_url"),
    )
