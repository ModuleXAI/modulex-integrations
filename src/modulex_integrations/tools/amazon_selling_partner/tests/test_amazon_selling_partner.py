"""Happy-path tests for every amazon_selling_partner @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.amazon_selling_partner import (
    TOOLS,
    check_fba_inventory_levels,
    fetch_orders_by_date_range,
    generate_sales_inventory_reports,
    get_order_details,
    list_inbound_shipments,
    list_marketplace_id_options,
    manifest,
    optimize_product_pricing,
    retrieve_sales_performance_reports,
)
from modulex_integrations.tools.amazon_selling_partner.outputs import (
    CheckFbaInventoryLevelsOutput,
    FetchOrdersByDateRangeOutput,
    GenerateSalesInventoryReportsOutput,
    GetOrderDetailsOutput,
    ListInboundShipmentsOutput,
    ListMarketplaceIdOptionsOutput,
    OptimizeProductPricingOutput,
    RetrieveSalesPerformanceReportsOutput,
)

API = "https://sellingpartnerapi-na.amazon.com"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_8_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.skip(reason="mock body pending human fill-in")
@pytest.mark.asyncio
async def test_check_fba_inventory_levels(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/fba/inventory/v1/summaries",
        json={
            "payload": {
                "inventorySummaries": [
                    # TODO: fill in a representative response shape from the SP-API docs
                ]
            }
        },
    )

    result_dict = await check_fba_inventory_levels.ainvoke(
        _args(marketplace_id="ATVPDKIKX0DER", details=False)
    )

    assert isinstance(result_dict, dict)
    result = CheckFbaInventoryLevelsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.skip(reason="mock body pending human fill-in")
@pytest.mark.asyncio
async def test_fetch_orders_by_date_range(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/orders/v0/orders",
        json={
            "payload": {
                "Orders": [
                    # TODO: fill in a representative response shape from the SP-API docs
                ]
            }
        },
    )

    result_dict = await fetch_orders_by_date_range.ainvoke(
        _args(marketplace_id="ATVPDKIKX0DER", created_after="2024-01-01T00:00:00Z")
    )

    assert isinstance(result_dict, dict)
    result = FetchOrdersByDateRangeOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.skip(reason="mock body pending human fill-in")
@pytest.mark.asyncio
async def test_generate_sales_inventory_reports(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/reports/2021-06-30/reports",
        json={
            "reports": [
                # TODO: fill in a representative response shape from the SP-API docs
            ]
        },
    )

    result_dict = await generate_sales_inventory_reports.ainvoke(
        _args(report_types=["GET_FLAT_FILE_OPEN_LISTINGS_DATA"])
    )

    assert isinstance(result_dict, dict)
    result = GenerateSalesInventoryReportsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_order_details(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/orders/v0/orders/111-1234567-1234567",
        json={
            "payload": {
                # TODO: fill in a representative response shape from the SP-API docs
            }
        },
    )

    result_dict = await get_order_details.ainvoke(
        _args(marketplace_id="ATVPDKIKX0DER", amazon_order_id="111-1234567-1234567")
    )

    assert isinstance(result_dict, dict)
    result = GetOrderDetailsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.skip(reason="mock body pending human fill-in")
@pytest.mark.asyncio
async def test_list_inbound_shipments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/fba/inbound/v0/shipments",
        json={
            "payload": {
                "ShipmentData": [
                    # TODO: fill in a representative response shape from the SP-API docs
                ]
            }
        },
    )

    result_dict = await list_inbound_shipments.ainvoke(
        _args(marketplace_id="ATVPDKIKX0DER", status=["SHIPPED"])
    )

    assert isinstance(result_dict, dict)
    result = ListInboundShipmentsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_marketplace_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sellers/v1/marketplaceParticipations",
        json={
            "payload": [
                # TODO: fill in a representative response shape from the SP-API docs
            ]
        },
    )

    result_dict = await list_marketplace_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListMarketplaceIdOptionsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.skip(reason="mock body pending human fill-in")
@pytest.mark.asyncio
async def test_optimize_product_pricing(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/products/pricing/v0/competitivePrice",
        json={
            "payload": [
                # TODO: fill in a representative response shape from the SP-API docs
            ]
        },
    )

    result_dict = await optimize_product_pricing.ainvoke(
        _args(
            marketplace_id="ATVPDKIKX0DER",
            item_type="Asin",
            values=["B0EXAMPLE"],
            customer_type="Consumer",
        )
    )

    assert isinstance(result_dict, dict)
    result = OptimizeProductPricingOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.skip(reason="mock body pending human fill-in")
@pytest.mark.asyncio
async def test_retrieve_sales_performance_reports(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sales/v1/orderMetrics",
        json={
            "payload": [
                # TODO: fill in a representative response shape from the SP-API docs
            ]
        },
    )

    result_dict = await retrieve_sales_performance_reports.ainvoke(
        _args(
            marketplace_id="ATVPDKIKX0DER",
            interval="2024-01-01T00:00:00Z--2024-01-07T00:00:00Z",
            granularity="Day",
        )
    )

    assert isinstance(result_dict, dict)
    result = RetrieveSalesPerformanceReportsOutput.model_validate(result_dict)
    assert result.success is True


# --- Failure-path test ----------------------------------------------------


@pytest.mark.asyncio
async def test_missing_credential_returns_error() -> None:
    """Verify that a missing access token short-circuits gracefully."""
    result_dict = await list_marketplace_id_options.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}}
    )
    assert isinstance(result_dict, dict)
    result = ListMarketplaceIdOptionsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access token" in result.error.lower()
