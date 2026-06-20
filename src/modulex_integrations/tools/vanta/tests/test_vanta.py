"""Tests for the vanta integration."""
from __future__ import annotations

import base64
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from modulex_integrations.tools.vanta import TOOLS, manifest
from modulex_integrations.tools.vanta.tools import (
    download_document_file,
    get_control,
    get_document,
    get_framework,
    get_person,
    get_policy,
    get_risk_scenario,
    get_test,
    get_vendor,
    get_vulnerable_asset,
    list_control_documents,
    list_control_tests,
    list_controls,
    list_document_uploads,
    list_documents,
    list_framework_controls,
    list_frameworks,
    list_monitored_computers,
    list_people,
    list_policies,
    list_risk_scenarios,
    list_test_entities,
    list_tests,
    list_vendors,
    list_vulnerabilities,
    list_vulnerability_remediations,
    list_vulnerable_assets,
    submit_document,
    upload_document_file,
)

_TOKEN_URL = "https://api.vanta.com/oauth/token"
_BASE = "https://api.vanta.com/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "client_id": "cid-123",
        "client_secret": "secret-456",
        "region": "us",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


def _mock_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=_TOKEN_URL,
        method="POST",
        json={"access_token": "tok-abc", "expires_in": 3600},
    )


def _list_envelope(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "results": {
            "data": rows,
            "pageInfo": {
                "startCursor": "s",
                "endCursor": "e",
                "hasNextPage": False,
                "hasPreviousPage": False,
            },
        }
    }


# --- Manifest shape -------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_29_actions(self) -> None:
        assert len(manifest.actions) == 29

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}

    def test_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:vanta-themed"


# --- Happy-path: list actions --------------------------------------------


@pytest.mark.asyncio
async def test_list_frameworks(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/frameworks?pageSize=1",
        json=_list_envelope([{"id": "soc2", "displayName": "SOC 2", "numControlsTotal": 50}]),
    )
    result = await list_frameworks.ainvoke(_args(page_size=1))
    assert isinstance(result, dict)
    out = result
    assert out["success"] is True
    assert out["frameworks"][0]["id"] == "soc2"
    assert out["page_info"]["end_cursor"] == "e"


@pytest.mark.asyncio
async def test_list_framework_controls(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/frameworks/soc2/controls",
        json=_list_envelope([{"id": "c1", "name": "Access Control"}]),
    )
    result = await list_framework_controls.ainvoke(_args(framework_id="soc2"))
    assert result["success"] is True
    assert result["controls"][0]["name"] == "Access Control"


@pytest.mark.asyncio
async def test_list_controls(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/controls",
        json=_list_envelope([{"id": "c1", "name": "MFA", "domains": ["IAM"]}]),
    )
    result = await list_controls.ainvoke(_args())
    assert result["success"] is True
    assert result["controls"][0]["domains"] == ["IAM"]


@pytest.mark.asyncio
async def test_list_control_tests(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/controls/c1/tests",
        json=_list_envelope([{"id": "t1", "name": "CloudTrail enabled", "status": "OK"}]),
    )
    result = await list_control_tests.ainvoke(_args(control_id="c1"))
    assert result["success"] is True
    assert result["tests"][0]["status"] == "OK"


@pytest.mark.asyncio
async def test_list_control_documents(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/controls/c1/documents",
        json=_list_envelope([{"id": "d1", "title": "Policy"}]),
    )
    result = await list_control_documents.ainvoke(_args(control_id="c1"))
    assert result["success"] is True
    assert result["documents"][0]["title"] == "Policy"


@pytest.mark.asyncio
async def test_list_tests(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/tests?statusFilter=NEEDS_ATTENTION",
        json=_list_envelope([{"id": "t1", "status": "NEEDS_ATTENTION", "integrations": ["aws"]}]),
    )
    result = await list_tests.ainvoke(_args(status_filter="NEEDS_ATTENTION"))
    assert result["success"] is True
    assert result["tests"][0]["integrations"] == ["aws"]


@pytest.mark.asyncio
async def test_list_test_entities(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/tests/t1/entities?entityStatus=FAILING",
        json=_list_envelope([{"id": "e1", "entityStatus": "FAILING", "displayName": "bucket-x"}]),
    )
    result = await list_test_entities.ainvoke(_args(test_id="t1", entity_status="FAILING"))
    assert result["success"] is True
    assert result["entities"][0]["display_name"] == "bucket-x"


@pytest.mark.asyncio
async def test_list_documents(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/documents",
        json=_list_envelope([{"id": "d1", "title": "Access Review", "uploadStatus": "OK"}]),
    )
    result = await list_documents.ainvoke(_args())
    assert result["success"] is True
    assert result["documents"][0]["upload_status"] == "OK"


@pytest.mark.asyncio
async def test_list_document_uploads(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/documents/d1/uploads",
        json=_list_envelope(
            [{"id": "u1", "fileName": "evidence.pdf", "mimeType": "application/pdf"}]
        ),
    )
    result = await list_document_uploads.ainvoke(_args(document_id="d1"))
    assert result["success"] is True
    assert result["uploads"][0]["file_name"] == "evidence.pdf"


