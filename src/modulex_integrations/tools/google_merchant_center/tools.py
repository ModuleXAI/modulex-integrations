"""Google Merchant Center LangChain @tool functions."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_merchant_center.outputs import (
    CreateProductOutput,
    UpdateProductOutput,
)

__all__ = [
    "create_product",
    "update_product",
]

_BASE_URL = "https://shoppingcontent.googleapis.com/content/v2.1"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google Shopping Content API."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _get_merchant_id(auth_data: dict[str, Any]) -> str:
    """Extract merchant_id from auth_data."""
    return str(auth_data.get("merchant_id", ""))


# --- Input schemas --------------------------------------------------------


class CreateProductInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    offer_id: str = Field(description="A unique identifier for the item")
    content_language: str = Field(description="The two-letter ISO 639-1 language code for the item (e.g. 'en', 'fr', 'de')")
    target_country: str = Field(description="The CLDR territory code for the item's country of sale (e.g. 'US', 'GB', 'DE')")
    channel: str = Field(description="The item's channel: 'local' or 'online'")
    title: str | None = Field(default=None, description="Your product's name (max 150 characters)")
    description: str | None = Field(default=None, description="Your product's description (max 5000 characters)")
    additional_options: dict[str, Any] | None = Field(default=None, description="Additional product attributes as a JSON object")


class UpdateProductInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    product_id: str = Field(description="The ID of the product to update (e.g. 'online:en:US:offer123')")
    updated_values: dict[str, Any] = Field(description="Product attributes to update as a JSON object")
    update_mask: list[str] | None = Field(default=None, description="List of product attribute names to update")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateProductInput)
@serialize_pydantic_return
async def create_product(
    auth_type: str,
    auth_data: dict[str, Any],
    offer_id: str,
    content_language: str,
    target_country: str,
    channel: str,
    title: str | None = None,
    description: str | None = None,
    additional_options: dict[str, Any] | None = None,
) -> CreateProductOutput:
    """Creates a product in your Google Merchant Center account"""
    if not auth_data.get("access_token"):
        return CreateProductOutput(
            success=False,
            error="Missing or empty access_token in auth_data.",
        )
    headers = _get_auth_headers(auth_type, auth_data)
    merchant_id = _get_merchant_id(auth_data)
    if not merchant_id:
        return CreateProductOutput(
            success=False,
            error="Merchant ID is missing from auth_data. Please configure it in your credentials.",
        )

    body: dict[str, Any] = {
        "offerId": offer_id,
        "contentLanguage": content_language,
        "targetCountry": target_country,
        "channel": channel,
    }
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if additional_options:
        body.update(additional_options)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/{merchant_id}/products",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateProductOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateProductOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateProductOutput(success=False, error=f"Call failed: {exc}")

    return CreateProductOutput(success=True, data=data)


@tool(args_schema=UpdateProductInput)
@serialize_pydantic_return
async def update_product(
    auth_type: str,
    auth_data: dict[str, Any],
    product_id: str,
    updated_values: dict[str, Any],
    update_mask: list[str] | None = None,
) -> UpdateProductOutput:
    """Updates an existing product in your Google Merchant Center account"""
    if not auth_data.get("access_token"):
        return UpdateProductOutput(
            success=False,
            error="Missing or empty access_token in auth_data.",
        )
    headers = _get_auth_headers(auth_type, auth_data)
    merchant_id = _get_merchant_id(auth_data)
    if not merchant_id:
        return UpdateProductOutput(
            success=False,
            error="Merchant ID is missing from auth_data. Please configure it in your credentials.",
        )

    params: dict[str, str] = {}
    if update_mask:
        params["updateMask"] = ",".join(update_mask)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{_BASE_URL}/{merchant_id}/products/{quote(product_id, safe='')}",
                headers=headers,
                json=updated_values,
                params=params,
            )
        if response.status_code != 200:
            return UpdateProductOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateProductOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateProductOutput(success=False, error=f"Call failed: {exc}")

    return UpdateProductOutput(success=True, data=data)
