"""Happy-path tests for every amplitude @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.amplitude import (
    TOOLS,
    event_segmentation,
    get_active_users,
    get_revenue,
    group_identify,
    identify_user,
    list_events,
    manifest,
    realtime_active_users,
    send_event,
    user_activity,
    user_profile,
    user_search,
)
from modulex_integrations.tools.amplitude.outputs import (
    EventSegmentationOutput,
    GetActiveUsersOutput,
    GetRevenueOutput,
    GroupIdentifyOutput,
    IdentifyUserOutput,
    ListEventsOutput,
    RealtimeActiveUsersOutput,
    SendEventOutput,
    UserActivityOutput,
    UserProfileOutput,
    UserSearchOutput,
)

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "api_key": "fake_api_key",
        "secret_key": "fake_secret_key",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a .ainvoke() input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_11_actions(self) -> None:
        assert len(manifest.actions) == 11

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_send_event(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url="https://api2.amplitude.com/2/httpapi",
        json={
            "code": 200,
            "events_ingested": 1,
            "payload_size_bytes": 120,
            "server_upload_time": 1700000000000,
        },
    )

    result_dict = await send_event.ainvoke(
        _args(event_type="page_view", user_id="user-1", event_properties={"page": "/home"})
    )

    assert isinstance(result_dict, dict)
    result = SendEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.events_ingested == 1
    assert result.code == 200


@pytest.mark.asyncio
async def test_identify_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url="https://api2.amplitude.com/identify",
        text="success",
    )

    result_dict = await identify_user.ainvoke(
        _args(user_id="user-1", user_properties={"$set": {"plan": "premium"}})
    )

    assert isinstance(result_dict, dict)
    result = IdentifyUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.code == 200
    assert result.message == "success"


@pytest.mark.asyncio
async def test_group_identify(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url="https://api2.amplitude.com/groupidentify",
        text="success",
    )

    result_dict = await group_identify.ainvoke(
        _args(
            group_type="company",
            group_value="Acme Corp",
            group_properties={"$set": {"industry": "tech"}},
        )
    )

    assert isinstance(result_dict, dict)
    result = GroupIdentifyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.code == 200


@pytest.mark.asyncio
async def test_user_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://amplitude.com/api/2/usersearch?user=user-1",
        json={
            "matches": [{"amplitude_id": 12345, "user_id": "user-1"}],
            "type": "match_user_or_device_id",
        },
    )

    result_dict = await user_search.ainvoke(_args(user="user-1"))

    assert isinstance(result_dict, dict)
    result = UserSearchOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.matches) == 1
    assert result.matches[0].amplitude_id == 12345
    assert result.type == "match_user_or_device_id"


@pytest.mark.asyncio
async def test_user_activity(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://amplitude.com/api/2/useractivity?user=12345",
        json={
            "events": [
                {
                    "event_type": "page_view",
                    "event_time": "2024-01-15 10:00:00.000000",
                    "event_properties": {"page": "/home"},
                    "user_properties": {"plan": "premium"},
                    "session_id": 1700000000000,
                    "platform": "Web",
                    "country": "US",
                    "city": "San Francisco",
                }
            ],
            "userData": {
                "user_id": "user-1",
                "canonical_amplitude_id": 12345,
                "num_events": 42,
                "num_sessions": 7,
                "platform": "Web",
                "country": "US",
            },
        },
    )

    result_dict = await user_activity.ainvoke(_args(amplitude_id="12345"))

    assert isinstance(result_dict, dict)
    result = UserActivityOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.events) == 1
    assert result.events[0].event_type == "page_view"
    assert result.user_data is not None
    assert result.user_data.num_events == 42


@pytest.mark.asyncio
async def test_user_profile(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://profile-api.amplitude.com/v1/userprofile?user_id=user-1",
        json={
            "userData": {
                "user_id": "user-1",
                "device_id": "device-9",
                "amp_props": {"library": "amplitude-js"},
                "cohort_ids": ["cohort-1"],
                "computations": {"ltv": 99.5},
            }
        },
    )

    result_dict = await user_profile.ainvoke(_args(user_id="user-1"))

    assert isinstance(result_dict, dict)
    result = UserProfileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user_id == "user-1"
    assert result.cohort_ids == ["cohort-1"]


@pytest.mark.asyncio
async def test_event_segmentation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "data": {
                "series": [[10, 20, 30]],
                "seriesLabels": ["page_view"],
                "seriesCollapsed": [[{"setId": "0", "value": 60}]],
                "xValues": ["2024-01-01", "2024-01-02", "2024-01-03"],
            }
        },
    )

    result_dict = await event_segmentation.ainvoke(
        _args(event_type="page_view", start="20240101", end="20240103")
    )

    assert isinstance(result_dict, dict)
    result = EventSegmentationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.series_labels == ["page_view"]
    assert len(result.x_values) == 3


@pytest.mark.asyncio
async def test_get_active_users(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "data": {
                "series": [[100, 110, 120]],
                "seriesMeta": ["Active"],
                "xValues": ["2024-01-01", "2024-01-02", "2024-01-03"],
            }
        },
    )

    result_dict = await get_active_users.ainvoke(
        _args(start="20240101", end="20240103")
    )

    assert isinstance(result_dict, dict)
    result = GetActiveUsersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.series_meta == ["Active"]
    assert len(result.x_values) == 3


@pytest.mark.asyncio
async def test_realtime_active_users(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://amplitude.com/api/2/realtime",
        json={
            "data": {
                "series": [[5, 6, 7]],
                "seriesLabels": ["Today"],
                "xValues": ["15:00", "15:05", "15:10"],
            }
        },
    )

    result_dict = await realtime_active_users.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = RealtimeActiveUsersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.series_labels == ["Today"]


@pytest.mark.asyncio
async def test_list_events(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://amplitude.com/api/2/events/list",
        json={
            "data": [
                {
                    "value": "page_view",
                    "display": "Page View",
                    "totals": 1234,
                    "hidden": False,
                    "deleted": False,
                }
            ]
        },
    )

    result_dict = await list_events.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListEventsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.events) == 1
    assert result.events[0].value == "page_view"
    assert result.events[0].display_name == "Page View"


@pytest.mark.asyncio
async def test_get_revenue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "data": {
                "series": [[1000.0, 1100.0]],
                "seriesLabels": ["Total Revenue"],
                "xValues": ["2024-01-01", "2024-01-02"],
            }
        },
    )

    result_dict = await get_revenue.ainvoke(
        _args(start="20240101", end="20240102")
    )

    assert isinstance(result_dict, dict)
    result = GetRevenueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.series_labels == ["Total Revenue"]


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_send_event_api_error(httpx_mock):  # type: ignore[no-untyped-def]
    """A non-2xx response is returned as success=False, not raised."""
    httpx_mock.add_response(
        method="POST",
        url="https://api2.amplitude.com/2/httpapi",
        status_code=400,
        text="invalid_api_key",
    )

    result_dict = await send_event.ainvoke(_args(event_type="page_view", user_id="user-1"))

    assert isinstance(result_dict, dict)
    result = SendEventOutput.model_validate(result_dict)
    assert result.success is False
    assert "400" in (result.error or "")


# --- Empty-credential tests ------------------------------------------------


@pytest.mark.asyncio
async def test_send_event_missing_api_key() -> None:
    """send_event must fail immediately when the API key is missing."""
    result_dict = await send_event.ainvoke(
        {"auth_type": "custom", "auth_data": {}, "event_type": "page_view", "user_id": "u1"}
    )

    assert isinstance(result_dict, dict)
    result = SendEventOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")


@pytest.mark.asyncio
async def test_user_search_missing_secret_key() -> None:
    """Dashboard ops must fail immediately when the Secret key is missing."""
    result_dict = await user_search.ainvoke(
        {"auth_type": "custom", "auth_data": {"api_key": "fake_api_key"}, "user": "user-1"}
    )

    assert isinstance(result_dict, dict)
    result = UserSearchOutput.model_validate(result_dict)
    assert result.success is False
    assert "Secret key" in (result.error or "")


@pytest.mark.asyncio
async def test_user_profile_missing_secret_key() -> None:
    """user_profile must fail immediately when the Secret key is missing."""
    result_dict = await user_profile.ainvoke(
        {"auth_type": "custom", "auth_data": {"api_key": "fake_api_key"}, "user_id": "user-1"}
    )

    assert isinstance(result_dict, dict)
    result = UserProfileOutput.model_validate(result_dict)
    assert result.success is False
    assert "Secret key" in (result.error or "")
