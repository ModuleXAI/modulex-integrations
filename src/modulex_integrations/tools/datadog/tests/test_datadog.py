"""Happy-path tests for every datadog @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.datadog import (
    TOOLS,
    get_account_info,
    get_metric_data,
    manifest,
    post_metric_data,
    search_dashboards,
    search_events,
    search_hosts,
    search_incidents,
    search_logs,
    search_metrics,
    search_monitors,
    search_services,
)
from modulex_integrations.tools.datadog.outputs import (
    GetAccountInfoOutput,
    GetMetricDataOutput,
    PostMetricDataOutput,
    SearchDashboardsOutput,
    SearchEventsOutput,
    SearchHostsOutput,
    SearchIncidentsOutput,
    SearchLogsOutput,
    SearchMetricsOutput,
    SearchMonitorsOutput,
    SearchServicesOutput,
)

_API_KEY = "fake-api-key"
_APP_KEY = "fake-application-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, application_key=_APP_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_11_actions(self) -> None:
        assert len(manifest.actions) == 11

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_get_account_info(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v1/validate",
        json={"valid": True},
    )

    result_dict = await get_account_info.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetAccountInfoOutput.model_validate(result_dict)
    assert result.success is True
    assert result.region == "datadoghq.com"


@pytest.mark.asyncio
async def test_get_metric_data(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v1/query?query=avg%3Asystem.cpu.user%7B%2A%7D&from=1640995200&to=1640998800",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "series": [{"metric": "system.cpu.user", "pointlist": [[1640995200, 42.0]]}],
            "from_date": 1640995200,
            "to_date": 1640998800,
            "query": "avg:system.cpu.user{*}",
        },
    )

    result_dict = await get_metric_data.ainvoke(
        _args(region="datadoghq.com", query="avg:system.cpu.user{*}", from_ts=1640995200, to_ts=1640998800)
    )

    assert isinstance(result_dict, dict)
    result = GetMetricDataOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_post_metric_data(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url="https://api.datadoghq.com/api/v2/series",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "errors": [],
        },
    )

    result_dict = await post_metric_data.ainvoke(
        _args(region="datadoghq.com", metric="custom.metric", points={"1640995200": 1.0})
    )

    assert isinstance(result_dict, dict)
    result = PostMetricDataOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_dashboards(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v1/dashboard",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "dashboards": [{"id": "abc-123", "title": "My Dashboard"}],
        },
    )

    result_dict = await search_dashboards.ainvoke(_args(region="datadoghq.com"))

    assert isinstance(result_dict, dict)
    result = SearchDashboardsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_events(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v1/events?start=1640995200&end=1640998800",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "events": [{"id": 1, "title": "Test event"}],
        },
    )

    result_dict = await search_events.ainvoke(
        _args(region="datadoghq.com", start=1640995200, end=1640998800)
    )

    assert isinstance(result_dict, dict)
    result = SearchEventsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_hosts(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v1/hosts",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "host_list": [{"name": "web-01", "id": 12345}],
            "total_matching": 1,
        },
    )

    result_dict = await search_hosts.ainvoke(_args(region="datadoghq.com"))

    assert isinstance(result_dict, dict)
    result = SearchHostsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_incidents(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v2/incidents",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "data": [{"id": "inc-1", "type": "incidents"}],
        },
    )

    result_dict = await search_incidents.ainvoke(_args(region="datadoghq.com"))

    assert isinstance(result_dict, dict)
    result = SearchIncidentsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_logs(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url="https://api.datadoghq.com/api/v2/logs/events/search",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "data": [{"id": "log-1", "type": "log"}],
        },
    )

    result_dict = await search_logs.ainvoke(
        _args(region="datadoghq.com", query="service:web status:error")
    )

    assert isinstance(result_dict, dict)
    result = SearchLogsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_metrics(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v1/metrics?from=1",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "metrics": ["system.cpu.user", "system.mem.used"],
        },
    )

    result_dict = await search_metrics.ainvoke(_args(region="datadoghq.com"))

    assert isinstance(result_dict, dict)
    result = SearchMetricsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_monitors(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v1/monitor",
        json=[
            # TODO: fill in a representative response shape from the upstream API docs
            {"id": 1, "name": "CPU monitor", "type": "metric alert"},
        ],
    )

    result_dict = await search_monitors.ainvoke(_args(region="datadoghq.com"))

    assert isinstance(result_dict, dict)
    result = SearchMonitorsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_services(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://api.datadoghq.com/api/v2/services/definitions",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "data": [{"id": "svc-1", "type": "service-definition"}],
        },
    )

    result_dict = await search_services.ainvoke(_args(region="datadoghq.com"))

    assert isinstance(result_dict, dict)
    result = SearchServicesOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_account_info_empty_credentials() -> None:
    """Failure path: empty API key returns success=False without hitting the network."""
    result_dict = await get_account_info.ainvoke({"api_key": "", "application_key": ""})

    assert isinstance(result_dict, dict)
    result = GetAccountInfoOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "empty" in result.error.lower() or "credential" in result.error.lower()
