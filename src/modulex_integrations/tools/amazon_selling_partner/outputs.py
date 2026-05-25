"""Pydantic response models for the amazon_selling_partner integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CheckFbaInventoryLevelsOutput",
    "FetchOrdersByDateRangeOutput",
    "GenerateSalesInventoryReportsOutput",
    "GetOrderDetailsOutput",
    "InventorySummary",
    "ListInboundShipmentsOutput",
    "ListMarketplaceIdOptionsOutput",
    "MarketplaceOption",
    "OptimizeProductPricingOutput",
    "RetrieveSalesPerformanceReportsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class InventorySummary(_Base):
    asin: str | None = None
    fn_sku: str | None = None
    seller_sku: str | None = None
    condition: str | None = None
    total_quantity: int | None = None
    product_name: str | None = None


class MarketplaceOption(_Base):
    label: str | None = None
    value: str | None = None


# --- Per-action output models ---------------------------------------------


class CheckFbaInventoryLevelsOutput(_Base):
    success: bool
    error: str | None = None
    inventory_summaries: list[InventorySummary] = Field(default_factory=list)


class FetchOrdersByDateRangeOutput(_Base):
    success: bool
    error: str | None = None
    orders: list[dict[str, object]] = Field(default_factory=list)


class GenerateSalesInventoryReportsOutput(_Base):
    success: bool
    error: str | None = None
    reports: list[dict[str, object]] = Field(default_factory=list)


class GetOrderDetailsOutput(_Base):
    success: bool
    error: str | None = None
    order: dict[str, object] | None = None


class ListInboundShipmentsOutput(_Base):
    success: bool
    error: str | None = None
    shipments: list[dict[str, object]] = Field(default_factory=list)


class ListMarketplaceIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    marketplaces: list[MarketplaceOption] = Field(default_factory=list)


class OptimizeProductPricingOutput(_Base):
    success: bool
    error: str | None = None
    pricing_data: list[dict[str, object]] = Field(default_factory=list)


class RetrieveSalesPerformanceReportsOutput(_Base):
    success: bool
    error: str | None = None
    order_metrics: list[dict[str, object]] = Field(default_factory=list)
