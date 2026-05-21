"""Happy-path tests for every hootsuite @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.hootsuite import (
    TOOLS,
    create_media_upload_job,
    get_media_upload_status,
    list_social_profiles,
    manifest,
    schedule_message,
)
from modulex_integrations.tools.hootsuite.outputs import (
    CreateMediaUploadJobOutput,
    GetMediaUploadStatusOutput,
    ListSocialProfilesOutput,
    ScheduleMessageOutput,
)

API = "https://platform.hootsuite.com/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_media_upload_job(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/media",
        json={
            "data": {
                "id": "media123",
                "uploadUrl": "https://upload.hootsuite.com/upload/media123",
            }
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/image.png",
        content=b"fake-image-bytes",
    )
    httpx_mock.add_response(
        method="PUT",
        url="https://upload.hootsuite.com/upload/media123",
        status_code=200,
    )

    result_dict = await create_media_upload_job.ainvoke(
        _args(size_bytes=1024, mime_type="image/png", file_url="https://example.com/image.png")
    )

    assert isinstance(result_dict, dict)
    result = CreateMediaUploadJobOutput.model_validate(result_dict)
    assert result.success is True
    assert result.file_id == "media123"


@pytest.mark.asyncio
async def test_get_media_upload_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/media/media123",
        json={
            "data": {
                "id": "media123",
                "state": "READY",
                "downloadUrl": "https://cdn.hootsuite.com/media123.png",
                "thumbnailUrl": "https://cdn.hootsuite.com/media123_thumb.png",
            }
        },
    )

    result_dict = await get_media_upload_status.ainvoke(_args(file_id="media123"))

    assert isinstance(result_dict, dict)
    result = GetMediaUploadStatusOutput.model_validate(result_dict)
    assert result.success is True
    assert result.state == "READY"
    assert result.download_url == "https://cdn.hootsuite.com/media123.png"


@pytest.mark.asyncio
async def test_list_social_profiles(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/socialProfiles",
        json={
            "data": [
                {
                    "id": "prof1",
                    "type": "TWITTER",
                    "socialNetworkUsername": "myhandle",
                    "socialNetworkId": "123456",
                },
            ]
        },
    )

    result_dict = await list_social_profiles.ainvoke(_AUTH)

    assert isinstance(result_dict, dict)
    result = ListSocialProfilesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.profiles) == 1
    assert result.profiles[0].id == "prof1"


@pytest.mark.asyncio
async def test_schedule_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/messages",
        json={
            "data": [
                {
                    "id": "msg001",
                    "state": "SCHEDULED",
                    "text": "Hello world",
                    "scheduledSendTime": "2026-06-01T12:00:00Z",
                },
            ]
        },
    )

    result_dict = await schedule_message.ainvoke(
        _args(
            text="Hello world",
            social_profile_ids=["prof1"],
            scheduled_send_time="2026-06-01T12:00:00Z",
        )
    )

    assert isinstance(result_dict, dict)
    result = ScheduleMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.messages) == 1
    assert result.messages[0].id == "msg001"
    assert result.messages[0].state == "SCHEDULED"


@pytest.mark.asyncio
async def test_list_social_profiles_empty_token() -> None:
    """Failure path: empty access_token returns error without hitting the wire."""
    result_dict = await list_social_profiles.ainvoke(
        {"auth_type": "oauth2", "auth_data": {"access_token": ""}}
    )
    assert isinstance(result_dict, dict)
    result = ListSocialProfilesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
