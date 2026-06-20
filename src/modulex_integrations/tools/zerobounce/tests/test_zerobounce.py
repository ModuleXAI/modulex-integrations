"""Happy-path tests per action + failure-path and empty-credential tests.

ZeroBounce returns HTTP 200 with an ``{"error": ...}`` envelope on auth
failure (and ``{"Credits": -1}`` from getcredits), so the tools detect
errors from the body, not just the HTTP status — exercised below.
"""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.zerobounce import (
    TOOLS,
    get_credits,
    manifest,
    verify_email,
)
from modulex_integrations.tools.zerobounce.outputs import (
    GetCreditsOutput,
    VerifyEmailOutput,
)

_API_KEY = "fake-api-key"
_VALIDATE_RE = re.compile(r"^https://api\.zerobounce\.net/v2/validate")
_CREDITS_RE = re.compile(r"^https://api\.zerobounce\.net/v2/getcredits")


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_has_exactly_one_auth_schema(self) -> None:
        assert len(manifest.auth_schemas) == 1


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=_VALIDATE_RE,
        json={
            "address": "john@example.com",
            "status": "valid",
            "sub_status": "",
            "free_email": False,
            "did_you_mean": "",
            "domain": "example.com",
        },
    )

    result_dict = await verify_email.ainvoke(_args(email="john@example.com"))

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email == "john@example.com"
    assert result.status == "valid"
    assert result.deliverable is True
    assert result.free_email is False

    sent = httpx_mock.get_requests()[0]
    assert sent.url.params["api_key"] == _API_KEY
    assert sent.url.params["email"] == "john@example.com"
    assert sent.url.params["ip_address"] == ""


@pytest.mark.asyncio
async def test_verify_email_normalizes_catch_all(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=_VALIDATE_RE,
        json={
            "address": "info@example.com",
            "status": "catch-all",
            "sub_status": "",
            "free_email": False,
            "did_you_mean": "",
        },
    )

    result_dict = await verify_email.ainvoke(_args(email="info@example.com"))

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    # Hyphenated 'catch-all' is normalized to 'catch_all'; not deliverable.
    assert result.status == "catch_all"
    assert result.deliverable is False


@pytest.mark.asyncio
async def test_get_credits(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=_CREDITS_RE,
        json={"Credits": 2375323},
    )

    result_dict = await get_credits.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.credits == 2375323

    sent = httpx_mock.get_requests()[0]
    assert sent.url.params["api_key"] == _API_KEY


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_email_returns_error_on_envelope(httpx_mock):  # type: ignore[no-untyped-def]
    """ZeroBounce answers HTTP 200 with an ``{"error": ...}`` envelope on
    auth failure; the tool surfaces it as ``success=False`` + ``error``."""
    httpx_mock.add_response(
        method="GET",
        url=_VALIDATE_RE,
        json={"error": "Invalid API Key or your account ran out of credits"},
    )

    result_dict = await verify_email.ainvoke(_args(email="x@example.com"))

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Invalid API Key" in result.error


@pytest.mark.asyncio
async def test_get_credits_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=_CREDITS_RE,
        status_code=500,
        text="Internal Server Error",
    )

    result_dict = await get_credits.ainvoke(_args())

    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "500" in result.error


@pytest.mark.asyncio
async def test_verify_email_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await verify_email.ainvoke({"email": "x@example.com", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_get_credits_validates_empty_api_key() -> None:
    result_dict = await get_credits.ainvoke({"api_key": "   "})

    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
