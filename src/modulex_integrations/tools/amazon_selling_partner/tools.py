"""Amazon Selling Partner LangChain @tool functions."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.amazon_selling_partner.outputs import (
    CheckFbaInventoryLevelsOutput,
    FetchOrdersByDateRangeOutput,
    GenerateSalesInventoryReportsOutput,
    GetOrderDetailsOutput,
    InventorySummary,
    ListInboundShipmentsOutput,
    ListMarketplaceIdOptionsOutput,
    MarketplaceOption,
    OptimizeProductPricingOutput,
    RetrieveSalesPerformanceReportsOutput,
)

__all__ = [
    "check_fba_inventory_levels",
    "fetch_orders_by_date_range",
    "generate_sales_inventory_reports",
    "get_order_details",
    "list_inbound_shipments",
    "list_marketplace_id_options",
    "optimize_product_pricing",
    "retrieve_sales_performance_reports",
]

_BASE_URL = "https://sellingpartnerapi-na.amazon.com"

_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the SP-API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["x-amz-access-token"] = access_token
    return headers


# --- Input schemas --------------------------------------------------------


class CheckFbaInventoryLevelsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    marketplace_id: str = Field(description="The Amazon Marketplace ID (e.g. ATVPDKIKX0DER for US)")
    details: bool = Field(default=False, description="Set to true to return additional summarized inventory details")
    start_date_time: str | None = Field(default=None, description="A start date and time in ISO8601 format")
    seller_skus: list[str] | None = Field(default=None, description="A list of seller SKUs (up to 50)")


class FetchOrdersByDateRangeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    marketplace_id: str = Field(description="The Amazon Marketplace ID")
    created_after: str = Field(description="Fetch orders created after this ISO date")
    created_before: str | None = Field(default=None, description="Fetch orders created before this ISO date")
    buyer_email: str | None = Field(default=None, description="The email address of a buyer")
    amazon_order_id: str | None = Field(default=None, description="An order identifier specified by the seller")


class GenerateSalesInventoryReportsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    report_types: list[str] = Field(description="A list of report types used to filter reports")
    marketplace_id: str | None = Field(default=None, description="The Amazon Marketplace ID")
    processing_statuses: list[str] | None = Field(default=None, description="A list of processing statuses. Valid values: CANCELLED, DONE, FATAL, IN_PROGRESS, IN_QUEUE")
    created_since: str | None = Field(default=None, description="Earliest report creation date in ISO 8601 format")
    created_until: str | None = Field(default=None, description="Latest report creation date in ISO 8601 format")


class GetOrderDetailsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    marketplace_id: str = Field(description="The Amazon Marketplace ID")
    amazon_order_id: str = Field(description="The Amazon order ID to fetch details for")


class ListInboundShipmentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    marketplace_id: str = Field(description="The Amazon Marketplace ID")
    status: list[str] = Field(description="Filter by status. Valid values: WORKING, SHIPPED, RECEIVING, CANCELLED, DELETED, CLOSED, ERROR, IN_TRANSIT, DELIVERED, CHECKED_IN")
    last_updated_after: str | None = Field(default=None, description="Filter shipments updated after this date")
    last_updated_before: str | None = Field(default=None, description="Filter shipments updated before this date")


class ListMarketplaceIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class OptimizeProductPricingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    marketplace_id: str = Field(description="The Amazon Marketplace ID")
    item_type: str = Field(description="Whether ASIN or SKU values are used. Valid values: Asin, Sku")
    values: list[str] = Field(description="A list of ASINs or seller SKUs (up to 20)")
    customer_type: str = Field(description="Filters by customer type. Valid values: Consumer, Business")


class RetrieveSalesPerformanceReportsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    marketplace_id: str = Field(description="The Amazon Marketplace ID")
    interval: str = Field(description="Time interval as two ISO8601 dates separated by --")
    granularity: str = Field(description="Grouping granularity. Valid values: Hour, Day, Week, Month, Year, Total")
    granularity_time_zone: str | None = Field(default=None, description="IANA time zone for day boundary")
    buyer_type: str | None = Field(default=None, description="Filter by buyer type. Valid values: All, B2B, B2C")
    fulfillment_network: str | None = Field(default=None, description="Filter by fulfillment network. Valid values: MFN, AFN")
    first_day_of_week: str | None = Field(default=None, description="Week start day when granularity=Week. Valid values: Monday, Sunday")
    asin: str | None = Field(default=None, description="Filter by ASIN. Cannot be used with sku.")
    sku: str | None = Field(default=None, description="Filter by SKU. Cannot be used with asin.")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CheckFbaInventoryLevelsInput)
@serialize_pydantic_return
async def check_fba_inventory_levels(
    auth_type: str,
    auth_data: dict[str, Any],
    marketplace_id: str,
    details: bool = False,
    start_date_time: str | None = None,
    seller_skus: list[str] | None = None,
) -> CheckFbaInventoryLevelsOutput:
    """Retrieves inventory summaries from Amazon fulfillment centers to monitor stock availability"""
    if not auth_data.get("access_token"):
        return CheckFbaInventoryLevelsOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {
        "details": str(details).lower(),
        "granularityType": "Marketplace",
        "granularityId": marketplace_id,
        "marketplaceIds": marketplace_id,
    }
    if start_date_time:
        params["startDateTime"] = start_date_time
    if seller_skus:
        params["sellerSkus"] = ",".join(seller_skus)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/fba/inventory/v1/summaries",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return CheckFbaInventoryLevelsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CheckFbaInventoryLevelsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CheckFbaInventoryLevelsOutput(success=False, error=f"Call failed: {exc}")

    summaries = data.get("payload", {}).get("inventorySummaries", [])
    return CheckFbaInventoryLevelsOutput(
        success=True,
        inventory_summaries=[
            InventorySummary(
                asin=s.get("asin"),
                fn_sku=s.get("fnSku"),
                seller_sku=s.get("sellerSku"),
                condition=s.get("condition"),
                total_quantity=s.get("inventoryDetails", {}).get("fulfillableQuantity") if details else None,
                product_name=s.get("productName"),
            )
            for s in summaries
        ],
    )


@tool(args_schema=FetchOrdersByDateRangeInput)
@serialize_pydantic_return
async def fetch_orders_by_date_range(
    auth_type: str,
    auth_data: dict[str, Any],
    marketplace_id: str,
    created_after: str,
    created_before: str | None = None,
    buyer_email: str | None = None,
    amazon_order_id: str | None = None,
) -> FetchOrdersByDateRangeOutput:
    """Retrieves a list of orders based on a specified date range, buyer email, or order ID"""
    if not auth_data.get("access_token"):
        return FetchOrdersByDateRangeOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {
        "MarketplaceIds": marketplace_id,
        "CreatedAfter": created_after,
    }
    if created_before:
        params["CreatedBefore"] = created_before
    if buyer_email:
        params["BuyerEmail"] = buyer_email
    if amazon_order_id:
        params["AmazonOrderId"] = amazon_order_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/orders/v0/orders",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return FetchOrdersByDateRangeOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return FetchOrdersByDateRangeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FetchOrdersByDateRangeOutput(success=False, error=f"Call failed: {exc}")

    orders = data.get("payload", {}).get("Orders", [])
    return FetchOrdersByDateRangeOutput(success=True, orders=orders)


@tool(args_schema=GenerateSalesInventoryReportsInput)
@serialize_pydantic_return
async def generate_sales_inventory_reports(
    auth_type: str,
    auth_data: dict[str, Any],
    report_types: list[str],
    marketplace_id: str | None = None,
    processing_statuses: list[str] | None = None,
    created_since: str | None = None,
    created_until: str | None = None,
) -> GenerateSalesInventoryReportsOutput:
    """Requests reports on sales, inventory, and fulfillment performance"""
    if not auth_data.get("access_token"):
        return GenerateSalesInventoryReportsOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {
        "reportTypes": ",".join(report_types),
    }
    if marketplace_id:
        params["marketplaceIds"] = marketplace_id
    if processing_statuses:
        params["processingStatuses"] = ",".join(processing_statuses)
    if created_since:
        params["createdSince"] = created_since
    if created_until:
        params["createdUntil"] = created_until
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/reports/2021-06-30/reports",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return GenerateSalesInventoryReportsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GenerateSalesInventoryReportsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GenerateSalesInventoryReportsOutput(success=False, error=f"Call failed: {exc}")

    reports = data.get("reports", [])
    return GenerateSalesInventoryReportsOutput(success=True, reports=reports)


@tool(args_schema=GetOrderDetailsInput)
@serialize_pydantic_return
async def get_order_details(
    auth_type: str,
    auth_data: dict[str, Any],
    marketplace_id: str,
    amazon_order_id: str,
) -> GetOrderDetailsOutput:
    """Fetches detailed information about a specific order using its order ID"""
    if not auth_data.get("access_token"):
        return GetOrderDetailsOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/orders/v0/orders/{quote(amazon_order_id, safe='')}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetOrderDetailsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetOrderDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrderDetailsOutput(success=False, error=f"Call failed: {exc}")

    order = data.get("payload", data)
    return GetOrderDetailsOutput(success=True, order=order)


@tool(args_schema=ListInboundShipmentsInput)
@serialize_pydantic_return
async def list_inbound_shipments(
    auth_type: str,
    auth_data: dict[str, Any],
    marketplace_id: str,
    status: list[str],
    last_updated_after: str | None = None,
    last_updated_before: str | None = None,
) -> ListInboundShipmentsOutput:
    """Fetches inbound shipment details to track stock movement and replenishment"""
    if not auth_data.get("access_token"):
        return ListInboundShipmentsOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {
        "MarketplaceId": marketplace_id,
        "ShipmentStatusList": ",".join(status),
        "QueryType": "SHIPMENT",
    }
    if last_updated_after:
        params["LastUpdatedAfter"] = last_updated_after
    if last_updated_before:
        params["LastUpdatedBefore"] = last_updated_before
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/fba/inbound/v0/shipments",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListInboundShipmentsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListInboundShipmentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListInboundShipmentsOutput(success=False, error=f"Call failed: {exc}")

    shipments = data.get("payload", {}).get("ShipmentData", [])
    return ListInboundShipmentsOutput(success=True, shipments=shipments)


@tool(args_schema=ListMarketplaceIdOptionsInput)
@serialize_pydantic_return
async def list_marketplace_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListMarketplaceIdOptionsOutput:
    """Retrieves available marketplace participation options for the authenticated seller"""
    if not auth_data.get("access_token"):
        return ListMarketplaceIdOptionsOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/sellers/v1/marketplaceParticipations",
                headers=headers,
            )
        if response.status_code != 200:
            return ListMarketplaceIdOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListMarketplaceIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMarketplaceIdOptionsOutput(success=False, error=f"Call failed: {exc}")

    payload = data.get("payload", [])
    marketplaces = [
        MarketplaceOption(
            label=item.get("marketplace", {}).get("name"),
            value=item.get("marketplace", {}).get("id"),
        )
        for item in payload
    ]
    return ListMarketplaceIdOptionsOutput(success=True, marketplaces=marketplaces)


@tool(args_schema=OptimizeProductPricingInput)
@serialize_pydantic_return
async def optimize_product_pricing(
    auth_type: str,
    auth_data: dict[str, Any],
    marketplace_id: str,
    item_type: str,
    values: list[str],
    customer_type: str,
) -> OptimizeProductPricingOutput:
    """Retrieves competitive pricing data to adjust product prices dynamically based on market trends"""
    if not auth_data.get("access_token"):
        return OptimizeProductPricingOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {
        "MarketplaceId": marketplace_id,
        "ItemType": item_type,
        "CustomerType": customer_type,
    }
    values_key = "Asins" if item_type == "Asin" else "Skus"
    params[values_key] = ",".join(values)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/products/pricing/v0/competitivePrice",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return OptimizeProductPricingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return OptimizeProductPricingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return OptimizeProductPricingOutput(success=False, error=f"Call failed: {exc}")

    pricing_data = data.get("payload", [])
    return OptimizeProductPricingOutput(success=True, pricing_data=pricing_data)


@tool(args_schema=RetrieveSalesPerformanceReportsInput)
@serialize_pydantic_return
async def retrieve_sales_performance_reports(
    auth_type: str,
    auth_data: dict[str, Any],
    marketplace_id: str,
    interval: str,
    granularity: str,
    granularity_time_zone: str | None = None,
    buyer_type: str | None = None,
    fulfillment_network: str | None = None,
    first_day_of_week: str | None = None,
    asin: str | None = None,
    sku: str | None = None,
) -> RetrieveSalesPerformanceReportsOutput:
    """Fetches sales order metrics for visualization in dashboarding tools"""
    if not auth_data.get("access_token"):
        return RetrieveSalesPerformanceReportsOutput(success=False, error="Missing OAuth access token.")
    if asin and sku:
        return RetrieveSalesPerformanceReportsOutput(
            success=False,
            error="Cannot specify both asin and sku at the same time.",
        )
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {
        "marketplaceIds": marketplace_id,
        "interval": interval,
        "granularity": granularity,
    }
    if granularity_time_zone:
        params["granularityTimeZone"] = granularity_time_zone
    if buyer_type:
        params["buyerType"] = buyer_type
    if fulfillment_network:
        params["fulfillmentNetwork"] = fulfillment_network
    if first_day_of_week:
        params["firstDayOfWeek"] = first_day_of_week
    if asin:
        params["asin"] = asin
    if sku:
        params["sku"] = sku
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/sales/v1/orderMetrics",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return RetrieveSalesPerformanceReportsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RetrieveSalesPerformanceReportsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RetrieveSalesPerformanceReportsOutput(success=False, error=f"Call failed: {exc}")

    order_metrics = data.get("payload", [])
    return RetrieveSalesPerformanceReportsOutput(success=True, order_metrics=order_metrics)
