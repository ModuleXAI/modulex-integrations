"""Etsy LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.etsy.outputs import (
    CreateDraftListingProductOutput,
    DeleteListingOutput,
    GetListingInventoryOutput,
    GetListingOutput,
    InventoryProduct,
    ListingProperty,
    ListingResource,
    Offering,
    PropertyValue,
    UpdateListingInventoryOutput,
    UpdateListingPropertyOutput,
)

__all__ = [
    "create_draft_listing_product",
    "delete_listing",
    "get_listing",
    "get_listing_inventory",
    "update_listing_inventory",
    "update_listing_property",
]

_BASE_URL = "https://openapi.etsy.com/v3"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Etsy API. Requires both Bearer token and x-api-key."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        client_id = auth_data.get("oauth_client_id")
        if client_id:
            headers["x-api-key"] = client_id
    return headers


async def _get_shop_id(headers: dict[str, str]) -> str:
    """Resolve the authenticated user's primary shop ID."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_BASE_URL}/application/users/me", headers=headers)
        resp.raise_for_status()
        user = resp.json()
    user_id = user["user_id"]
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_BASE_URL}/application/users/{user_id}/shops", headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
    return str(data["results"][0]["shop_id"])


def _parse_listing(data: dict[str, Any]) -> ListingResource:
    price_obj = data.get("price") or {}
    price_str = None
    if isinstance(price_obj, dict):
        amount = price_obj.get("amount")
        divisor = price_obj.get("divisor", 100)
        if amount is not None and divisor:
            price_str = str(amount / divisor)
    elif isinstance(price_obj, (int, float)):
        price_str = str(price_obj)
    return ListingResource(
        listing_id=data.get("listing_id"),
        title=data.get("title"),
        description=data.get("description"),
        state=data.get("state"),
        url=data.get("url"),
        quantity=data.get("quantity"),
        price=price_str,
        who_made=data.get("who_made"),
        when_made=data.get("when_made"),
        taxonomy_id=data.get("taxonomy_id"),
        is_supply=data.get("is_supply"),
        listing_type=data.get("listing_type"),
        views=data.get("views"),
        num_favorers=data.get("num_favorers"),
        shipping_profile_id=data.get("shipping_profile_id"),
    )


def _parse_inventory_product(p: dict[str, Any]) -> InventoryProduct:
    return InventoryProduct(
        product_id=p.get("product_id"),
        sku=p.get("sku"),
        property_values=[
            PropertyValue(
                property_id=pv.get("property_id"),
                property_name=pv.get("property_name"),
                value_ids=pv.get("value_ids") or [],
                values=pv.get("values") or [],
            )
            for pv in (p.get("property_values") or [])
        ],
        offerings=[
            Offering(
                offering_id=o.get("offering_id"),
                price=str(o["price"]["amount"] / o["price"]["divisor"])
                if isinstance(o.get("price"), dict)
                and o["price"].get("amount") is not None
                else None,
                quantity=o.get("quantity"),
                is_enabled=o.get("is_enabled"),
            )
            for o in (p.get("offerings") or [])
        ],
    )


# --- Input schemas --------------------------------------------------------


class CreateDraftListingProductInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    quantity: int = Field(description="Number of products available for purchase")
    title: str = Field(description="The listing's title string")
    description: str = Field(description="A description of the product for sale")
    price: str = Field(description="The positive non-zero price as a decimal string")
    who_made: str = Field(
        description="Who made the product: i_did, collective, someone_else"
    )
    when_made: str = Field(
        description="Era when product was made: made_to_order, 2020_2023, 2010_2019, etc."
    )
    taxonomy_id: str = Field(description="The numerical taxonomy ID of the listing")
    is_supply: bool = Field(
        description="When true, tags the listing as a supply product"
    )
    listing_type: str = Field(description="Listing type: physical, download, both")
    shipping_profile_id: str | None = Field(
        default=None,
        description="Numeric ID of the shipping profile. Required for physical listings.",
    )


class DeleteListingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    listing_id: str = Field(description="The ID of the listing to delete")


class GetListingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    listing_id: str = Field(description="The ID of the listing to retrieve")


class GetListingInventoryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    listing_id: str = Field(
        description="The ID of the listing whose inventory to retrieve"
    )


class UpdateListingInventoryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    listing_id: str = Field(
        description="The ID of the listing whose inventory to update"
    )
    products: list[dict[str, Any]] | None = Field(
        default=None,
        description="Array of product objects with sku, property_values, and offerings",
    )
    price_on_property: list[int] | None = Field(
        default=None,
        description="Property IDs that change product prices",
    )
    quantity_on_property: list[int] | None = Field(
        default=None,
        description="Property IDs that change product quantity",
    )
    sku_on_property: list[int] | None = Field(
        default=None,
        description="Property IDs that change product SKU",
    )


class UpdateListingPropertyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    listing_id: str = Field(description="The ID of the listing")
    property_id: str = Field(description="The ID of the property to update")
    value_ids: list[int] = Field(description="Array of integer value IDs")
    values: list[str] = Field(
        description="Array of string value labels (e.g. 'Black', 'Christmas')"
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateDraftListingProductInput)
@serialize_pydantic_return
async def create_draft_listing_product(
    auth_type: str,
    auth_data: dict[str, Any],
    quantity: int,
    title: str,
    description: str,
    price: str,
    who_made: str,
    when_made: str,
    taxonomy_id: str,
    is_supply: bool,
    listing_type: str,
    shipping_profile_id: str | None = None,
) -> CreateDraftListingProductOutput:
    """Creates a physical draft listing product in a shop on Etsy."""
    headers = _get_auth_headers(auth_type, auth_data)
    shop_id = await _get_shop_id(headers)
    body: dict[str, Any] = {
        "quantity": quantity,
        "title": title,
        "description": description,
        "price": float(price),
        "who_made": who_made,
        "when_made": when_made,
        "taxonomy_id": int(taxonomy_id),
        "is_supply": is_supply,
        "type": listing_type,
    }
    if shipping_profile_id:
        body["shipping_profile_id"] = int(shipping_profile_id)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/application/shops/{shop_id}/listings",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return CreateDraftListingProductOutput(
        success=True,
        listing=_parse_listing(data),
    )


@tool(args_schema=DeleteListingInput)
@serialize_pydantic_return
async def delete_listing(
    auth_type: str,
    auth_data: dict[str, Any],
    listing_id: str,
) -> DeleteListingOutput:
    """Delete an Etsy listing by listing ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{_BASE_URL}/application/listings/{listing_id}",
            headers=headers,
        )
        response.raise_for_status()
    return DeleteListingOutput(success=True, listing_id=listing_id)


@tool(args_schema=GetListingInput)
@serialize_pydantic_return
async def get_listing(
    auth_type: str,
    auth_data: dict[str, Any],
    listing_id: str,
) -> GetListingOutput:
    """Retrieve an Etsy listing record by listing ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/application/listings/{listing_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetListingOutput(success=True, listing=_parse_listing(data))


@tool(args_schema=GetListingInventoryInput)
@serialize_pydantic_return
async def get_listing_inventory(
    auth_type: str,
    auth_data: dict[str, Any],
    listing_id: str,
) -> GetListingInventoryOutput:
    """Retrieve the inventory record for a listing by listing ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/application/listings/{listing_id}/inventory",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    products = [_parse_inventory_product(p) for p in (data.get("products") or [])]
    return GetListingInventoryOutput(
        success=True,
        products=products,
        price_on_property=data.get("price_on_property") or [],
        quantity_on_property=data.get("quantity_on_property") or [],
        sku_on_property=data.get("sku_on_property") or [],
    )


@tool(args_schema=UpdateListingInventoryInput)
@serialize_pydantic_return
async def update_listing_inventory(
    auth_type: str,
    auth_data: dict[str, Any],
    listing_id: str,
    products: list[dict[str, Any]] | None = None,
    price_on_property: list[int] | None = None,
    quantity_on_property: list[int] | None = None,
    sku_on_property: list[int] | None = None,
) -> UpdateListingInventoryOutput:
    """Update the inventory for a listing identified by listing ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if products is not None:
        body["products"] = products
    if price_on_property is not None:
        body["price_on_property"] = price_on_property
    if quantity_on_property is not None:
        body["quantity_on_property"] = quantity_on_property
    if sku_on_property is not None:
        body["sku_on_property"] = sku_on_property
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{_BASE_URL}/application/listings/{listing_id}/inventory",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    inv_products = [_parse_inventory_product(p) for p in (data.get("products") or [])]
    return UpdateListingInventoryOutput(
        success=True,
        products=inv_products,
        price_on_property=data.get("price_on_property") or [],
        quantity_on_property=data.get("quantity_on_property") or [],
        sku_on_property=data.get("sku_on_property") or [],
    )


@tool(args_schema=UpdateListingPropertyInput)
@serialize_pydantic_return
async def update_listing_property(
    auth_type: str,
    auth_data: dict[str, Any],
    listing_id: str,
    property_id: str,
    value_ids: list[int],
    values: list[str],
) -> UpdateListingPropertyOutput:
    """Update or populate the properties list defining product offerings for a listing."""
    headers = _get_auth_headers(auth_type, auth_data)
    shop_id = await _get_shop_id(headers)
    body: dict[str, Any] = {
        "value_ids": value_ids,
        "values": values,
    }
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{_BASE_URL}/application/shops/{shop_id}/listings/{listing_id}/properties/{property_id}",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return UpdateListingPropertyOutput(
        success=True,
        listing_property=ListingProperty(
            property_id=data.get("property_id"),
            property_name=data.get("property_name"),
            scale_id=data.get("scale_id"),
            value_ids=data.get("value_ids") or [],
            values=data.get("values") or [],
        ),
    )
