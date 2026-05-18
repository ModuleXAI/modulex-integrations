"""Google Analytics LangChain @tool functions."""
from __future__ import annotations

import re
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_analytics.outputs import (
    AccountSummary,
    CreateGa4PropertyOutput,
    CreateKeyEventOutput,
    KeyEventResource,
    ListAccountOptionsOutput,
    ListPropertyOptionsOutput,
    PropertyResource,
    PropertySummary,
    RunReportInGa4Output,
    RunReportOutput,
)

__all__ = [
    "create_ga4_property",
    "create_key_event",
    "list_account_options",
    "list_property_options",
    "run_report",
    "run_report_in_ga4",
]


_ADMIN_BASE_URL = "https://analyticsadmin.googleapis.com/v1beta"
_DATA_BASE_URL = "https://analyticsdata.googleapis.com/v1beta"
_REPORTING_V4_URL = (
    "https://analyticsreporting.googleapis.com/v4/reports:batchGet"
)
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build auth + content headers for the upstream Google Analytics APIs."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _missing_token() -> str:
    return (
        "OAuth access_token missing from auth_data. "
        "Re-authenticate via the ModuleX credential UI."
    )


def _extract_property_id(value: str) -> str:
    """Accept 'properties/123' or '123'; return the numeric id only."""
    match = re.search(r"\d+", value or "")
    return match.group(0) if match else ""


# --- Input schemas --------------------------------------------------------


class ListAccountOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access_token"
    )
    page_size: int = Field(
        default=50,
        description="Max accounts to return per page (server caps at 200).",
    )
    page_token: str | None = Field(
        default=None,
        description="Optional page token from a previous response.",
    )


class ListPropertyOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access_token"
    )


class CreateGa4PropertyInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access_token"
    )
    account: str = Field(
        description="Parent account resource name, e.g. 'accounts/123456789'."
    )
    display_name: str = Field(
        description="Human-readable display name for the property (max 100 UTF-16 units)."
    )
    time_zone: str = Field(
        description="Reporting time zone (IANA tz identifier, e.g. 'America/Los_Angeles')."
    )
    industry_category: str | None = Field(
        default=None,
        description=(
            "Industry category for the property "
            "(e.g. 'TECHNOLOGY', 'FINANCE', 'SHOPPING')."
        ),
    )
    currency_code: str | None = Field(
        default=None,
        description="ISO 4217 currency code, e.g. 'USD', 'EUR', 'JPY'.",
    )


class CreateKeyEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access_token"
    )
    parent: str = Field(
        description="Parent property resource name, e.g. 'properties/123'."
    )
    event_name: str = Field(
        description="Immutable key event name, e.g. 'purchase'."
    )
    counting_method: str = Field(
        description=(
            "ONCE_PER_EVENT, ONCE_PER_SESSION, or "
            "COUNTING_METHOD_UNSPECIFIED."
        ),
    )


class RunReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access_token"
    )
    view_id: str = Field(
        description="Universal Analytics view ID (legacy reporting API v4)."
    )
    start_date: str = Field(description="Start date in YYYY-MM-DD format.")
    end_date: str = Field(description="End date in YYYY-MM-DD format.")
    metrics: list[str] = Field(
        description="Metric expression strings (e.g. ['ga:sessions'])."
    )
    dimensions: list[str] | None = Field(
        default=None,
        description="Optional dimension name strings (e.g. ['ga:country']).",
    )


