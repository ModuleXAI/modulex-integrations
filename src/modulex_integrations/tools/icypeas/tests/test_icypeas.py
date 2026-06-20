"""Happy-path tests per action (submit -> terminal poll), a non-terminal
-> terminal poll sequence, plus failure-path and empty-api_key tests.

Both actions submit a job then poll with ``asyncio.sleep`` between
attempts. The poll interval is monkeypatched to 0 so tests run
instantly."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.icypeas import (
    TOOLS,
    find_email,
    manifest,
    verify_email,
)
from modulex_integrations.tools.icypeas import tools as icypeas_tools
from modulex_integrations.tools.icypeas.outputs import (
    FindEmailOutput,
    VerifyEmailOutput,
)

SEARCH_URL = "https://app.icypeas.com/api/email-search"
VERIFY_URL = "https://app.icypeas.com/api/email-verification"
READ_URL = "https://app.icypeas.com/api/bulk-single-searchs/read"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


@pytest.fixture(autouse=True)
def _instant_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the poll interval zero so tests don't actually sleep."""
    monkeypatch.setattr(icypeas_tools, "_POLL_INTERVAL_SECONDS", 0.0)


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
    # Submit returns a non-terminal job id.
    httpx_mock.add_response(
        method="POST",
        url=SEARCH_URL,
        json={"success": True, "item": {"_id": "abc123", "status": "NONE"}},
    )
    # First poll already terminal.
    httpx_mock.add_response(
        method="POST",
        url=READ_URL,
        json={
            "success": True,
            "item": {
                "_id": "abc123",
                "status": "DEBITED",
                "results": {
                    "firstname": "John",
                    "lastname": "Doe",
                    "emails": [{"email": "john@stripe.com"}],
                },
            },
        },
    )

    result_dict = await find_email.ainvoke(
        _args(domain_or_company="stripe.com", firstname="John", lastname="Doe")
    )

    assert isinstance(result_dict, dict)

    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.search_id == "abc123"
    assert result.status == "DEBITED"
    assert result.email == "john@stripe.com"
    assert result.firstname == "John"
    assert result.lastname == "Doe"
    assert result.item is not None

    submit = httpx_mock.get_requests()[0]
    assert submit.headers["Authorization"] == _API_KEY
    assert "Bearer" not in submit.headers["Authorization"]


@pytest.mark.asyncio
async def test_verify_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=VERIFY_URL,
        json={"success": True, "item": {"_id": "ver456", "status": "NONE"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=READ_URL,
        json={
            "success": True,
            "item": {
                "_id": "ver456",
                "status": "FOUND",
                "email": "john@stripe.com",
            },
        },
    )

    result_dict = await verify_email.ainvoke(_args(email="john@stripe.com"))

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.search_id == "ver456"
    assert result.status == "FOUND"
    assert result.email == "john@stripe.com"
    assert result.valid is True
    assert result.item is not None


@pytest.mark.asyncio
async def test_verify_email_non_terminal_then_terminal(httpx_mock):  # type: ignore[no-untyped-def]
    """The first poll returns an in-progress status; a later poll is terminal."""
    httpx_mock.add_response(
        method="POST",
        url=VERIFY_URL,
        json={"success": True, "item": {"_id": "ver789", "status": "NONE"}},
    )
    # First poll: still in progress (non-terminal).
    httpx_mock.add_response(
        method="POST",
        url=READ_URL,
        json={"success": True, "item": {"_id": "ver789", "status": "IN_PROGRESS"}},
    )
    # Second poll: terminal NOT_FOUND -> a definitive, successful verdict.
    httpx_mock.add_response(
        method="POST",
        url=READ_URL,
        json={
            "success": True,
            "item": {
                "_id": "ver789",
                "status": "NOT_FOUND",
                "email": "ghost@nowhere.test",
            },
        },
    )

    result_dict = await verify_email.ainvoke(_args(email="ghost@nowhere.test"))

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "NOT_FOUND"
    assert result.valid is False


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_find_email_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """A non-2xx submit response comes back as ``success=False`` + ``error``."""
    httpx_mock.add_response(
        method="POST",
        url=SEARCH_URL,
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await find_email.ainvoke(_args(domain_or_company="stripe.com"))

    assert isinstance(result_dict, dict)

    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_verify_email_poll_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """A non-2xx poll response surfaces as ``success=False`` + ``error``."""
    httpx_mock.add_response(
        method="POST",
        url=VERIFY_URL,
        json={"success": True, "item": {"_id": "verERR", "status": "NONE"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=READ_URL,
        status_code=429,
        text="Rate limited",
    )

    result_dict = await verify_email.ainvoke(_args(email="x@stripe.com"))

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "429" in result.error


@pytest.mark.asyncio
async def test_find_email_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await find_email.ainvoke(
        {"domain_or_company": "stripe.com", "api_key": ""}
    )

    assert isinstance(result_dict, dict)

    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_verify_email_validates_empty_api_key() -> None:
    result_dict = await verify_email.ainvoke({"email": "x@stripe.com", "api_key": "   "})

    assert isinstance(result_dict, dict)

    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
