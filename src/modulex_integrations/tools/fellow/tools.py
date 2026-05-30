"""Fellow LangChain @tool functions."""
from __future__ import annotations

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.fellow.outputs import (
    ArchiveActionItemOutput,
    CompleteActionItemOutput,
    GetNoteByIdOutput,
)

__all__ = [
    "archive_action_item",
    "complete_action_item",
    "get_note_by_id",
]

_TIMEOUT = 30.0


def _base_url(subdomain: str) -> str:
    return f"https://{subdomain}.fellow.app/api/v1"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class ArchiveActionItemInput(BaseModel):
    action_item_id: str = Field(description="The ID of the action item to archive")
    subdomain: str = Field(description="Fellow workspace subdomain")
    api_key: str = Field(description="Fellow API key")


class CompleteActionItemInput(BaseModel):
    action_item_id: str = Field(description="The ID of the action item to mark as complete")
    subdomain: str = Field(description="Fellow workspace subdomain")
    api_key: str = Field(description="Fellow API key")


class GetNoteByIdInput(BaseModel):
    note_id: str = Field(description="The ID of the note to retrieve")
    subdomain: str = Field(description="Fellow workspace subdomain")
    api_key: str = Field(description="Fellow API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ArchiveActionItemInput)
@serialize_pydantic_return
async def archive_action_item(
    action_item_id: str,
    subdomain: str,
    api_key: str,
) -> ArchiveActionItemOutput:
    """Archive an action item."""
    if not api_key or not api_key.strip():
        return ArchiveActionItemOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not subdomain or not subdomain.strip():
        return ArchiveActionItemOutput(
            success=False,
            error="Subdomain is empty. Please configure your Fellow workspace subdomain.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(subdomain)}/action_item/{action_item_id}/archive",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return ArchiveActionItemOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ArchiveActionItemOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ArchiveActionItemOutput(success=False, error=f"Call failed: {exc}")

    return ArchiveActionItemOutput(success=True, data=data)


@tool(args_schema=CompleteActionItemInput)
@serialize_pydantic_return
async def complete_action_item(
    action_item_id: str,
    subdomain: str,
    api_key: str,
) -> CompleteActionItemOutput:
    """Complete an action item."""
    if not api_key or not api_key.strip():
        return CompleteActionItemOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not subdomain or not subdomain.strip():
        return CompleteActionItemOutput(
            success=False,
            error="Subdomain is empty. Please configure your Fellow workspace subdomain.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(subdomain)}/action_item/{action_item_id}/complete",
                headers=_headers(api_key),
                json={"completed": True},
            )
        if response.status_code != 200:
            return CompleteActionItemOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CompleteActionItemOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CompleteActionItemOutput(success=False, error=f"Call failed: {exc}")

    return CompleteActionItemOutput(success=True, data=data)


@tool(args_schema=GetNoteByIdInput)
@serialize_pydantic_return
async def get_note_by_id(
    note_id: str,
    subdomain: str,
    api_key: str,
) -> GetNoteByIdOutput:
    """Get a note by its ID."""
    if not api_key or not api_key.strip():
        return GetNoteByIdOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not subdomain or not subdomain.strip():
        return GetNoteByIdOutput(
            success=False,
            error="Subdomain is empty. Please configure your Fellow workspace subdomain.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(subdomain)}/note/{note_id}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetNoteByIdOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetNoteByIdOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetNoteByIdOutput(success=False, error=f"Call failed: {exc}")

    return GetNoteByIdOutput(success=True, data=data)
