"""Datadog LangChain @tool functions."""
from __future__ import annotations

import time
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "get_account_info",
    "get_metric_data",
    "post_metric_data",
    "search_dashboards",
    "search_events",
    "search_hosts",
    "search_incidents",
    "search_logs",
    "search_metrics",
    "search_monitors",
    "search_services",
]

_REGIONS = [
    ("datadoghq.com", "US1 - East"),
    ("us3.datadoghq.com", "US3 - West"),
    ("us5.datadoghq.com", "US5 - West"),
    ("datadoghq.eu", "EU1 - Frankfurt"),
    ("ddog-gov.com", "US1-FED - GovCloud"),
    ("ap1.datadoghq.com", "AP1 - Tokyo"),
]

_TIMEOUT = 30.0


def _headers(api_key: str, application_key: str) -> dict[str, str]:
    return {
        "DD-API-KEY": api_key,
        "DD-APPLICATION-KEY": application_key,
        "Content-Type": "application/json",
    }


def _api_url(region: str) -> str:
    return f"https://api.{region}/api"


# --- Input schemas --------------------------------------------------------


class GetAccountInfoInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")


class GetMetricDataInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    query: str = Field(description="Metric query string (e.g. avg:system.cpu.user{*})")
    from_ts: int = Field(description="Start of the query window as POSIX timestamp in seconds")
    to_ts: int = Field(description="End of the query window as POSIX timestamp in seconds")


class PostMetricDataInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    metric: str = Field(description="The name of the timeseries metric")
    points: dict[str, float] = Field(description="Points as JSON object where keys are Unix timestamps and values are numeric")


class SearchDashboardsInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    filter_shared: bool | None = Field(default=None, description="If true, only return shared dashboards")
    count: int | None = Field(default=None, description="Maximum number of dashboards to return")
    start: int | None = Field(default=None, description="Offset for pagination")


class SearchEventsInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    start: int | None = Field(default=None, description="POSIX timestamp (seconds) for start of query window; defaults to 24 hours ago")
    end: int | None = Field(default=None, description="POSIX timestamp (seconds) for end of query window; defaults to now")
    priority: str | None = Field(default=None, description="Filter by event priority: normal or low")
    sources: str | None = Field(default=None, description="Comma-separated list of sources (e.g. nagios,hudson)")
    tags: str | None = Field(default=None, description="Comma-separated list of tags (e.g. env:prod,role:db)")


class SearchHostsInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    filter: str | None = Field(default=None, description="Filter hosts by name, alias, or tag")
    sort_field: str | None = Field(default=None, description="Field to sort by: status, apps, cpu, iowait, or load")
    sort_dir: str | None = Field(default=None, description="Direction of sort: asc or desc")
    count: int | None = Field(default=None, description="Number of hosts to return (max 1000)")


class SearchIncidentsInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    query: str | None = Field(default=None, description="Search query using field:value syntax (e.g. state:active)")
    page_size: int | None = Field(default=None, description="Number of incidents per page (default 10)")
    page_offset: int | None = Field(default=None, description="Offset for pagination")


class SearchLogsInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    query: str = Field(default="*", description="Search query following log search syntax (e.g. service:web-app status:error)")
    from_time: str | None = Field(default=None, description="Minimum timestamp; supports date math (now-15m), ISO-8601, or epoch ms")
    to_time: str | None = Field(default=None, description="Maximum timestamp; supports date math (now), ISO-8601, or epoch ms")
    indexes: list[str] | None = Field(default=None, description="List of log index names to search")
    limit: int | None = Field(default=None, description="Maximum number of logs to return (default 10, max 1000)")
    sort: str | None = Field(default=None, description="Sort order: -timestamp (newest first) or timestamp (oldest first)")


class SearchMetricsInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    host: str | None = Field(default=None, description="Filter metrics by host name")


class SearchMonitorsInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    query: str | None = Field(default=None, description="Filter monitors by name, tag, or attributes")
    tags: str | None = Field(default=None, description="Comma-separated list of tags (e.g. env:prod,team:backend)")
    page: int | None = Field(default=None, description="Page number to return (0-indexed)")
    page_size: int | None = Field(default=None, description="Number of monitors per page (default 100)")


class SearchServicesInput(BaseModel):
    api_key: str = Field(description="Datadog API key")
    application_key: str = Field(description="Datadog Application key")
    region: str = Field(description="The regional site for the Datadog account (e.g. datadoghq.com)")
    page_size: int | None = Field(default=None, description="Number of services per page (default 10)")
    page_number: int | None = Field(default=None, description="Page number (0-indexed)")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=GetAccountInfoInput)
