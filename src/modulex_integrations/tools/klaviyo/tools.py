"""Klaviyo LangChain ``@tool`` functions."""
from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.klaviyo.outputs import (
    AddMembersToListOutput,
    CreateListOutput,
    GetListOutput,
    GetListsOutput,
    GetProfilesOutput,
    KlaviyoList,
    KlaviyoProfile,
)

__all__ = [
    "add_members_to_list",
    "create_list",
    "get_list",
    "get_lists",
    "get_profiles",
]

_BASE_URL = "https://a.klaviyo.com/api"
_API_REVISION = "2024-10-15"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Klaviyo-API-Key {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "revision": _API_REVISION,
    }


def _cursor_from_next_link(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("page[cursor]", [None])[0]


def _empty_key_error(name: str) -> str:
    return f"Klaviyo API key is empty for {name}. Please configure a valid credential."


class GetListsInput(BaseModel):
    api_key: str = Field(description="Klaviyo API key (provided by credential system)")
    sort: str | None = Field(default="created", description="Field to sort by")
    sort_direction: str | None = Field(default="desc", description="'asc' or 'desc'")
    max_results: int | None = Field(default=100, description="Maximum lists to return")


class GetListInput(BaseModel):
    api_key: str = Field(description="Klaviyo API key (provided by credential system)")
    list_id: str = Field(description="The ID of the Klaviyo list to retrieve")


class CreateListInput(BaseModel):
    api_key: str = Field(description="Klaviyo API key (provided by credential system)")
    name: str = Field(description="The name for the new list")


class GetProfilesInput(BaseModel):
    api_key: str = Field(description="Klaviyo API key (provided by credential system)")
    max_results: int | None = Field(default=100, description="Maximum profiles to return")
    sort: str | None = Field(default="created", description="Field to sort by")
    sort_direction: str | None = Field(default="desc", description="'asc' or 'desc'")


class AddMembersToListInput(BaseModel):
    api_key: str = Field(description="Klaviyo API key (provided by credential system)")
    list_id: str = Field(description="The ID of the list to add members to")
    profile_ids: list[str] = Field(description="List of profile IDs to add to the list")


@tool(args_schema=GetListsInput)
@serialize_pydantic_return
async def get_lists(
    api_key: str,
    sort: str | None = "created",
    sort_direction: str | None = "desc",
    max_results: int | None = 100,
) -> GetListsOutput:
    """Get all lists in a Klaviyo account, paginated up to ``max_results``."""
    if not api_key or not api_key.strip():
        return GetListsOutput(success=False, error=_empty_key_error("get_lists"))

    limit = max_results or 100
    sort_prefix = "-" if sort_direction == "desc" else ""
    sort_param = f"{sort_prefix}{sort or 'created'}"

    collected: list[KlaviyoList] = []
    cursor: str | None = None

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while len(collected) < limit:
                params: dict[str, Any] = {"sort": sort_param}
                if cursor:
                    params["page[cursor]"] = cursor
                response = await client.get(
                    f"{_BASE_URL}/lists", headers=_headers(api_key), params=params
                )
                if response.status_code != 200:
                    return GetListsOutput(
                        success=False,
                        error=f"API error {response.status_code}: {response.text}",
                    )
                data = response.json() or {}
                for item in data.get("data", []):
                    if len(collected) >= limit:
                        break
                    attrs = item.get("attributes") or {}
                    collected.append(
                        KlaviyoList(
                            id=item.get("id"),
                            name=attrs.get("name"),
                            created=attrs.get("created"),
                            updated=attrs.get("updated"),
                            opt_in_process=attrs.get("opt_in_process"),
                        )
                    )
                next_link = (data.get("links") or {}).get("next")
                cursor = _cursor_from_next_link(next_link)
                if not cursor:
                    break
    except Exception as exc:
        return GetListsOutput(success=False, error=f"get_lists failed: {exc}")

    return GetListsOutput(success=True, lists=collected, count=len(collected))


@tool(args_schema=GetListInput)
@serialize_pydantic_return
async def get_list(api_key: str, list_id: str) -> GetListOutput:
    """Get a specific Klaviyo list by ID."""
    if not api_key or not api_key.strip():
        return GetListOutput(success=False, error=_empty_key_error("get_list"))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/lists/{list_id}", headers=_headers(api_key)
            )
        if response.status_code == 404:
            return GetListOutput(success=False, error=f"List not found: {list_id}")
        if response.status_code != 200:
            return GetListOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
        item = (response.json() or {}).get("data") or {}
    except Exception as exc:
        return GetListOutput(success=False, error=f"get_list failed: {exc}")

    attrs = item.get("attributes") or {}
    return GetListOutput(
        success=True,
        id=item.get("id"),
        name=attrs.get("name"),
        created=attrs.get("created"),
        updated=attrs.get("updated"),
        opt_in_process=attrs.get("opt_in_process"),
    )


