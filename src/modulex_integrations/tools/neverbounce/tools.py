"""NeverBounce LangChain ``@tool`` functions.

Two async tools wrapping the NeverBounce v4 REST API. The calling
convention is *key-based*: the modulex ``ToolExecutor`` injects an
``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair.

NeverBounce authenticates by passing the API key as a ``key`` query
parameter (not an Authorization header). The v4 API returns HTTP 200
even for API-level failures and signals the outcome through the response
envelope's ``status`` field, so we treat ``status != "success"`` as an
error and surface ``message`` when present. Non-2xx responses, timeouts,
and unexpected exceptions are also caught and returned as
``success=False`` + ``error`` rather than raising.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.neverbounce.outputs import (
    GetCreditsOutput,
    VerifyEmailOutput,
)

__all__ = ["get_credits", "verify_email"]

_NEVERBOUNCE_API_BASE = "https://api.neverbounce.com/v4"
_REQUEST_TIMEOUT = 30.0

# Maps a NeverBounce raw ``result`` to the shared verification vocabulary.
_STATUS_MAP: dict[str, str] = {
    "valid": "valid",
    "invalid": "invalid",
    "catchall": "catch_all",
    "disposable": "disposable",
    "unknown": "unknown",
}


# --- Input schemas (args_schema for each @tool) ----------------------------


class VerifyEmailInput(BaseModel):
    email: str = Field(description="Email address to verify (e.g., john@example.com)")
    api_key: str = Field(description="NeverBounce API key (provided by credential system)")


class GetCreditsInput(BaseModel):
    api_key: str = Field(description="NeverBounce API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=VerifyEmailInput)
@serialize_pydantic_return
async def verify_email(email: str, api_key: str) -> VerifyEmailOutput:
    """Verify the deliverability of an email address. Uses one verification credit."""
    if not api_key or not api_key.strip():
        return VerifyEmailOutput(
            success=False,
            error="NeverBounce API key is empty. Please configure a valid NeverBounce credential.",
        )
    if not email or not email.strip():
        return VerifyEmailOutput(success=False, error="No email address provided.")

    params: dict[str, Any] = {
        "key": api_key.strip(),
        "email": email.strip(),
        "address_info": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{_NEVERBOUNCE_API_BASE}/single/check",
                params=params,
                headers={"Accept": "application/json"},
            )
        if response.status_code != 200:
            return VerifyEmailOutput(
                success=False,
                error=f"NeverBounce API error ({response.status_code}): {response.text}",
                email=email,
            )
        data = response.json()
    except httpx.TimeoutException:
        return VerifyEmailOutput(success=False, error="Request timed out.", email=email)
    except Exception as exc:
        return VerifyEmailOutput(success=False, error=f"Verify email failed: {exc}", email=email)

    # NeverBounce returns HTTP 200 for API-level errors; the envelope status
    # distinguishes a successful check from an auth/quota failure.
    if data.get("status") != "success":
        return VerifyEmailOutput(
            success=False,
            error=data.get("message")
            or f"NeverBounce API error: status={data.get('status')}",
            email=email,
        )

    result = str(data.get("result") or "")
    flags = data.get("flags") or []
    if not isinstance(flags, list):
        flags = []
    return VerifyEmailOutput(
        success=True,
        email=email,
        status=_STATUS_MAP.get(result, result),
        deliverable=result == "valid",
        role_account="role_account" in flags,
        free_email="free_email_host" in flags,
        did_you_mean=data.get("suggested_correction") or "",
        flags=flags,
        result=result or None,
    )


@tool(args_schema=GetCreditsInput)
@serialize_pydantic_return
async def get_credits(api_key: str) -> GetCreditsOutput:
    """Retrieve the remaining paid and free verification credits for the account."""
    if not api_key or not api_key.strip():
        return GetCreditsOutput(
            success=False,
            error="NeverBounce API key is empty. Please configure a valid NeverBounce credential.",
        )

    params: dict[str, Any] = {"key": api_key.strip()}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{_NEVERBOUNCE_API_BASE}/account/info",
                params=params,
                headers={"Accept": "application/json"},
            )
        if response.status_code != 200:
            return GetCreditsOutput(
                success=False,
                error=f"NeverBounce API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetCreditsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCreditsOutput(success=False, error=f"Get credits failed: {exc}")

    if data.get("status") != "success":
        return GetCreditsOutput(
            success=False,
            error=data.get("message")
            or f"NeverBounce API error: status={data.get('status')}",
        )

    credits_info = data.get("credits_info") or {}
    if not isinstance(credits_info, dict):
        credits_info = {}
    return GetCreditsOutput(
        success=True,
        credits=credits_info.get("paid_credits_remaining") or 0,
        free_credits=credits_info.get("free_credits_remaining") or 0,
    )
