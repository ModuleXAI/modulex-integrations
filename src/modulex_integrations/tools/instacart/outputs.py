"""Pydantic response models for the Instacart integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateRecipePageOutput",
    "CreateShoppingListPageOutput",
    "GetNearbyRetailersOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateRecipePageOutput(_Base):
    success: bool
    error: str | None = None
    shareable_url: str | None = None
    title: str | None = None
    ingredient_count: int = 0
    ingredients: list[str] = Field(default_factory=list)


class CreateShoppingListPageOutput(_Base):
    success: bool
    error: str | None = None
    shareable_url: str | None = None
    title: str | None = None
    item_count: int = 0
    items: list[str] = Field(default_factory=list)


class GetNearbyRetailersOutput(_Base):
    success: bool
    error: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    retailer_count: int = 0
    # Retailers are passed through as raw dicts — Instacart's response
    # carries presentational fields (hero_image, badges, etc.) that the
    # LLM doesn't need typed, and legacy code never normalized them.
    retailers: list[dict[str, Any]] = Field(default_factory=list)
    # Fallback fields when the API endpoint fails: legacy returns a
    # store-finder URL instead of typed retailer data.
    store_finder_url: str | None = None
    message: str | None = None
