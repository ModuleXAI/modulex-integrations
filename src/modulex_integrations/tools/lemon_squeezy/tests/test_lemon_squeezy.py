"""Tests for the Lemon Squeezy integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.lemon_squeezy import (
    TOOLS,
    list_customers,
    list_orders,
    list_products,
    list_stores,
    list_subscriptions,
    manifest,
    retrieve_customer,
    retrieve_order,
    retrieve_product,
    retrieve_store,
    retrieve_subscription,
)
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

API = "https://api.lemonsqueezy.com/v1"
_API_KEY = "ls-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _list_envelope(kind: str) -> dict[str, Any]:
    return {
        "data": [
            {"id": "1", "type": kind, "attributes": {"name": "First"}},
            {"id": "2", "type": kind, "attributes": {"name": "Second"}},
        ],
        "meta": {"page": {"total": 2, "currentPage": 1}},
    }


def _retrieve_envelope(kind: str, item_id: str) -> dict[str, Any]:
    return {
        "data": {"id": item_id, "type": kind, "attributes": {"name": "One"}}
    }


class TestManifest:
    def test_manifest_exposes_ten_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_list_customers(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/customers?page%5Bnumber%5D=1&page%5Bsize%5D=10",
        json=_list_envelope("customers"),
    )

    result_dict = await list_customers.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListCustomersOutput.model_validate(result_dict)
    assert result.success is True
    assert isinstance(result.data, list) and len(result.data) == 2
    assert result.meta is not None
    assert result.meta["page"]["total"] == 2


@pytest.mark.asyncio
async def test_retrieve_customer_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/customers/42",
        json=_retrieve_envelope("customers", "42"),
    )
    result = RetrieveCustomerOutput.model_validate(
        await retrieve_customer.ainvoke(_args(customer_id="42"))
    )
    assert result.success is True
    assert result.data["id"] == "42"


@pytest.mark.asyncio
async def test_retrieve_customer_not_found(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/customers/ghost", status_code=404, text="not found"
    )
    result = RetrieveCustomerOutput.model_validate(
        await retrieve_customer.ainvoke(_args(customer_id="ghost"))
    )
    assert result.success is False
    assert result.error is not None and "ghost" in result.error


@pytest.mark.asyncio
async def test_list_orders_with_filters(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/orders?page%5Bnumber%5D=1&page%5Bsize%5D=10"
            "&filter%5Bstore_id%5D=99&filter%5Buser_email%5D=a%40x.io"
        ),
        json=_list_envelope("orders"),
    )
    result = ListOrdersOutput.model_validate(
        await list_orders.ainvoke(_args(store_id="99", user_email="a@x.io"))
    )
    assert result.success is True
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_retrieve_order(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/orders/o1",
        json=_retrieve_envelope("orders", "o1"),
    )
    result = RetrieveOrderOutput.model_validate(
        await retrieve_order.ainvoke(_args(order_id="o1"))
    )
    assert result.success is True
    assert result.data["id"] == "o1"


@pytest.mark.asyncio
async def test_list_products_filtered(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/products?page%5Bnumber%5D=1&page%5Bsize%5D=10"
            "&filter%5Bstore_id%5D=99"
        ),
        json=_list_envelope("products"),
    )
    result = ListProductsOutput.model_validate(
        await list_products.ainvoke(_args(store_id="99"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_retrieve_product(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/products/p1",
        json=_retrieve_envelope("products", "p1"),
    )
    result = RetrieveProductOutput.model_validate(
        await retrieve_product.ainvoke(_args(product_id="p1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_subscriptions(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/subscriptions?page%5Bnumber%5D=1&page%5Bsize%5D=10"
            "&filter%5Bstatus%5D=active"
        ),
        json=_list_envelope("subscriptions"),
    )
    result = ListSubscriptionsOutput.model_validate(
        await list_subscriptions.ainvoke(_args(status="active"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_retrieve_subscription(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/subscriptions/sub1",
        json=_retrieve_envelope("subscriptions", "sub1"),
    )
    result = RetrieveSubscriptionOutput.model_validate(
        await retrieve_subscription.ainvoke(_args(subscription_id="sub1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_stores(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/stores?page%5Bnumber%5D=1&page%5Bsize%5D=10",
        json=_list_envelope("stores"),
    )
    result = ListStoresOutput.model_validate(
        await list_stores.ainvoke(_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_retrieve_store(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/stores/s1",
        json=_retrieve_envelope("stores", "s1"),
    )
    result = RetrieveStoreOutput.model_validate(
        await retrieve_store.ainvoke(_args(store_id="s1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_returns_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/customers?page%5Bnumber%5D=1&page%5Bsize%5D=10",
        status_code=401,
        text="invalid token",
    )
    result = ListCustomersOutput.model_validate(await list_customers.ainvoke(_args()))
    assert result.success is False
    assert result.error is not None and "401" in result.error


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = ListCustomersOutput.model_validate(
        await list_customers.ainvoke({"api_key": ""})
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