@serialize_pydantic_return
async def get_account_info(
    api_key: str,
    application_key: str,
) -> GetAccountInfoOutput:
    """Detect the Datadog region for the connected account by validating the API key across all regions."""
    if not api_key or not api_key.strip():
        return GetAccountInfoOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for region_domain, label in _REGIONS:
                try:
                    response = await client.get(
                        f"https://api.{region_domain}/api/v1/validate",
                        headers={"DD-API-KEY": api_key},
                    )
                    if response.status_code == 200:
                        return GetAccountInfoOutput(
                            success=True,
                            region=region_domain,
                            label=label,
                            api_url=f"https://api.{region_domain}",
                        )
                except httpx.RequestError:
                    continue
    except httpx.TimeoutException:
        return GetAccountInfoOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAccountInfoOutput(success=False, error=f"Call failed: {exc}")
    return GetAccountInfoOutput(
        success=False,
        error="Could not validate API key against any known Datadog region.",
    )


@tool(args_schema=GetMetricDataInput)
@serialize_pydantic_return
async def get_metric_data(
    api_key: str,
    application_key: str,
    region: str,
    query: str,
    from_ts: int,
    to_ts: int,
) -> GetMetricDataOutput:
    """Query time-series metric data for analyzing trends and system performance."""
    if not api_key or not api_key.strip():
        return GetMetricDataOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_api_url(region)}/v1/query",
                headers=_headers(api_key, application_key),
                params={"query": query, "from": from_ts, "to": to_ts},
            )
        if response.status_code != 200:
            return GetMetricDataOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMetricDataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMetricDataOutput(success=False, error=f"Call failed: {exc}")
    return GetMetricDataOutput(
        success=True,
        series=data.get("series", []),
        from_date=data.get("from_date"),
        to_date=data.get("to_date"),
        query=data.get("query"),
    )


@tool(args_schema=PostMetricDataInput)
@serialize_pydantic_return
async def post_metric_data(
    api_key: str,
    application_key: str,
    region: str,
    metric: str,
    points: dict[str, float],
) -> PostMetricDataOutput:
    """Post custom time-series metric data points to Datadog."""
    if not api_key or not api_key.strip():
        return PostMetricDataOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    series_points = [
        {"timestamp": int(ts), "value": val}
        for ts, val in points.items()
    ]
    payload = {
        "series": [
            {
                "metric": metric,
                "type": 0,
                "points": series_points,
            }
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_api_url(region)}/v2/series",
                headers=_headers(api_key, application_key),
                json=payload,
            )
        if response.status_code not in (200, 202):
            return PostMetricDataOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PostMetricDataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PostMetricDataOutput(success=False, error=f"Call failed: {exc}")
    return PostMetricDataOutput(
        success=True,
        errors=data.get("errors", []),
    )


@tool(args_schema=SearchDashboardsInput)
@serialize_pydantic_return
async def search_dashboards(
    api_key: str,
    application_key: str,
    region: str,
    filter_shared: bool | None = None,
    count: int | None = None,
    start: int | None = None,
) -> SearchDashboardsOutput:
    """List and search Datadog dashboards with their IDs, titles, and URLs."""
    if not api_key or not api_key.strip():
        return SearchDashboardsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {}
    if filter_shared is not None:
        params["filter[shared]"] = str(filter_shared).lower()
    if count is not None:
        params["count"] = count
    if start is not None:
        params["start"] = start
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_api_url(region)}/v1/dashboard",
                headers=_headers(api_key, application_key),
                params=params,
            )
        if response.status_code != 200:
            return SearchDashboardsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchDashboardsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchDashboardsOutput(success=False, error=f"Call failed: {exc}")
    return SearchDashboardsOutput(
        success=True,
        dashboards=data.get("dashboards", []),
    )


@tool(args_schema=SearchEventsInput)
@serialize_pydantic_return
async def search_events(
    api_key: str,
    application_key: str,
    region: str,
    start: int | None = None,
    end: int | None = None,
    priority: str | None = None,
    sources: str | None = None,
    tags: str | None = None,
) -> SearchEventsOutput:
    """Search Datadog events including monitor state changes, deployment markers, and error spikes."""
    if not api_key or not api_key.strip():
        return SearchEventsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    now = int(time.time())
    effective_end = end if end is not None else now
    effective_start = start if start is not None else now - 86400
    params: dict[str, Any] = {
        "start": effective_start,
        "end": effective_end,
    }
    if priority:
        params["priority"] = priority
    if sources:
        params["sources"] = sources
    if tags:
        params["tags"] = tags
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_api_url(region)}/v1/events",
                headers=_headers(api_key, application_key),
                params=params,
            )
        if response.status_code != 200:
            return SearchEventsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchEventsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchEventsOutput(success=False, error=f"Call failed: {exc}")
    return SearchEventsOutput(
        success=True,
        events=data.get("events", []),
    )


@tool(args_schema=SearchHostsInput)
@serialize_pydantic_return
async def search_hosts(
    api_key: str,
    application_key: str,
    region: str,
    filter: str | None = None,
    sort_field: str | None = None,
    sort_dir: str | None = None,
    count: int | None = None,
) -> SearchHostsOutput:
    """Search monitored infrastructure hosts with filtering by tag, name, or partial match."""
    if not api_key or not api_key.strip():
        return SearchHostsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {}
    if filter:
        params["filter"] = filter
    if sort_field:
        params["sort_field"] = sort_field
    if sort_dir:
        params["sort_dir"] = sort_dir
    if count is not None:
        params["count"] = count
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_api_url(region)}/v1/hosts",
                headers=_headers(api_key, application_key),
                params=params,
            )
        if response.status_code != 200:
            return SearchHostsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchHostsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchHostsOutput(success=False, error=f"Call failed: {exc}")
    return SearchHostsOutput(
        success=True,
        host_list=data.get("host_list", []),
        total_matching=data.get("total_matching"),
    )


