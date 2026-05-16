"""Tests for the Calendly integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.calendly import (
    TOOLS,
    create_invitee_no_show,
    create_scheduling_link,
    get_current_user,
    get_event,
    list_event_invitees,
    list_event_types,
    list_events,
    list_groups,
    list_organization_members,
    list_user_availability_schedules,
    list_webhook_subscriptions,
    manifest,
)
from modulex_integrations.tools.calendly.outputs import (
    CreateInviteeNoShowOutput,
    CreateSchedulingLinkOutput,
    GetCurrentUserOutput,
    GetEventOutput,
    ListEventInviteesOutput,
    ListEventsOutput,
    ListEventTypesOutput,
    ListGroupsOutput,
    ListOrganizationMembersOutput,
    ListUserAvailabilitySchedulesOutput,
    ListWebhookSubscriptionsOutput,
)

API = "https://api.calendly.com"

_OAUTH_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "cal-oauth-token"},
}
_PAT_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "cal-pat-token"},
}


def _args(auth: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return dict(auth, **extra)


def _user_me_payload(uri: str = f"{API}/users/U1") -> dict[str, Any]:
    return {
        "resource": {
            "uri": uri,
            "name": "Ada",
            "email": "ada@example.com",
            "current_organization": f"{API}/organizations/O1",
            "scheduling_url": "https://calendly.com/ada",
            "timezone": "UTC",
            "avatar_url": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-02-01T00:00:00Z",
        }
    }


class TestManifest:
    def test_manifest_exposes_eleven_actions(self) -> None:
        assert len(manifest.actions) == 11

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_bearer_token_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}

    def test_oauth_config_present(self) -> None:
        oauth = next(a for a in manifest.auth_schemas if a.auth_type == "oauth2")
        assert oauth.oauth_config.auth_url == "https://auth.calendly.com/oauth/authorize"
        assert oauth.oauth_config.scopes == ["default"]


@pytest.mark.asyncio
async def test_get_current_user_oauth(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/users/me", json=_user_me_payload())

    result_dict = await get_current_user.ainvoke(_args(_OAUTH_AUTH))
    assert isinstance(result_dict, dict)
    result = GetCurrentUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.resource is not None
    assert result.resource["email"] == "ada@example.com"


@pytest.mark.asyncio
async def test_get_current_user_bearer(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/users/me", json=_user_me_payload())

    result = GetCurrentUserOutput.model_validate(
        await get_current_user.ainvoke(_args(_PAT_AUTH))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_current_user_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/users/me", status_code=401, text="unauthorized"
    )
    result = GetCurrentUserOutput.model_validate(
        await get_current_user.ainvoke(_args(_OAUTH_AUTH))
    )
    assert result.success is False
    assert result.error is not None and "401" in result.error


@pytest.mark.asyncio
async def test_list_events_auto_resolves_user(httpx_mock: Any) -> None:
    # 1st call: /users/me to resolve the default user URI.
    httpx_mock.add_response(method="GET", url=f"{API}/users/me", json=_user_me_payload())
    # 2nd call: /scheduled_events with the resolved user param.
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/scheduled_events?count=20&user={API}/users/U1",
        json={
            "collection": [
                {"uri": f"{API}/scheduled_events/E1", "name": "Standup", "status": "active"}
            ],
            "pagination": {"count": 1, "next_page_token": None, "next_page": None},
        },
    )

    result = ListEventsOutput.model_validate(
        await list_events.ainvoke(_args(_OAUTH_AUTH))
    )
    assert result.success is True
    assert result.count == 1
    assert result.events[0]["name"] == "Standup"


@pytest.mark.asyncio
async def test_get_event(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/scheduled_events/E1",
        json={
            "resource": {
                "uri": f"{API}/scheduled_events/E1",
                "name": "Standup",
                "status": "active",
                "start_time": "2026-05-16T10:00:00Z",
                "end_time": "2026-05-16T10:30:00Z",
            }
        },
    )
    result = GetEventOutput.model_validate(
        await get_event.ainvoke(_args(_OAUTH_AUTH, event_uuid="E1"))
    )
    assert result.success is True
    assert result.resource is not None
    assert result.resource["name"] == "Standup"


@pytest.mark.asyncio
async def test_list_event_invitees(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/scheduled_events/E1/invitees?count=20",
        json={
            "collection": [
                {"uri": f"{API}/scheduled_events/E1/invitees/I1", "email": "x@y.io"},
            ],
            "pagination": {"count": 1, "next_page_token": None, "next_page": None},
        },
    )
    result = ListEventInviteesOutput.model_validate(
        await list_event_invitees.ainvoke(_args(_OAUTH_AUTH, event_uuid="E1"))
    )
    assert result.success is True
    assert result.invitees[0]["email"] == "x@y.io"


@pytest.mark.asyncio
async def test_list_event_types_with_explicit_user(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/event_types?count=20&user={API}/users/U1&active=true",
        json={
            "collection": [
                {"uri": f"{API}/event_types/ET1", "name": "30 min", "duration": 30}
            ],
            "pagination": {"count": 1, "next_page_token": None, "next_page": None},
        },
    )
    result = ListEventTypesOutput.model_validate(
        await list_event_types.ainvoke(
            _args(_OAUTH_AUTH, user=f"{API}/users/U1", active=True)
        )
    )
    assert result.success is True
    assert result.event_types[0]["name"] == "30 min"


@pytest.mark.asyncio
async def test_create_scheduling_link_promotes_uuid(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(
            201,
            json={
                "resource": {
                    "booking_url": "https://calendly.com/d/abc",
                    "owner": f"{API}/event_types/ET1",
                    "owner_type": "EventType",
                }
            },
        )

    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/scheduling_links")
    result = CreateSchedulingLinkOutput.model_validate(
        await create_scheduling_link.ainvoke(
            _args(_OAUTH_AUTH, owner="ET1", max_event_count=3)
        )
    )
    assert result.success is True
    assert result.booking_url == "https://calendly.com/d/abc"
    # Bare UUID got promoted to full URI.
    assert captured["owner"] == f"{API}/event_types/ET1"
    assert captured["max_event_count"] == 3


@pytest.mark.asyncio
async def test_create_invitee_no_show(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invitee_no_shows",
        status_code=201,
        json={
            "resource": {
                "uri": f"{API}/invitee_no_shows/N1",
                "invitee": f"{API}/scheduled_events/E1/invitees/I1",
                "created_at": "2026-05-16T11:00:00Z",
            }
        },
    )
    result = CreateInviteeNoShowOutput.model_validate(
        await create_invitee_no_show.ainvoke(
            _args(
                _OAUTH_AUTH,
                invitee_uri=f"{API}/scheduled_events/E1/invitees/I1",
            )
        )
    )
    assert result.success is True
    assert result.resource is not None
    assert result.resource["created_at"] == "2026-05-16T11:00:00Z"


@pytest.mark.asyncio
async def test_list_user_availability_schedules(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/user_availability_schedules?user={API}/users/U1",
        json={
            "collection": [
                {"uri": f"{API}/user_availability_schedules/S1", "name": "Workdays"}
            ]
        },
    )
    result = ListUserAvailabilitySchedulesOutput.model_validate(
        await list_user_availability_schedules.ainvoke(
            _args(_OAUTH_AUTH, user="U1")
        )
    )
    assert result.success is True
    assert result.count == 1
    assert result.schedules[0]["name"] == "Workdays"


@pytest.mark.asyncio
async def test_list_organization_members_auto_org(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/users/me", json=_user_me_payload())
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/organization_memberships?count=20&organization={API}/organizations/O1",
        json={
            "collection": [
                {"uri": f"{API}/organization_memberships/M1", "role": "owner"}
            ],
            "pagination": {"count": 1, "next_page_token": None, "next_page": None},
        },
    )
    result = ListOrganizationMembersOutput.model_validate(
        await list_organization_members.ainvoke(_args(_OAUTH_AUTH))
    )
    assert result.success is True
    assert result.members[0]["role"] == "owner"


@pytest.mark.asyncio
async def test_list_groups(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/groups?organization={API}/organizations/O1&count=20",
        json={
            "collection": [{"uri": f"{API}/groups/G1", "name": "Engineering"}],
            "pagination": {"count": 1, "next_page_token": None, "next_page": None},
        },
    )
    result = ListGroupsOutput.model_validate(
        await list_groups.ainvoke(
            _args(_OAUTH_AUTH, organization=f"{API}/organizations/O1")
        )
    )
    assert result.success is True
    assert result.groups[0]["name"] == "Engineering"


@pytest.mark.asyncio
async def test_list_webhook_subscriptions(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/webhook_subscriptions"
            f"?organization={API}/organizations/O1&scope=organization&count=20"
        ),
        json={
            "collection": [{"uri": f"{API}/webhook_subscriptions/W1", "state": "active"}],
            "pagination": {"count": 1, "next_page_token": None, "next_page": None},
        },
    )
    result = ListWebhookSubscriptionsOutput.model_validate(
        await list_webhook_subscriptions.ainvoke(
            _args(
                _OAUTH_AUTH,
                organization=f"{API}/organizations/O1",
                scope="organization",
            )
        )
    )
    assert result.success is True
    assert result.webhooks[0]["state"] == "active"
