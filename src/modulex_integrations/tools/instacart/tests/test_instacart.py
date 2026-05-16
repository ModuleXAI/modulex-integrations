"""Tests for the Instacart integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.instacart import (
    TOOLS,
    create_recipe_page,
    create_shopping_list_page,
    get_nearby_retailers,
    manifest,
)
from modulex_integrations.tools.instacart.outputs import (
    CreateRecipePageOutput,
    CreateShoppingListPageOutput,
    GetNearbyRetailersOutput,
)

API = "https://www.instacart.com"


class TestManifest:
    def test_three_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_tools_match_actions(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_auth_is_modulex_key_only_with_no_test_endpoint(self) -> None:
        assert len(manifest.auth_schemas) == 1
        auth = manifest.auth_schemas[0]
        assert auth.auth_type == "modulex_key"
        # Public API: legacy declared no test_endpoint.
        assert auth.test_endpoint is None


@pytest.mark.asyncio
async def test_create_recipe_page_builds_shareable_url() -> None:
    result_dict = await create_recipe_page.ainvoke(
        {"title": "Pasta", "ingredients": ["spaghetti", "tomato sauce"]}
    )
    assert isinstance(result_dict, dict)
    result = CreateRecipePageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "Pasta"
    assert result.ingredient_count == 2
    assert result.shareable_url is not None
    assert "ingredients[]=spaghetti" in result.shareable_url


@pytest.mark.asyncio
async def test_create_recipe_page_requires_title() -> None:
    result_dict = await create_recipe_page.ainvoke({"title": "", "ingredients": ["a"]})
    result = CreateRecipePageOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "title" in result.error.lower()


@pytest.mark.asyncio
async def test_create_recipe_page_requires_ingredients() -> None:
    result_dict = await create_recipe_page.ainvoke({"title": "Pasta", "ingredients": []})
    result = CreateRecipePageOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "ingredient" in result.error.lower()


@pytest.mark.asyncio
async def test_create_shopping_list_page() -> None:
    result_dict = await create_shopping_list_page.ainvoke(
        {"title": "Weekly", "items": ["milk", "bread"], "partner_id": "p1"}
    )
    result = CreateShoppingListPageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.item_count == 2
    assert result.shareable_url is not None
    assert "partner_id=p1" in result.shareable_url


@pytest.mark.asyncio
async def test_get_nearby_retailers_hits_public_endpoint(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v3/retailers?postal_code=10001&country_code=US",
        json={
            "retailers": [
                {"id": "r1", "name": "Shop A", "slug": "shop-a"},
                {"id": "r2", "name": "Shop B", "slug": "shop-b"},
            ]
        },
    )

    result_dict = await get_nearby_retailers.ainvoke({"postal_code": "10001"})
    result = GetNearbyRetailersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.retailer_count == 2
    assert result.retailers[0]["name"] == "Shop A"


@pytest.mark.asyncio
async def test_get_nearby_retailers_falls_back_on_non_200(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v3/retailers?postal_code=10001&country_code=US",
        status_code=503,
        text="upstream error",
    )

    result_dict = await get_nearby_retailers.ainvoke({"postal_code": "10001"})
    result = GetNearbyRetailersOutput.model_validate(result_dict)
    # Legacy behavior: non-200 returns success=True with a store-finder URL.
    assert result.success is True
    assert result.store_finder_url is not None
    assert "zipcode=10001" in result.store_finder_url
