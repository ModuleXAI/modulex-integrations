"""Happy-path tests per action + failure-path and empty-credential tests.

Both actions submit a job then poll a result endpoint with a sleep
between attempts. Tests neutralize that wait by monkeypatching
``asyncio.sleep`` to a no-op coroutine, so the poll loop runs instantly.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from modulex_integrations.tools.enrow import (
    TOOLS,
    find_email,
    manifest,
    verify_email,
)
from modulex_integrations.tools.enrow.outputs import (
    FindEmailOutput,
    VerifyEmailOutput,
)

API = "https://api.enrow.io"
FIND_URL = f"{API}/email/find/single"
VERIFY_URL = f"{API}/email/verify/single"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the submit->poll loop instant."""

    async def _instant(_seconds: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _instant)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_find_email(httpx_mock):  # type: ignore[no-untyped-def]
    # Submit -> returns a job id.
    httpx_mock.add_response(
        method="POST",
        url=FIND_URL,
        json={"id": "job-123"},
    )
    # Poll -> terminal HTTP 200 with the resolved result.
    httpx_mock.add_response(
        method="GET",
        url=f"{FIND_URL}?id=job-123",
        status_code=200,
        json={
            "email": "john@stripe.com",
            "qualification": "valid",
            "fullname": "John Doe",
            "company_name": "Stripe",
            "company_domain": "stripe.com",
            "linkedin_url": "https://linkedin.com/in/johndoe",
        },
    )

    result_dict = await find_email.ainvoke(
        _args(fullname="John Doe", company_domain="stripe.com")
    )

    assert isinstance(result_dict, dict)

    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "job-123"
    assert result.email == "john@stripe.com"
    assert result.qualification == "valid"
    assert result.linkedin_url == "https://linkedin.com/in/johndoe"

    submit = httpx_mock.get_requests()[0]
    assert submit.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_verify_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=VERIFY_URL,
        json={"id": "ver-456"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{VERIFY_URL}?id=ver-456",
        status_code=200,
        json={"email": "john@example.com", "qualification": "valid"},
    )

    result_dict = await verify_email.ainvoke(_args(email="john@example.com"))

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "ver-456"
    assert result.email == "john@example.com"
    assert result.qualification == "valid"


@pytest.mark.asyncio
async def test_find_email_polls_through_202(httpx_mock):  # type: ignore[no-untyped-def]
    """A non-terminal HTTP 202 keeps the loop going until the HTTP 200."""
    httpx_mock.add_response(method="POST", url=FIND_URL, json={"id": "job-789"})
    # First poll: still running.
    httpx_mock.add_response(
        method="GET", url=f"{FIND_URL}?id=job-789", status_code=202
    )
    # Second poll: complete.
    httpx_mock.add_response(
        method="GET",
        url=f"{FIND_URL}?id=job-789",
        status_code=200,
        json={"email": "jane@apple.com", "qualification": "valid"},
    )

    result_dict = await find_email.ainvoke(
        _args(fullname="Jane Roe", company_name="Apple")
    )

    assert isinstance(result_dict, dict)

    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email == "jane@apple.com"
    # Three HTTP calls: submit + two polls.
    assert len(httpx_mock.get_requests()) == 3


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_find_email_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """A non-2xx submit response is wrapped in success=False + error."""
    httpx_mock.add_response(
        method="POST",
        url=FIND_URL,
        status_code=401,
        text="Invalid apikey",
    )

    result_dict = await find_email.ainvoke(_args(fullname="John Doe", company_domain="x.com"))

    assert isinstance(result_dict, dict)

    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_verify_email_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await verify_email.ainvoke({"email": "x@y.com", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
