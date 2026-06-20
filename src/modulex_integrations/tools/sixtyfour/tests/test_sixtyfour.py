"""Happy-path tests per action + failure-path and empty-credential tests
for the non-2xx -> success=False branch (Sixtyfour AI tools don't raise)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.sixtyfour import (
    TOOLS,
    enrich_company,
    enrich_lead,
    find_email,
    find_phone,
    manifest,
)
from modulex_integrations.tools.sixtyfour.outputs import (
    EnrichCompanyOutput,
    EnrichLeadOutput,
    FindEmailOutput,
    FindPhoneOutput,
)

API = "https://api.sixtyfour.ai"
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
async def test_find_phone(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/find-phone",
        json={
            "name": "John Doe",
            "company": "Acme Inc",
            "phone": "+1 555 123 4567",
            "linkedin_url": "https://linkedin.com/in/johndoe",
        },
    )

    result_dict = await find_phone.ainvoke(_args(name="John Doe", company="Acme Inc"))

    assert isinstance(result_dict, dict)

    result = FindPhoneOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "John Doe"
    assert result.phone == "+1 555 123 4567"
    assert result.linkedin_url == "https://linkedin.com/in/johndoe"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_find_phone_joins_phone_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/find-phone",
        json={
            "name": "Jane Roe",
            "phone": [{"number": "+1 555 000 1111"}, {"number": "+1 555 222 3333"}],
        },
    )

    result_dict = await find_phone.ainvoke(_args(name="Jane Roe"))
    result = FindPhoneOutput.model_validate(result_dict)
    assert result.success is True
    assert result.phone == "+1 555 000 1111, +1 555 222 3333"


@pytest.mark.asyncio
async def test_find_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/find-email",
        json={
            "name": "John Doe",
            "company": "Acme Inc",
            "title": "CEO",
            "phone": "+1 555 123 4567",
            "linkedin": "https://linkedin.com/in/johndoe",
            "email": [["john@acme.com", "OK", "COMPANY"]],
            "personal_email": [["john.doe@gmail.com", "UNKNOWN", "PERSONAL"]],
        },
    )

    result_dict = await find_email.ainvoke(_args(name="John Doe", company="Acme Inc"))

    assert isinstance(result_dict, dict)

    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "CEO"
    assert result.linkedin_url == "https://linkedin.com/in/johndoe"
    assert result.emails[0].address == "john@acme.com"
    assert result.emails[0].status == "OK"
    assert result.emails[0].type == "COMPANY"
    assert result.personal_emails[0].address == "john.doe@gmail.com"


@pytest.mark.asyncio
async def test_enrich_lead(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/enrich-lead",
        json={
            "notes": "Researched profile.",
            "structured_data": {"email": "john@acme.com", "title": "CEO"},
            "references": {"linkedin": "https://linkedin.com/in/johndoe"},
            "confidence_score": 9.5,
        },
    )

    result_dict = await enrich_lead.ainvoke(
        _args(
            lead_info='{"name": "John Doe", "company": "Acme Inc"}',
            struct='{"email": "Email address", "title": "Job title"}',
        )
    )

    assert isinstance(result_dict, dict)

    result = EnrichLeadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.notes == "Researched profile."
    assert result.structured_data["email"] == "john@acme.com"
    assert result.confidence_score == 9.5


@pytest.mark.asyncio
async def test_enrich_company(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/enrich-company",
        json={
            "notes": "Company profile.",
            "structured_data": {"num_employees": 250, "website": "https://acme.com"},
            "references": {"crunchbase": "https://crunchbase.com/acme"},
            "confidence_score": 8.0,
            "org_chart": [{"name": "John Doe", "title": "CEO"}],
        },
    )

    result_dict = await enrich_company.ainvoke(
        _args(
            target_company='{"name": "Acme Inc", "domain": "acme.com"}',
            struct='{"website": "Company website URL", "num_employees": "Employee count"}',
            find_people=True,
            full_org_chart=True,
        )
    )

    assert isinstance(result_dict, dict)

    result = EnrichCompanyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.structured_data["num_employees"] == 250
    assert result.confidence_score == 8.0
    assert result.org_chart == [{"name": "John Doe", "title": "CEO"}]

    sent = httpx_mock.get_requests()[0]
    import json as _json

    body = _json.loads(sent.content)
    assert body["find_people"] is True
    assert body["full_org_chart"] is True
    assert body["target_company"] == {"name": "Acme Inc", "domain": "acme.com"}


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_find_phone_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Non-2xx responses are wrapped in success=False + error, not raised."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/find-phone",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await find_phone.ainvoke(_args(name="Anyone"))

    assert isinstance(result_dict, dict)

    result = FindPhoneOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_enrich_lead_rejects_invalid_json() -> None:
    """A non-JSON lead_info short-circuits before the HTTP call."""
    result_dict = await enrich_lead.ainvoke(
        _args(lead_info="not json", struct='{"email": "Email"}')
    )

    assert isinstance(result_dict, dict)

    result = EnrichLeadOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "lead_info" in result.error


@pytest.mark.asyncio
async def test_find_email_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await find_email.ainvoke({"name": "John", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
