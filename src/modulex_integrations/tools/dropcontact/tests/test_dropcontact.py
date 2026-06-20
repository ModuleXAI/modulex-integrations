"""Tests for the Dropcontact integration.

Enrichment is a submit-then-poll flow, so the happy-path test mocks
BOTH legs: the submit ``POST /v1/enrich/all`` (returns a request_id)
and the poll ``GET /v1/enrich/all/{request_id}`` (returns the ready
result). ``asyncio.sleep`` is patched to a no-op so the 5-second poll
interval does not slow the suite.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.dropcontact import (
    TOOLS,
    enrich_contact,
    manifest,
)
from modulex_integrations.tools.dropcontact.outputs import EnrichContactOutput

API = "https://api.dropcontact.com"
SUBMIT_URL = f"{API}/v1/enrich/all"
_API_KEY = "fake-api-key"
_REQUEST_ID = "req-12345"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip the real 5s poll interval."""

    async def _instant(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        "modulex_integrations.tools.dropcontact.tools.asyncio.sleep", _instant
    )


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:dropcontact"


# --- Happy path ------------------------------------------------------------


@pytest.mark.asyncio
async def test_enrich_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=SUBMIT_URL,
        json={"success": True, "error": False, "request_id": _REQUEST_ID},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{SUBMIT_URL}/{_REQUEST_ID}",
        json={
            "success": True,
            "error": False,
            "data": [
                {
                    "civility": "Mr",
                    "first_name": "John",
                    "last_name": "Doe",
                    "full_name": "John Doe",
                    "email": [
                        {"email": "john.doe@acme.com", "qualification": "nominative@pro"}
                    ],
                    "phone": "+1 555 555 5555",
                    "mobile_phone": None,
                    "company": "Acme Corp",
                    "website": "acme.com",
                    "company_linkedin": "https://linkedin.com/company/acme",
                    "linkedin": "https://linkedin.com/in/johndoe",
                    "country": "US",
                    "siren": None,
                    "siret": None,
                    "vat": None,
                    "nb_employees": "11-50",
                    "employee_count": 42,
                    "naf5_code": None,
                    "naf5_des": None,
                    "industry": "Software",
                    "job": "Head of Sales",
                    "job_level": "C-level",
                    "job_function": "Sales",
                    "company_turnover": "$1M-$10M",
                    "company_results": None,
                }
            ],
        },
    )

    result_dict = await enrich_contact.ainvoke(
        _args(first_name="John", last_name="Doe", company="Acme Corp")
    )

    assert isinstance(result_dict, dict)

    result = EnrichContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.request_id == _REQUEST_ID
    assert result.email_found is True
    assert result.email == "john.doe@acme.com"
    assert result.emails[0].qualification == "nominative@pro"
    assert result.company == "Acme Corp"
    assert result.employee_count == 42
    assert result.job_level == "C-level"

    submit = httpx_mock.get_requests()[0]
    assert submit.headers["X-Access-Token"] == _API_KEY


@pytest.mark.asyncio
async def test_enrich_contact_polls_until_ready(httpx_mock):  # type: ignore[no-untyped-def]
    """A pending poll (success=false, error=false) is retried until ready."""
    httpx_mock.add_response(
        method="POST",
        url=SUBMIT_URL,
        json={"success": True, "error": False, "request_id": _REQUEST_ID},
    )
    # First poll: not ready yet.
    httpx_mock.add_response(
        method="GET",
        url=f"{SUBMIT_URL}/{_REQUEST_ID}",
        json={"success": False, "error": False, "reason": "Request not ready yet"},
    )
    # Second poll: ready, but no verified email found.
    httpx_mock.add_response(
        method="GET",
        url=f"{SUBMIT_URL}/{_REQUEST_ID}",
        json={
            "success": True,
            "error": False,
            "data": [{"first_name": "Jane", "email": []}],
        },
    )

    result_dict = await enrich_contact.ainvoke(_args(email="jane@example.com"))

    result = EnrichContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.first_name == "Jane"
    assert result.email_found is False
    assert result.email is None
    assert result.emails == []


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_enrich_contact_submit_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=SUBMIT_URL,
        status_code=401,
        text="Invalid token",
    )

    result_dict = await enrich_contact.ainvoke(_args(email="x@example.com"))

    assert isinstance(result_dict, dict)
    result = EnrichContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_enrich_contact_api_error_flag(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=SUBMIT_URL,
        json={"error": True, "reason": "Not enough credits"},
    )

    result_dict = await enrich_contact.ainvoke(_args(email="x@example.com"))

    result = EnrichContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Not enough credits" in result.error


@pytest.mark.asyncio
async def test_enrich_contact_poll_error(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=SUBMIT_URL,
        json={"success": True, "error": False, "request_id": _REQUEST_ID},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{SUBMIT_URL}/{_REQUEST_ID}",
        json={"error": True, "reason": "Enrichment failed"},
    )

    result_dict = await enrich_contact.ainvoke(_args(email="x@example.com"))

    result = EnrichContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Enrichment failed" in result.error


@pytest.mark.asyncio
async def test_enrich_contact_no_request_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=SUBMIT_URL,
        json={"success": True, "error": False},
    )

    result_dict = await enrich_contact.ainvoke(_args(email="x@example.com"))

    result = EnrichContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "request_id" in result.error


@pytest.mark.asyncio
async def test_enrich_contact_no_fields() -> None:
    """No contact fields supplied short-circuits before any HTTP call."""
    result_dict = await enrich_contact.ainvoke({"api_key": _API_KEY})

    result = EnrichContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "No contact fields" in result.error


@pytest.mark.asyncio
async def test_enrich_contact_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await enrich_contact.ainvoke({"api_key": "", "email": "x@example.com"})

    assert isinstance(result_dict, dict)
    result = EnrichContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
