"""Happy-path tests for every pagerduty @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.pagerduty import (
    TOOLS,
    acknowledge_incident,
    find_oncall_user,
    manifest,
    resolve_incident,
    trigger_incident,
)
from modulex_integrations.tools.pagerduty.outputs import (
    AcknowledgeIncidentOutput,
    FindOncallUserOutput,
    ResolveIncidentOutput,
    TriggerIncidentOutput,
)

API = "https://api.pagerduty.com"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_trigger_incident(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/incidents",
        json={
            # TODO: fill in a representative response shape from the PagerDuty API docs
            "incident": {
                "id": "PT4KHLK",
                "type": "incident",
                "summary": "[#1234] Test incident",
                "status": "triggered",
                "title": "Test incident",
                "urgency": "high",
                "incident_key": "test-key-123",
                "html_url": "https://subdomain.pagerduty.com/incidents/PT4KHLK",
                "created_at": "2024-01-01T00:00:00Z",
                "service": {"id": "PSERVICE", "type": "service_reference"},
                "escalation_policy": {"id": "PPOLICY", "type": "escalation_policy_reference"},
                "assignments": [],
            },
        },
    )

    result_dict = await trigger_incident.ainvoke(
        _args(title="Test incident", service_id="PSERVICE")
    )

    assert isinstance(result_dict, dict)
    result = TriggerIncidentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident is not None
    assert result.incident.id == "PT4KHLK"
    assert result.incident.status == "triggered"


@pytest.mark.asyncio
async def test_acknowledge_incident(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/incidents/PT4KHLK",
        json={
            # TODO: fill in a representative response shape from the PagerDuty API docs
            "incident": {
                "id": "PT4KHLK",
                "type": "incident",
                "summary": "[#1234] Test incident",
                "status": "acknowledged",
                "title": "Test incident",
                "html_url": "https://subdomain.pagerduty.com/incidents/PT4KHLK",
                "created_at": "2024-01-01T00:00:00Z",
                "service": {"id": "PSERVICE", "type": "service_reference"},
                "escalation_policy": {"id": "PPOLICY", "type": "escalation_policy_reference"},
                "assignments": [],
            },
        },
    )

    result_dict = await acknowledge_incident.ainvoke(
        _args(incident_id="PT4KHLK")
    )

    assert isinstance(result_dict, dict)
    result = AcknowledgeIncidentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident is not None
    assert result.incident.status == "acknowledged"


@pytest.mark.asyncio
async def test_resolve_incident(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/incidents/PT4KHLK",
        json={
            # TODO: fill in a representative response shape from the PagerDuty API docs
            "incident": {
                "id": "PT4KHLK",
                "type": "incident",
                "summary": "[#1234] Test incident",
                "status": "resolved",
                "title": "Test incident",
                "html_url": "https://subdomain.pagerduty.com/incidents/PT4KHLK",
                "created_at": "2024-01-01T00:00:00Z",
                "service": {"id": "PSERVICE", "type": "service_reference"},
                "escalation_policy": {"id": "PPOLICY", "type": "escalation_policy_reference"},
                "assignments": [],
            },
        },
    )

    result_dict = await resolve_incident.ainvoke(
        _args(incident_id="PT4KHLK")
    )

    assert isinstance(result_dict, dict)
    result = ResolveIncidentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident is not None
    assert result.incident.status == "resolved"


@pytest.mark.asyncio
async def test_find_oncall_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/schedules/PSCHED1/users",
        json={
            # TODO: fill in a representative response shape from the PagerDuty API docs
            "users": [
                {
                    "id": "PUSER1",
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                    "type": "user",
                    "html_url": "https://subdomain.pagerduty.com/users/PUSER1",
                },
                {
                    "id": "PUSER2",
                    "name": "John Smith",
                    "email": "john@example.com",
                    "type": "user",
                    "html_url": "https://subdomain.pagerduty.com/users/PUSER2",
                },
            ],
        },
    )

    result_dict = await find_oncall_user.ainvoke(
        _args(schedule_id="PSCHED1", user_id="PUSER1")
    )

    assert isinstance(result_dict, dict)
    result = FindOncallUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.found is True
    assert result.user is not None
    assert result.user.id == "PUSER1"
    assert result.user.name == "Jane Doe"
