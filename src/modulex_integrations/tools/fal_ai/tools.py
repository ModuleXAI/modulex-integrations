"""fal.ai LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.fal_ai.outputs import (
    AddRequestToQueueOutput,
    CancelRequestOutput,
    GetRequestResponseOutput,
    GetRequestStatusOutput,
    LogEntry,
)

__all__ = [
    "add_request_to_queue",
    "cancel_request",
    "get_request_response",
    "get_request_status",
]

_BASE_URL = "https://queue.fal.run/fal-ai"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class AddRequestToQueueInput(BaseModel):
    app_id: str = Field(description="The unique identifier for the fal.ai app/model (e.g. 'lora', 'fast-sdxl')")
    data: dict[str, Any] = Field(description="Input data for the model")
    webhook_url: str | None = Field(default=None, description="Optional URL to receive webhook updates about the request status")
    api_key: str = Field(description="fal.ai API key")


class CancelRequestInput(BaseModel):
    app_id: str = Field(description="The unique identifier for the fal.ai app/model")
    request_id: str = Field(description="The unique identifier for the request to cancel")
    api_key: str = Field(description="fal.ai API key")


class GetRequestResponseInput(BaseModel):
    app_id: str = Field(description="The unique identifier for the fal.ai app/model")
    request_id: str = Field(description="The unique identifier for the request")
    api_key: str = Field(description="fal.ai API key")


class GetRequestStatusInput(BaseModel):
    app_id: str = Field(description="The unique identifier for the fal.ai app/model")
    request_id: str = Field(description="The unique identifier for the request")
    logs: bool | None = Field(default=None, description="Whether to include logs in the status response")
    api_key: str = Field(description="fal.ai API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddRequestToQueueInput)
@serialize_pydantic_return
async def add_request_to_queue(
    app_id: str,
    data: dict[str, Any],
    api_key: str,
    webhook_url: str | None = None,
) -> AddRequestToQueueOutput:
    """Adds a request to the queue for asynchronous processing, including specifying a webhook URL for receiving updates."""
    if not api_key or not api_key.strip():
        return AddRequestToQueueOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        params: dict[str, str] = {}
        if webhook_url:
            params["fal_webhook"] = webhook_url
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/{app_id}",
                headers=_headers(api_key),
                params=params,
                json=data,
            )
        if response.status_code not in (200, 201):
            return AddRequestToQueueOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        result = response.json()
    except httpx.TimeoutException:
        return AddRequestToQueueOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddRequestToQueueOutput(success=False, error=f"Call failed: {exc}")

    return AddRequestToQueueOutput(
        success=True,
        request_id=result.get("request_id"),
        response_url=result.get("response_url"),
        status_url=result.get("status_url"),
        cancel_url=result.get("cancel_url"),
    )


@tool(args_schema=CancelRequestInput)
@serialize_pydantic_return
async def cancel_request(
    app_id: str,
    request_id: str,
    api_key: str,
) -> CancelRequestOutput:
    """Cancels a request in the queue to stop a long-running task that is no longer needed."""
    if not api_key or not api_key.strip():
        return CancelRequestOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/{app_id}/requests/{request_id}/cancel",
                headers=_headers(api_key),
            )
        if response.status_code not in (200, 202):
            return CancelRequestOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return CancelRequestOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CancelRequestOutput(success=False, error=f"Call failed: {exc}")

    return CancelRequestOutput(success=True)


@tool(args_schema=GetRequestResponseInput)
@serialize_pydantic_return
async def get_request_response(
    app_id: str,
    request_id: str,
    api_key: str,
) -> GetRequestResponseOutput:
    """Gets the response of a completed request in the queue to retrieve results of an asynchronous task."""
    if not api_key or not api_key.strip():
        return GetRequestResponseOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/{app_id}/requests/{request_id}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetRequestResponseOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        result = response.json()
    except httpx.TimeoutException:
        return GetRequestResponseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRequestResponseOutput(success=False, error=f"Call failed: {exc}")

    return GetRequestResponseOutput(
        success=True,
        data=result,
    )


@tool(args_schema=GetRequestStatusInput)
@serialize_pydantic_return
async def get_request_status(
    app_id: str,
    request_id: str,
    api_key: str,
    logs: bool | None = None,
) -> GetRequestStatusOutput:
    """Gets the status of a request in the queue to monitor the progress of an asynchronous task."""
    if not api_key or not api_key.strip():
        return GetRequestStatusOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        params: dict[str, str] = {}
        if logs:
            params["logs"] = "1"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/{app_id}/requests/{request_id}/status",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetRequestStatusOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        result = response.json()
    except httpx.TimeoutException:
        return GetRequestStatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRequestStatusOutput(success=False, error=f"Call failed: {exc}")

    log_entries: list[LogEntry] = []
    for entry in result.get("logs", []) or []:
        log_entries.append(
            LogEntry(
                message=entry.get("message"),
                level=entry.get("level"),
                timestamp=entry.get("timestamp"),
            )
        )

    return GetRequestStatusOutput(
        success=True,
        status=result.get("status"),
        queue_position=result.get("queue_position"),
        logs=log_entries,
    )
