"""Happy-path tests for every google_analytics @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_analytics import (
    TOOLS,
    create_ga4_property,
    create_key_event,
    list_account_options,
    list_property_options,
    manifest,
    run_report,
    run_report_in_ga4,
)
from modulex_integrations.tools.google_analytics.outputs import (
    CreateGa4PropertyOutput,
    CreateKeyEventOutput,
    ListAccountOptionsOutput,
    ListPropertyOptionsOutput,
    RunReportInGa4Output,
    RunReportOutput,
)

ADMIN = "https://analyticsadmin.googleapis.com/v1beta"
DATA = "https://analyticsdata.googleapis.com/v1beta"
REPORTING_V4 = "https://analyticsreporting.googleapis.com/v4/reports:batchGet"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_list_account_options(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: confirm the response shape against the Google Analytics Admin API
    # /v1beta/accounts docs. See:
    # https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/accounts/list
    httpx_mock.add_response(
        method="GET",
        url=f"{ADMIN}/accounts?pageSize=50",
        json={
            "accounts": [
                {
                    "name": "accounts/123456789",
                    "displayName": "Example Account",
                },
            ],
            "nextPageToken": "",
        },
    )

    result_dict = await list_account_options.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListAccountOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.accounts) == 1
    assert result.accounts[0].display_name == "Example Account"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_list_property_options(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: confirm the response shape against the Google Analytics Admin API
    # /v1beta/accountSummaries docs.
    httpx_mock.add_response(
        method="GET",
        url=f"{ADMIN}/accountSummaries",
        json={
            "accountSummaries": [
                {
                    "name": "accountSummaries/123",
                    "account": "accounts/123",
                    "displayName": "Example",
                    "propertySummaries": [
                        {
                            "property": "properties/456",
                            "displayName": "Example Property",
                            "propertyType": "PROPERTY_TYPE_ORDINARY",
                        },
                    ],
                },
            ],
        },
    )

    result_dict = await list_property_options.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListPropertyOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.properties) == 1
    assert result.properties[0].property == "properties/456"


@pytest.mark.asyncio
async def test_create_ga4_property(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: confirm the response shape against POST /v1beta/properties:
    # https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties/create
    httpx_mock.add_response(
        method="POST",
        url=f"{ADMIN}/properties",
        json={
            "name": "properties/999",
            "parent": "accounts/123",
            "displayName": "My GA4 Property",
            "industryCategory": "TECHNOLOGY",
            "timeZone": "America/Los_Angeles",
            "currencyCode": "USD",
            "propertyType": "PROPERTY_TYPE_ORDINARY",
            "createTime": "2025-01-01T00:00:00Z",
            "updateTime": "2025-01-01T00:00:00Z",
        },
        status_code=200,
    )

    result_dict = await create_ga4_property.ainvoke(
        _args(
            account="accounts/123",
            display_name="My GA4 Property",
            time_zone="America/Los_Angeles",
            industry_category="TECHNOLOGY",
            currency_code="USD",
        )
    )
    assert isinstance(result_dict, dict)
    result = CreateGa4PropertyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.property is not None
    assert result.property.name == "properties/999"


@pytest.mark.asyncio
async def test_create_key_event(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: confirm the response shape against POST /v1beta/{parent}/keyEvents:
    # https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.keyEvents/create
    httpx_mock.add_response(
        method="POST",
        url=f"{ADMIN}/properties/123/keyEvents",
        json={
            "name": "properties/123/keyEvents/abc",
            "eventName": "purchase",
            "countingMethod": "ONCE_PER_EVENT",
            "createTime": "2025-01-01T00:00:00Z",
            "deletable": True,
            "custom": False,
        },
        status_code=200,
    )

    result_dict = await create_key_event.ainvoke(
        _args(
            parent="properties/123",
            event_name="purchase",
            counting_method="ONCE_PER_EVENT",
        )
    )
    assert isinstance(result_dict, dict)
    result = CreateKeyEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.key_event is not None
    assert result.key_event.event_name == "purchase"


@pytest.mark.asyncio
async def test_run_report(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: confirm the response shape against the (legacy) Reporting API v4
    # batchGet docs:
    # https://developers.google.com/analytics/devguides/reporting/core/v4/rest/v4/reports/batchGet
    httpx_mock.add_response(
        method="POST",
        url=REPORTING_V4,
        json={
            "reports": [
                {
                    "columnHeader": {
                        "metricHeader": {
                            "metricHeaderEntries": [
                                {"name": "ga:sessions", "type": "INTEGER"},
                            ],
                        },
                    },
                    "data": {
                        "rows": [
                            {
                                "metrics": [
                                    {"values": ["10"]},
                                ],
                            },
                        ],
                        "totals": [{"values": ["10"]}],
                        "rowCount": 1,
                    },
                },
            ],
        },
    )

    result_dict = await run_report.ainvoke(
        _args(
            view_id="123456789",
            start_date="2025-01-01",
            end_date="2025-01-31",
            metrics=["ga:sessions"],
        )
    )
    assert isinstance(result_dict, dict)
    result = RunReportOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.reports) == 1


@pytest.mark.asyncio
async def test_run_report_in_ga4(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: confirm the response shape against POST
    # /v1beta/properties/{id}:runReport:
    # https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport
    httpx_mock.add_response(
        method="POST",
        url=f"{DATA}/properties/123456789:runReport",
        json={
            "dimensionHeaders": [{"name": "country"}],
            "metricHeaders": [
                {"name": "activeUsers", "type": "TYPE_INTEGER"},
            ],
            "rows": [
                {
                    "dimensionValues": [{"value": "United States"}],
                    "metricValues": [{"value": "42"}],
                },
            ],
            "totals": [
                {
                    "metricValues": [{"value": "42"}],
                },
            ],
            "rowCount": 1,
        },
    )

    result_dict = await run_report_in_ga4.ainvoke(
        _args(
            property="properties/123456789",
            start_date="2025-01-01",
            end_date="2025-01-31",
            metrics=["activeUsers"],
            dimensions=["country"],
        )
    )
    assert isinstance(result_dict, dict)
    result = RunReportInGa4Output.model_validate(result_dict)
    assert result.success is True
    assert result.row_count == 1
    assert len(result.rows) == 1


# --- Failure-path tests (Pattern B) ---------------------------------------


@pytest.mark.asyncio
async def test_run_report_in_ga4_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{DATA}/properties/123:runReport",
        status_code=401,
        text="Unauthorized",
    )
    result_dict = await run_report_in_ga4.ainvoke(
        _args(
            property="123",
            start_date="2025-01-01",
            end_date="2025-01-31",
            metrics=["activeUsers"],
        )
    )
    result = RunReportInGa4Output.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_list_account_options_missing_token() -> None:
    """Empty auth_data short-circuits before any HTTP call."""
    result_dict = await list_account_options.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}}
    )
    result = ListAccountOptionsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error