@pytest.mark.asyncio
async def test_list_people(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/people?employmentStatus=CURRENT",
        json=_list_envelope([{"id": "p1", "emailAddress": "a@b.com", "groupIds": ["g1"]}]),
    )
    result = await list_people.ainvoke(_args(employment_status="CURRENT"))
    assert result["success"] is True
    assert result["people"][0]["group_ids"] == ["g1"]


@pytest.mark.asyncio
async def test_list_policies(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/policies",
        json=_list_envelope([{"id": "pol1", "name": "Acceptable Use", "status": "OK"}]),
    )
    result = await list_policies.ainvoke(_args())
    assert result["success"] is True
    assert result["policies"][0]["name"] == "Acceptable Use"


@pytest.mark.asyncio
async def test_list_vendors(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/vendors?name=AWS",
        json=_list_envelope([{"id": "v1", "name": "AWS", "category": {"displayName": "Cloud"}}]),
    )
    result = await list_vendors.ainvoke(_args(name="AWS"))
    assert result["success"] is True
    assert result["vendors"][0]["category"] == "Cloud"


@pytest.mark.asyncio
async def test_list_monitored_computers(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/monitored-computers",
        json=_list_envelope([{"id": "m1", "screenlock": {"outcome": "PASS"}}]),
    )
    result = await list_monitored_computers.ainvoke(_args())
    assert result["success"] is True
    assert result["computers"][0]["screenlock"] == "PASS"


@pytest.mark.asyncio
async def test_list_vulnerabilities(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/vulnerabilities?severity=CRITICAL",
        json=_list_envelope([{"id": "vuln1", "severity": "CRITICAL", "externalURL": "http://x"}]),
    )
    result = await list_vulnerabilities.ainvoke(_args(severity="CRITICAL"))
    assert result["success"] is True
    assert result["vulnerabilities"][0]["external_url"] == "http://x"


@pytest.mark.asyncio
async def test_list_vulnerability_remediations(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/vulnerability-remediations?severity=HIGH",
        json=_list_envelope([{"id": "r1", "vulnerabilityId": "vuln1", "severity": "HIGH"}]),
    )
    result = await list_vulnerability_remediations.ainvoke(_args(severity="HIGH"))
    assert result["success"] is True
    assert result["remediations"][0]["vulnerability_id"] == "vuln1"


@pytest.mark.asyncio
async def test_list_vulnerable_assets(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/vulnerable-assets?assetType=SERVER",
        json=_list_envelope([{"id": "a1", "name": "web-1", "assetType": "SERVER"}]),
    )
    result = await list_vulnerable_assets.ainvoke(_args(asset_type="SERVER"))
    assert result["success"] is True
    assert result["assets"][0]["asset_type"] == "SERVER"


@pytest.mark.asyncio
async def test_list_risk_scenarios(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/risk-scenarios?searchString=phishing",
        json=_list_envelope([{"riskId": "rs1", "description": "Phishing", "likelihood": 3}]),
    )
    result = await list_risk_scenarios.ainvoke(_args(search_string="phishing"))
    assert result["success"] is True
    assert result["risk_scenarios"][0]["risk_id"] == "rs1"


# --- Happy-path: get actions ---------------------------------------------


@pytest.mark.asyncio
async def test_get_framework(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/frameworks/soc2",
        json={"id": "soc2", "displayName": "SOC 2", "requirementCategories": [{"id": "cat1"}]},
    )
    result = await get_framework.ainvoke(_args(framework_id="soc2"))
    assert result["success"] is True
    assert result["framework"]["requirement_categories"][0]["id"] == "cat1"


