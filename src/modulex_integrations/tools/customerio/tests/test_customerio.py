"""Tests for the Customer.io integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.customerio import (
    TOOLS,
    add_customers_to_segment,
    create_or_update_customer,
    manifest,
    send_event,
)
from modulex_integrations.tools.customerio.outputs import (
    AddCustomersToSegmentOutput,
    CreateOrUpdateCustomerOutput,
    SendEventOutput,
)

API = "https://track.customer.io/api/v1"
_CREDS = {"site_id": "site-1", "api_key": "key-1"}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_CREDS, **extra)


class TestManifest:
    def test_three_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_tools_match_actions(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_test_endpoint_is_reachability_check(self) -> None:
        # Customer.io requires Base64 Basic Auth which the credential
        # tester can't synthesize. The manifest ships a reachability
        # endpoint with success_codes=[200, 401] so the credential
        # save flow has something to test. Real auth runs at first
        # call in tools.py.
        te = manifest.auth_schemas[0].test_endpoint
        assert te is not None
        assert "customer.io" in te.url
        assert 401 in te.success_indicators.status_codes


@pytest.mark.asyncio
async def test_create_or_update_customer(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/customers/cust1",
        status_code=200,
        text="",
    )

    result_dict = await create_or_update_customer.ainvoke(
        _args(customer_id="cust1", email="alice@example.com", attributes={"plan": "pro"})
    )
    result = CreateOrUpdateCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.customer_id == "cust1"
    assert result.email == "alice@example.com"

    # Confirm Basic Auth header was sent
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"].startswith("Basic ")


@pytest.mark.asyncio
async def test_send_event(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/customers/cust1/events",
        status_code=200,
        text="",
    )

    result_dict = await send_event.ainvoke(
        _args(customer_id="cust1", event_name="signup", data={"plan": "pro"})
    )
    result = SendEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event_name == "signup"


@pytest.mark.asyncio
async def test_add_customers_to_segment(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/segments/seg1/add_customers?id_type=email",
        status_code=200,
        text="",
    )

    result_dict = await add_customers_to_segment.ainvoke(
        _args(segment_id="seg1", customer_ids=["a", "b", "c"], id_type="email")
    )
    result = AddCustomersToSegmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.customer_count == 3
    assert result.id_type == "email"


@pytest.mark.asyncio
async def test_segment_limit_enforced() -> None:
    too_many = [f"c{i}" for i in range(1001)]
    result_dict = await add_customers_to_segment.ainvoke(
        _args(segment_id="seg1", customer_ids=too_many)
    )
    result = AddCustomersToSegmentOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "1000" in result.error


@pytest.mark.asyncio
async def test_missing_creds_short_circuit() -> None:
    result_dict = await send_event.ainvoke(
        {"customer_id": "x", "event_name": "y", "site_id": "", "api_key": ""}
    )
    result = SendEventOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "credentials" in result.error.lower()
