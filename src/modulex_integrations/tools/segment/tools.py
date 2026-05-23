"""Segment LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.segment.outputs import (
    AliasOutput,
    GroupOutput,
    IdentifyOutput,
    PageOutput,
    ScreenOutput,
    TrackOutput,
)

__all__ = [
    "alias",
    "group",
    "identify",
    "page",
    "screen",
    "track",
]

_BASE_URL = "https://api.segment.io/v1"
_TIMEOUT = 30.0


def _auth(write_key: str) -> httpx.BasicAuth:
    return httpx.BasicAuth(username=write_key, password="")


def _build_body(fields: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in fields.items() if v is not None}


# --- Input schemas --------------------------------------------------------


class AliasInput(BaseModel):
    previous_id: str = Field(description="Previous unique identifier for the user")
    write_key: str = Field(description="Segment source Write Key")
    user_id: str | None = Field(default=None, description="Unique identifier for the user in your database")
    context: dict[str, Any] | None = Field(default=None, description="Dictionary of extra context about the message")
    integrations: dict[str, Any] | None = Field(default=None, description="Dictionary of destinations to enable or disable")
    timestamp: str | None = Field(default=None, description="ISO 8601 timestamp of when the message occurred")


class GroupInput(BaseModel):
    group_id: str = Field(description="Unique identifier for the group in your database")
    write_key: str = Field(description="Segment source Write Key")
    user_id: str | None = Field(default=None, description="Unique identifier for the user")
    anonymous_id: str | None = Field(default=None, description="Pseudo-unique substitute for a User ID")
    traits: dict[str, Any] | None = Field(default=None, description="Free-form dictionary of traits of the group")
    context: dict[str, Any] | None = Field(default=None, description="Dictionary of extra context about the message")
    integrations: dict[str, Any] | None = Field(default=None, description="Dictionary of destinations to enable or disable")
    timestamp: str | None = Field(default=None, description="ISO 8601 timestamp of when the message occurred")


class IdentifyInput(BaseModel):
    write_key: str = Field(description="Segment source Write Key")
    user_id: str | None = Field(default=None, description="Unique identifier for the user")
    anonymous_id: str | None = Field(default=None, description="Pseudo-unique substitute for a User ID")
    traits: dict[str, Any] | None = Field(default=None, description="Free-form dictionary of traits of the user")
    context: dict[str, Any] | None = Field(default=None, description="Dictionary of extra context about the message")
    integrations: dict[str, Any] | None = Field(default=None, description="Dictionary of destinations to enable or disable")
    timestamp: str | None = Field(default=None, description="ISO 8601 timestamp of when the message occurred")


class PageInput(BaseModel):
    write_key: str = Field(description="Segment source Write Key")
    user_id: str | None = Field(default=None, description="Unique identifier for the user")
    anonymous_id: str | None = Field(default=None, description="Pseudo-unique substitute for a User ID")
    name: str | None = Field(default=None, description="Name of the page being viewed")
    properties: dict[str, Any] | None = Field(default=None, description="Free-form dictionary of properties of the page")
    context: dict[str, Any] | None = Field(default=None, description="Dictionary of extra context about the message")
    integrations: dict[str, Any] | None = Field(default=None, description="Dictionary of destinations to enable or disable")
    timestamp: str | None = Field(default=None, description="ISO 8601 timestamp of when the message occurred")


class ScreenInput(BaseModel):
    write_key: str = Field(description="Segment source Write Key")
    user_id: str | None = Field(default=None, description="Unique identifier for the user")
    anonymous_id: str | None = Field(default=None, description="Pseudo-unique substitute for a User ID")
    name: str | None = Field(default=None, description="Name of the screen being viewed")
    properties: dict[str, Any] | None = Field(default=None, description="Free-form dictionary of properties of the screen")
    context: dict[str, Any] | None = Field(default=None, description="Dictionary of extra context about the message")
    integrations: dict[str, Any] | None = Field(default=None, description="Dictionary of destinations to enable or disable")
    timestamp: str | None = Field(default=None, description="ISO 8601 timestamp of when the message occurred")


class TrackInput(BaseModel):
    event: str = Field(description="Name of the action the user has performed")
    write_key: str = Field(description="Segment source Write Key")
    user_id: str | None = Field(default=None, description="Unique identifier for the user")
    anonymous_id: str | None = Field(default=None, description="Pseudo-unique substitute for a User ID")
    properties: dict[str, Any] | None = Field(default=None, description="Free-form dictionary of properties of the event")
    context: dict[str, Any] | None = Field(default=None, description="Dictionary of extra context about the message")
    integrations: dict[str, Any] | None = Field(default=None, description="Dictionary of destinations to enable or disable")
    timestamp: str | None = Field(default=None, description="ISO 8601 timestamp of when the message occurred")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AliasInput)
@serialize_pydantic_return
async def alias(
    previous_id: str,
    write_key: str,
    user_id: str | None = None,
    context: dict[str, Any] | None = None,
    integrations: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> AliasOutput:
    """Associate one user identity with another in Segment."""
    if not write_key or not write_key.strip():
        return AliasOutput(success=False, error="Write key is empty. Please configure a valid credential.")
    body = _build_body({
        "previousId": previous_id,
        "userId": user_id,
        "context": context,
        "integrations": integrations,
        "timestamp": timestamp,
    })
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/alias",
                auth=_auth(write_key),
                json=body,
            )
        if response.status_code != 200:
            return AliasOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        return AliasOutput(success=True)
    except httpx.TimeoutException:
        return AliasOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AliasOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=GroupInput)
@serialize_pydantic_return
async def group(
    group_id: str,
    write_key: str,
    user_id: str | None = None,
    anonymous_id: str | None = None,
    traits: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    integrations: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> GroupOutput:
    """Associate an identified user with a group in Segment."""
    if not write_key or not write_key.strip():
        return GroupOutput(success=False, error="Write key is empty. Please configure a valid credential.")
    body = _build_body({
        "groupId": group_id,
        "userId": user_id,
        "anonymousId": anonymous_id,
        "traits": traits,
        "context": context,
        "integrations": integrations,
        "timestamp": timestamp,
    })
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/group",
                auth=_auth(write_key),
                json=body,
            )
        if response.status_code != 200:
            return GroupOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        return GroupOutput(success=True)
    except httpx.TimeoutException:
        return GroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GroupOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=IdentifyInput)
@serialize_pydantic_return
async def identify(
    write_key: str,
    user_id: str | None = None,
    anonymous_id: str | None = None,
    traits: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    integrations: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> IdentifyOutput:
    """Identify a user and record traits about them in Segment."""
    if not write_key or not write_key.strip():
        return IdentifyOutput(success=False, error="Write key is empty. Please configure a valid credential.")
    body = _build_body({
        "userId": user_id,
        "anonymousId": anonymous_id,
        "traits": traits,
        "context": context,
        "integrations": integrations,
        "timestamp": timestamp,
    })
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/identify",
                auth=_auth(write_key),
                json=body,
            )
        if response.status_code != 200:
            return IdentifyOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        return IdentifyOutput(success=True)
    except httpx.TimeoutException:
        return IdentifyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return IdentifyOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=PageInput)
@serialize_pydantic_return
async def page(
    write_key: str,
    user_id: str | None = None,
    anonymous_id: str | None = None,
    name: str | None = None,
    properties: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    integrations: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> PageOutput:
    """Record a page view on your website in Segment."""
    if not write_key or not write_key.strip():
        return PageOutput(success=False, error="Write key is empty. Please configure a valid credential.")
    body = _build_body({
        "userId": user_id,
        "anonymousId": anonymous_id,
        "name": name,
        "properties": properties,
        "context": context,
        "integrations": integrations,
        "timestamp": timestamp,
    })
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/page",
                auth=_auth(write_key),
                json=body,
            )
        if response.status_code != 200:
            return PageOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        return PageOutput(success=True)
    except httpx.TimeoutException:
        return PageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PageOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ScreenInput)
@serialize_pydantic_return
async def screen(
    write_key: str,
    user_id: str | None = None,
    anonymous_id: str | None = None,
    name: str | None = None,
    properties: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    integrations: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> ScreenOutput:
    """Record a screen view in your mobile app in Segment."""
    if not write_key or not write_key.strip():
        return ScreenOutput(success=False, error="Write key is empty. Please configure a valid credential.")
    body = _build_body({
        "userId": user_id,
        "anonymousId": anonymous_id,
        "name": name,
        "properties": properties,
        "context": context,
        "integrations": integrations,
        "timestamp": timestamp,
    })
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/screen",
                auth=_auth(write_key),
                json=body,
            )
        if response.status_code != 200:
            return ScreenOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        return ScreenOutput(success=True)
    except httpx.TimeoutException:
        return ScreenOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ScreenOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=TrackInput)
@serialize_pydantic_return
async def track(
    event: str,
    write_key: str,
    user_id: str | None = None,
    anonymous_id: str | None = None,
    properties: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    integrations: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> TrackOutput:
    """Track an event that a user has performed in Segment."""
    if not write_key or not write_key.strip():
        return TrackOutput(success=False, error="Write key is empty. Please configure a valid credential.")
    body = _build_body({
        "event": event,
        "userId": user_id,
        "anonymousId": anonymous_id,
        "properties": properties,
        "context": context,
        "integrations": integrations,
        "timestamp": timestamp,
    })
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/track",
                auth=_auth(write_key),
                json=body,
            )
        if response.status_code != 200:
            return TrackOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        return TrackOutput(success=True)
    except httpx.TimeoutException:
        return TrackOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return TrackOutput(success=False, error=f"Call failed: {exc}")
