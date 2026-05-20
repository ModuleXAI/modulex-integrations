"""Hootsuite LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.hootsuite.outputs import (
    CreateMediaUploadJobOutput,
    GetMediaUploadStatusOutput,
    ListSocialProfilesOutput,
    ScheduledMessage,
    ScheduleMessageOutput,
    SocialProfile,
)

__all__ = [
    "create_media_upload_job",
    "get_media_upload_status",
    "list_social_profiles",
    "schedule_message",
]

_BASE_URL = "https://platform.hootsuite.com/v1"
_TIMEOUT = 60.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Hootsuite API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class CreateMediaUploadJobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    size_bytes: int = Field(description="The size of the file in bytes")
    mime_type: str = Field(description="The MIME type of the file (e.g. image/png, image/jpeg)")
    file_url: str = Field(description="A publicly-accessible URL to the file to upload")


class GetMediaUploadStatusInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    file_id: str = Field(description="The ID of the media file to check status for")


class ListSocialProfilesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ScheduleMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    text: str = Field(description="The message text to publish")
    social_profile_ids: list[str] = Field(description="Array of social profile ID strings to post to")
    scheduled_send_time: str | None = Field(default=None, description="ISO-8601 UTC time to send (must end with 'Z')")
    media_urls: list[str] | None = Field(default=None, description="Array of ow.ly media URLs to attach")
    media: list[str] | None = Field(default=None, description="Array of media IDs to attach")
    tags: list[str] | None = Field(default=None, description="Array of Hootsuite message tags (case sensitive)")
    webhook_urls: list[str] | None = Field(default=None, description="Array of webhook URLs for state change notifications")
    targeting: dict[str, Any] | None = Field(default=None, description="Targeting object for Facebook/LinkedIn posts")
    privacy: dict[str, Any] | None = Field(default=None, description="Privacy settings object")
    latitude: float | None = Field(default=None, description="Latitude in decimal degrees (-90 to 90)")
    longitude: float | None = Field(default=None, description="Longitude in decimal degrees (-180 to 180)")
    email_notification: bool | None = Field(default=None, description="Whether to send email notification on publish")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateMediaUploadJobInput)
@serialize_pydantic_return
async def create_media_upload_job(
    auth_type: str,
    auth_data: dict[str, Any],
    size_bytes: int,
    mime_type: str,
    file_url: str,
) -> CreateMediaUploadJobOutput:
    """Creates a new media upload job on Hootsuite by uploading a file from a public URL"""
    if not auth_data.get("access_token"):
        return CreateMediaUploadJobOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            init_response = await client.post(
                f"{_BASE_URL}/media",
                headers={**headers, "Content-Type": "application/json"},
                json={"sizeBytes": size_bytes, "mimeType": mime_type},
            )
            if init_response.status_code not in (200, 201):
                return CreateMediaUploadJobOutput(
                    success=False,
                    error=f"Failed to initialize upload ({init_response.status_code}): {init_response.text}",
                )
            init_data = init_response.json()
            upload_url = init_data.get("data", {}).get("uploadUrl")
            file_id = init_data.get("data", {}).get("id")
            if not upload_url:
                return CreateMediaUploadJobOutput(
                    success=False,
                    error="No uploadUrl returned from Hootsuite",
                )

            file_response = await client.get(file_url)
            if file_response.status_code != 200:
                return CreateMediaUploadJobOutput(
                    success=False,
                    error=f"Failed to download file from URL ({file_response.status_code})",
                )

            upload_response = await client.put(
                upload_url,
                content=file_response.content,
                headers={"Content-Type": mime_type},
            )
            if upload_response.status_code not in (200, 201, 204):
                return CreateMediaUploadJobOutput(
                    success=False,
                    error=f"Failed to upload file ({upload_response.status_code}): {upload_response.text}",
                )
    except httpx.TimeoutException:
        return CreateMediaUploadJobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateMediaUploadJobOutput(success=False, error=f"Call failed: {exc}")

    return CreateMediaUploadJobOutput(success=True, file_id=file_id)


@tool(args_schema=GetMediaUploadStatusInput)
@serialize_pydantic_return
async def get_media_upload_status(
    auth_type: str,
    auth_data: dict[str, Any],
    file_id: str,
) -> GetMediaUploadStatusOutput:
    """Gets the status of a media upload job on Hootsuite"""
    if not auth_data.get("access_token"):
        return GetMediaUploadStatusOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/media/{file_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetMediaUploadStatusOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return GetMediaUploadStatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMediaUploadStatusOutput(success=False, error=f"Call failed: {exc}")

    return GetMediaUploadStatusOutput(
        success=True,
        id=data.get("id"),
        state=data.get("state"),
        download_url=data.get("downloadUrl"),
        thumbnail_url=data.get("thumbnailUrl"),
    )


@tool(args_schema=ListSocialProfilesInput)
@serialize_pydantic_return
async def list_social_profiles(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListSocialProfilesOutput:
    """Retrieves a list of social profiles for the authenticated Hootsuite account"""
    if not auth_data.get("access_token"):
        return ListSocialProfilesOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/socialProfiles",
                headers=headers,
            )
        if response.status_code != 200:
            return ListSocialProfilesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", [])
    except httpx.TimeoutException:
        return ListSocialProfilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSocialProfilesOutput(success=False, error=f"Call failed: {exc}")

    profiles = [
        SocialProfile(
            id=p.get("id"),
            type=p.get("type"),
            social_network_username=p.get("socialNetworkUsername"),
            social_network_id=p.get("socialNetworkId"),
        )
        for p in data
    ]
    return ListSocialProfilesOutput(success=True, profiles=profiles)


@tool(args_schema=ScheduleMessageInput)
@serialize_pydantic_return
async def schedule_message(
    auth_type: str,
    auth_data: dict[str, Any],
    text: str,
    social_profile_ids: list[str],
    scheduled_send_time: str | None = None,
    media_urls: list[str] | None = None,
    media: list[str] | None = None,
    tags: list[str] | None = None,
    webhook_urls: list[str] | None = None,
    targeting: dict[str, Any] | None = None,
    privacy: dict[str, Any] | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    email_notification: bool | None = None,
) -> ScheduleMessageOutput:
    """Schedules a message to be published on one or more social profiles"""
    if not auth_data.get("access_token"):
        return ScheduleMessageOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {
        "text": text,
        "socialProfileIds": social_profile_ids,
    }
    if scheduled_send_time is not None:
        payload["scheduledSendTime"] = scheduled_send_time
    if media_urls is not None:
        payload["mediaUrls"] = media_urls
    if media is not None:
        payload["media"] = [{"id": m} for m in media]
    if tags is not None:
        payload["tags"] = tags
    if webhook_urls is not None:
        payload["webhookUrls"] = webhook_urls
    if targeting is not None:
        payload["targeting"] = targeting
    if privacy is not None:
        payload["privacy"] = privacy
    if latitude is not None:
        payload["location"] = {"latitude": latitude, "longitude": longitude}
    elif longitude is not None:
        payload["location"] = {"latitude": latitude, "longitude": longitude}
    if email_notification is not None:
        payload["emailNotification"] = email_notification

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/messages",
                headers={**headers, "Content-Type": "application/json"},
                json=payload,
            )
        if response.status_code not in (200, 201):
            return ScheduleMessageOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", [])
    except httpx.TimeoutException:
        return ScheduleMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ScheduleMessageOutput(success=False, error=f"Call failed: {exc}")

    messages = [
        ScheduledMessage(
            id=m.get("id"),
            state=m.get("state"),
            text=m.get("text"),
            scheduled_send_time=m.get("scheduledSendTime"),
        )
        for m in data
    ]
    return ScheduleMessageOutput(success=True, messages=messages)
