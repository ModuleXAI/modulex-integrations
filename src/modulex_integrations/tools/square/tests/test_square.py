"""Happy-path tests for every square @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.square import (
    TOOLS,
    create_customer,
    create_invoice,
    create_order,
    list_event_types_options,
    list_location_options,
    manifest,
    send_invoice,
)
from modulex_integrations.tools.square.outputs import (
    CreateCustomerOutput,
    CreateInvoiceOutput,
    CreateOrderOutput,
    ListEventTypesOptionsOutput,
    ListLocationOptionsOutput,
    SendInvoiceOutput,
)

API = "https://connect.squareup.com/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
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
async def test_create_customer(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/customers",
        json={
            # TODO: fill in a representative response shape from the Square API docs
            "customer": {
                "id": "CUST123",
                "given_name": "John",
                "family_name": "Doe",
                "email_address": "john@example.com",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        },
    )

    result_dict = await create_customer.ainvoke(_args(given_name="John", family_name="Doe", email_address="john@example.com"))

    assert isinstance(result_dict, dict)
    result = CreateCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.customer is not None
    assert result.customer.id == "CUST123"


@pytest.mark.asyncio
async def test_create_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invoices",
        json={
            # TODO: fill in a representative response shape from the Square API docs
            "invoice": {
                "id": "INV123",
                "version": 0,
                "location_id": "LOC1",
                "order_id": "ORD1",
                "status": "DRAFT",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        },
    )

    result_dict = await create_invoice.ainvoke(
        _args(
            location_id="LOC1",
            order_id="ORD1",
            customer_id="CUST1",
            due_date="2024-02-01",
            accepted_payment_methods=["card", "bank_account"],
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateInvoiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.invoice is not None
    assert result.invoice.id == "INV123"


@pytest.mark.asyncio
async def test_create_order(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/orders",
        json={
            # TODO: fill in a representative response shape from the Square API docs
            "order": {
                "id": "ORD123",
                "location_id": "LOC1",
                "state": "OPEN",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        },
    )

    result_dict = await create_order.ainvoke(_args(location_id="LOC1"))

    assert isinstance(result_dict, dict)
    result = CreateOrderOutput.model_validate(result_dict)
    assert result.success is True
    assert result.order is not None
    assert result.order.id == "ORD123"


@pytest.mark.asyncio
async def test_list_event_types_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/webhooks/event-types",
        json={
            # TODO: fill in a representative response shape from the Square API docs
            "event_types": ["payment.created", "payment.updated", "order.created"],
        },
    )

    result_dict = await list_event_types_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListEventTypesOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.event_types) == 3


@pytest.mark.asyncio
async def test_list_location_options(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/locations",
        json={
            # TODO: fill in a representative response shape from the Square API docs
            "locations": [
                {"id": "LOC1", "name": "Main Store", "status": "ACTIVE"},
                {"id": "LOC2", "name": "Warehouse", "status": "ACTIVE"},
            ],
        },
    )

    result_dict = await list_location_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListLocationOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.locations) == 2
    assert result.locations[0].id == "LOC1"


@pytest.mark.asyncio
async def test_send_invoice(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/invoices/INV123",
        json={
            "invoice": {
                "id": "INV123",
                "version": 1,
                "status": "DRAFT",
            },
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/invoices/INV123/publish",
        json={
            # TODO: fill in a representative response shape from the Square API docs
            "invoice": {
                "id": "INV123",
                "version": 2,
                "location_id": "LOC1",
                "order_id": "ORD1",
                "status": "PUBLISHED",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
            },
        },
    )

    result_dict = await send_invoice.ainvoke(_args(location_id="LOC1", invoice_id="INV123"))

    assert isinstance(result_dict, dict)
    result = SendInvoiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.invoice is not None
    assert result.invoice.status == "PUBLISHED"


@pytest.mark.asyncio
async def test_create_customer_empty_credentials() -> None:
    """Verify that empty credentials return an inline error without hitting the network."""
    result_dict = await create_customer.ainvoke(
        _args(auth_data={"access_token": ""}, given_name="Test")
    )
    assert isinstance(result_dict, dict)
    result = CreateCustomerOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access token" in result.error.lower()
