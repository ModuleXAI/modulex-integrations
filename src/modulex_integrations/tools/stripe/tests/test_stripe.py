"""Happy-path tests per action (50) plus form-encoding fidelity, a
failure-path test, and an empty-credential test.

Stripe does not raise on non-2xx; the tools wrap everything and return
``success=False`` + ``error``. Each happy-path test mocks the Stripe JSON
for the endpoint, asserts a dict at the ``@tool`` boundary, roundtrips
through the output model, and checks ``success is True``.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs

from modulex_integrations.tools.stripe import (
    TOOLS,
    cancel_payment_intent,
    cancel_subscription,
    capture_charge,
    capture_payment_intent,
    confirm_payment_intent,
    create_charge,
    create_customer,
    create_invoice,
    create_payment_intent,
    create_price,
    create_product,
    create_subscription,
    delete_customer,
    delete_invoice,
    delete_product,
    finalize_invoice,
    list_charges,
    list_customers,
    list_events,
    list_invoices,
    list_payment_intents,
    list_prices,
    list_products,
    list_subscriptions,
    manifest,
    pay_invoice,
    resume_subscription,
    retrieve_charge,
    retrieve_customer,
    retrieve_event,
    retrieve_invoice,
    retrieve_payment_intent,
    retrieve_price,
    retrieve_product,
    retrieve_subscription,
    search_charges,
    search_customers,
    search_invoices,
    search_payment_intents,
    search_prices,
    search_products,
    search_subscriptions,
    send_invoice,
    update_charge,
    update_customer,
    update_invoice,
    update_payment_intent,
    update_price,
    update_product,
    update_subscription,
    void_invoice,
)
from modulex_integrations.tools.stripe.outputs import (
    ChargeListOutput,
    ChargeOutput,
    CustomerDeleteOutput,
    CustomerListOutput,
    CustomerOutput,
    EventListOutput,
    EventOutput,
    InvoiceDeleteOutput,
    InvoiceListOutput,
    InvoiceOutput,
    PaymentIntentListOutput,
    PaymentIntentOutput,
    PriceListOutput,
    PriceOutput,
    ProductDeleteOutput,
    ProductListOutput,
    ProductOutput,
    SubscriptionListOutput,
    SubscriptionOutput,
)

API = "https://api.stripe.com/v1"
_API_KEY = "sk_test_fake"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_50_actions(self) -> None:
        assert len(manifest.actions) == 50

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:stripe-themed"

    def test_first_category_is_finance_and_payments(self) -> None:
        assert manifest.categories[0] == "Finance & Payments"


# --- Payment Intents --------------------------------------------------------


async def test_create_payment_intent(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/payment_intents",
        json={"id": "pi_1", "status": "requires_confirmation", "amount": 2000, "currency": "usd"},
    )
    result_dict = await create_payment_intent.ainvoke(
        _args(amount=2000, currency="usd", metadata={"order": "42"})
    )
    assert isinstance(result_dict, dict)
    result = PaymentIntentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.payment_intent is not None
    assert result.metadata is not None
    assert result.metadata.amount == 2000


async def test_retrieve_payment_intent(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/payment_intents/pi_1",
        json={"id": "pi_1", "status": "succeeded", "amount": 2000, "currency": "usd"},
    )
    result_dict = await retrieve_payment_intent.ainvoke(_args(id="pi_1"))
    result = PaymentIntentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.status == "succeeded"


async def test_update_payment_intent(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/payment_intents/pi_1",
        json={"id": "pi_1", "status": "requires_confirmation", "amount": 3000, "currency": "usd"},
    )
    result_dict = await update_payment_intent.ainvoke(_args(id="pi_1", amount=3000))
    result = PaymentIntentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.amount == 3000


async def test_confirm_payment_intent(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/payment_intents/pi_1/confirm",
        json={"id": "pi_1", "status": "succeeded", "amount": 2000, "currency": "usd"},
    )
    result_dict = await confirm_payment_intent.ainvoke(_args(id="pi_1", payment_method="pm_1"))
    result = PaymentIntentOutput.model_validate(result_dict)
    assert result.success is True


async def test_capture_payment_intent(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/payment_intents/pi_1/capture",
        json={"id": "pi_1", "status": "succeeded", "amount": 2000, "currency": "usd"},
    )
    result_dict = await capture_payment_intent.ainvoke(_args(id="pi_1", amount_to_capture=1500))
    result = PaymentIntentOutput.model_validate(result_dict)
    assert result.success is True


async def test_cancel_payment_intent(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/payment_intents/pi_1/cancel",
        json={"id": "pi_1", "status": "canceled", "amount": 2000, "currency": "usd"},
    )
    result_dict = await cancel_payment_intent.ainvoke(
        _args(id="pi_1", cancellation_reason="requested_by_customer")
    )
    result = PaymentIntentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.status == "canceled"


async def test_list_payment_intents(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/payment_intents?limit=2",
        json={"data": [{"id": "pi_1"}, {"id": "pi_2"}], "has_more": False},
    )
    result_dict = await list_payment_intents.ainvoke(_args(limit=2))
    result = PaymentIntentListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.count == 2


async def test_search_payment_intents(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/payment_intents/search?query=status%3A%27succeeded%27",
        json={"data": [{"id": "pi_1"}], "has_more": False},
    )
    result_dict = await search_payment_intents.ainvoke(_args(query="status:'succeeded'"))
    result = PaymentIntentListOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.payment_intents) == 1


# --- Customers --------------------------------------------------------------


async def test_create_customer(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/customers",
        json={"id": "cus_1", "email": "a@b.com", "name": "Alice"},
    )
    result_dict = await create_customer.ainvoke(
        _args(email="a@b.com", name="Alice", address={"line1": "1 Main St", "country": "US"})
    )
    result = CustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.email == "a@b.com"


async def test_retrieve_customer(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/customers/cus_1",
        json={"id": "cus_1", "email": "a@b.com", "name": "Alice"},
    )
    result_dict = await retrieve_customer.ainvoke(_args(id="cus_1"))
    result = CustomerOutput.model_validate(result_dict)
    assert result.success is True


async def test_update_customer(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/customers/cus_1",
        json={"id": "cus_1", "email": "new@b.com", "name": "Alice"},
    )
    result_dict = await update_customer.ainvoke(_args(id="cus_1", email="new@b.com"))
    result = CustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.email == "new@b.com"


async def test_delete_customer(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/customers/cus_1",
        json={"id": "cus_1", "deleted": True},
    )
    result_dict = await delete_customer.ainvoke(_args(id="cus_1"))
    result = CustomerDeleteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


async def test_list_customers(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/customers?limit=1",
        json={"data": [{"id": "cus_1"}], "has_more": True},
    )
    result_dict = await list_customers.ainvoke(_args(limit=1))
    result = CustomerListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.has_more is True


async def test_search_customers(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/customers/search?query=email%3A%27a%40b.com%27",
        json={"data": [{"id": "cus_1"}], "has_more": False},
    )
    result_dict = await search_customers.ainvoke(_args(query="email:'a@b.com'"))
    result = CustomerListOutput.model_validate(result_dict)
    assert result.success is True


# --- Subscriptions ----------------------------------------------------------


async def test_create_subscription(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscriptions",
        json={"id": "sub_1", "status": "active", "customer": "cus_1"},
    )
    result_dict = await create_subscription.ainvoke(
        _args(customer="cus_1", items=[{"price": "price_1", "quantity": 2}])
    )
    result = SubscriptionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.customer == "cus_1"


async def test_retrieve_subscription(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/subscriptions/sub_1",
        json={"id": "sub_1", "status": "active", "customer": "cus_1"},
    )
    result_dict = await retrieve_subscription.ainvoke(_args(id="sub_1"))
    result = SubscriptionOutput.model_validate(result_dict)
    assert result.success is True


async def test_update_subscription(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscriptions/sub_1",
        json={"id": "sub_1", "status": "active", "customer": "cus_1"},
    )
    result_dict = await update_subscription.ainvoke(
        _args(id="sub_1", items=[{"price": "price_2"}])
    )
    result = SubscriptionOutput.model_validate(result_dict)
    assert result.success is True


async def test_cancel_subscription(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/subscriptions/sub_1",
        json={"id": "sub_1", "status": "canceled", "customer": "cus_1"},
    )
    result_dict = await cancel_subscription.ainvoke(_args(id="sub_1", prorate=True))
    result = SubscriptionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.status == "canceled"


async def test_resume_subscription(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscriptions/sub_1/resume",
        json={"id": "sub_1", "status": "active", "customer": "cus_1"},
    )
    result_dict = await resume_subscription.ainvoke(_args(id="sub_1"))
    result = SubscriptionOutput.model_validate(result_dict)
    assert result.success is True


async def test_list_subscriptions(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/subscriptions?status=active",
        json={"data": [{"id": "sub_1"}], "has_more": False},
    )
    result_dict = await list_subscriptions.ainvoke(_args(status="active"))
    result = SubscriptionListOutput.model_validate(result_dict)
    assert result.success is True


async def test_search_subscriptions(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/subscriptions/search?query=status%3A%27active%27",
        json={"data": [{"id": "sub_1"}], "has_more": False},
    )
    result_dict = await search_subscriptions.ainvoke(_args(query="status:'active'"))
    result = SubscriptionListOutput.model_validate(result_dict)
    assert result.success is True


# --- Invoices ---------------------------------------------------------------


async def test_create_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invoices",
        json={"id": "in_1", "status": "draft", "amount_due": 1000, "currency": "usd"},
    )
    result_dict = await create_invoice.ainvoke(_args(customer="cus_1"))
    result = InvoiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.amount_due == 1000


async def test_retrieve_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/invoices/in_1",
        json={"id": "in_1", "status": "open", "amount_due": 1000, "currency": "usd"},
    )
    result_dict = await retrieve_invoice.ainvoke(_args(id="in_1"))
    result = InvoiceOutput.model_validate(result_dict)
    assert result.success is True


async def test_update_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invoices/in_1",
        json={"id": "in_1", "status": "draft", "amount_due": 1000, "currency": "usd"},
    )
    result_dict = await update_invoice.ainvoke(_args(id="in_1", description="memo"))
    result = InvoiceOutput.model_validate(result_dict)
    assert result.success is True


async def test_delete_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/invoices/in_1",
        json={"id": "in_1", "deleted": True},
    )
    result_dict = await delete_invoice.ainvoke(_args(id="in_1"))
    result = InvoiceDeleteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


async def test_finalize_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invoices/in_1/finalize",
        json={"id": "in_1", "status": "open", "amount_due": 1000, "currency": "usd"},
    )
    result_dict = await finalize_invoice.ainvoke(_args(id="in_1", auto_advance=True))
    result = InvoiceOutput.model_validate(result_dict)
    assert result.success is True


async def test_pay_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invoices/in_1/pay",
        json={"id": "in_1", "status": "paid", "amount_due": 0, "currency": "usd"},
    )
    result_dict = await pay_invoice.ainvoke(_args(id="in_1", paid_out_of_band=False))
    result = InvoiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.status == "paid"


async def test_void_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invoices/in_1/void",
        json={"id": "in_1", "status": "void", "amount_due": 0, "currency": "usd"},
    )
    result_dict = await void_invoice.ainvoke(_args(id="in_1"))
    result = InvoiceOutput.model_validate(result_dict)
    assert result.success is True


async def test_send_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invoices/in_1/send",
        json={"id": "in_1", "status": "open", "amount_due": 1000, "currency": "usd"},
    )
    result_dict = await send_invoice.ainvoke(_args(id="in_1"))
    result = InvoiceOutput.model_validate(result_dict)
    assert result.success is True


async def test_list_invoices(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/invoices?status=open",
        json={"data": [{"id": "in_1"}], "has_more": False},
    )
    result_dict = await list_invoices.ainvoke(_args(status="open"))
    result = InvoiceListOutput.model_validate(result_dict)
    assert result.success is True


async def test_search_invoices(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/invoices/search?query=customer%3A%27cus_1%27",
        json={"data": [{"id": "in_1"}], "has_more": False},
    )
    result_dict = await search_invoices.ainvoke(_args(query="customer:'cus_1'"))
    result = InvoiceListOutput.model_validate(result_dict)
    assert result.success is True


# --- Charges ----------------------------------------------------------------


async def test_create_charge(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/charges",
        json={"id": "ch_1", "status": "succeeded", "amount": 2000, "currency": "usd", "paid": True},
    )
    result_dict = await create_charge.ainvoke(
        _args(amount=2000, currency="usd", metadata={"order": "9"})
    )
    result = ChargeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.paid is True


async def test_retrieve_charge(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/charges/ch_1",
        json={"id": "ch_1", "status": "succeeded", "amount": 2000, "currency": "usd", "paid": True},
    )
    result_dict = await retrieve_charge.ainvoke(_args(id="ch_1"))
    result = ChargeOutput.model_validate(result_dict)
    assert result.success is True


async def test_update_charge(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/charges/ch_1",
        json={"id": "ch_1", "status": "succeeded", "amount": 2000, "currency": "usd", "paid": True},
    )
    result_dict = await update_charge.ainvoke(_args(id="ch_1", description="updated"))
    result = ChargeOutput.model_validate(result_dict)
    assert result.success is True


async def test_capture_charge(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/charges/ch_1/capture",
        json={"id": "ch_1", "status": "succeeded", "amount": 1500, "currency": "usd", "paid": True},
    )
    result_dict = await capture_charge.ainvoke(_args(id="ch_1", amount=1500))
    result = ChargeOutput.model_validate(result_dict)
    assert result.success is True


async def test_list_charges(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/charges?limit=2",
        json={"data": [{"id": "ch_1"}, {"id": "ch_2"}], "has_more": False},
    )
    result_dict = await list_charges.ainvoke(_args(limit=2))
    result = ChargeListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.count == 2


async def test_search_charges(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/charges/search?query=status%3A%27succeeded%27",
        json={"data": [{"id": "ch_1"}], "has_more": False},
    )
    result_dict = await search_charges.ainvoke(_args(query="status:'succeeded'"))
    result = ChargeListOutput.model_validate(result_dict)
    assert result.success is True


# --- Products ---------------------------------------------------------------


async def test_create_product(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/products",
        json={"id": "prod_1", "name": "Widget", "active": True},
    )
    result_dict = await create_product.ainvoke(
        _args(name="Widget", images=["https://x.test/a.jpg"], active=True)
    )
    result = ProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.active is True


async def test_retrieve_product(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/products/prod_1",
        json={"id": "prod_1", "name": "Widget", "active": True},
    )
    result_dict = await retrieve_product.ainvoke(_args(id="prod_1"))
    result = ProductOutput.model_validate(result_dict)
    assert result.success is True


async def test_update_product(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/products/prod_1",
        json={"id": "prod_1", "name": "Widget v2", "active": False},
    )
    result_dict = await update_product.ainvoke(_args(id="prod_1", name="Widget v2", active=False))
    result = ProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.active is False


async def test_delete_product(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/products/prod_1",
        json={"id": "prod_1", "deleted": True},
    )
    result_dict = await delete_product.ainvoke(_args(id="prod_1"))
    result = ProductDeleteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


async def test_list_products(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/products?active=true",
        json={"data": [{"id": "prod_1"}], "has_more": False},
    )
    result_dict = await list_products.ainvoke(_args(active=True))
    result = ProductListOutput.model_validate(result_dict)
    assert result.success is True


async def test_search_products(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/products/search?query=name%3A%27Widget%27",
        json={"data": [{"id": "prod_1"}], "has_more": False},
    )
    result_dict = await search_products.ainvoke(_args(query="name:'Widget'"))
    result = ProductListOutput.model_validate(result_dict)
    assert result.success is True


# --- Prices -----------------------------------------------------------------


async def test_create_price(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/prices",
        json={"id": "price_1", "product": "prod_1", "unit_amount": 1000, "currency": "usd"},
    )
    result_dict = await create_price.ainvoke(
        _args(
            product="prod_1",
            currency="usd",
            unit_amount=1000,
            recurring={"interval": "month", "interval_count": 1},
            billing_scheme="per_unit",
        )
    )
    result = PriceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.unit_amount == 1000


async def test_retrieve_price(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/prices/price_1",
        json={"id": "price_1", "product": "prod_1", "unit_amount": 1000, "currency": "usd"},
    )
    result_dict = await retrieve_price.ainvoke(_args(id="price_1"))
    result = PriceOutput.model_validate(result_dict)
    assert result.success is True


async def test_update_price(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/prices/price_1",
        json={"id": "price_1", "product": "prod_1", "unit_amount": 1000, "currency": "usd"},
    )
    result_dict = await update_price.ainvoke(_args(id="price_1", active=False))
    result = PriceOutput.model_validate(result_dict)
    assert result.success is True


async def test_list_prices(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/prices?product=prod_1",
        json={"data": [{"id": "price_1"}], "has_more": False},
    )
    result_dict = await list_prices.ainvoke(_args(product="prod_1"))
    result = PriceListOutput.model_validate(result_dict)
    assert result.success is True


async def test_search_prices(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/prices/search?query=active%3A%27true%27",
        json={"data": [{"id": "price_1"}], "has_more": False},
    )
    result_dict = await search_prices.ainvoke(_args(query="active:'true'"))
    result = PriceListOutput.model_validate(result_dict)
    assert result.success is True


# --- Events -----------------------------------------------------------------


async def test_retrieve_event(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/events/evt_1",
        json={"id": "evt_1", "type": "payment_intent.succeeded", "created": 1633024800},
    )
    result_dict = await retrieve_event.ainvoke(_args(id="evt_1"))
    result = EventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is not None and result.metadata.type == "payment_intent.succeeded"


async def test_list_events(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/events?type=payment_intent.created",
        json={"data": [{"id": "evt_1"}], "has_more": False},
    )
    result_dict = await list_events.ainvoke(_args(type="payment_intent.created"))
    result = EventListOutput.model_validate(result_dict)
    assert result.success is True


# --- Form-encoding fidelity -------------------------------------------------


async def test_create_subscription_form_encoding(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """Nested array items must use Stripe's bracket notation, the Bearer
    header must be set, and booleans must be lowercase."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscriptions",
        json={"id": "sub_1", "status": "active", "customer": "cus_1"},
    )
    await create_subscription.ainvoke(
        _args(
            customer="cus_1",
            items=[{"price": "price_1", "quantity": 2}],
            cancel_at_period_end=True,
        )
    )
    sent = httpx_mock.get_requests()[0]
    body = parse_qs(sent.content.decode())
    assert body["items[0][price]"] == ["price_1"]
    assert body["items[0][quantity]"] == ["2"]
    assert body["customer"] == ["cus_1"]
    # Boolean is lowercase, never Python's "True".
    assert body["cancel_at_period_end"] == ["true"]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    assert sent.headers["content-type"] == "application/x-www-form-urlencoded"


