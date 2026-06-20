"""Happy-path tests per action + failure-path and empty-credential tests.

NeverBounce returns HTTP 200 even for API-level errors and signals the
outcome through the response envelope's ``status`` field, so we exercise
both the non-``success`` envelope branch and the empty-credential
short-circuit.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.neverbounce import (
    TOOLS,
    get_credits,
    manifest,
    verify_email,
)
from modulex_integrations.tools.neverbounce.outputs import (
    GetCreditsOutput,
    VerifyEmailOutput,
)

API = "https://api.neverbounce.com/v4"
_API_KEY = "fake-api-key"


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

    def test_manifest_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:neverbounce-themed"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/single/check?key={_API_KEY}&email=john%40gmail.com&address_info=1",
        json={
            "status": "success",
            "result": "valid",
            "flags": ["has_dns", "has_dns_mx", "free_email_host"],
            "suggested_correction": "",
            "retry_token": "",
            "execution_time": 0.123,
        },
    )

    result_dict = await verify_email.ainvoke(_args(email="john@gmail.com"))

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email == "john@gmail.com"
    assert result.status == "valid"
    assert result.deliverable is True
    assert result.free_email is True
    assert result.role_account is False
    assert result.result == "valid"
    assert "has_dns" in result.flags

    sent = httpx_mock.get_requests()[0]
    assert sent.url.params["key"] == _API_KEY
    assert sent.url.params["email"] == "john@gmail.com"


@pytest.mark.asyncio
async def test_verify_email_maps_catchall_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/single/check?key={_API_KEY}&email=sales%40example.com&address_info=1",
        json={
            "status": "success",
            "result": "catchall",
            "flags": ["role_account"],
            "suggested_correction": "",
        },
    )

    result_dict = await verify_email.ainvoke(_args(email="sales@example.com"))
    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "catch_all"
    assert result.deliverable is False
    assert result.role_account is True


@pytest.mark.asyncio
async def test_get_credits(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/account/info?key={_API_KEY}",
        json={
            "status": "success",
            "billing_type": "credit",
            "credits_info": {
                "paid_credits_used": 5,
                "free_credits_used": 2,
                "paid_credits_remaining": 995,
                "free_credits_remaining": 998,
                "monthly_api_usage": 7,
            },
            "job_counts": {
                "completed": 0,
                "under_review": 0,
                "queued": 0,
                "processing": 0,
            },
            "execution_time": 0.05,
        },
    )

    result_dict = await get_credits.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.credits == 995
    assert result.free_credits == 998

    sent = httpx_mock.get_requests()[0]
    assert sent.url.params["key"] == _API_KEY


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_email_envelope_failure(httpx_mock):  # type: ignore[no-untyped-def]
    """NeverBounce returns HTTP 200 with a non-success envelope status on
    auth/quota failures; we surface that as success=False + error."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/single/check?key={_API_KEY}&email=bad%40example.com&address_info=1",
        status_code=200,
        json={
            "status": "auth_failure",
            "message": "The API key provided is invalid",
            "execution_time": 0.01,
        },
    )

    result_dict = await verify_email.ainvoke(_args(email="bad@example.com"))

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "invalid" in result.error.lower()
    assert result.email == "bad@example.com"


@pytest.mark.asyncio
async def test_get_credits_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/account/info?key={_API_KEY}",
        status_code=500,
        text="Internal Server Error",
    )

    result_dict = await get_credits.ainvoke(_args())

    assert isinstance(result_dict, dict)

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

    assert isinstance(result_dict, dict)

    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