class RunReportInGa4Input(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access_token"
    )
    property: str = Field(
        description="GA4 property id (numeric or 'properties/<id>' resource path)."
    )
    start_date: str = Field(description="Start date in YYYY-MM-DD format.")
    end_date: str = Field(description="End date in YYYY-MM-DD format.")
    metrics: list[str] = Field(
        description="GA4 metric names (e.g. ['activeUsers', 'screenPageViews'])."
    )
    dimensions: list[str] | None = Field(
        default=None,
        description="Optional GA4 dimension names (e.g. ['country']).",
    )
    dimension_filter: dict[str, Any] | None = Field(
        default=None,
        description="Optional GA4 FilterExpression object.",
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ListAccountOptionsInput)
@serialize_pydantic_return
async def list_account_options(
    auth_type: str,
    auth_data: dict[str, Any],
    page_size: int = 50,
    page_token: str | None = None,
) -> ListAccountOptionsOutput:
    """List Google Analytics accounts via the Admin API /accounts endpoint."""
    headers = _get_auth_headers(auth_type, auth_data)
    if "Authorization" not in headers:
        return ListAccountOptionsOutput(success=False, error=_missing_token())
    params: dict[str, Any] = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_ADMIN_BASE_URL}/accounts",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListAccountOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAccountOptionsOutput(
            success=False, error="Request timed out."
        )
    except Exception as exc:
        return ListAccountOptionsOutput(
            success=False, error=f"Call failed: {exc}"
        )

    accounts = [
        AccountSummary(
            name=a.get("name"),
            display_name=a.get("displayName"),
            account=a.get("name"),
        )
        for a in data.get("accounts", []) or []
    ]
    return ListAccountOptionsOutput(
        success=True,
        accounts=accounts,
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=ListPropertyOptionsInput)
@serialize_pydantic_return
async def list_property_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListPropertyOptionsOutput:
    """List GA4 properties by flattening propertySummaries from /accountSummaries."""
    headers = _get_auth_headers(auth_type, auth_data)
    if "Authorization" not in headers:
        return ListPropertyOptionsOutput(success=False, error=_missing_token())
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_ADMIN_BASE_URL}/accountSummaries",
                headers=headers,
            )
        if response.status_code != 200:
            return ListPropertyOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListPropertyOptionsOutput(
            success=False, error="Request timed out."
        )
    except Exception as exc:
        return ListPropertyOptionsOutput(
            success=False, error=f"Call failed: {exc}"
        )

    properties: list[PropertySummary] = []
    for summary in data.get("accountSummaries", []) or []:
        parent_account = summary.get("name") or summary.get("account")
        for prop in summary.get("propertySummaries", []) or []:
            properties.append(
                PropertySummary(
                    property=prop.get("property"),
                    display_name=prop.get("displayName"),
                    property_type=prop.get("propertyType"),
                    parent=parent_account,
                )
            )
    return ListPropertyOptionsOutput(success=True, properties=properties)


@tool(args_schema=CreateGa4PropertyInput)
@serialize_pydantic_return
async def create_ga4_property(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    display_name: str,
    time_zone: str,
    industry_category: str | None = None,
    currency_code: str | None = None,
) -> CreateGa4PropertyOutput:
    """Create a GA4 property via the Admin API (POST /properties)."""
    headers = _get_auth_headers(auth_type, auth_data)
    if "Authorization" not in headers:
        return CreateGa4PropertyOutput(success=False, error=_missing_token())
    body: dict[str, Any] = {
        "parent": account,
        "displayName": display_name,
        "timeZone": time_zone,
        "propertyType": "PROPERTY_TYPE_ORDINARY",
    }
    if industry_category is not None:
        body["industryCategory"] = industry_category
    if currency_code is not None:
        body["currencyCode"] = currency_code
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_ADMIN_BASE_URL}/properties",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateGa4PropertyOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateGa4PropertyOutput(
            success=False, error="Request timed out."
        )
    except Exception as exc:
        return CreateGa4PropertyOutput(
            success=False, error=f"Call failed: {exc}"
        )

    return CreateGa4PropertyOutput(
        success=True,
        property=PropertyResource(
            name=data.get("name"),
            parent=data.get("parent"),
            display_name=data.get("displayName"),
            industry_category=data.get("industryCategory"),
            time_zone=data.get("timeZone"),
            currency_code=data.get("currencyCode"),
            property_type=data.get("propertyType"),
            create_time=data.get("createTime"),
            update_time=data.get("updateTime"),
        ),
        raw=data,
    )


