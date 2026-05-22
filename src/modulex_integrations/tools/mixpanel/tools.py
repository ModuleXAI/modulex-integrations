"""Mixpanel LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.mixpanel.outputs import EmitEventToOutput

__all__ = [
    "emit_event_to",
]

_BASE_URL = "https://api.mixpanel.com"


class EmitEventToInput(BaseModel):
    event_name: str = Field(description="The name of the event (e.g. 'Button Click', 'Sign Up', 'Item Purchased')")
    distinct_id: str = Field(description="The unique identifier for the user performing the event")
    properties: dict[str, Any] | None = Field(default=None, description="A set of properties to include with the event describing the user or event details")
    api_key: str = Field(description="Mixpanel Project Token (provided by credential system)")


@tool(args_schema=EmitEventToInput)
@serialize_pydantic_return
async def emit_event_to(
    event_name: str,
    distinct_id: str,
    api_key: str,
    properties: dict[str, Any] | None = None,
) -> EmitEventToOutput:
    """Send an event to Mixpanel"""
    if not api_key or not api_key.strip():
        return EmitEventToOutput(
            success=False,
            error="API key is empty. Please configure a valid Mixpanel Project Token.",
        )
    event_properties: dict[str, Any] = {
        "token": api_key,
        "distinct_id": distinct_id,
    }
    if properties:
        event_properties.update(properties)
    payload = [{"event": event_name, "properties": event_properties}]
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/track",
                headers={"Content-Type": "application/json", "Accept": "text/plain"},
                json=payload,
            )
        if response.status_code != 200:
            return EmitEventToOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        response_text = response.text.strip()
        if response_text == "0":
            return EmitEventToOutput(
                success=False,
                error="Mixpanel rejected the event (returned 0). Check the project token and event data.",
            )
    except httpx.TimeoutException:
        return EmitEventToOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EmitEventToOutput(success=False, error=f"Call failed: {exc}")

    return EmitEventToOutput(
        success=True,
        distinct_id=distinct_id,
        properties=event_properties,
    )
