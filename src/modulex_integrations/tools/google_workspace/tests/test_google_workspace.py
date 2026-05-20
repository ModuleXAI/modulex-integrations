"""Happy-path tests for every google_workspace @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_workspace import (
    TOOLS,
    list_activities_by_admin,
    list_activities_by_event_and_admin,
    list_activities_by_event_name,
    list_all_activities,
    manifest,
)
from modulex_integrations.tools.google_workspace.outputs import (
    ListActivitiesByAdminOutput,
    ListActivitiesByEventAndAdminOutput,
    ListActivitiesByEventNameOutput,
    ListAllActivitiesOutput,
)

API = "https://admin.googleapis.com/admin/reports/v1"

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
async def test_list_activities_by_admin(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/activity/users/admin@example.com/applications/admin",
        json={
            # TODO: fill in a representative response shape from the Google Admin SDK Reports API docs
            "kind": "admin#reports#activities",
            "items": [
                {
                    "kind": "admin#reports#activity",
                    "id": {"time": "2026-01-01T00:00:00.000Z", "uniqueQualifier": "123", "applicationName": "admin", "customerId": "C00000000"},
                    "actor": {"email": "admin@example.com", "profileId": "100000000000000000000"},
                    "events": [{"type": "ADMIN_SETTINGS", "name": "CHANGE_SETTING"}],
                }
            ],
        },
    )

    result_dict = await list_activities_by_admin.ainvoke(
        _args(application_name="admin", user_key="admin@example.com")
    )

    assert isinstance(result_dict, dict)
    result = ListActivitiesByAdminOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.activities) == 1

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_list_activities_by_event_and_admin(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/activity/users/admin@example.com/applications/admin?eventName=CHANGE_SETTING",
        json={
            # TODO: fill in a representative response shape from the Google Admin SDK Reports API docs
            "kind": "admin#reports#activities",
            "items": [
                {
                    "kind": "admin#reports#activity",
                    "id": {"time": "2026-01-01T00:00:00.000Z", "uniqueQualifier": "456", "applicationName": "admin", "customerId": "C00000000"},
                    "actor": {"email": "admin@example.com", "profileId": "100000000000000000000"},
                    "events": [{"type": "ADMIN_SETTINGS", "name": "CHANGE_SETTING"}],
                }
            ],
        },
    )

    result_dict = await list_activities_by_event_and_admin.ainvoke(
        _args(application_name="admin", event_name="CHANGE_SETTING", user_key="admin@example.com")
    )

    assert isinstance(result_dict, dict)
    result = ListActivitiesByEventAndAdminOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.activities) == 1

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_list_activities_by_event_name(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/activity/users/all/applications/admin?eventName=CHANGE_SETTING",
        json={
            # TODO: fill in a representative response shape from the Google Admin SDK Reports API docs
            "kind": "admin#reports#activities",
            "items": [
                {
                    "kind": "admin#reports#activity",
                    "id": {"time": "2026-01-01T00:00:00.000Z", "uniqueQualifier": "789", "applicationName": "admin", "customerId": "C00000000"},
                    "actor": {"email": "admin@example.com", "profileId": "100000000000000000000"},
                    "events": [{"type": "ADMIN_SETTINGS", "name": "CHANGE_SETTING"}],
                }
            ],
        },
    )

    result_dict = await list_activities_by_event_name.ainvoke(
        _args(application_name="admin", event_name="CHANGE_SETTING")
    )

    assert isinstance(result_dict, dict)
    result = ListActivitiesByEventNameOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.activities) == 1

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_list_all_activities(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/activity/users/all/applications/admin",
        json={
            # TODO: fill in a representative response shape from the Google Admin SDK Reports API docs
            "kind": "admin#reports#activities",
            "items": [
                {
                    "kind": "admin#reports#activity",
                    "id": {"time": "2026-01-01T00:00:00.000Z", "uniqueQualifier": "012", "applicationName": "admin", "customerId": "C00000000"},
                    "actor": {"email": "admin@example.com", "profileId": "100000000000000000000"},
                    "events": [{"type": "ADMIN_SETTINGS", "name": "CHANGE_SETTING"}],
                }
            ],
        },
    )

    result_dict = await list_all_activities.ainvoke(
        _args(application_name="admin")
    )

    assert isinstance(result_dict, dict)
    result = ListAllActivitiesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.activities) == 1

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_list_activities_by_admin_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/activity/users/admin@example.com/applications/admin",
        status_code=403,
        json={"error": {"message": "Insufficient permissions", "code": 403}},
    )

    result_dict = await list_activities_by_admin.ainvoke(
        _args(application_name="admin", user_key="admin@example.com")
    )

    assert isinstance(result_dict, dict)
    result = ListActivitiesByAdminOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "403" in result.error
