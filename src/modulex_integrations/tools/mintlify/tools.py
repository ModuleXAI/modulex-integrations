"""Mintlify LangChain @tool functions."""
from __future__ import annotations

import uuid
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.mintlify.outputs import (
    ChatWithAssistantOutput,
    SearchDocumentationOutput,
    SearchResultItem,
    TriggerUpdateOutput,
)

__all__ = [
    "chat_with_assistant",
    "search_documentation",
    "trigger_update",
]

_BASE_URL = "https://api-dsc.mintlify.com/v1"
_UPDATE_BASE_URL = "https://api.mintlify.com/v1"
_TIMEOUT = 30.0


def _get_auth_headers(auth_data: dict[str, Any], use_admin: bool = False) -> dict[str, str]:
    """Build headers for the upstream API based on credential fields."""
    if use_admin:
        token = auth_data.get("admin_api_key", "")
    else:
        token = auth_data.get("assistant_api_key", "")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class ChatWithAssistantInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    domain: str = Field(description="The domain identifier from your domain.mintlify.app URL.")
    fp: str = Field(description="Browser fingerprint or arbitrary string identifier for message tracking.")
    message: str = Field(description="The content of the message to send to the assistant.")


class SearchDocumentationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    domain: str = Field(description="The domain identifier from your domain.mintlify.app URL.")
    query: str = Field(description="The search query to execute against your documentation content.")
    page_size: int | None = Field(default=None, description="Number of search results to return. Defaults to 10 if not specified.")
    version: str | None = Field(default=None, description="Filter results by documentation version.")
    language: str | None = Field(default=None, description="Filter results by content language.")


class TriggerUpdateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ChatWithAssistantInput)
@serialize_pydantic_return
async def chat_with_assistant(
    auth_type: str,
    auth_data: dict[str, Any],
    domain: str,
    fp: str,
    message: str,
) -> ChatWithAssistantOutput:
    """Generates a response message from the assistant for the specified domain."""
    assistant_api_key = auth_data.get("assistant_api_key", "")
    if not assistant_api_key or not assistant_api_key.strip():
        return ChatWithAssistantOutput(
            success=False,
            error="Assistant API key is empty. Please configure a valid credential.",
        )

    headers = _get_auth_headers(auth_data)
    message_id = str(uuid.uuid4())
    payload = {
        "messages": [
            {
                "id": message_id,
                "role": "user",
                "parts": [{"type": "text", "content": message}],
            },
        ],
        "fp": fp,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/assistant/{domain}/message",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return ChatWithAssistantOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChatWithAssistantOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChatWithAssistantOutput(success=False, error=f"Call failed: {exc}")

    return ChatWithAssistantOutput(
        success=True,
        message_id=data.get("id") if isinstance(data, dict) else message_id,
        response=data,
    )


@tool(args_schema=SearchDocumentationInput)
@serialize_pydantic_return
async def search_documentation(
    auth_type: str,
    auth_data: dict[str, Any],
    domain: str,
    query: str,
    page_size: int | None = None,
    version: str | None = None,
    language: str | None = None,
) -> SearchDocumentationOutput:
    """Perform semantic and keyword searches across your documentation."""
    assistant_api_key = auth_data.get("assistant_api_key", "")
    if not assistant_api_key or not assistant_api_key.strip():
        return SearchDocumentationOutput(
            success=False,
            error="Assistant API key is empty. Please configure a valid credential.",
        )

    headers = _get_auth_headers(auth_data)
    payload: dict[str, Any] = {"query": query}
    if page_size is not None:
        payload["pageSize"] = page_size
    filter_obj: dict[str, str] = {}
    if version is not None:
        filter_obj["version"] = version
    if language is not None:
        filter_obj["language"] = language
    if filter_obj:
        payload["filter"] = filter_obj

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search/{domain}",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return SearchDocumentationOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchDocumentationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchDocumentationOutput(success=False, error=f"Call failed: {exc}")

    results: list[SearchResultItem] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                results.append(
                    SearchResultItem(
                        title=item.get("title"),
                        url=item.get("url"),
                        content=item.get("content"),
                        score=item.get("score"),
                    )
                )
        total = len(results)
    else:
        total = None

    return SearchDocumentationOutput(
        success=True,
        results=results,
        total=total,
    )


@tool(args_schema=TriggerUpdateInput)
@serialize_pydantic_return
async def trigger_update(
    auth_type: str,
    auth_data: dict[str, Any],
) -> TriggerUpdateOutput:
    """Trigger an update for a project."""
    admin_api_key = auth_data.get("admin_api_key", "")
    project_id = auth_data.get("project_id", "")
    if not admin_api_key or not admin_api_key.strip():
        return TriggerUpdateOutput(
            success=False,
            error="Admin API key is empty. Please configure a valid credential.",
        )
    if not project_id or not project_id.strip():
        return TriggerUpdateOutput(
            success=False,
            error="Project ID is empty. Please configure a valid credential.",
        )

    headers = _get_auth_headers(auth_data, use_admin=True)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_UPDATE_BASE_URL}/project/update/{project_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return TriggerUpdateOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return TriggerUpdateOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return TriggerUpdateOutput(success=False, error=f"Call failed: {exc}")

    return TriggerUpdateOutput(
        success=True,
        data=data if isinstance(data, dict) else None,
    )
