"""Google Ad Manager LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_ad_manager.outputs import (
    CreateReportOutput,
    ListNetworkOptionsOutput,
)

__all__ = [
    "create_report",
    "list_network_options",
]

_BASE_URL = "https://admanager.googleapis.com/v1"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google Ad Manager API."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class CreateReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    parent: str = Field(description="The parent resource. Format: networks/{networkCode}")
    name: str = Field(description="Resource name of the report. Format: networks/{networkCode}/reports/{reportId}")
    visibility: str = Field(description="Report visibility: HIDDEN, DRAFT, or SAVED")
    dimensions: list[str] = Field(description="List of dimension identifiers to report on")
    metrics: list[str] = Field(description="List of metric identifiers to report on")
    report_type: str = Field(description="Report type: REPORT_TYPE_UNSPECIFIED or HISTORICAL")
    date_range: str = Field(description="Date range type: fixed or relative")
    display_name: str | None = Field(default=None, description="Display name of the report")
    schedule_options: dict[str, Any] | None = Field(default=None, description="Schedule options for the report")
    filters: list[dict[str, Any]] | None = Field(default=None, description="Filters for this report")
    time_zone: str | None = Field(default=None, description="Time zone in IANA format")
    currency_code: str | None = Field(default=None, description="ISO 4217 currency code")
    custom_dimension_key_ids: list[str] | None = Field(default=None, description="Custom dimension key IDs")
    line_item_custom_field_ids: list[str] | None = Field(default=None, description="Line item custom field IDs")
    order_custom_field_ids: list[str] | None = Field(default=None, description="Order custom field IDs")
    creative_custom_field_ids: list[str] | None = Field(default=None, description="Creative custom field IDs")
    time_period_column: str | None = Field(default=None, description="Time period column for comparison")
    flags: list[dict[str, Any]] | None = Field(default=None, description="Flags for this report")
    sorts: list[dict[str, Any]] | None = Field(default=None, description="Sorts for this report")
    start_date_year: int | None = Field(default=None, description="Start date year (required when date_range is 'fixed')")
    start_date_month: int | None = Field(default=None, description="Start date month (required when date_range is 'fixed')")
    start_date_day: int | None = Field(default=None, description="Start date day (required when date_range is 'fixed')")
    end_date_year: int | None = Field(default=None, description="End date year (required when date_range is 'fixed')")
    end_date_month: int | None = Field(default=None, description="End date month (required when date_range is 'fixed')")
    end_date_day: int | None = Field(default=None, description="End date day (required when date_range is 'fixed')")
    relative: str | None = Field(default=None, description="Relative date range identifier (required when date_range is 'relative')")
    comparison_date_range: str | None = Field(default=None, description="Comparison date range type: fixed or relative")
    comparison_start_date_year: int | None = Field(default=None, description="Comparison start date year")
    comparison_start_date_month: int | None = Field(default=None, description="Comparison start date month")
    comparison_start_date_day: int | None = Field(default=None, description="Comparison start date day")
    comparison_end_date_year: int | None = Field(default=None, description="Comparison end date year")
    comparison_end_date_month: int | None = Field(default=None, description="Comparison end date month")
    comparison_end_date_day: int | None = Field(default=None, description="Comparison end date day")
    comparison_relative: str | None = Field(default=None, description="Relative comparison date range identifier")


class ListNetworkOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions ------------------------------------------------------


def _build_date_object(
    year: int | None, month: int | None, day: int | None,
) -> dict[str, int] | None:
    if year is None and month is None and day is None:
        return None
    result: dict[str, int] = {}
    if year is not None:
        result["year"] = year
    if month is not None:
        result["month"] = month
    if day is not None:
        result["day"] = day
    return result


@tool(args_schema=CreateReportInput)
@serialize_pydantic_return
async def create_report(
    auth_type: str,
    auth_data: dict[str, Any],
    parent: str,
    name: str,
    visibility: str,
    dimensions: list[str],
    metrics: list[str],
    report_type: str,
    date_range: str,
    display_name: str | None = None,
    schedule_options: dict[str, Any] | None = None,
    filters: list[dict[str, Any]] | None = None,
    time_zone: str | None = None,
    currency_code: str | None = None,
    custom_dimension_key_ids: list[str] | None = None,
    line_item_custom_field_ids: list[str] | None = None,
    order_custom_field_ids: list[str] | None = None,
    creative_custom_field_ids: list[str] | None = None,
    time_period_column: str | None = None,
    flags: list[dict[str, Any]] | None = None,
    sorts: list[dict[str, Any]] | None = None,
    start_date_year: int | None = None,
    start_date_month: int | None = None,
    start_date_day: int | None = None,
    end_date_year: int | None = None,
    end_date_month: int | None = None,
    end_date_day: int | None = None,
    relative: str | None = None,
    comparison_date_range: str | None = None,
    comparison_start_date_year: int | None = None,
    comparison_start_date_month: int | None = None,
    comparison_start_date_day: int | None = None,
    comparison_end_date_year: int | None = None,
    comparison_end_date_month: int | None = None,
    comparison_end_date_day: int | None = None,
    comparison_relative: str | None = None,
) -> CreateReportOutput:
    """Create a report in Google Ad Manager."""
    if not auth_data.get("access_token"):
        return CreateReportOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    report_definition: dict[str, Any] = {
        "reportType": report_type,
        "dimensions": dimensions,
        "metrics": metrics,
    }
    if filters:
        report_definition["filters"] = filters
    if time_zone:
        report_definition["timeZone"] = time_zone
    if currency_code:
        report_definition["currencyCode"] = currency_code
    if custom_dimension_key_ids:
        report_definition["customDimensionKeyIds"] = custom_dimension_key_ids
    if line_item_custom_field_ids:
        report_definition["lineItemCustomFieldIds"] = line_item_custom_field_ids
    if order_custom_field_ids:
        report_definition["orderCustomFieldIds"] = order_custom_field_ids
    if creative_custom_field_ids:
        report_definition["creativeCustomFieldIds"] = creative_custom_field_ids
    if time_period_column:
        report_definition["timePeriodColumn"] = time_period_column
    if flags:
        report_definition["flags"] = flags
    if sorts:
        report_definition["sorts"] = sorts

    date_range_obj: dict[str, Any] = {}
    if date_range == "fixed":
        start_date = _build_date_object(start_date_year, start_date_month, start_date_day)
        end_date = _build_date_object(end_date_year, end_date_month, end_date_day)
        if start_date:
            date_range_obj["fixedDateRange"] = {"startDate": start_date, "endDate": end_date}
    elif date_range == "relative":
        if relative:
            date_range_obj["relativeDateRange"] = relative

    if date_range_obj:
        report_definition["dateRange"] = date_range_obj

    comparison_obj: dict[str, Any] = {}
    if comparison_date_range == "fixed":
        comp_start = _build_date_object(comparison_start_date_year, comparison_start_date_month, comparison_start_date_day)
        comp_end = _build_date_object(comparison_end_date_year, comparison_end_date_month, comparison_end_date_day)
        if comp_start:
            comparison_obj["fixedDateRange"] = {"startDate": comp_start, "endDate": comp_end}
    elif comparison_date_range == "relative":
        if comparison_relative:
            comparison_obj["relativeDateRange"] = comparison_relative

    if comparison_obj:
        report_definition["comparisonDateRange"] = comparison_obj

    body: dict[str, Any] = {
        "name": name,
        "visibility": visibility,
        "reportDefinition": report_definition,
    }
    if display_name:
        body["displayName"] = display_name
    if schedule_options:
        body["scheduleOptions"] = schedule_options

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/{parent}/reports",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateReportOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateReportOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateReportOutput(success=False, error=f"Call failed: {exc}")

    return CreateReportOutput(success=True, data=data)


@tool(args_schema=ListNetworkOptionsInput)
@serialize_pydantic_return
async def list_network_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListNetworkOptionsOutput:
    """Retrieve available network options for Google Ad Manager."""
    if not auth_data.get("access_token"):
        return ListNetworkOptionsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/networks",
                headers=headers,
            )
        if response.status_code != 200:
            return ListNetworkOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListNetworkOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListNetworkOptionsOutput(success=False, error=f"Call failed: {exc}")

    networks = [n.get("displayName", n.get("networkCode", "")) for n in data.get("networks", [])]
    return ListNetworkOptionsOutput(success=True, networks=networks)
