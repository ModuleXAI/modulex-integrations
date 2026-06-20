"""Happy-path tests per action + failure-path and empty-credential tests.

RevenueCat returns proper HTTP status codes; the tools wrap non-2xx and
timeouts into ``success=False`` + ``error`` rather than raising.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.revenuecat import (
    TOOLS,
    create_purchase,
    defer_google_subscription,
    delete_customer,
    get_customer,
    grant_entitlement,
    list_offerings,
    manifest,
    refund_google_subscription,
    revoke_entitlement,
    revoke_google_subscription,
    update_subscriber_attributes,
)
from modulex_integrations.tools.revenuecat.outputs import (
    CreatePurchaseOutput,
    DeferGoogleSubscriptionOutput,
    DeleteCustomerOutput,
    GetCustomerOutput,
    GrantEntitlementOutput,
    ListOfferingsOutput,
    RefundGoogleSubscriptionOutput,
    RevokeEntitlementOutput,
    RevokeGoogleSubscriptionOutput,
    UpdateSubscriberAttributesOutput,
)

API = "https://api.revenuecat.com/v1"
_API_KEY = "sk_fake-api-key"

_SUBSCRIBER = {
    "first_seen": "2024-01-01T00:00:00Z",
    "last_seen": "2024-06-01T00:00:00Z",
    "original_app_user_id": "user_123",
    "management_url": "https://apps.apple.com/account/subscriptions",
    "subscriptions": {
        "monthly_sub": {
            "expires_date": "2999-01-01T00:00:00Z",
            "grace_period_expires_date": None,
            "store": "play_store",
        }
    },
    "entitlements": {
        "premium": {
            "expires_date": "2999-01-01T00:00:00Z",
            "product_identifier": "monthly_sub",
        }
    },
    "non_subscriptions": {},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_10_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_has_only_one_auth_schema(self) -> None:
        # Key-based tools ship exactly one ApiKeyAuthSchema (no modulex_key).
        assert len(manifest.auth_schemas) == 1


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_get_customer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/subscribers/user_123",
        json={"request_date": "2024-06-15T00:00:00Z", "subscriber": _SUBSCRIBER},
    )

    result_dict = await get_customer.ainvoke(_args(app_user_id="user_123"))
    assert isinstance(result_dict, dict)

    result = GetCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.subscriber is not None
    assert result.subscriber.original_app_user_id == "user_123"
    assert result.metadata is not None
    assert result.metadata.active_entitlements == 1
    assert result.metadata.active_subscriptions == 1

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_delete_customer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/subscribers/user_123",
        json={"deleted": True, "app_user_id": "user_123"},
    )

    result_dict = await delete_customer.ainvoke(_args(app_user_id="user_123"))
    assert isinstance(result_dict, dict)

    result = DeleteCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True
    assert result.app_user_id == "user_123"


@pytest.mark.asyncio
async def test_create_purchase(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/receipts",
        json={"subscriber": _SUBSCRIBER, "customer": {"original_app_user_id": "user_123"}},
    )

    result_dict = await create_purchase.ainvoke(
        _args(
            app_user_id="user_123",
            fetch_token="token_abc",
            platform="android",
            product_id="monthly_sub",
            price=9.99,
            currency="USD",
        )
    )
    assert isinstance(result_dict, dict)

    result = CreatePurchaseOutput.model_validate(result_dict)
    assert result.success is True
    assert result.subscriber is not None
    assert result.customer == {"original_app_user_id": "user_123"}

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-Platform"] == "android"
    body = sent.read().decode()
    assert "fetch_token" in body
    assert "9.99" in body


@pytest.mark.asyncio
async def test_grant_entitlement(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscribers/user_123/entitlements/premium/promotional",
        json={"subscriber": _SUBSCRIBER},
    )

    result_dict = await grant_entitlement.ainvoke(
        _args(app_user_id="user_123", entitlement_identifier="premium", duration="monthly")
    )
    assert isinstance(result_dict, dict)

    result = GrantEntitlementOutput.model_validate(result_dict)
    assert result.success is True
    assert result.subscriber is not None


@pytest.mark.asyncio
async def test_grant_entitlement_requires_one_time_param() -> None:
    result_dict = await grant_entitlement.ainvoke(
        _args(app_user_id="user_123", entitlement_identifier="premium")
    )
    result = GrantEntitlementOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "duration or end_time_ms" in result.error


@pytest.mark.asyncio
async def test_revoke_entitlement(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscribers/user_123/entitlements/premium/revoke_promotionals",
        json={"subscriber": _SUBSCRIBER},
    )

    result_dict = await revoke_entitlement.ainvoke(
        _args(app_user_id="user_123", entitlement_identifier="premium")
    )
    assert isinstance(result_dict, dict)

    result = RevokeEntitlementOutput.model_validate(result_dict)
    assert result.success is True
    assert result.subscriber is not None


@pytest.mark.asyncio
async def test_list_offerings(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/subscribers/user_123/offerings",
        json={
            "current_offering_id": "default",
            "offerings": [
                {
                    "identifier": "default",
                    "description": "Default offering",
                    "packages": [
                        {
                            "identifier": "$rc_monthly",
                            "platform_product_identifier": "monthly_sub",
                        }
                    ],
                }
            ],
        },
    )

    result_dict = await list_offerings.ainvoke(_args(app_user_id="user_123"))
    assert isinstance(result_dict, dict)

    result = ListOfferingsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.current_offering_id == "default"
    assert result.offerings[0].identifier == "default"
    assert result.offerings[0].packages[0].identifier == "$rc_monthly"
    assert result.metadata is not None
    assert result.metadata.count == 1


@pytest.mark.asyncio
async def test_update_subscriber_attributes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscribers/user_123/attributes",
        json={},
    )

    result_dict = await update_subscriber_attributes.ainvoke(
        _args(
            app_user_id="user_123",
            attributes='{"$email": {"value": "a@b.com", "updated_at_ms": 1709195668093}}',
        )
    )
    assert isinstance(result_dict, dict)

    result = UpdateSubscriberAttributesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.updated is True
    assert result.app_user_id == "user_123"

    sent = httpx_mock.get_requests()[0]
    assert '"attributes"' in sent.read().decode()


@pytest.mark.asyncio
async def test_update_subscriber_attributes_invalid_json() -> None:
    result_dict = await update_subscriber_attributes.ainvoke(
        _args(app_user_id="user_123", attributes="not-json")
    )
    result = UpdateSubscriberAttributesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "valid JSON" in result.error


@pytest.mark.asyncio
async def test_defer_google_subscription(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscribers/user_123/subscriptions/monthly_sub/defer",
        json={"subscriber": _SUBSCRIBER},
    )

    result_dict = await defer_google_subscription.ainvoke(
        _args(app_user_id="user_123", product_id="monthly_sub", extend_by_days=7)
    )
    assert isinstance(result_dict, dict)

    result = DeferGoogleSubscriptionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.subscriber is not None

    sent = httpx_mock.get_requests()[0]
    assert "extend_by_days" in sent.read().decode()


@pytest.mark.asyncio
async def test_defer_google_subscription_rejects_out_of_range() -> None:
    result_dict = await defer_google_subscription.ainvoke(
        _args(app_user_id="user_123", product_id="monthly_sub", extend_by_days=999)
    )
    result = DeferGoogleSubscriptionOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "1 and 365" in result.error


@pytest.mark.asyncio
async def test_refund_google_subscription(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscribers/user_123/transactions/GPA.1234/refund",
        json={"value": {"subscriber": _SUBSCRIBER}},
    )

    result_dict = await refund_google_subscription.ainvoke(
        _args(app_user_id="user_123", store_transaction_id="GPA.1234")
    )
    assert isinstance(result_dict, dict)

    result = RefundGoogleSubscriptionOutput.model_validate(result_dict)
    assert result.success is True
    # Verifies the {value: {subscriber}} envelope is unwrapped correctly.
    assert result.subscriber is not None
    assert result.subscriber.original_app_user_id == "user_123"


@pytest.mark.asyncio
async def test_revoke_google_subscription(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/subscribers/user_123/subscriptions/monthly_sub/revoke",
        json={"subscriber": _SUBSCRIBER},
    )

    result_dict = await revoke_google_subscription.ainvoke(
        _args(app_user_id="user_123", product_id="monthly_sub")
    )
    assert isinstance(result_dict, dict)

    result = RevokeGoogleSubscriptionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.subscriber is not None


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_get_customer_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/subscribers/user_123",
        status_code=401,
        json={"code": 7220, "message": "Invalid API Key."},
    )

    result_dict = await get_customer.ainvoke(_args(app_user_id="user_123"))
    assert isinstance(result_dict, dict)

    result = GetCustomerOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Invalid API Key" in result.error


@pytest.mark.asyncio
async def test_get_customer_validates_empty_api_key() -> None:
    result_dict = await get_customer.ainvoke({"app_user_id": "user_123", "api_key": ""})
    assert isinstance(result_dict, dict)

    result = GetCustomerOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