@tool(args_schema=CreateListInput)
@serialize_pydantic_return
async def create_list(api_key: str, name: str) -> CreateListOutput:
    """Create a new list in a Klaviyo account."""
    if not api_key or not api_key.strip():
        return CreateListOutput(success=False, error=_empty_key_error("create_list"))

    payload = {"data": {"type": "list", "attributes": {"name": name}}}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/lists", headers=_headers(api_key), json=payload
            )
        if response.status_code not in (200, 201):
            return CreateListOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
        item = (response.json() or {}).get("data") or {}
    except Exception as exc:
        return CreateListOutput(success=False, error=f"create_list failed: {exc}")

    attrs = item.get("attributes") or {}
    return CreateListOutput(
        success=True,
        id=item.get("id"),
        name=attrs.get("name"),
        created=attrs.get("created"),
        updated=attrs.get("updated"),
        opt_in_process=attrs.get("opt_in_process"),
    )


@tool(args_schema=GetProfilesInput)
@serialize_pydantic_return
async def get_profiles(
    api_key: str,
    max_results: int | None = 100,
    sort: str | None = "created",
    sort_direction: str | None = "desc",
) -> GetProfilesOutput:
    """Get profiles from a Klaviyo account, paginated up to ``max_results``."""
    if not api_key or not api_key.strip():
        return GetProfilesOutput(success=False, error=_empty_key_error("get_profiles"))

    limit = max_results or 100
    sort_prefix = "-" if sort_direction == "desc" else ""
    sort_param = f"{sort_prefix}{sort or 'created'}"

    collected: list[KlaviyoProfile] = []
    cursor: str | None = None

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while len(collected) < limit:
                params: dict[str, Any] = {"sort": sort_param}
                if cursor:
                    params["page[cursor]"] = cursor
                response = await client.get(
                    f"{_BASE_URL}/profiles", headers=_headers(api_key), params=params
                )
                if response.status_code != 200:
                    return GetProfilesOutput(
                        success=False,
                        error=f"API error {response.status_code}: {response.text}",
                    )
                data = response.json() or {}
                for item in data.get("data", []):
                    if len(collected) >= limit:
                        break
                    attrs = item.get("attributes") or {}
                    collected.append(
                        KlaviyoProfile(
                            id=item.get("id"),
                            email=attrs.get("email"),
                            first_name=attrs.get("first_name"),
                            last_name=attrs.get("last_name"),
                            phone_number=attrs.get("phone_number"),
                            created=attrs.get("created"),
                            updated=attrs.get("updated"),
                        )
                    )
                next_link = (data.get("links") or {}).get("next")
                cursor = _cursor_from_next_link(next_link)
                if not cursor:
                    break
    except Exception as exc:
        return GetProfilesOutput(success=False, error=f"get_profiles failed: {exc}")

    return GetProfilesOutput(success=True, profiles=collected, count=len(collected))


@tool(args_schema=AddMembersToListInput)
@serialize_pydantic_return
async def add_members_to_list(
    api_key: str,
    list_id: str,
    profile_ids: list[str],
) -> AddMembersToListOutput:
    """Add profiles to a Klaviyo list by their profile IDs."""
    if not api_key or not api_key.strip():
        return AddMembersToListOutput(
            success=False, error=_empty_key_error("add_members_to_list")
        )

    payload = {
        "data": [{"type": "profile", "id": pid} for pid in profile_ids],
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/lists/{list_id}/relationships/profiles",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code == 404:
            return AddMembersToListOutput(
                success=False, error=f"List not found: {list_id}"
            )
        # 204 No Content is the documented success for this endpoint
        if response.status_code not in (200, 201, 204):
            return AddMembersToListOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
    except Exception as exc:
        return AddMembersToListOutput(
            success=False, error=f"add_members_to_list failed: {exc}"
        )

    return AddMembersToListOutput(
        success=True,
        list_id=list_id,
        profiles_added=len(profile_ids),
        profile_ids=profile_ids,
    )