@tool(args_schema=CreateKeyEventInput)
@serialize_pydantic_return
async def create_key_event(
    auth_type: str,
    auth_data: dict[str, Any],
    parent: str,
    event_name: str,
    counting_method: str,
) -> CreateKeyEventOutput:
    """Create a GA4 key event (POST /{parent}/keyEvents)."""
    headers = _get_auth_headers(auth_type, auth_data)
    if "Authorization" not in headers:
        return CreateKeyEventOutput(success=False, error=_missing_token())
    parent_path = parent.lstrip("/")
    url = f"{_ADMIN_BASE_URL}/{parent_path}/keyEvents"
    body = {
        "eventName": event_name,
        "countingMethod": counting_method,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=body)
        if response.status_code not in (200, 201):
            return CreateKeyEventOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateKeyEventOutput(
            success=False, error="Request timed out."
        )
    except Exception as exc:
        return CreateKeyEventOutput(
            success=False, error=f"Call failed: {exc}"
        )

    return CreateKeyEventOutput(
        success=True,
        key_event=KeyEventResource(
            name=data.get("name"),
            event_name=data.get("eventName"),
            counting_method=data.get("countingMethod"),
            create_time=data.get("createTime"),
            deletable=data.get("deletable"),
            custom=data.get("custom"),
        ),
        raw=data,
    )


@tool(args_schema=RunReportInput)
@serialize_pydantic_return
async def run_report(
    auth_type: str,
    auth_data: dict[str, Any],
    view_id: str,
    start_date: str,
    end_date: str,
    metrics: list[str],
    dimensions: list[str] | None = None,
) -> RunReportOutput:
    """Run a Universal Analytics v4 batchGet report (legacy; UA was sunset July 2024)."""
    headers = _get_auth_headers(auth_type, auth_data)
    if "Authorization" not in headers:
        return RunReportOutput(success=False, error=_missing_token())
    body = {
        "reportRequests": [
            {
                "viewId": view_id,
                "dateRanges": [
                    {"startDate": start_date, "endDate": end_date},
                ],
                "dimensions": [
                    {"name": d} for d in (dimensions or [])
                ],
                "metrics": [
                    {"expression": m} for m in (metrics or [])
                ],
            },
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _REPORTING_V4_URL, headers=headers, json=body
            )
        if response.status_code != 200:
            return RunReportOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RunReportOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RunReportOutput(success=False, error=f"Call failed: {exc}")

    return RunReportOutput(
        success=True,
        reports=data.get("reports", []) or [],
        raw=data,
    )


@tool(args_schema=RunReportInGa4Input)
@serialize_pydantic_return
async def run_report_in_ga4(
    auth_type: str,
    auth_data: dict[str, Any],
    property: str,
    start_date: str,
    end_date: str,
    metrics: list[str],
    dimensions: list[str] | None = None,
    dimension_filter: dict[str, Any] | None = None,
) -> RunReportInGa4Output:
    """Run a GA4 Data API report (POST /properties/{id}:runReport)."""
    headers = _get_auth_headers(auth_type, auth_data)
    if "Authorization" not in headers:
        return RunReportInGa4Output(success=False, error=_missing_token())
    property_id = _extract_property_id(property)
    if not property_id:
        return RunReportInGa4Output(
            success=False,
            error=(
                "Could not extract numeric GA4 property id from input "
                f"{property!r}; expected 'properties/<id>' or '<id>'."
            ),
        )
    body: dict[str, Any] = {
        "dateRanges": [
            {"startDate": start_date, "endDate": end_date},
        ],
        "dimensions": [
            {"name": d} for d in (dimensions or [])
        ],
        "metrics": [
            {"name": m} for m in (metrics or [])
        ],
    }
    if dimension_filter is not None:
        body["dimensionFilter"] = dimension_filter
    url = f"{_DATA_BASE_URL}/properties/{property_id}:runReport"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=body)
        if response.status_code != 200:
            return RunReportInGa4Output(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RunReportInGa4Output(
            success=False, error="Request timed out."
        )
    except Exception as exc:
        return RunReportInGa4Output(
            success=False, error=f"Call failed: {exc}"
        )

    row_count_raw = data.get("rowCount")
    row_count: int | None
    try:
        row_count = int(row_count_raw) if row_count_raw is not None else None
    except (TypeError, ValueError):
        row_count = None

    return RunReportInGa4Output(
        success=True,
        row_count=row_count,
        dimension_headers=data.get("dimensionHeaders", []) or [],
        metric_headers=data.get("metricHeaders", []) or [],
        rows=data.get("rows", []) or [],
        totals=data.get("totals", []) or [],
        raw=data,
    )
