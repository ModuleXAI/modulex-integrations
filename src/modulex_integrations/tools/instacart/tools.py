"""Instacart LangChain ``@tool`` functions.

Public Instacart integration: no API key required for any of the three
actions (the api_key parameter is accepted for signature uniformity
but ignored). Two of the actions build shareable URLs without any
HTTP call; ``get_nearby_retailers`` calls Instacart's public retailer
endpoint and falls back to a store-finder URL on errors.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.instacart.outputs import (
    CreateRecipePageOutput,
    CreateShoppingListPageOutput,
    GetNearbyRetailersOutput,
)

__all__ = [
    "create_recipe_page",
    "create_shopping_list_page",
    "get_nearby_retailers",
]

_INSTACART_URL = "https://www.instacart.com"
_REQUEST_TIMEOUT = 30.0


class CreateRecipePageInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    title: str = Field(description="The title of the recipe")
    ingredients: list[str] = Field(description="List of ingredients for the recipe")
    instructions: str | None = Field(default=None, description="Recipe instructions")
    servings: int | None = Field(default=None, description="Number of servings")
    image_url: str | None = Field(default=None, description="URL to recipe image")
    source_url: str | None = Field(default=None, description="Original recipe source URL")
    partner_id: str | None = Field(default=None, description="Partner ID for tracking")


class CreateShoppingListPageInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    title: str = Field(description="The title of the shopping list")
    items: list[str] = Field(description="List of items to add to the shopping list")
    partner_id: str | None = Field(default=None, description="Partner ID for tracking")


class GetNearbyRetailersInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    postal_code: str = Field(description="Postal/ZIP code to search near")
    country_code: str = Field(default="US", description="Country code (US, CA)")


@tool(args_schema=CreateRecipePageInput)
@serialize_pydantic_return
async def create_recipe_page(
    title: str,
    ingredients: list[str],
    api_key: str | None = None,
    instructions: str | None = None,
    servings: int | None = None,
    image_url: str | None = None,
    source_url: str | None = None,
    partner_id: str | None = None,
) -> CreateRecipePageOutput:
    """Create a Recipe Page on Instacart and return a shareable URL."""
    if not title or not title.strip():
        return CreateRecipePageOutput(success=False, error="Recipe title is required")
    if not ingredients:
        return CreateRecipePageOutput(success=False, error="At least one ingredient is required")

    ingredient_params = "&".join(f"ingredients[]={ing}" for ing in ingredients)
    shareable_url = f"{_INSTACART_URL}/store/recipes/new?title={title}&{ingredient_params}"
    if partner_id:
        shareable_url += f"&partner_id={partner_id}"

    return CreateRecipePageOutput(
        success=True,
        shareable_url=shareable_url,
        title=title,
        ingredient_count=len(ingredients),
        ingredients=ingredients,
    )


@tool(args_schema=CreateShoppingListPageInput)
@serialize_pydantic_return
async def create_shopping_list_page(
    title: str,
    items: list[str],
    api_key: str | None = None,
    partner_id: str | None = None,
) -> CreateShoppingListPageOutput:
    """Create a Shopping List Page on Instacart and return a shareable URL."""
    if not title or not title.strip():
        return CreateShoppingListPageOutput(
            success=False, error="Shopping list title is required"
        )
    if not items:
        return CreateShoppingListPageOutput(success=False, error="At least one item is required")

    item_params = "&".join(f"items[]={item}" for item in items)
    shareable_url = f"{_INSTACART_URL}/store/shopping_list/new?title={title}&{item_params}"
    if partner_id:
        shareable_url += f"&partner_id={partner_id}"

    return CreateShoppingListPageOutput(
        success=True,
        shareable_url=shareable_url,
        title=title,
        item_count=len(items),
        items=items,
    )


@tool(args_schema=GetNearbyRetailersInput)
@serialize_pydantic_return
async def get_nearby_retailers(
    postal_code: str,
    country_code: str = "US",
    api_key: str | None = None,
) -> GetNearbyRetailersOutput:
    """Get nearby retailers available on Instacart by postal code."""
    if not postal_code or not postal_code.strip():
        return GetNearbyRetailersOutput(success=False, error="Postal code is required")

    headers = {"Accept": "application/json", "User-Agent": "ModuleX/1.0"}
    fallback_url = f"{_INSTACART_URL}/store?zipcode={postal_code}"

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{_INSTACART_URL}/v3/retailers",
                params={"postal_code": postal_code, "country_code": country_code},
                headers=headers,
            )
        if response.status_code == 200:
            data = response.json()
            retailers: list[dict[str, Any]] = data.get("retailers") or []
            return GetNearbyRetailersOutput(
                success=True,
                postal_code=postal_code,
                country_code=country_code,
                retailer_count=len(retailers),
                retailers=retailers,
            )
        # Non-200 from public API: legacy returns the store-finder URL
        # as a usable fallback rather than failing.
        return GetNearbyRetailersOutput(
            success=True,
            postal_code=postal_code,
            country_code=country_code,
            store_finder_url=fallback_url,
            message="Use the store finder URL to browse available retailers in your area",
        )
    except httpx.TimeoutException:
        return GetNearbyRetailersOutput(
            success=True,
            postal_code=postal_code,
            country_code=country_code,
            store_finder_url=fallback_url,
            message="Use the store finder URL to browse available retailers in your area",
        )
    except Exception as exc:
        return GetNearbyRetailersOutput(
            success=False, error=f"Failed to get nearby retailers: {exc}"
        )
