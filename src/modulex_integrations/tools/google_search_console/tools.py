"""Google Search Console LangChain @tool functions."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_search_console.outputs import (
    RetrieveSitePerformanceDataOutput,
    SearchAnalyticsRow,
    SubmitUrlForIndexingOutput,
    UrlNotificationMetadata,
)

__all__ = [
    "retrieve_site_performance_data",
    "submit_url_for_indexing",
]

_SEARCH_ANALYTICS_URL = "https://searchconsole.googleapis.com/webmasters/v3/sites"
_INDEXING_URL = "https://indexing.googleapis.com/v3/urlNotifications:publish"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the upstream API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class RetrieveSitePerformanceDataInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    site_url: str = Field(description="The site URL as registered in Search Console (e.g. 'sc-domain:example.com' or 'https://example.com/')")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    dimensions: list[str] | None = Field(default=None, description="Dimensions to group results by. Allowed values: country, device, page, query, searchAppearance, date")
    search_type: str = Field(default="web", description="Type of search. Allowed values: web, image, video, news, googleNews, discover")
    aggregation_type: str | None = Field(default=None, description="Aggregation type. Allowed values: auto, byPage")
    row_limit: int = Field(default=10, description="Maximum number of rows to return")
    start_row: int | None = Field(default=None, description="Start row for pagination (zero-based)")
    subdomain_filter: str | None = Field(default=None, description="Filter results to a specific subdomain when using a domain property")
    filter_dimension: str = Field(default="page", description="Dimension to filter by when subdomain_filter is used. Allowed values: country, device, page, query")
    filter_operator: str = Field(default="contains", description="Filter operator. Allowed values: contains, equals, notContains, notEquals, includingRegex, excludingRegex")
    advanced_dimension_filters: dict[str, Any] | None = Field(default=None, description="Custom dimension filter groups following the Search Console API structure")
    data_state: str = Field(default="final", description="Data state to use. Allowed values: all, final")


class SubmitUrlForIndexingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    site_url: str = Field(description="The URL to submit for indexing (must be a canonical URL verified in Google Search Console)")
    notification_type: str = Field(default="URL_UPDATED", description="Type of notification. Allowed values: URL_UPDATED, URL_DELETED")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=RetrieveSitePerformanceDataInput)
@serialize_pydantic_return
async def retrieve_site_performance_data(
    auth_type: str,
    auth_data: dict[str, Any],
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: list[str] | None = None,
    search_type: str = "web",
    aggregation_type: str | None = None,
    row_limit: int = 10,
    start_row: int | None = None,
    subdomain_filter: str | None = None,
    filter_dimension: str = "page",
    filter_operator: str = "contains",
    advanced_dimension_filters: dict[str, Any] | None = None,
    data_state: str = "final",
) -> RetrieveSitePerformanceDataOutput:
    """Fetches search analytics from Google Search Console for a verified site"""
    if not auth_data.get("access_token"):
        return RetrieveSitePerformanceDataOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    body: dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "searchType": search_type,
        "dataState": data_state,
        "rowLimit": row_limit,
    }
    if dimensions:
        body["dimensions"] = dimensions
    if aggregation_type:
        body["aggregationType"] = aggregation_type
    if start_row is not None:
        body["startRow"] = start_row

    if advanced_dimension_filters:
        body["dimensionFilterGroups"] = [advanced_dimension_filters]
    elif subdomain_filter:
        body["dimensionFilterGroups"] = [
            {
                "filters": [
                    {
                        "dimension": filter_dimension,
                        "operator": filter_operator,
                        "expression": subdomain_filter,
                    }
                ]
            }
        ]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_SEARCH_ANALYTICS_URL}/{quote(site_url, safe='')}/searchAnalytics/query",
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return RetrieveSitePerformanceDataOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RetrieveSitePerformanceDataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RetrieveSitePerformanceDataOutput(success=False, error=f"Call failed: {exc}")

    rows = [
        SearchAnalyticsRow(
            keys=row.get("keys", []),
            clicks=row.get("clicks"),
            impressions=row.get("impressions"),
            ctr=row.get("ctr"),
            position=row.get("position"),
        )
        for row in data.get("rows", [])
    ]

    return RetrieveSitePerformanceDataOutput(
        success=True,
        rows=rows,
        response_aggregation_type=data.get("responseAggregationType"),
    )


@tool(args_schema=SubmitUrlForIndexingInput)
@serialize_pydantic_return
async def submit_url_for_indexing(
    auth_type: str,
    auth_data: dict[str, Any],
    site_url: str,
    notification_type: str = "URL_UPDATED",
) -> SubmitUrlForIndexingOutput:
    """Sends a URL update notification to the Google Indexing API"""
    if not auth_data.get("access_token"):
        return SubmitUrlForIndexingOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    body = {
        "url": site_url.strip(),
        "type": notification_type,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _INDEXING_URL,
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return SubmitUrlForIndexingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SubmitUrlForIndexingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubmitUrlForIndexingOutput(success=False, error=f"Call failed: {exc}")

    metadata = data.get("urlNotificationMetadata")
    notification_metadata = None
    if metadata:
        notification_metadata = UrlNotificationMetadata(
            url=metadata.get("url"),
            latest_update=metadata.get("latestUpdate"),
            latest_remove=metadata.get("latestRemove"),
        )

    return SubmitUrlForIndexingOutput(
        success=True,
        url_notification_metadata=notification_metadata,
    )