@tool(args_schema=SearchIncidentsInput)
@serialize_pydantic_return
async def search_incidents(
    api_key: str,
    application_key: str,
    region: str,
    query: str | None = None,
    page_size: int | None = None,
    page_offset: int | None = None,
) -> SearchIncidentsOutput:
    """Search Datadog incidents by state, severity, and metadata."""
    if not api_key or not api_key.strip():
        return SearchIncidentsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {}
    if query:
        params["filter[query]"] = query
    if page_size is not None:
        params["page[size]"] = page_size
    if page_offset is not None:
        params["page[offset]"] = page_offset
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_api_url(region)}/v2/incidents",
                headers=_headers(api_key, application_key),
                params=params,
            )
        if response.status_code != 200:
            return SearchIncidentsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchIncidentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchIncidentsOutput(success=False, error=f"Call failed: {exc}")
    return SearchIncidentsOutput(
        success=True,
        incidents=data.get("data", []),
    )


@tool(args_schema=SearchLogsInput)
@serialize_pydantic_return
async def search_logs(
    api_key: str,
    application_key: str,
    region: str,
    query: str = "*",
    from_time: str | None = None,
    to_time: str | None = None,
    indexes: list[str] | None = None,
    limit: int | None = None,
    sort: str | None = None,
) -> SearchLogsOutput:
    """Search Datadog logs matching a query with support for facets and time ranges."""
    if not api_key or not api_key.strip():
        return SearchLogsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {
        "filter": {"query": query},
    }
    if from_time or to_time:
        time_range: dict[str, str] = {}
        if from_time:
            time_range["from"] = from_time
        if to_time:
            time_range["to"] = to_time
        body["filter"]["from"] = time_range.get("from", "now-15m")
        body["filter"]["to"] = time_range.get("to", "now")
    if indexes:
        body["filter"]["indexes"] = indexes
    if limit is not None:
        body["page"] = {"limit": limit}
    if sort:
        body["sort"] = sort
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_api_url(region)}/v2/logs/events/search",
                headers=_headers(api_key, application_key),
                json=body,
            )
        if response.status_code != 200:
            return SearchLogsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchLogsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchLogsOutput(success=False, error=f"Call failed: {exc}")
    return SearchLogsOutput(
        success=True,
        logs=data.get("data", []),
    )


@tool(args_schema=SearchMetricsInput)
@serialize_pydantic_return
async def search_metrics(
    api_key: str,
    application_key: str,
    region: str,
    host: str | None = None,
) -> SearchMetricsOutput:
    """List available Datadog metric names, optionally filtered by host."""
    if not api_key or not api_key.strip():
        return SearchMetricsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {"from": "1"}
    if host:
        params["host"] = host
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_api_url(region)}/v1/metrics",
                headers=_headers(api_key, application_key),
                params=params,
            )
        if response.status_code != 200:
            return SearchMetricsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchMetricsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchMetricsOutput(success=False, error=f"Call failed: {exc}")
    return SearchMetricsOutput(
        success=True,
        metrics=data.get("metrics", []),
    )


@tool(args_schema=SearchMonitorsInput)
@serialize_pydantic_return
async def search_monitors(
    api_key: str,
    application_key: str,
    region: str,
    query: str | None = None,
    tags: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> SearchMonitorsOutput:
    """Search Datadog monitors (alerting rules) including status, thresholds, and conditions."""
    if not api_key or not api_key.strip():
        return SearchMonitorsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {}
    if query:
        params["query"] = query
    if tags:
        params["monitor_tags"] = tags
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["page_size"] = page_size
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_api_url(region)}/v1/monitor",
                headers=_headers(api_key, application_key),
                params=params,
            )
        if response.status_code != 200:
            return SearchMonitorsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchMonitorsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchMonitorsOutput(success=False, error=f"Call failed: {exc}")
    monitors = data if isinstance(data, list) else data.get("monitors", [])
    return SearchMonitorsOutput(
        success=True,
        monitors=monitors,
    )


@tool(args_schema=SearchServicesInput)
@serialize_pydantic_return
async def search_services(
    api_key: str,
    application_key: str,
    region: str,
    page_size: int | None = None,
    page_number: int | None = None,
) -> SearchServicesOutput:
    """List services from Datadog Service Catalog with ownership, metadata, and team info."""
    if not api_key or not api_key.strip():
        return SearchServicesOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page[size]"] = page_size
    if page_number is not None:
        params["page[number]"] = page_number
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_api_url(region)}/v2/services/definitions",
                headers=_headers(api_key, application_key),
                params=params,
            )
        if response.status_code != 200:
            return SearchServicesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchServicesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchServicesOutput(success=False, error=f"Call failed: {exc}")
    return SearchServicesOutput(
        success=True,
        services=data.get("data", []),
    )
