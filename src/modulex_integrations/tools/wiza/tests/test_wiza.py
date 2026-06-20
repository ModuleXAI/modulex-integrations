"""Happy-path tests per action + failure-path and empty-credential
tests for the non-2xx -> success=False branch (Wiza tools do not raise
on errors)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.wiza import (
    TOOLS,
    company_enrichment,
    get_credits,
    individual_reveal,
    manifest,
    prospect_search,
)
from modulex_integrations.tools.wiza.outputs import (
    CompanyEnrichmentOutput,
    GetCreditsOutput,
    IndividualRevealOutput,
    ProspectSearchOutput,
)

API = "https://wiza.co/api"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_prospect_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/prospects/search",
        json={
            "status": {"code": 200, "message": "ok"},
            "data": {
                "total": 1234,
                "profiles": [
                    {
                        "full_name": "John Doe",
                        "linkedin_url": "https://linkedin.com/in/johndoe",
                        "industry": "Computer Software",
                        "job_title": "CEO",
                        "job_title_role": "operations",
                        "job_title_sub_role": "executive",
                        "job_company_name": "Wiza",
                        "job_company_website": "wiza.co",
                        "location_name": "Toronto, Ontario, Canada",
                    }
                ],
            },
        },
    )

    result_dict = await prospect_search.ainvoke(
        _args(job_title=[{"v": "CEO", "s": "i"}], size=1)
    )

    assert isinstance(result_dict, dict)

    result = ProspectSearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1234
    assert result.profiles[0].full_name == "John Doe"
    assert result.profiles[0].job_company_name == "Wiza"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_company_enrichment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/company_enrichments",
        json={
            "status": {"code": 200, "message": "ok"},
            "data": {
                "company_name": "Wiza",
                "company_domain": "wiza.co",
                "domain": "wiza.co",
                "company_industry": "Computer Software",
                "company_size": 75,
                "company_size_range": "51-200",
                "company_founded": 2019,
                "credits": {"api_credits": {"total": 2, "company_credits": 2}},
            },
        },
    )

    result_dict = await company_enrichment.ainvoke(_args(company_domain="wiza.co"))

    assert isinstance(result_dict, dict)

    result = CompanyEnrichmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.company_name == "Wiza"
    assert result.company_size == 75
    assert result.credits == {"api_credits": {"total": 2, "company_credits": 2}}


@pytest.mark.asyncio
async def test_individual_reveal_synchronous(httpx_mock):  # type: ignore[no-untyped-def]
    """A reveal that resolves on the initial POST (terminal status) skips polling."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/individual_reveals",
        json={
            "status": {"code": 200, "message": "ok"},
            "data": {
                "id": 987654,
                "status": "finished",
                "is_complete": True,
                "name": "John Doe",
                "enrichment_level": "full",
                "email": "john@wiza.co",
                "email_status": "valid",
                "emails": [
                    {
                        "email": "john@wiza.co",
                        "email_type": "work",
                        "email_status": "valid",
                    }
                ],
                "mobile_phone": "+1-555-0100",
                "phones": [
                    {
                        "number": "+15550100",
                        "pretty_number": "+1 555-0100",
                        "type": "mobile",
                    }
                ],
                "credits": {"api_credits": {"total": 7, "email_credits": 2, "phone_credits": 5}},
            },
        },
    )

    result_dict = await individual_reveal.ainvoke(
        _args(enrichment_level="full", email="john@wiza.co")
    )

    assert isinstance(result_dict, dict)

    result = IndividualRevealOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 987654
    assert result.status == "finished"
    assert result.email == "john@wiza.co"
    assert result.emails[0].email_status == "valid"
    assert result.phones[0].type == "mobile"


@pytest.mark.asyncio
async def test_individual_reveal_polls_until_terminal(httpx_mock):  # type: ignore[no-untyped-def]
    """A queued reveal is polled via GET until it reaches a terminal status."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/individual_reveals",
        json={"data": {"id": 555, "status": "queued", "is_complete": False}},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/individual_reveals/555",
        json={
            "data": {
                "id": 555,
                "status": "finished",
                "is_complete": True,
                "name": "Jane Doe",
                "email": "jane@wiza.co",
                "email_status": "valid",
            }
        },
    )

    result_dict = await individual_reveal.ainvoke(
        _args(enrichment_level="partial", profile_url="https://linkedin.com/in/janedoe")
    )

    assert isinstance(result_dict, dict)

    result = IndividualRevealOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "finished"
    assert result.name == "Jane Doe"


@pytest.mark.asyncio
async def test_get_credits(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meta/credits",
        json={
            "credits": {
                "email_credits": "unlimited",
                "phone_credits": 100,
                "export_credits": 0,
                "api_credits": 1000,
            }
        },
    )

    result_dict = await get_credits.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email_credits == "unlimited"
    assert result.phone_credits == 100
    assert result.api_credits == 1000


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_get_credits_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Wiza errors come back as HTTP 4xx/5xx; the tool wraps them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meta/credits",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await get_credits.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_prospect_search_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await prospect_search.ainvoke({"api_key": ""})

    assert isinstance(result_dict, dict)

    result = ProspectSearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
