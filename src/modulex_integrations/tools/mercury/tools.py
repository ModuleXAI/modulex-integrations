"""Mercury LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.mercury.outputs import GetAccountInfoOutput

__all__ = [
    "get_account_info",
]

_BASE_URL = "https://backend.mercury.com/api/v1"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Mercury API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "bearer_token":
        token = auth_data.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


class GetAccountInfoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="The unique ID of the Mercury account to retrieve")


@tool(args_schema=GetAccountInfoInput)
@serialize_pydantic_return
async def get_account_info(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
) -> GetAccountInfoOutput:
    """Retrieve information about a specific Mercury bank account."""
    headers = _get_auth_headers(auth_type, auth_data)
    if not headers.get("Authorization"):
        return GetAccountInfoOutput(
            success=False,
            error="Bearer token is missing. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/account/{account_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetAccountInfoOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetAccountInfoOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAccountInfoOutput(success=False, error=f"Call failed: {exc}")

    return GetAccountInfoOutput(
        success=True,
        account_id=data.get("id"),
        name=data.get("name"),
        status=data.get("status"),
        account_type=data.get("type"),
        current_balance=data.get("currentBalance"),
        available_balance=data.get("availableBalance"),
        routing_number=data.get("routingNumber"),
        account_number=data.get("accountNumber"),
        created_at=data.get("createdAt"),
    )
