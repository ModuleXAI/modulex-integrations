"""Happy-path tests for every woocommerce @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.woocommerce import (
    TOOLS,
    add_order_note,
    create_customer,
    create_order,
    create_product,
    create_refund,
    delete_order,
    get_customer,
    get_order,
    get_order_note,
    get_product,
    list_order_notes,
    list_orders,
    list_payment_method_options,
    list_products,
    manifest,
    search_customers,
    update_order_status,
    update_product,
)
from modulex_integrations.tools.woocommerce.outputs import (
    AddOrderNoteOutput,
    CreateCustomerOutput,
    CreateOrderOutput,
    CreateProductOutput,
    CreateRefundOutput,
    DeleteOrderOutput,
    GetCustomerOutput,
    GetOrderNoteOutput,
    GetOrderOutput,
    GetProductOutput,
    ListOrderNotesOutput,
    ListOrdersOutput,
    ListPaymentMethodOptionsOutput,
    ListProductsOutput,
    SearchCustomersOutput,
    UpdateOrderStatusOutput,
    UpdateProductOutput,
)

API = "https://mystore.example.com/wp-json/wc/v3"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "store_url": "https://mystore.example.com",
        "consumer_key": "ck_fake_key",
        "consumer_secret": "cs_fake_secret",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_17_actions(self) -> None:
        assert len(manifest.actions) == 17

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/orders",
        json={
            # TODO: fill in a representative response shape from the WooCommerce API docs
            "id": 123,
            "number": "123",
            "status": "pending",
            "total": "50.00",
            "currency": "USD",
            "customer_id": 1,
            "payment_method": "bacs",
            "date_created": "2024-01-01T00:00:00",
            "date_modified": "2024-01-01T00:00:00",
            "line_items": [],
            "billing": {},
            "shipping": {},
        },
        status_code=201,
    )

    result_dict = await create_order.ainvoke(_args(line_items=[{"product_id": 1, "quantity": 2}]))

    assert isinstance(result_dict, dict)
    result = CreateOrderOutput.model_validate(result_dict)
    assert result.success is True
    assert result.order is not None
    assert result.order.id == 123


@pytest.mark.asyncio
async def test_get_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/orders/123",
        json={
            "id": 123,
            "number": "123",
            "status": "processing",
            "total": "99.00",
            "currency": "USD",
            "customer_id": 2,
            "payment_method": "paypal",
            "date_created": "2024-01-01T00:00:00",
            "date_modified": "2024-01-02T00:00:00",
            "line_items": [],
            "billing": {},
            "shipping": {},
        },
    )

    result_dict = await get_order.ainvoke(_args(order_id=123))

    assert isinstance(result_dict, dict)
    result = GetOrderOutput.model_validate(result_dict)
    assert result.success is True
    assert result.order is not None
    assert result.order.status == "processing"


@pytest.mark.asyncio
async def test_list_orders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/orders?per_page=20&status=pending",
        json=[
            {"id": 1, "number": "1", "status": "pending", "total": "10.00", "currency": "USD", "customer_id": 0, "payment_method": "", "date_created": "2024-01-01T00:00:00", "date_modified": "2024-01-01T00:00:00", "line_items": [], "billing": {}, "shipping": {}},
        ],
    )

    result_dict = await list_orders.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListOrdersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_delete_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/orders/123",
        json={"id": 123, "number": "123", "status": "trash", "total": "0.00", "currency": "USD", "customer_id": 0, "payment_method": "", "date_created": "2024-01-01T00:00:00", "date_modified": "2024-01-01T00:00:00", "line_items": [], "billing": {}, "shipping": {}},
    )

    result_dict = await delete_order.ainvoke(_args(order_id=123))

    assert isinstance(result_dict, dict)
    result = DeleteOrderOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_order_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/orders/123",
        json={"id": 123, "number": "123", "status": "completed", "total": "50.00", "currency": "USD", "customer_id": 1, "payment_method": "bacs", "date_created": "2024-01-01T00:00:00", "date_modified": "2024-01-02T00:00:00", "line_items": [], "billing": {}, "shipping": {}},
    )

    result_dict = await update_order_status.ainvoke(_args(order_id=123, status="completed"))

    assert isinstance(result_dict, dict)
    result = UpdateOrderStatusOutput.model_validate(result_dict)
    assert result.success is True
    assert result.order is not None
    assert result.order.status == "completed"


@pytest.mark.asyncio
async def test_create_product(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/products",
        json={
            "id": 456,
            "name": "Test Product",
            "slug": "test-product",
            "type": "simple",
            "status": "publish",
            "regular_price": "29.99",
            "sale_price": "",
            "price": "29.99",
            "description": "A test product",
            "categories": [],
            "images": [],
            "date_created": "2024-01-01T00:00:00",
        },
        status_code=201,
    )

    result_dict = await create_product.ainvoke(_args(name="Test Product", regular_price="29.99"))

    assert isinstance(result_dict, dict)
    result = CreateProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.product is not None
    assert result.product.name == "Test Product"


@pytest.mark.asyncio
async def test_update_product(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/products/456",
        json={
            "id": 456,
            "name": "Updated Product",
            "slug": "updated-product",
            "type": "simple",
            "status": "publish",
            "regular_price": "39.99",
            "sale_price": "",
            "price": "39.99",
            "description": "",
            "categories": [],
            "images": [],
            "date_created": "2024-01-01T00:00:00",
        },
    )

    result_dict = await update_product.ainvoke(_args(product_id=456, name="Updated Product", regular_price="39.99"))

    assert isinstance(result_dict, dict)
    result = UpdateProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.product is not None
    assert result.product.regular_price == "39.99"


@pytest.mark.asyncio
async def test_get_product(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/products/456",
        json={
            "id": 456,
            "name": "Test Product",
            "slug": "test-product",
            "type": "simple",
            "status": "publish",
            "regular_price": "29.99",
            "sale_price": "",
            "price": "29.99",
            "description": "",
            "categories": [],
            "images": [],
            "date_created": "2024-01-01T00:00:00",
        },
    )

    result_dict = await get_product.ainvoke(_args(product_id=456))

    assert isinstance(result_dict, dict)
    result = GetProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.product is not None
    assert result.product.id == 456


@pytest.mark.asyncio
async def test_list_products(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/products?per_page=20&status=publish&type=simple",
        json=[
            {"id": 1, "name": "P1", "slug": "p1", "type": "simple", "status": "publish", "regular_price": "10.00", "sale_price": "", "price": "10.00", "description": "", "categories": [], "images": [], "date_created": "2024-01-01T00:00:00"},
        ],
    )

    result_dict = await list_products.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListProductsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_search_customers(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/customers?per_page=20&role=customer",
        json=[
            {"id": 10, "email": "test@example.com", "first_name": "Test", "last_name": "User", "username": "testuser", "role": "customer", "date_created": "2024-01-01T00:00:00", "billing": {}, "shipping": {}, "is_paying_customer": True},
        ],
    )

    result_dict = await search_customers.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = SearchCustomersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_get_customer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/customers/10",
        json={"id": 10, "email": "test@example.com", "first_name": "Test", "last_name": "User", "username": "testuser", "role": "customer", "date_created": "2024-01-01T00:00:00", "billing": {}, "shipping": {}, "is_paying_customer": True},
    )

    result_dict = await get_customer.ainvoke(_args(customer_id=10))

    assert isinstance(result_dict, dict)
    result = GetCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.customer is not None
    assert result.customer.email == "test@example.com"


@pytest.mark.asyncio
async def test_create_customer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/customers",
        json={"id": 11, "email": "new@example.com", "first_name": "New", "last_name": "Customer", "username": "newcustomer", "role": "customer", "date_created": "2024-01-01T00:00:00", "billing": {}, "shipping": {}, "is_paying_customer": False},
        status_code=201,
    )

    result_dict = await create_customer.ainvoke(_args(email="new@example.com", first_name="New", last_name="Customer"))

    assert isinstance(result_dict, dict)
    result = CreateCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.customer is not None
    assert result.customer.id == 11


@pytest.mark.asyncio
async def test_add_order_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/orders/123/notes",
        json={"id": 1, "author": "system", "date_created": "2024-01-01T00:00:00", "note": "Test note", "customer_note": False},
        status_code=201,
    )

    result_dict = await add_order_note.ainvoke(_args(order_id=123, note="Test note"))

    assert isinstance(result_dict, dict)
    result = AddOrderNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.note is not None
    assert result.note.note == "Test note"


@pytest.mark.asyncio
async def test_get_order_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/orders/123/notes/1",
        json={"id": 1, "author": "system", "date_created": "2024-01-01T00:00:00", "note": "A note", "customer_note": False},
    )

    result_dict = await get_order_note.ainvoke(_args(order_id=123, note_id=1))

    assert isinstance(result_dict, dict)
    result = GetOrderNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.note is not None


@pytest.mark.asyncio
async def test_list_order_notes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/orders/123/notes",
        json=[
            {"id": 1, "author": "system", "date_created": "2024-01-01T00:00:00", "note": "Note 1", "customer_note": False},
            {"id": 2, "author": "admin", "date_created": "2024-01-02T00:00:00", "note": "Note 2", "customer_note": True},
        ],
    )

    result_dict = await list_order_notes.ainvoke(_args(order_id=123))

    assert isinstance(result_dict, dict)
    result = ListOrderNotesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.notes) == 2


@pytest.mark.asyncio
async def test_create_refund(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/orders/123/refunds",
        json={"id": 5, "amount": "25.00", "reason": "Damaged item", "refunded_by": 1, "date_created": "2024-01-01T00:00:00", "line_items": []},
        status_code=201,
    )

    result_dict = await create_refund.ainvoke(_args(order_id=123, amount="25.00", reason="Damaged item"))

    assert isinstance(result_dict, dict)
    result = CreateRefundOutput.model_validate(result_dict)
    assert result.success is True
    assert result.refund is not None
    assert result.refund.amount == "25.00"


@pytest.mark.asyncio
async def test_list_payment_method_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/payment_gateways",
        json=[
            {"id": "bacs", "title": "Direct bank transfer", "description": "Make your payment directly.", "enabled": True},
            {"id": "cod", "title": "Cash on delivery", "description": "Pay with cash.", "enabled": True},
        ],
    )

    result_dict = await list_payment_method_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListPaymentMethodOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.payment_methods) == 2


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_empty_credentials() -> None:
    """Credential validation rejects empty store_url / consumer_key / consumer_secret."""
    result_dict = await create_order.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {
                "store_url": "",
                "consumer_key": "",
                "consumer_secret": "",
            },
        }
    )

    assert isinstance(result_dict, dict)
    result = CreateOrderOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
