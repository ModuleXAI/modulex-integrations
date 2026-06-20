"""Enrow LangChain ``@tool`` functions.

Two async tools wrapping the Enrow B2B email API. The calling
convention is the modulex *api_key* convention: the ``ToolExecutor``
injects an ``api_key: str`` directly (resolved from the user's
``api_key`` credential), not an ``auth_type``/``auth_data`` pair.

Both endpoints are asynchronous: a ``POST`` submit call returns a job
``id``, then a ``GET`` result endpoint is polled (HTTP 202 = still
running, HTTP 200 = complete) until the job resolves or a polling cap
is reached. Each ``@tool`` folds the submit + poll loop into a single
call so callers get a fully resolved result.

Error model: non-2xx HTTP responses, timeouts, and an expired polling
window are caught and returned as ``success=False`` + ``error`` rather
than raising.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.enrow.outputs import (
    FindEmailOutput,
    VerifyEmailOutput,
)

__all__ = ["find_email", "verify_email"]

_ENROW_API_BASE = "https://api.enrow.io"
_FIND_PATH = "/email/find/single"
_VERIFY_PATH = "/email/verify/single"

# Async submit -> poll loop tuning. The result endpoint returns HTTP 202
# while the job is still running; poll on this interval until it resolves
# to HTTP 200 or the cap is reached.
_POLL_INTERVAL_SECONDS = 3.0
_MAX_POLL_SECONDS = 120.0
_REQUEST_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class FindEmailInput(BaseModel):
    fullname: str = Field(description='Full name of the person (e.g. "John Doe")')
    api_key: str = Field(description="Enrow API key (provided by credential system)")
    company_domain: str | None = Field(
        default=None,
        description=(
            'Company domain (e.g. "apple.com"). Preferred over company_name. '
            "Provide company_domain or company_name."
        ),
    )
    company_name: str | None = Field(
        default=None,
        description=(
            'Company name (e.g. "Apple"). Used when the company domain is '
            "unavailable. Provide company_domain or company_name."
        ),
    )


class VerifyEmailInput(BaseModel):
    email: str = Field(description='Email address to verify (e.g. "john@example.com")')
    api_key: str = Field(description="Enrow API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=FindEmailInput)
@serialize_pydantic_return
async def find_email(
    fullname: str,
    api_key: str,
    company_domain: str | None = None,
    company_name: str | None = None,
) -> FindEmailOutput:
    """Find a verified B2B email address from a full name and company domain
    or name. Submits an asynchronous search and polls until the result is
    ready. Provide company_domain (preferred) or company_name."""
    if not api_key or not api_key.strip():
        return FindEmailOutput(
            success=False,
            error="Enrow API key is empty. Please configure a valid Enrow credential.",
        )

    body: dict[str, Any] = {"fullname": fullname}
    if company_domain:
        body["company_domain"] = company_domain
    if company_name:
        body["company_name"] = company_name

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            submit = await client.post(
                f"{_ENROW_API_BASE}{_FIND_PATH}",
                headers=_headers(api_key),
                json=body,
            )
            if submit.status_code != 200:
                return FindEmailOutput(
                    success=False,
                    error=f"Enrow API error ({submit.status_code}): {submit.text}",
                )
            job_id = (submit.json() or {}).get("id")
            if not job_id:
                return FindEmailOutput(
                    success=False,
                    error="Enrow find-email did not return a job id.",
                )

            elapsed = 0.0
            while elapsed < _MAX_POLL_SECONDS:
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                elapsed += _POLL_INTERVAL_SECONDS

                poll = await client.get(
                    f"{_ENROW_API_BASE}{_FIND_PATH}",
                    headers=_headers(api_key),
                    params={"id": job_id},
                )
                if poll.status_code == 202:
                    # Still in progress — keep polling.
                    continue
                if poll.status_code != 200:
                    return FindEmailOutput(
                        success=False,
                        error=(
                            f"Enrow find-email poll error ({poll.status_code}): "
                            f"{poll.text}"
                        ),
                    )

                data = poll.json() or {}
                return FindEmailOutput(
                    success=True,
                    id=str(job_id),
                    email=data.get("email"),
                    qualification=data.get("qualification"),
                    fullname=data.get("fullname"),
                    company_name=data.get("company_name"),
                    company_domain=data.get("company_domain"),
                    linkedin_url=data.get("linkedin_url"),
                )
    except httpx.TimeoutException:
        return FindEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindEmailOutput(success=False, error=f"Find email failed: {exc}")

    return FindEmailOutput(
        success=False,
        error="Enrow find-email did not complete within the polling window.",
    )


@tool(args_schema=VerifyEmailInput)
@serialize_pydantic_return
async def verify_email(
    email: str,
    api_key: str,
) -> VerifyEmailOutput:
    """Verify the deliverability of an email address. Submits an asynchronous
    verification and polls until the result is ready."""
    if not api_key or not api_key.strip():
        return VerifyEmailOutput(
            success=False,
            error="Enrow API key is empty. Please configure a valid Enrow credential.",
        )

    body: dict[str, Any] = {"email": email}

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            submit = await client.post(
                f"{_ENROW_API_BASE}{_VERIFY_PATH}",
                headers=_headers(api_key),
                json=body,
            )
            if submit.status_code != 200:
                return VerifyEmailOutput(
                    success=False,
                    error=f"Enrow API error ({submit.status_code}): {submit.text}",
                )
            job_id = (submit.json() or {}).get("id")
            if not job_id:
                return VerifyEmailOutput(
                    success=False,
                    error="Enrow verify-email did not return a job id.",
                )

            elapsed = 0.0
            while elapsed < _MAX_POLL_SECONDS:
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                elapsed += _POLL_INTERVAL_SECONDS

                poll = await client.get(
                    f"{_ENROW_API_BASE}{_VERIFY_PATH}",
                    headers=_headers(api_key),
                    params={"id": job_id},
                )
                if poll.status_code == 202:
                    # Still in progress — keep polling.
                    continue
                if poll.status_code != 200:
                    return VerifyEmailOutput(
                        success=False,
                        error=(
                            f"Enrow verify-email poll error ({poll.status_code}): "
                            f"{poll.text}"
                        ),
                    )

                data = poll.json() or {}
                return VerifyEmailOutput(
                    success=True,
                    id=str(job_id),
                    email=data.get("email"),
                    qualification=data.get("qualification"),
                )
    except httpx.TimeoutException:
        return VerifyEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VerifyEmailOutput(success=False, error=f"Verify email failed: {exc}")

    return VerifyEmailOutput(
        success=False,
        error="Enrow verify-email did not complete within the polling window.",
    )