@pytest.mark.asyncio
async def test_get_control(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/controls/c1",
        json={"id": "c1", "name": "MFA", "status": "COMPLETED", "numTestsTotal": 3},
    )
    result = await get_control.ainvoke(_args(control_id="c1"))
    assert result["success"] is True
    assert result["control"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_get_test(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/tests/t1",
        json={
            "id": "t1",
            "name": "CloudTrail",
            "status": "OK",
            "version": {"major": 1, "minor": 0},
        },
    )
    result = await get_test.ainvoke(_args(test_id="t1"))
    assert result["success"] is True
    assert result["test"]["version"]["major"] == 1


@pytest.mark.asyncio
async def test_get_document(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/documents/d1",
        json={"id": "d1", "title": "Access Review", "subscribers": ["a@b.com"]},
    )
    result = await get_document.ainvoke(_args(document_id="d1"))
    assert result["success"] is True
    assert result["document"]["subscribers"] == ["a@b.com"]


@pytest.mark.asyncio
async def test_get_person(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/people/p1",
        json={"id": "p1", "emailAddress": "a@b.com", "name": {"display": "Alice"}},
    )
    result = await get_person.ainvoke(_args(person_id="p1"))
    assert result["success"] is True
    assert result["person"]["name"]["display"] == "Alice"


@pytest.mark.asyncio
async def test_get_policy(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/policies/pol1",
        json={"id": "pol1", "name": "AUP", "latestVersion": {"status": "APPROVED"}},
    )
    result = await get_policy.ainvoke(_args(policy_id="pol1"))
    assert result["success"] is True
    assert result["policy"]["latest_version_status"] == "APPROVED"


@pytest.mark.asyncio
async def test_get_vendor(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/vendors/v1",
        json={"id": "v1", "name": "AWS", "inherentRiskLevel": "HIGH"},
    )
    result = await get_vendor.ainvoke(_args(vendor_id="v1"))
    assert result["success"] is True
    assert result["vendor"]["inherent_risk_level"] == "HIGH"


@pytest.mark.asyncio
async def test_get_vulnerable_asset(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/vulnerable-assets/a1",
        json={"id": "a1", "name": "web-1", "scanners": [{"resourceId": "res-1"}]},
    )
    result = await get_vulnerable_asset.ainvoke(_args(vulnerable_asset_id="a1"))
    assert result["success"] is True
    assert result["asset"]["scanners"][0]["resourceId"] == "res-1"


@pytest.mark.asyncio
async def test_get_risk_scenario(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/risk-scenarios/rs1",
        json={"riskId": "rs1", "description": "Phishing", "treatment": "Mitigate"},
    )
    result = await get_risk_scenario.ainvoke(_args(risk_scenario_id="rs1"))
    assert result["success"] is True
    assert result["risk_scenario"]["treatment"] == "Mitigate"


# --- Happy-path: document file + submit actions --------------------------


@pytest.mark.asyncio
async def test_upload_document_file(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/documents/d1/uploads",
        method="POST",
        json={"id": "u1", "fileName": "evidence.pdf", "mimeType": "application/pdf"},
    )
    content = base64.b64encode(b"hello evidence").decode("ascii")
    result = await upload_document_file.ainvoke(
        _args(
            document_id="d1",
            file_content=content,
            file_name="evidence.pdf",
            mime_type="application/pdf",
            description="Q3 access review",
        )
    )
    assert result["success"] is True
    assert result["upload"]["id"] == "u1"


@pytest.mark.asyncio
async def test_download_document_file(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/documents/d1/uploads/u1/download",
        content=b"binary-file-bytes",
        headers={"Content-Type": "application/pdf"},
    )
    result = await download_document_file.ainvoke(
        _args(document_id="d1", uploaded_file_id="u1")
    )
    assert result["success"] is True
    assert result["mime_type"] == "application/pdf"
    assert base64.b64decode(result["data"]) == b"binary-file-bytes"
    assert result["size"] == len(b"binary-file-bytes")


@pytest.mark.asyncio
async def test_submit_document(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/documents/submit",
        method="POST",
        json={"ok": True},
    )
    result = await submit_document.ainvoke(_args(document_id="d1"))
    assert result["success"] is True
    assert result["document_id"] == "d1"
    assert result["submitted"] is True


# --- Failure + empty-credential paths ------------------------------------


@pytest.mark.asyncio
async def test_api_error_returns_failure(httpx_mock: HTTPXMock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        url=f"{_BASE}/frameworks?pageSize=1",
        status_code=403,
        text="forbidden",
    )
    result = await list_frameworks.ainvoke(_args(page_size=1))
    assert result["success"] is False
    assert "403" in (result["error"] or "")


@pytest.mark.asyncio
async def test_token_exchange_failure(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=_TOKEN_URL,
        method="POST",
        status_code=401,
        text="invalid_client",
    )
    result = await list_frameworks.ainvoke(_args())
    assert result["success"] is False
    assert "401" in (result["error"] or "")


@pytest.mark.asyncio
async def test_missing_credentials_short_circuits() -> None:
    result = await list_frameworks.ainvoke(
        {"auth_type": "custom", "auth_data": {}}
    )
    assert result["success"] is False
    assert "Missing Vanta credentials" in (result["error"] or "")


@pytest.mark.asyncio
async def test_invalid_base64_upload() -> None:
    result = await upload_document_file.ainvoke(
        _args(document_id="d1", file_content="not!!base64", file_name="x.pdf")
    )
    assert result["success"] is False
    assert "base64" in (result["error"] or "")


@pytest.mark.asyncio
async def test_gov_region_uses_gov_host(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.vanta-gov.com/oauth/token",
        method="POST",
        json={"access_token": "tok-gov", "expires_in": 3600},
    )
    httpx_mock.add_response(
        url="https://api.vanta-gov.com/v1/frameworks",
        json=_list_envelope([{"id": "soc2"}]),
    )
    auth = {
        "auth_type": "custom",
        "auth_data": {
            "client_id": "cid",
            "client_secret": "sec",
            "region": "gov",
        },
    }
    result = await list_frameworks.ainvoke(auth)
    assert result["success"] is True
    assert result["frameworks"][0]["id"] == "soc2"
