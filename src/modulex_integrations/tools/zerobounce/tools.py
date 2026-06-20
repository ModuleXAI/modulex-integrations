"""ZeroBounce LangChain ``@tool`` functions.

Two async tools wrapping the ZeroBounce v2 REST API. The calling
convention is the modulex *key-based* one: the runtime injects an
``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair. ZeroBounce
authenticates by passing the key as the ``api_key`` query parameter.

Error model: ZeroBounce may answer HTTP 200 with an ``{"error": ...}``
body (invalid key / out of credits), and ``getcredits`` signals an
invalid key with ``{"Credits": -1}``. Every call is wrapped in
try/except and detects API-level errors from the body, so non-2xx,
error envelopes, and timeouts all surface as ``success=False`` +
``error`` rather than raising.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.zerobounce.outputs import (
    GetCreditsOutput,
    VerifyEmailOutput,
)

__all__ = ["get_credits", "verify_email"]

_ZEROBOUNCE_API_BASE = "https://api.zerobounce.net/v2"
_REQUEST_TIMEOUT = 30.0


# --- Input schemas (args_schema for each @tool) ----------------------------


class VerifyEmailInput(BaseModel):
    email: str = Field(description="Email address to validate (e.g., john@example.com)")
    api_key: str = Field(description="ZeroBounce API key (provided by credential system)")
    ip_address: str | None = Field(
        default=None,
        description="Optional IP address the email signed up from (improves scoring)",
    )


class GetCreditsInput(BaseModel):
    api_key: str = Field(description="ZeroBounce API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=VerifyEmailInput)
@serialize_pydantic_return
async def verify_email(
    email: str,
    api_key: str,
    ip_address: str | None = None,
) -> VerifyEmailOutput:
    """Validate an email address deliverability in real time. Uses one validation credit."""
    if not api_key or not api_key.strip():
        return VerifyEmailOutput(
            success=False,
            error="ZeroBounce API key is empty. Please configure a valid ZeroBounce credential.",
        )

    params: dict[str, Any] = {
        "api_key": api_key.strip(),
        "email": email.strip(),
        # ZeroBounce expects the ip_address parameter to always be present;
        # an empty string is the documented "no IP" sentinel.
        "ip_address": ip_address.strip() if ip_address else "",
    }

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{_ZEROBOUNCE_API_BASE}/validate",
                headers={"Accept": "application/json"},
                params=params,
            )
    except httpx.TimeoutException:
        return VerifyEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VerifyEmailOutput(success=False, error=f"verify_email failed: {exc}")

    # ZeroBounce may send a non-JSON body on hard failures; tolerate it.
    try:
        data = response.json()
    except Exception:
        data = {}

    # ZeroBounce can answer HTTP 200 with an {"error": ...} envelope, so
    # detect API-level errors from the body, not just the HTTP status.
    error_message = ""
    if isinstance(data, dict) and isinstance(data.get("error"), str):
        error_message = data["error"]
    if response.status_code != 200 or error_message:
        return VerifyEmailOutput(
            success=False,
            error=error_message
            or f"ZeroBounce API error ({response.status_code}): {response.text}",
        )

    raw_status = str(data.get("status") or "")
    # Normalize ZeroBounce's hyphenated 'catch-all' to the shared
    # 'catch_all' vocabulary used across the email-verification tools.
    status = "catch_all" if raw_status == "catch-all" else raw_status
    return VerifyEmailOutput(
        success=True,
        email=data.get("address") or "",
        status=status,
        deliverable=raw_status == "valid",
        sub_status=data.get("sub_status") or "",
        free_email=data.get("free_email") or False,
        did_you_mean=data.get("did_you_mean") or "",
    )


@tool(args_schema=GetCreditsInput)
@serialize_pydantic_return
async def get_credits(api_key: str) -> GetCreditsOutput:
    """Retrieve the remaining validation credits for the authenticated account."""
    if not api_key or not api_key.strip():
        return GetCreditsOutput(
            success=False,
            error="ZeroBounce API key is empty. Please configure a valid ZeroBounce credential.",
        )

    params: dict[str, Any] = {"api_key": api_key.strip()}

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{_ZEROBOUNCE_API_BASE}/getcredits",
                headers={"Accept": "application/json"},
                params=params,
            )
    except httpx.TimeoutException:
        return GetCreditsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCreditsOutput(success=False, error=f"get_credits failed: {exc}")

    # ZeroBounce may send a non-JSON body on hard failures; tolerate it.
    try:
        data = response.json()
    except Exception:
        data = {}

    # ZeroBounce returns HTTP 200 with an {"error": ...} envelope on auth
    # failure, so detect API-level errors from the body, not just status.
    error_message = ""
    if isinstance(data, dict) and isinstance(data.get("error"), str):
        error_message = data["error"]
    if response.status_code != 200 or error_message:
        return GetCreditsOutput(
            success=False,
            error=error_message
            or f"ZeroBounce API error ({response.status_code}): {response.text}",
        )

    try:
        credits = int(data.get("Credits", 0))
    except (TypeError, ValueError):
        credits = 0
    return GetCreditsOutput(success=True, credits=credits)
