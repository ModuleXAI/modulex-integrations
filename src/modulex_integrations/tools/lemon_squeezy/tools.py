"""Lemon Squeezy LangChain ``@tool`` functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.lemon_squeezy.outputs import (
    ListCustomersOutput,
    ListOrdersOutput,
    ListProductsOutput,
    ListStoresOutput,
    ListSubscriptionsOutput,
    RetrieveCustomerOutput,
    RetrieveOrderOutput,
    RetrieveProductOutput,
    RetrieveStoreOutput,
    RetrieveSubscriptionOutput,
)

__all__ = [
    "list_customers",
    "list_orders",
    "list_products",
    "list_stores",
    "list_subscriptions",
    "retrieve_customer",
    "retrieve_order",
    "retrieve_product",
    "retrieve_store",
    "retrieve_subscription",
]

_BASE_URL = "https://api.lemonsqueezy.com/v1"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


def _empty_key_error(name: str) -> str:
    return (
        f"Lemon Squeezy API key is empty for {name}. "
        "Please configure a valid credential."
    )


def _page_params(page: int, per_page: int) -> dict[str, Any]:
    return {"page[number]": page, "page[size]": min(per_page, 100)}


async def _get_list(
    path: str, api_key: str, params: dict[str, Any]
) -> tuple[bool, str | None, Any, dict[str, Any] | None]:
    """GET a list endpoint. Returns (success, error, data, meta)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}{path}", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return False, f"API error: {response.status_code} - {response.text}", None, None
        body = response.json() or {}
    except Exception as exc:
        return False, f"Request failed: {exc}", None, None
    return True, None, body.get("data"), body.get("meta")