async def test_create_charge_metadata_bracket_keys(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/charges",
        json={"id": "ch_1", "status": "succeeded", "amount": 500, "currency": "usd", "paid": True},
    )
    await create_charge.ainvoke(
        _args(amount=500, currency="usd", capture=False, metadata={"order_id": "abc"})
    )
    sent = httpx_mock.get_requests()[0]
    body = parse_qs(sent.content.decode())
    assert body["metadata[order_id]"] == ["abc"]
    assert body["capture"] == ["false"]
    assert body["amount"] == ["500"]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


async def test_create_customer_address_bracket_keys(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/customers",
        json={"id": "cus_1", "email": "a@b.com", "name": "Alice"},
    )
    await create_customer.ainvoke(
        _args(name="Alice", address={"line1": "1 Main St", "country": "US"})
    )
    sent = httpx_mock.get_requests()[0]
    body = parse_qs(sent.content.decode())
    assert body["address[line1]"] == ["1 Main St"]
    assert body["address[country]"] == ["US"]


# --- Failure paths ----------------------------------------------------------


async def test_create_charge_returns_error_on_non_2xx(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/charges",
        status_code=402,
        text="Your card was declined.",
    )
    result_dict = await create_charge.ainvoke(_args(amount=2000, currency="usd"))
    assert isinstance(result_dict, dict)
    result = ChargeOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "402" in result.error


async def test_create_payment_intent_validates_empty_api_key() -> None:
    """Empty / whitespace api_key short-circuits before any HTTP call."""
    result_dict = await create_payment_intent.ainvoke(
        {"amount": 100, "currency": "usd", "api_key": ""}
    )
    assert isinstance(result_dict, dict)
    result = PaymentIntentOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
