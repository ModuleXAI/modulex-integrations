"""Icypeas LangChain ``@tool`` functions.

Two async tools wrapping the Icypeas REST API for professional email
discovery and verification. **The calling convention is key-based**:
the modulex ``ToolExecutor`` injects an ``api_key: str`` directly
(resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair.

Both operations are asynchronous on Icypeas' side: a submit call
returns a job ``_id`` with a non-terminal status, then the result is
fetched by polling a read endpoint with that ``_id`` until a terminal
status appears. Both steps are folded into a single ``@tool`` body
(one open ``AsyncClient``, ``asyncio.sleep`` between polls, a cap of
``_MAX_POLL_SECONDS``).

Auth header: Icypeas expects the raw API key as the ``Authorization``
header value (no ``Bearer`` prefix) plus ``Content-Type:
application/json``.

Error model: non-2xx responses, timeouts, and an expired polling
window all surface as ``success=False`` + ``error`` rather than
raising.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.icypeas.outputs import (
    FindEmailOutput,
    VerifyEmailOutput,
)

__all__ = ["find_email", "verify_email"]

_BASE_URL = "https://app.icypeas.com/api"
_EMAIL_SEARCH_URL = f"{_BASE_URL}/email-search"
_EMAIL_VERIFICATION_URL = f"{_BASE_URL}/email-verification"
_READ_URL = f"{_BASE_URL}/bulk-single-searchs/read"

_SUBMIT_TIMEOUT = 30.0
_POLL_TIMEOUT = 30.0

# Seconds between poll attempts. Exposed as a module-level constant so
# tests can monkeypatch it to 0 for instant runs.
_POLL_INTERVAL_SECONDS = 3.0
# Hard ceiling on how long we keep polling before giving up.
_MAX_POLL_SECONDS = 120.0

# Statuses that mean the search has finished (success or failure).
_TERMINAL_STATUSES = frozenset(
    {
        "FOUND",
        "DEBITED",
        "NOT_FOUND",
        "DEBITED_NOT_FOUND",
        "BAD_INPUT",
        "INSUFFICIENT_FUNDS",
        "ABORTED",
    }
)
# Statuses that mean a result was actually found / the email is valid.
_FOUND_STATUSES = frozenset({"FOUND", "DEBITED"})


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    # Icypeas expects the raw API key as the Authorization value — no
    # "Bearer " prefix.
    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class FindEmailInput(BaseModel):
    domain_or_company: str = Field(
        description="Target company domain (e.g. stripe.com) or company name (e.g. Stripe)"
    )
    api_key: str = Field(description="Icypeas API key (provided by credential system)")
    firstname: str | None = Field(default=None, description="Target person's first name")
    lastname: str | None = Field(default=None, description="Target person's last name")


class VerifyEmailInput(BaseModel):
    email: str = Field(description="Email address to verify (e.g. john@stripe.com)")
    api_key: str = Field(description="Icypeas API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=FindEmailInput)
@serialize_pydantic_return
async def find_email(
    domain_or_company: str,
    api_key: str,
    firstname: str | None = None,
    lastname: str | None = None,
) -> FindEmailOutput:
    """Find a professional email address from a first name, last name, and
    company domain or name. Submits the search and polls until a result is
    available."""
    if not api_key or not api_key.strip():
        return FindEmailOutput(
            success=False,
            error="Icypeas API key is empty. Please configure a valid Icypeas credential.",
        )

    body: dict[str, Any] = {"domainOrCompany": domain_or_company}
    if firstname:
        body["firstname"] = firstname
    if lastname:
        body["lastname"] = lastname

    try:
        async with httpx.AsyncClient(timeout=_SUBMIT_TIMEOUT) as client:
            response = await client.post(
                _EMAIL_SEARCH_URL, headers=_headers(api_key), json=body
            )
            if response.status_code != 200:
                return FindEmailOutput(
                    success=False,
                    error=f"Icypeas API error ({response.status_code}): {response.text}",
                )
            item = (response.json() or {}).get("item") or {}
            search_id = item.get("_id")
            if not search_id:
                return FindEmailOutput(
                    success=False,
                    error="Icypeas email-search did not return an item id.",
                )

            item, poll_error = await _poll_until_terminal(client, api_key, search_id, item)
            if poll_error is not None:
                return FindEmailOutput(success=False, error=poll_error)
    except httpx.TimeoutException:
        return FindEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindEmailOutput(success=False, error=f"find_email failed: {exc}")

    # results.emails[0].email holds the discovered address.
    # TODO (unverified): this reads the single-search result from a singular
    # "item" object; the published docs excerpt also references an "items"
    # array shape — confirm the exact key per
    # https://api-doc.icypeas.com/getting-started/
    results = item.get("results") or {}
    emails = results.get("emails") if isinstance(results.get("emails"), list) else []
    email = emails[0].get("email") if emails else None
    return FindEmailOutput(
        success=True,
        search_id=item.get("_id"),
        status=item.get("status"),
        email=email,
        firstname=results.get("firstname"),
        lastname=results.get("lastname"),
        item=item,
    )


@tool(args_schema=VerifyEmailInput)
@serialize_pydantic_return
async def verify_email(
    email: str,
    api_key: str,
) -> VerifyEmailOutput:
    """Verify whether an email address is valid and deliverable. Submits the
    verification and polls until a result is available."""
    if not api_key or not api_key.strip():
        return VerifyEmailOutput(
            success=False,
            error="Icypeas API key is empty. Please configure a valid Icypeas credential.",
        )

    body: dict[str, Any] = {"email": email}

    try:
        async with httpx.AsyncClient(timeout=_SUBMIT_TIMEOUT) as client:
            response = await client.post(
                _EMAIL_VERIFICATION_URL, headers=_headers(api_key), json=body
            )
            if response.status_code != 200:
                return VerifyEmailOutput(
                    success=False,
                    error=f"Icypeas API error ({response.status_code}): {response.text}",
                )
            item = (response.json() or {}).get("item") or {}
            search_id = item.get("_id")
            if not search_id:
                return VerifyEmailOutput(
                    success=False,
                    error="Icypeas email-verification did not return an item id.",
                )

            item, poll_error = await _poll_until_terminal(client, api_key, search_id, item)
            if poll_error is not None:
                return VerifyEmailOutput(success=False, error=poll_error)
    except httpx.TimeoutException:
        return VerifyEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VerifyEmailOutput(success=False, error=f"verify_email failed: {exc}")

    status = item.get("status")
    # Verify payloads put the address on item.email; fall back to the nested
    # results.emails[0].email shape that some responses use.
    results = item.get("results") or {}
    emails = results.get("emails") if isinstance(results.get("emails"), list) else []
    email_value = item.get("email") or (emails[0].get("email") if emails else None)
    valid = status in _FOUND_STATUSES if status is not None else None
    return VerifyEmailOutput(
        success=True,
        search_id=item.get("_id"),
        status=status,
        email=email_value,
        valid=valid,
        item=item,
    )


# --- Polling internals -----------------------------------------------------


async def _poll_until_terminal(
    client: httpx.AsyncClient,
    api_key: str,
    search_id: str,
    submit_item: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    """Poll the read endpoint with ``search_id`` until a terminal status is
    reached. Returns ``(item, None)`` on success or ``(item, error)`` when a
    poll fails or the window expires. Reuses the submit response if it is
    already terminal."""
    if submit_item.get("status") in _TERMINAL_STATUSES:
        return submit_item, None

    elapsed = 0.0
    while elapsed < _MAX_POLL_SECONDS:
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        elapsed += _POLL_INTERVAL_SECONDS

        response = await client.post(
            _READ_URL,
            headers=_headers(api_key),
            json={"id": search_id},
            timeout=_POLL_TIMEOUT,
        )
        if response.status_code != 200:
            return submit_item, (
                f"Icypeas poll error ({response.status_code}): {response.text}"
            )

        item = (response.json() or {}).get("item") or {}
        status = item.get("status")
        if status in _TERMINAL_STATUSES:
            return item, None

    return submit_item, "Icypeas search did not complete within the polling window."
