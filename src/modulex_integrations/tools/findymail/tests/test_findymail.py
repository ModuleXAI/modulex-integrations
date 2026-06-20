"""Happy-path tests per action + failure-path and empty-credential tests."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.findymail import (
    TOOLS,
    find_email_from_linkedin,
    find_email_from_name,
    find_emails_by_domain,
    find_employees,
    find_phone,
    get_company,
    get_credits,
    lookup_technologies,
    manifest,
    reverse_email_lookup,
    search_technologies,
    verify_email,
)
from modulex_integrations.tools.findymail.outputs import (
    FindEmailFromLinkedinOutput,
    FindEmailFromNameOutput,
    FindEmailsByDomainOutput,
    FindEmployeesOutput,
    FindPhoneOutput,
    GetCompanyOutput,
    GetCreditsOutput,
    LookupTechnologiesOutput,
    ReverseEmailLookupOutput,
    SearchTechnologiesOutput,
    VerifyEmailOutput,
)

API = "https://app.findymail.com/api"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_11_actions(self) -> None:
        assert len(manifest.actions) == 11

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/verify",
        json={"email": "john@example.com", "verified": True, "provider": "Google"},
    )
    result_dict = await verify_email.ainvoke(_args(email="john@example.com"))
    assert isinstance(result_dict, dict)
    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.verified is True
    assert result.provider == "Google"
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_find_email_from_name(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search/name",
        json={"contact": {"name": "John Doe", "email": "john@stripe.com", "domain": "stripe.com"}},
    )
    result_dict = await find_email_from_name.ainvoke(_args(name="John Doe", domain="stripe.com"))
    assert isinstance(result_dict, dict)
    result = FindEmailFromNameOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.email == "john@stripe.com"


@pytest.mark.asyncio
async def test_find_email_from_linkedin(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search/business-profile",
        json={"contact": {"name": "John Doe", "email": "john@stripe.com", "domain": "stripe.com"}},
    )
    result_dict = await find_email_from_linkedin.ainvoke(
        _args(linkedin_url="https://linkedin.com/in/johndoe")
    )
    assert isinstance(result_dict, dict)
    result = FindEmailFromLinkedinOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.name == "John Doe"


@pytest.mark.asyncio
async def test_find_emails_by_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search/domain",
        json={
            "contacts": [
                {"name": "Jane CEO", "email": "jane@stripe.com", "domain": "stripe.com"},
                {"name": "Jim Founder", "email": "jim@stripe.com", "domain": "stripe.com"},
            ]
        },
    )
    result_dict = await find_emails_by_domain.ainvoke(
        _args(domain="stripe.com", roles=["CEO", "Founder"])
    )
    assert isinstance(result_dict, dict)
    result = FindEmailsByDomainOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.contacts) == 2
    assert result.contacts[0].email == "jane@stripe.com"


@pytest.mark.asyncio
async def test_reverse_email_lookup(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search/reverse-email",
        json={
            "email": "john@example.com",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "fullName": "John Doe",
            "jobTitle": "CEO",
            "companyName": "Stripe",
            "isPremium": True,
            "skills": ["Sales"],
        },
    )
    result_dict = await reverse_email_lookup.ainvoke(
        _args(email="john@example.com", with_profile=True)
    )
    assert isinstance(result_dict, dict)
    result = ReverseEmailLookupOutput.model_validate(result_dict)
    assert result.success is True
    assert result.full_name == "John Doe"
    assert result.job_title == "CEO"
    assert result.is_premium is True
    assert result.skills == ["Sales"]
    sent = httpx_mock.get_requests()[0]
    assert b"with_profile" in sent.content


@pytest.mark.asyncio
async def test_get_company(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search/company",
        json={
            "name": "Stripe",
            "domain": "stripe.com",
            "company_size": "1001-5000",
            "industry": "Fintech",
        },
    )
    result_dict = await get_company.ainvoke(_args(domain="stripe.com"))
    assert isinstance(result_dict, dict)
    result = GetCompanyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Stripe"
    assert result.company_size == "1001-5000"


@pytest.mark.asyncio
async def test_find_employees(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search/employees",
        json={
            "data": [
                {
                    "name": "Alice Eng",
                    "linkedinUrl": "https://linkedin.com/in/alice",
                    "companyWebsite": "google.com",
                    "companyName": "Google",
                    "jobTitle": "Software Engineer",
                }
            ]
        },
    )
    result_dict = await find_employees.ainvoke(
        _args(website="google.com", job_titles=["Software Engineer"], count=1)
    )
    assert isinstance(result_dict, dict)
    result = FindEmployeesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.employees[0].name == "Alice Eng"
    assert result.employees[0].job_title == "Software Engineer"


@pytest.mark.asyncio
async def test_find_phone(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search/phone",
        json={"phone": "+14155550100", "line_type": "Mobile"},
    )
    result_dict = await find_phone.ainvoke(_args(linkedin_url="https://linkedin.com/in/johndoe"))
    assert isinstance(result_dict, dict)
    result = FindPhoneOutput.model_validate(result_dict)
    assert result.success is True
    assert result.phone == "+14155550100"
    assert result.line_type == "Mobile"


@pytest.mark.asyncio
async def test_search_technologies(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/technologies/search?q=React",
        json={
            "data": [
                {"name": "React", "category": "JavaScript Frameworks", "subcategory": "UI"}
            ]
        },
    )
    result_dict = await search_technologies.ainvoke(_args(q="React"))
    assert isinstance(result_dict, dict)
    result = SearchTechnologiesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.technologies[0].name == "React"


@pytest.mark.asyncio
async def test_lookup_technologies(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/technologies",
        json={
            "domain": "stripe.com",
            "technologies": [
                {"name": "React", "category": "Frameworks", "subcategory": "UI",
                 "last_detected_at": "2025-01-01"}
            ],
        },
    )
    result_dict = await lookup_technologies.ainvoke(
        _args(domain="stripe.com", technologies=["React"])
    )
    assert isinstance(result_dict, dict)
    result = LookupTechnologiesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.domain == "stripe.com"
    assert result.technologies[0].last_detected_at == "2025-01-01"


@pytest.mark.asyncio
async def test_get_credits(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/credits",
        json={"credits": 1200, "verifier_credits": 500},
    )
    result_dict = await get_credits.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.credits == 1200
    assert result.verifier_credits == 500


# --- Failure-path test -----------------------------------------------------


@pytest.mark.asyncio
async def test_verify_email_non_200_sets_success_false(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/verify",
        status_code=402,
        json={"message": "Not enough credits"},
    )
    result_dict = await verify_email.ainvoke(_args(email="john@example.com"))
    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Not enough credits" in result.error


# --- Empty-credential test -------------------------------------------------


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits() -> None:
    result_dict = await get_credits.ainvoke({"api_key": "   "})
    result = GetCreditsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error