async def _get_one(
    path: str, api_key: str, missing_label: str
) -> tuple[bool, str | None, Any]:
    """GET a retrieval endpoint. Returns (success, error, data)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}{path}", headers=_headers(api_key)
            )
        if response.status_code == 404:
            return False, missing_label, None
        if response.status_code != 200:
            return False, f"API error: {response.status_code} - {response.text}", None
        body = response.json() or {}
    except Exception as exc:
        return False, f"Request failed: {exc}", None
    return True, None, body.get("data")


# --- Input schemas ---------------------------------------------------------


class _ListInput(BaseModel):
    api_key: str = Field(description="Lemon Squeezy API key (provided by credential system)")
    page: int = Field(default=1, description="Page number for pagination")
    per_page: int = Field(default=10, description="Results per page (max 100)")


class ListCustomersInput(_ListInput):
    pass


class RetrieveCustomerInput(BaseModel):
    api_key: str = Field(description="Lemon Squeezy API key (provided by credential system)")
    customer_id: str = Field(description="The ID of the customer to retrieve")


class ListOrdersInput(_ListInput):
    store_id: str | None = Field(default=None, description="Filter by store ID")
    user_email: str | None = Field(default=None, description="Filter by user email")


class RetrieveOrderInput(BaseModel):
    api_key: str = Field(description="Lemon Squeezy API key (provided by credential system)")
    order_id: str = Field(description="The ID of the order to retrieve")


class ListProductsInput(_ListInput):
    store_id: str | None = Field(default=None, description="Filter by store ID")


class RetrieveProductInput(BaseModel):
    api_key: str = Field(description="Lemon Squeezy API key (provided by credential system)")
    product_id: str = Field(description="The ID of the product to retrieve")


class ListSubscriptionsInput(_ListInput):
    store_id: str | None = Field(default=None, description="Filter by store ID")
    status: str | None = Field(default=None, description="Filter by subscription status")


class RetrieveSubscriptionInput(BaseModel):
    api_key: str = Field(description="Lemon Squeezy API key (provided by credential system)")
    subscription_id: str = Field(description="The ID of the subscription to retrieve")


class ListStoresInput(_ListInput):
    pass


class RetrieveStoreInput(BaseModel):
    api_key: str = Field(description="Lemon Squeezy API key (provided by credential system)")
    store_id: str = Field(description="The ID of the store to retrieve")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=ListCustomersInput)
@serialize_pydantic_return
async def list_customers(
    api_key: str, page: int = 1, per_page: int = 10
) -> ListCustomersOutput:
    """List all customers from your Lemon Squeezy account."""
    if not api_key or not api_key.strip():
        return ListCustomersOutput(success=False, error=_empty_key_error("list_customers"))

    ok, err, data, meta = await _get_list(
        "/customers", api_key, _page_params(page, per_page)
    )
    return ListCustomersOutput(success=ok, error=err, data=data, meta=meta)


@tool(args_schema=RetrieveCustomerInput)
@serialize_pydantic_return
async def retrieve_customer(api_key: str, customer_id: str) -> RetrieveCustomerOutput:
    """Retrieve a specific customer by ID."""
    if not api_key or not api_key.strip():
        return RetrieveCustomerOutput(
            success=False, error=_empty_key_error("retrieve_customer")
        )

    ok, err, data = await _get_one(
        f"/customers/{customer_id}", api_key, f"Customer with ID {customer_id} not found"
    )
    return RetrieveCustomerOutput(success=ok, error=err, data=data)


@tool(args_schema=ListOrdersInput)
@serialize_pydantic_return
async def list_orders(
    api_key: str,
    page: int = 1,
    per_page: int = 10,
    store_id: str | None = None,
    user_email: str | None = None,
) -> ListOrdersOutput:
    """List all orders from your Lemon Squeezy account."""
    if not api_key or not api_key.strip():
        return ListOrdersOutput(success=False, error=_empty_key_error("list_orders"))

    params = _page_params(page, per_page)
    if store_id:
        params["filter[store_id]"] = store_id
    if user_email:
        params["filter[user_email]"] = user_email

    ok, err, data, meta = await _get_list("/orders", api_key, params)
    return ListOrdersOutput(success=ok, error=err, data=data, meta=meta)


@tool(args_schema=RetrieveOrderInput)
@serialize_pydantic_return
async def retrieve_order(api_key: str, order_id: str) -> RetrieveOrderOutput:
    """Retrieve a specific order by ID."""
    if not api_key or not api_key.strip():
        return RetrieveOrderOutput(
            success=False, error=_empty_key_error("retrieve_order")
        )

    ok, err, data = await _get_one(
        f"/orders/{order_id}", api_key, f"Order with ID {order_id} not found"
    )
    return RetrieveOrderOutput(success=ok, error=err, data=data)


@tool(args_schema=ListProductsInput)
@serialize_pydantic_return
async def list_products(
    api_key: str,
    page: int = 1,
    per_page: int = 10,
    store_id: str | None = None,
) -> ListProductsOutput:
    """List all products from your Lemon Squeezy account."""
    if not api_key or not api_key.strip():
        return ListProductsOutput(success=False, error=_empty_key_error("list_products"))

    params = _page_params(page, per_page)
    if store_id:
        params["filter[store_id]"] = store_id

    ok, err, data, meta = await _get_list("/products", api_key, params)
    return ListProductsOutput(success=ok, error=err, data=data, meta=meta)


@tool(args_schema=RetrieveProductInput)
@serialize_pydantic_return
async def retrieve_product(api_key: str, product_id: str) -> RetrieveProductOutput:
    """Retrieve a specific product by ID."""
    if not api_key or not api_key.strip():
        return RetrieveProductOutput(
            success=False, error=_empty_key_error("retrieve_product")
        )

    ok, err, data = await _get_one(
        f"/products/{product_id}", api_key, f"Product with ID {product_id} not found"
    )
    return RetrieveProductOutput(success=ok, error=err, data=data)


@tool(args_schema=ListSubscriptionsInput)
@serialize_pydantic_return
async def list_subscriptions(
    api_key: str,
    page: int = 1,
    per_page: int = 10,
    store_id: str | None = None,
    status: str | None = None,
) -> ListSubscriptionsOutput:
    """List all subscriptions from your Lemon Squeezy account."""
    if not api_key or not api_key.strip():
        return ListSubscriptionsOutput(
            success=False, error=_empty_key_error("list_subscriptions")
        )

    params = _page_params(page, per_page)
    if store_id:
        params["filter[store_id]"] = store_id
    if status:
        params["filter[status]"] = status

    ok, err, data, meta = await _get_list("/subscriptions", api_key, params)
    return ListSubscriptionsOutput(success=ok, error=err, data=data, meta=meta)


@tool(args_schema=RetrieveSubscriptionInput)
@serialize_pydantic_return
async def retrieve_subscription(
    api_key: str, subscription_id: str
) -> RetrieveSubscriptionOutput:
    """Retrieve a specific subscription by ID."""
    if not api_key or not api_key.strip():
        return RetrieveSubscriptionOutput(
            success=False, error=_empty_key_error("retrieve_subscription")
        )

    ok, err, data = await _get_one(
        f"/subscriptions/{subscription_id}",
        api_key,
        f"Subscription with ID {subscription_id} not found",
    )
    return RetrieveSubscriptionOutput(success=ok, error=err, data=data)


@tool(args_schema=ListStoresInput)
@serialize_pydantic_return
async def list_stores(
    api_key: str, page: int = 1, per_page: int = 10
) -> ListStoresOutput:
    """List all stores from your Lemon Squeezy account."""
    if not api_key or not api_key.strip():
        return ListStoresOutput(success=False, error=_empty_key_error("list_stores"))

    ok, err, data, meta = await _get_list(
        "/stores", api_key, _page_params(page, per_page)
    )
    return ListStoresOutput(success=ok, error=err, data=data, meta=meta)


@tool(args_schema=RetrieveStoreInput)
@serialize_pydantic_return
async def retrieve_store(api_key: str, store_id: str) -> RetrieveStoreOutput:
    """Retrieve a specific store by ID."""
    if not api_key or not api_key.strip():
        return RetrieveStoreOutput(
            success=False, error=_empty_key_error("retrieve_store")
        )

    ok, err, data = await _get_one(
        f"/stores/{store_id}", api_key, f"Store with ID {store_id} not found"
    )
    return RetrieveStoreOutput(success=ok, error=err, data=data)
