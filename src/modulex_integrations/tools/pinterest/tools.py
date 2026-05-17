"""Pinterest LangChain ``@tool`` functions.

Both api_key and oauth2 auth flows resolve to a Bearer access token
at runtime — the modulex ToolExecutor injects either as ``api_key``,
so a single function signature handles both auth_schemas.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.pinterest.outputs import (
    CreatePinOutput,
    GetBoardSectionsOutput,
    ListBoardsOutput,
    ListPinsOutput,
)

__all__ = ["create_pin", "get_board_sections", "list_boards", "list_pins"]

_API_BASE = "https://api.pinterest.com/v5"
_TIMEOUT = 30.0
_DEFAULT_PAGE_SIZE = 25


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


_AUTH_ERROR_MSG = "Authentication failed. Please check your API key/access token."


def _auth_error(message: str = _AUTH_ERROR_MSG) -> str:
    return message


class ListBoardsInput(BaseModel):
    api_key: str = Field(description="Pinterest OAuth access token")
    page_size: int | None = Field(default=25, description="Boards per page (max 250)")
    bookmark: str | None = Field(default=None, description="Pagination cursor")


class GetBoardSectionsInput(BaseModel):
    api_key: str = Field(description="Pinterest OAuth access token")
    board_id: str = Field(description="The ID of the board")
    page_size: int | None = Field(default=25, description="Sections per page (max 250)")
    bookmark: str | None = Field(default=None, description="Pagination cursor")


class CreatePinInput(BaseModel):
    api_key: str = Field(description="Pinterest OAuth access token")
    board_id: str = Field(description="The ID of the board to pin to")
    title: str = Field(description="Title of the pin")
    media_url: str = Field(description="URL of the image to pin")
    description: str | None = Field(default=None, description="Description of the pin")
    link: str | None = Field(default=None, description="Source link/URL for the pin")
    alt_text: str | None = Field(default=None, description="Alt text for accessibility")
    board_section_id: str | None = Field(default=None, description="Board section ID")


class ListPinsInput(BaseModel):
    api_key: str = Field(description="Pinterest OAuth access token")
    board_id: str = Field(description="The ID of the board")
    board_section_id: str | None = Field(default=None, description="Board section ID")
    page_size: int | None = Field(default=25, description="Pins per page (max 250)")
    bookmark: str | None = Field(default=None, description="Pagination cursor")


@tool(args_schema=ListBoardsInput)
@serialize_pydantic_return
async def list_boards(
    api_key: str,
    page_size: int | None = 25,
    bookmark: str | None = None,
) -> ListBoardsOutput:
    """List all Pinterest boards for the authenticated user."""
    params: dict[str, Any] = {"page_size": min(page_size or _DEFAULT_PAGE_SIZE, 250)}
    if bookmark:
        params["bookmark"] = bookmark

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/boards", headers=_headers(api_key), params=params
            )
        if response.status_code == 401:
            return ListBoardsOutput(success=False, error=_auth_error())
        if response.status_code != 200:
            return ListBoardsOutput(
                success=False, error=f"API error {response.status_code}: {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListBoardsOutput(success=False, error="Request timed out while listing boards")
    except Exception as exc:
        return ListBoardsOutput(success=False, error=str(exc))

    boards = data.get("items") or []
    return ListBoardsOutput(
        success=True,
        boards=boards,
        count=len(boards),
        bookmark=data.get("bookmark"),
    )


@tool(args_schema=GetBoardSectionsInput)
@serialize_pydantic_return
async def get_board_sections(
    api_key: str,
    board_id: str,
    page_size: int | None = 25,
    bookmark: str | None = None,
) -> GetBoardSectionsOutput:
    """Get sections of a Pinterest board."""
    params: dict[str, Any] = {"page_size": min(page_size or _DEFAULT_PAGE_SIZE, 250)}
    if bookmark:
        params["bookmark"] = bookmark

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/boards/{board_id}/sections",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code == 401:
            return GetBoardSectionsOutput(success=False, error=_auth_error())
        if response.status_code == 404:
            return GetBoardSectionsOutput(success=False, error=f"Board {board_id} not found")
        if response.status_code != 200:
            return GetBoardSectionsOutput(
                success=False, error=f"API error {response.status_code}: {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetBoardSectionsOutput(
            success=False, error="Request timed out while getting board sections"
        )
    except Exception as exc:
        return GetBoardSectionsOutput(success=False, error=str(exc))

    sections = data.get("items") or []
    return GetBoardSectionsOutput(
        success=True,
        board_id=board_id,
        sections=sections,
        count=len(sections),
        bookmark=data.get("bookmark"),
    )


@tool(args_schema=CreatePinInput)
@serialize_pydantic_return
async def create_pin(
    api_key: str,
    board_id: str,
    title: str,
    media_url: str,
    description: str | None = None,
    link: str | None = None,
    alt_text: str | None = None,
    board_section_id: str | None = None,
) -> CreatePinOutput:
    """Create a new pin on a Pinterest board."""
    payload: dict[str, Any] = {
        "board_id": board_id,
        "title": title,
        "media_source": {"source_type": "image_url", "url": media_url},
    }
    if description:
        payload["description"] = description
    if link:
        payload["link"] = link
    if alt_text:
        payload["alt_text"] = alt_text
    if board_section_id:
        payload["board_section_id"] = board_section_id

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/pins", headers=_headers(api_key), json=payload
            )
        if response.status_code == 401:
            return CreatePinOutput(success=False, error=_auth_error())
        if response.status_code == 400:
            return CreatePinOutput(
                success=False,
                error=(
                    f"Bad request: {response.text}. "
                    "Please check the media URL and board ID."
                ),
            )
        if response.status_code == 404:
            return CreatePinOutput(success=False, error=f"Board {board_id} not found")
        if response.status_code not in (200, 201):
            return CreatePinOutput(
                success=False, error=f"API error {response.status_code}: {response.text}"
            )
        pin = response.json() or {}
    except httpx.TimeoutException:
        return CreatePinOutput(success=False, error="Request timed out while creating pin")
    except Exception as exc:
        return CreatePinOutput(success=False, error=str(exc))

    return CreatePinOutput(
        success=True,
        id=pin.get("id"),
        title=pin.get("title"),
        description=pin.get("description"),
        link=pin.get("link"),
        board_id=pin.get("board_id"),
        board_section_id=pin.get("board_section_id"),
        created_at=pin.get("created_at"),
        pin=pin,
    )


@tool(args_schema=ListPinsInput)
@serialize_pydantic_return
async def list_pins(
    api_key: str,
    board_id: str,
    board_section_id: str | None = None,
    page_size: int | None = 25,
    bookmark: str | None = None,
) -> ListPinsOutput:
    """List pins from a Pinterest board or board section."""
    params: dict[str, Any] = {"page_size": min(page_size or _DEFAULT_PAGE_SIZE, 250)}
    if bookmark:
        params["bookmark"] = bookmark

    url = (
        f"{_API_BASE}/boards/{board_id}/sections/{board_section_id}/pins"
        if board_section_id
        else f"{_API_BASE}/boards/{board_id}/pins"
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=_headers(api_key), params=params)
        if response.status_code == 401:
            return ListPinsOutput(success=False, error=_auth_error())
        if response.status_code == 404:
            return ListPinsOutput(
                success=False,
                error=(
                    f"Board {board_id} or section {board_section_id} not found"
                    if board_section_id
                    else f"Board {board_id} not found"
                ),
            )
        if response.status_code != 200:
            return ListPinsOutput(
                success=False, error=f"API error {response.status_code}: {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListPinsOutput(success=False, error="Request timed out while listing pins")
    except Exception as exc:
        return ListPinsOutput(success=False, error=str(exc))

    pins = data.get("items") or []
    return ListPinsOutput(
        success=True,
        board_id=board_id,
        board_section_id=board_section_id,
        pins=pins,
        count=len(pins),
        bookmark=data.get("bookmark"),
    )
