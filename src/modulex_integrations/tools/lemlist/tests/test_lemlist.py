"""Happy-path tests per action + failure-path and empty-credential tests
for the non-2xx -> success=False branch (Lemlist tools don't raise)."""
from __future__ import annotations

import base64
from typing import Any

import pytest

from modulex_integrations.tools.lemlist import (
    TOOLS,
    get_activities,
    get_lead,
    manifest,
    send_email,
)
from modulex_integrations.tools.lemlist.outputs import (
    GetActivitiesOutput,
    GetLeadOutput,
    SendEmailOutput,
)

API = "https://api.lemlist.com/api"
_API_KEY = "fake-api-key"
_EXPECTED_BASIC = "Basic " + base64.b64encode(f":{_API_KEY}".encode()).decode()


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_get_activities(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/activities?version=v2&type=emailOpened&limit=2",
        json=[
            {
                "_id": "act_1",
                "type": "emailOpened",
                "leadId": "lea_1",
                "campaignId": "cam_1",
                "sequenceId": "seq_1",
                "stepId": "stp_1",
                "createdAt": "2025-01-01T00:00:00Z",
            },
            {
                "_id": "act_2",
                "type": "emailOpened",
                "leadId": "lea_2",
                "campaignId": "cam_1",
                "sequenceId": None,
                "stepId": None,
                "createdAt": "2025-01-02T00:00:00Z",
            },
        ],
    )

    result_dict = await get_activities.ainvoke(
        _args(type="emailOpened", limit=2)
    )

    assert isinstance(result_dict, dict)

    result = GetActivitiesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 2
    assert result.activities[0].id == "act_1"
    assert result.activities[0].type == "emailOpened"
    assert result.activities[1].sequence_id is None

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == _EXPECTED_BASIC


@pytest.mark.asyncio
async def test_get_lead_by_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/leads/john%40example.com",
        json={
            "_id": "lea_1",
            "email": "john@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "companyName": "Acme",
            "jobTitle": "VP Sales",
            "companyDomain": "acme.com",
            "isPaused": False,
            "campaignId": "cam_1",
            "contactId": "con_1",
            "emailStatus": "valid",
        },
    )

    result_dict = await get_lead.ainvoke(_args(lead_identifier="john@example.com"))

    assert isinstance(result_dict, dict)

    result = GetLeadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "lea_1"
    assert result.email == "john@example.com"
    assert result.first_name == "John"
    assert result.is_paused is False
    assert result.email_status == "valid"


@pytest.mark.asyncio
async def test_get_lead_by_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/leads?id=lea_abc123",
        json={"_id": "lea_abc123", "email": "x@example.com"},
    )

    result_dict = await get_lead.ainvoke(_args(lead_identifier="lea_abc123"))

    assert isinstance(result_dict, dict)

    result = GetLeadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "lea_abc123"


@pytest.mark.asyncio
async def test_send_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inbox/email",
        json={"ok": True},
    )

    result_dict = await send_email.ainvoke(
        _args(
            send_user_id="usr_1",
            send_user_email="sales@company.com",
            send_user_mailbox_id="mbx_1",
            contact_id="con_1",
            lead_id="lea_1",
            subject="Hello",
            message="<p>Hi there</p>",
        )
    )

    assert isinstance(result_dict, dict)

    result = SendEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.ok is True

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == _EXPECTED_BASIC


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_get_activities_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Non-2xx is wrapped in success=False + error rather than raising."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/activities?version=v2",
        status_code=401,
        text="Unauthorized",
    )

    result_dict = await get_activities.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = GetActivitiesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_send_email_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await send_email.ainvoke(
        {
            "send_user_id": "usr_1",
            "send_user_email": "sales@company.com",
            "send_user_mailbox_id": "mbx_1",
            "contact_id": "con_1",
            "lead_id": "lea_1",
            "subject": "Hi",
            "message": "body",
            "api_key": "",
        }
    )

    assert isinstance(result_dict, dict)

    result = SendEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
