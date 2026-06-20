"""Granola LangChain ``@tool`` functions.

Three async tools wrapping the Granola REST API. The calling convention
is the modulex *api_key* one: the runtime injects an ``api_key: str``
directly (resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair.

Error model: non-2xx HTTP responses and timeouts do *not* raise — they
are returned as the typed output with ``success=False`` + ``error``.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.granola.outputs import (
    Attendee,
    FolderRef,
    GetNoteOutput,
    ListFoldersOutput,
    ListNotesOutput,
    NoteSummary,
    TranscriptSegment,
)

__all__ = ["get_note", "list_folders", "list_notes"]

_GRANOLA_API_BASE = "https://public-api.granola.ai/v1"
_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class ListNotesInput(BaseModel):
    api_key: str = Field(description="Granola API key (provided by credential system)")
    created_before: str | None = Field(
        default=None, description="Return notes created before this date (ISO 8601)"
    )
    created_after: str | None = Field(
        default=None, description="Return notes created after this date (ISO 8601)"
    )
    updated_after: str | None = Field(
        default=None, description="Return notes updated after this date (ISO 8601)"
    )
    folder_id: str | None = Field(
        default=None,
        description="Return notes in this folder and its child folders (e.g., fol_4y6LduVdwSKC27)",
    )
    cursor: str | None = Field(
        default=None, description="Pagination cursor from a previous response"
    )
    page_size: int | None = Field(
        default=None, description="Number of notes per page (1-30, default 10)"
    )


class GetNoteInput(BaseModel):
    note_id: str = Field(description="The note ID (e.g., not_1d3tmYTlCICgjy)")
    api_key: str = Field(description="Granola API key (provided by credential system)")
    include_transcript: bool = Field(
        default=False, description="Whether to include the meeting transcript"
    )


class ListFoldersInput(BaseModel):
    api_key: str = Field(description="Granola API key (provided by credential system)")
    cursor: str | None = Field(
        default=None, description="Pagination cursor from a previous response"
    )
    page_size: int | None = Field(
        default=None, description="Number of folders per page (1-30, default 10)"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListNotesInput)
@serialize_pydantic_return
async def list_notes(
    api_key: str,
    created_before: str | None = None,
    created_after: str | None = None,
    updated_after: str | None = None,
    folder_id: str | None = None,
    cursor: str | None = None,
    page_size: int | None = None,
) -> ListNotesOutput:
    """Lists meeting notes from Granola with optional date filters and pagination."""
    if not api_key or not api_key.strip():
        return ListNotesOutput(
            success=False,
            error="Granola API key is empty. Please configure a valid Granola credential.",
        )

    params: dict[str, Any] = {}
    if created_before:
        params["created_before"] = created_before
    if created_after:
        params["created_after"] = created_after
    if updated_after:
        params["updated_after"] = updated_after
    if folder_id:
        params["folder_id"] = folder_id.strip()
    if cursor:
        params["cursor"] = cursor
    if page_size is not None:
        params["page_size"] = page_size

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_GRANOLA_API_BASE}/notes", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListNotesOutput(
                success=False,
                error=f"Granola API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListNotesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListNotesOutput(success=False, error=f"List notes failed: {exc}")

    return ListNotesOutput(
        success=True,
        notes=[
            NoteSummary(
                id=note.get("id"),
                title=note.get("title"),
                owner_name=(note.get("owner") or {}).get("name"),
                owner_email=(note.get("owner") or {}).get("email"),
                created_at=note.get("created_at"),
                updated_at=note.get("updated_at"),
            )
            for note in data.get("notes") or []
        ],
        has_more=data.get("hasMore") or False,
        cursor=data.get("cursor"),
    )


@tool(args_schema=GetNoteInput)
@serialize_pydantic_return
async def get_note(
    note_id: str,
    api_key: str,
    include_transcript: bool = False,
) -> GetNoteOutput:
    """Retrieves a specific meeting note from Granola by ID.

    Includes summary, attendees, calendar event details, and optionally
    the transcript.
    """
    if not api_key or not api_key.strip():
        return GetNoteOutput(
            success=False,
            error="Granola API key is empty. Please configure a valid Granola credential.",
        )
    if not note_id or not note_id.strip():
        return GetNoteOutput(success=False, error="note_id is required.")

    params: dict[str, Any] = {}
    if include_transcript:
        params["include"] = "transcript"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_GRANOLA_API_BASE}/notes/{note_id.strip()}",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetNoteOutput(
                success=False,
                error=f"Granola API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetNoteOutput(success=False, error=f"Get note failed: {exc}")

    owner = data.get("owner") or {}
    calendar_event = data.get("calendar_event") or {}
    raw_transcript = data.get("transcript")
    transcript: list[TranscriptSegment] | None
    if raw_transcript is None:
        transcript = None
    else:
        transcript = [
            TranscriptSegment(
                speaker=(segment.get("speaker") or {}).get("source"),
                speaker_label=(segment.get("speaker") or {}).get("diarization_label"),
                text=segment.get("text"),
                start_time=segment.get("start_time"),
                end_time=segment.get("end_time"),
            )
            for segment in raw_transcript
        ]

    return GetNoteOutput(
        success=True,
        id=data.get("id"),
        title=data.get("title"),
        owner_name=owner.get("name"),
        owner_email=owner.get("email"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        web_url=data.get("web_url"),
        summary_text=data.get("summary_text"),
        summary_markdown=data.get("summary_markdown"),
        attendees=[
            Attendee(name=a.get("name"), email=a.get("email"))
            for a in data.get("attendees") or []
        ],
        folders=[
            FolderRef(id=f.get("id"), name=f.get("name"))
            for f in data.get("folder_membership") or []
        ],
        calendar_event_title=calendar_event.get("event_title"),
        calendar_organiser=calendar_event.get("organiser"),
        calendar_event_id=calendar_event.get("calendar_event_id"),
        scheduled_start_time=calendar_event.get("scheduled_start_time"),
        scheduled_end_time=calendar_event.get("scheduled_end_time"),
        invitees=[
            invitee.get("email")
            for invitee in calendar_event.get("invitees") or []
            if invitee.get("email")
        ],
        transcript=transcript,
    )


@tool(args_schema=ListFoldersInput)
@serialize_pydantic_return
async def list_folders(
    api_key: str,
    cursor: str | None = None,
    page_size: int | None = None,
) -> ListFoldersOutput:
    """Lists folders from Granola, sorted alphabetically, with pagination."""
    if not api_key or not api_key.strip():
        return ListFoldersOutput(
            success=False,
            error="Granola API key is empty. Please configure a valid Granola credential.",
        )

    params: dict[str, Any] = {}
    if cursor:
        params["cursor"] = cursor
    if page_size is not None:
        params["page_size"] = page_size

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_GRANOLA_API_BASE}/folders", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListFoldersOutput(
                success=False,
                error=f"Granola API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFoldersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFoldersOutput(success=False, error=f"List folders failed: {exc}")

    return ListFoldersOutput(
        success=True,
        folders=[
            FolderRef(
                id=folder.get("id"),
                name=folder.get("name"),
                parent_folder_id=folder.get("parent_folder_id"),
            )
            for folder in data.get("folders") or []
        ],
        has_more=data.get("hasMore") or False,
        cursor=data.get("cursor"),
    )
