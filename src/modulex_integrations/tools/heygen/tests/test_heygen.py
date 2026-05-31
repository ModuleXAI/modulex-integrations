"""Happy-path tests for every heygen @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.heygen import (
    TOOLS,
    create_talking_photo,
    create_video_from_template,
    list_custom_events_options,
    list_voice_id_options,
    manifest,
    retrieve_video_link,
)
from modulex_integrations.tools.heygen.outputs import (
    CreateTalkingPhotoOutput,
    CreateVideoFromTemplateOutput,
    ListCustomEventsOptionsOutput,
    ListVoiceIdOptionsOutput,
    RetrieveVideoLinkOutput,
)

API = "https://api.heygen.com"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_5_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_talking_photo(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/video/generate",
        json={
            "data": {
                "video_id": "vid_123",
                "status": "processing",
            },
        },
    )

    result_dict = await create_talking_photo.ainvoke(
        _args(
            talking_photo_id="tp_abc",
            text="Hello world",
            voice_id="voice_xyz",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateTalkingPhotoOutput.model_validate(result_dict)
    assert result.success is True
    assert result.video_id == "vid_123"
    assert result.status == "processing"


@pytest.mark.asyncio
async def test_create_video_from_template(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/template/tmpl_001/generate",
        json={
            "data": {
                "video_id": "vid_456",
                "status": "processing",
            },
        },
    )

    result_dict = await create_video_from_template.ainvoke(
        _args(template_id="tmpl_001")
    )

    assert isinstance(result_dict, dict)
    result = CreateVideoFromTemplateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.video_id == "vid_456"
    assert result.status == "processing"


@pytest.mark.asyncio
async def test_list_custom_events_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/webhook/webhook.list",
        json={
            "data": [
                "avatar_video.success",
                "avatar_video.fail",
            ],
        },
    )

    result_dict = await list_custom_events_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListCustomEventsOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert "avatar_video.success" in result.events


@pytest.mark.asyncio
async def test_list_voice_id_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/voices",
        json={
            "data": {
                "voices": [
                    {"voice_id": "v1", "name": "Sara"},
                    {"voice_id": "v2", "name": "Mark"},
                ],
            },
        },
    )

    result_dict = await list_voice_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListVoiceIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.voices) == 2
    assert result.voices[0].voice_id == "v1"


@pytest.mark.asyncio
async def test_retrieve_video_link(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/video_status.get?video_id=vid_123",
        json={
            "data": {
                "video_id": "vid_123",
                "status": "completed",
                "video_url": "https://files.heygen.ai/video.mp4",
                "thumbnail_url": "https://files.heygen.ai/thumb.jpg",
                "duration": 12.5,
                "caption_url": "https://files.heygen.ai/caption.srt",
            },
        },
    )

    result_dict = await retrieve_video_link.ainvoke(_args(video_id="vid_123"))

    assert isinstance(result_dict, dict)
    result = RetrieveVideoLinkOutput.model_validate(result_dict)
    assert result.success is True
    assert result.video_id == "vid_123"
    assert result.status == "completed"
    assert result.video_url == "https://files.heygen.ai/video.mp4"
    assert result.duration == 12.5


@pytest.mark.asyncio
async def test_create_talking_photo_validates_empty_api_key() -> None:
    result_dict = await create_talking_photo.ainvoke(
        {"talking_photo_id": "tp", "text": "hi", "voice_id": "v", "api_key": ""}
    )
    result = CreateTalkingPhotoOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
