"""Happy-path tests for every etsy @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.etsy import (
    TOOLS,
    create_draft_listing_product,
    delete_listing,
    get_listing,
    get_listing_inventory,
    manifest,
    update_listing_inventory,
    update_listing_property,
)
from modulex_integrations.tools.etsy.outputs import (
    CreateDraftListingProductOutput,
    DeleteListingOutput,
    GetListingInventoryOutput,
    GetListingOutput,
    UpdateListingInventoryOutput,
    UpdateListingPropertyOutput,
)

API = "https://openapi.etsy.com/v3"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token", "oauth_client_id": "fake_client_id"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
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
async def test_create_draft_listing_product(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/application/users/me",
        json={"user_id": 12345},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/application/users/12345/shops",
        json={"results": [{"shop_id": 67890}]},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/application/shops/67890/listings",
        json={
            # TODO: fill in a representative Etsy listing response
            "listing_id": 111,
            "title": "Test Listing",
            "description": "A test",
            "price": {"amount": 2999, "divisor": 100, "currency_code": "USD"},
            "quantity": 1,
            "state": "draft",
            "who_made": "i_did",
            "when_made": "made_to_order",
            "taxonomy_id": 1,
            "is_supply": False,
            "listing_type": "physical",
        },
    )

    result_dict = await create_draft_listing_product.ainvoke(
        _args(
            quantity=1,
            title="Test Listing",
            description="A test",
            price="29.99",
            who_made="i_did",
            when_made="made_to_order",
            taxonomy_id="1",
            is_supply=False,
            listing_type="physical",
            shipping_profile_id="999",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateDraftListingProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.listing is not None
    assert result.listing.listing_id == 111


@pytest.mark.asyncio
async def test_delete_listing(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/application/listings/222",
        status_code=204,
        content=b"",
    )

    result_dict = await delete_listing.ainvoke(_args(listing_id="222"))

    assert isinstance(result_dict, dict)
    result = DeleteListingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.listing_id == "222"


@pytest.mark.asyncio
async def test_get_listing(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/application/listings/333",
        json={
            # TODO: fill in a representative Etsy listing response
            "listing_id": 333,
            "title": "Handmade Mug",
            "description": "A nice mug",
            "price": {"amount": 1500, "divisor": 100, "currency_code": "USD"},
            "quantity": 5,
            "state": "active",
            "who_made": "i_did",
            "when_made": "2020_2023",
            "taxonomy_id": 42,
            "is_supply": False,
            "listing_type": "physical",
            "views": 100,
            "num_favorers": 10,
        },
    )

    result_dict = await get_listing.ainvoke(_args(listing_id="333"))

    assert isinstance(result_dict, dict)
    result = GetListingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.listing is not None
    assert result.listing.listing_id == 333
    assert result.listing.title == "Handmade Mug"


@pytest.mark.asyncio
async def test_get_listing_inventory(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/application/listings/444/inventory",
        json={
            # TODO: fill in a representative Etsy inventory response
            "products": [
                {
                    "product_id": 1001,
                    "sku": "SKU-001",
                    "property_values": [],
                    "offerings": [
                        {
                            "offering_id": 2001,
                            "price": {"amount": 2000, "divisor": 100, "currency_code": "USD"},
                            "quantity": 3,
                            "is_enabled": True,
                        }
                    ],
                }
            ],
            "price_on_property": [],
            "quantity_on_property": [],
            "sku_on_property": [],
        },
    )

    result_dict = await get_listing_inventory.ainvoke(_args(listing_id="444"))

    assert isinstance(result_dict, dict)
    result = GetListingInventoryOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.products) == 1
    assert result.products[0].product_id == 1001


@pytest.mark.asyncio
async def test_update_listing_inventory(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/application/listings/555/inventory",
        json={
            # TODO: fill in a representative Etsy inventory response
            "products": [
                {
                    "product_id": 1002,
                    "sku": "SKU-002",
                    "property_values": [],
                    "offerings": [
                        {
                            "offering_id": 2002,
                            "price": {"amount": 3000, "divisor": 100, "currency_code": "USD"},
                            "quantity": 10,
                            "is_enabled": True,
                        }
                    ],
                }
            ],
            "price_on_property": [1],
            "quantity_on_property": [],
            "sku_on_property": [],
        },
    )

    result_dict = await update_listing_inventory.ainvoke(
        _args(
            listing_id="555",
            products=[{"sku": "SKU-002", "property_values": [], "offerings": [{"price": 30.0, "quantity": 10, "is_enabled": True}]}],
            price_on_property=[1],
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateListingInventoryOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.products) == 1


@pytest.mark.asyncio
async def test_update_listing_property(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/application/users/me",
        json={"user_id": 12345},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/application/users/12345/shops",
        json={"results": [{"shop_id": 67890}]},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/application/shops/67890/listings/666/properties/100",
        json={
            # TODO: fill in a representative Etsy listing property response
            "property_id": 100,
            "property_name": "Color",
            "scale_id": None,
            "value_ids": [1, 2],
            "values": ["Black", "White"],
        },
    )

    result_dict = await update_listing_property.ainvoke(
        _args(
            listing_id="666",
            property_id="100",
            value_ids=[1, 2],
            values=["Black", "White"],
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateListingPropertyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.listing_property is not None
    assert result.listing_property.property_id == 100
    assert result.listing_property.values == ["Black", "White"]
