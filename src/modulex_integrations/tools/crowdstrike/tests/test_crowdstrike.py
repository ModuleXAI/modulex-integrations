"""Happy-path tests per action + failure-path and empty-credential tests.

Each action runs a two-step flow: an OAuth2 token exchange followed by
the Identity Protection call, so happy-path tests mock both the
``/oauth2/token`` endpoint and the data endpoint. Errors come back as
``success=False`` + ``error`` (nothing raises out of a ``@tool``)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.crowdstrike import (
    TOOLS,
    get_sensor_aggregates,
    get_sensor_details,
    manifest,
    query_sensors,
)
from modulex_integrations.tools.crowdstrike.outputs import (
    GetSensorAggregatesOutput,
    GetSensorDetailsOutput,
    QuerySensorsOutput,
)

BASE = "https://api.crowdstrike.com"
TOKEN_URL = f"{BASE}/oauth2/token"
_CLIENT_ID = "fake-client-id"
_API_KEY = "fake-client-secret"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(client_id=_CLIENT_ID, cloud="us-1", api_key=_API_KEY, **extra)


def _mock_token(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=TOKEN_URL,
        json={"access_token": "tok-123", "expires_in": 1799},
    )


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_has_single_auth_schema(self) -> None:
        # Key-based tools ship exactly one ApiKeyAuthSchema (no modulex_key).
        assert len(manifest.auth_schemas) == 1

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:crowdstrike"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_query_sensors(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/identity-protection/queries/devices/v1?filter=status%3A%27protected%27&limit=2",
        json={
            "resources": ["device-id-1", "device-id-2"],
            "meta": {"pagination": {"limit": 2, "offset": 0, "total": 42}},
            "errors": [],
        },
    )

    result_dict = await query_sensors.ainvoke(
        _args(filter="status:'protected'", limit=2)
    )

    assert isinstance(result_dict, dict)

    result = QuerySensorsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.device_ids == ["device-id-1", "device-id-2"]
    assert result.count == 2
    assert result.pagination is not None
    assert result.pagination.total == 42

    # The token exchange used the form-encoded client credentials.
    token_req = httpx_mock.get_requests()[0]
    assert token_req.url == TOKEN_URL
    body = token_req.read().decode()
    assert "client_id=fake-client-id" in body
    assert "client_secret=fake-client-secret" in body

    # The data call carried the bearer token from the exchange.
    data_req = httpx_mock.get_requests()[1]
    assert data_req.headers["Authorization"] == "Bearer tok-123"


@pytest.mark.asyncio
async def test_query_sensors_with_object_resources(httpx_mock):  # type: ignore[no-untyped-def]
    """If the upstream returns full device objects, they parse as sensors."""
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/identity-protection/queries/devices/v1",
        json={
            "resources": [
                {
                    "deviceId": "device-id-1",
                    "hostname": "server-01",
                    "status": "protected",
                    "statusCauses": ["healthy"],
                }
            ],
            "meta": {},
            "errors": [],
        },
    )

    result_dict = await query_sensors.ainvoke(_args())
    result = QuerySensorsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sensors[0].device_id == "device-id-1"
    assert result.sensors[0].hostname == "server-01"
    assert result.sensors[0].status_causes == ["healthy"]
    assert result.sensors[0].raw["hostname"] == "server-01"


@pytest.mark.asyncio
async def test_get_sensor_details(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/identity-protection/entities/devices/GET/v1",
        json={
            "resources": [
                {
                    "deviceId": "device-id-1",
                    "cid": "cid-123",
                    "hostname": "server-01",
                    "agentVersion": "7.10.0",
                    "status": "protected",
                }
            ],
            "meta": {},
            "errors": [],
        },
    )

    result_dict = await get_sensor_details.ainvoke(_args(ids=["device-id-1"]))

    assert isinstance(result_dict, dict)

    result = GetSensorDetailsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.sensors[0].agent_version == "7.10.0"
    assert result.sensors[0].cid == "cid-123"

    # The device IDs were sent in the POST body.
    data_req = httpx_mock.get_requests()[1]
    assert b"device-id-1" in data_req.read()


@pytest.mark.asyncio
async def test_get_sensor_aggregates(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/identity-protection/aggregates/devices/GET/v1",
        json={
            "resources": [
                {
                    "name": "by_status",
                    "buckets": [
                        {"key": "protected", "count": 30},
                        {"key": "unprotected", "count": 12},
                    ],
                    "sumOtherDocCount": 0,
                }
            ],
            "meta": {},
            "errors": [],
        },
    )

    result_dict = await get_sensor_aggregates.ainvoke(
        _args(aggregate_query={"field": "status", "name": "by_status", "type": "terms"})
    )

    assert isinstance(result_dict, dict)

    result = GetSensorAggregatesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.aggregates[0].name == "by_status"
    assert result.aggregates[0].buckets[0].count == 30
    assert result.aggregates[0].buckets[0].key == "protected"
    assert result.aggregates[0].sum_other_doc_count == 0


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_query_sensors_auth_failure(httpx_mock):  # type: ignore[no-untyped-def]
    """A non-2xx token exchange surfaces as success=False, no data call."""
    httpx_mock.add_response(
        method="POST",
        url=TOKEN_URL,
        status_code=401,
        text="access denied, invalid client credentials",
    )

    result_dict = await query_sensors.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = QuerySensorsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_get_sensor_details_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/identity-protection/entities/devices/GET/v1",
        status_code=403,
        text="forbidden",
    )

    result_dict = await get_sensor_details.ainvoke(_args(ids=["device-id-1"]))

    result = GetSensorDetailsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "403" in result.error


@pytest.mark.asyncio
async def test_query_sensors_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before any HTTP call."""
    result_dict = await query_sensors.ainvoke(
        {"client_id": _CLIENT_ID, "cloud": "us-1", "api_key": ""}
    )

    assert isinstance(result_dict, dict)

    result = QuerySensorsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "secret" in result.error


@pytest.mark.asyncio
async def test_query_sensors_rejects_unknown_cloud() -> None:
    """An unrecognized cloud region short-circuits before any HTTP call."""
    result_dict = await query_sensors.ainvoke(
        {"client_id": _CLIENT_ID, "cloud": "mars-1", "api_key": _API_KEY}
    )

    result = QuerySensorsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "cloud region" in result.error
