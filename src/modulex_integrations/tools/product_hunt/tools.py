"""Product Hunt LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.product_hunt.outputs import (
    ListTopicOptionsOutput,
    TopicOption,
)

__all__ = [
    "list_topic_options",
]

_BASE_URL = "https://api.producthunt.com/v2/api/graphql"

_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Product Hunt GraphQL API."""
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class ListTopicOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions ------------------------------------------------------

_LIST_TOPICS_QUERY = """\
query {
  topics {
    edges {
      node {
        name
        slug
      }
    }
  }
}
"""


@tool(args_schema=ListTopicOptionsInput)
@serialize_pydantic_return
async def list_topic_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListTopicOptionsOutput:
    """Retrieves available topic options with slug and display name"""
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _BASE_URL,
                headers=headers,
                json={"query": _LIST_TOPICS_QUERY},
            )
        if response.status_code != 200:
            return ListTopicOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListTopicOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTopicOptionsOutput(success=False, error=f"Call failed: {exc}")

    errors = data.get("errors")
    if errors:
        return ListTopicOptionsOutput(
            success=False,
            error=f"GraphQL error: {errors[0].get('message', str(errors))}",
        )

    edges = (data.get("data") or {}).get("topics", {}).get("edges", [])
    topics = [
        TopicOption(
            value=(edge.get("node") or {}).get("slug"),
            label=(edge.get("node") or {}).get("name"),
        )
        for edge in edges
    ]
    return ListTopicOptionsOutput(success=True, topics=topics)
