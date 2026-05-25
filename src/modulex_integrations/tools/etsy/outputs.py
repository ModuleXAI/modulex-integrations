"""Pydantic response models for the etsy integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateDraftListingProductOutput",
    "DeleteListingOutput",
    "GetListingInventoryOutput",
    "GetListingOutput",
    "InventoryProduct",
    "ListingProperty",
    "ListingResource",
    "Offering",
    "PropertyValue",
    "UpdateListingInventoryOutput",
    "UpdateListingPropertyOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class ListingResource(_Base):
    listing_id: int | None = None
    title: str | None = None
    description: str | None = None
    state: str | None = None
    url: str | None = None
    quantity: int | None = None
    price: str | None = None
    who_made: str | None = None
    when_made: str | None = None
    taxonomy_id: int | None = None
    is_supply: bool | None = None
    listing_type: str | None = None
    views: int | None = None
    num_favorers: int | None = None
    shipping_profile_id: int | None = None


class PropertyValue(_Base):
    property_id: int | None = None
    property_name: str | None = None
    value_ids: list[int] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)


class Offering(_Base):
    offering_id: int | None = None
    price: str | None = None
    quantity: int | None = None
    is_enabled: bool | None = None


class InventoryProduct(_Base):
    product_id: int | None = None
    sku: str | None = None
    property_values: list[PropertyValue] = Field(default_factory=list)
    offerings: list[Offering] = Field(default_factory=list)


class ListingProperty(_Base):
    property_id: int | None = None
    property_name: str | None = None
    scale_id: int | None = None
    value_ids: list[int] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)


# --- Per-action output models ---------------------------------------------


class CreateDraftListingProductOutput(_Base):
    success: bool
    listing: ListingResource | None = None


class DeleteListingOutput(_Base):
    success: bool
    listing_id: str | None = None


class GetListingOutput(_Base):
    success: bool
    listing: ListingResource | None = None


class GetListingInventoryOutput(_Base):
    success: bool
    products: list[InventoryProduct] = Field(default_factory=list)
    price_on_property: list[int] = Field(default_factory=list)
    quantity_on_property: list[int] = Field(default_factory=list)
    sku_on_property: list[int] = Field(default_factory=list)


class UpdateListingInventoryOutput(_Base):
    success: bool
    products: list[InventoryProduct] = Field(default_factory=list)
    price_on_property: list[int] = Field(default_factory=list)
    quantity_on_property: list[int] = Field(default_factory=list)
    sku_on_property: list[int] = Field(default_factory=list)


class UpdateListingPropertyOutput(_Base):
    success: bool
    listing_property: ListingProperty | None = None
