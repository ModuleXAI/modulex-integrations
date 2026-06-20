"""RevenueCat LangChain ``@tool`` functions.

Ten async tools wrapping the RevenueCat REST API v1
(``https://api.revenuecat.com/v1``). The modulex ``ToolExecutor``
injects an ``api_key: str`` directly (resolved from the user's
credential), not an ``auth_type``/``auth_data`` pair.

Auth: ``Authorization: Bearer <api_key>``.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.revenuecat.outputs import (
    CreatePurchaseOutput,
    DeferGoogleSubscriptionOutput,
    DeleteCustomerOutput,
    GetCustomerOutput,
    GrantEntitlementOutput,
    ListOfferingsOutput,
    Offering,
    OfferingPackage,
    OfferingsMetadata,
    RefundGoogleSubscriptionOutput,
    RevokeEntitlementOutput,
    RevokeGoogleSubscriptionOutput,
    Subscriber,
    SubscriberMetadata,
    UpdateSubscriberAttributesOutput,
)

__all__ = [
    "create_purchase",
    "defer_google_subscription",
    "delete_customer",
    "get_customer",
    "grant_entitlement",
    "list_offerings",
    "refund_google_subscription",
    "revoke_entitlement",
    "revoke_google_subscription",
    "update_subscriber_attributes",
]

_BASE_URL = "https://api.revenuecat.com/v1"
_TIMEOUT = 30.0


# --- Auth + shared helpers -------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _enc(value: str) -> str:
    """Path-segment encode (mirrors encodeURIComponent on the trimmed id)."""
    return quote(value.strip(), safe="")


def _error_message(response: httpx.Response) -> str:
    """RevenueCat returns ``{code, message}`` on 4xx/5xx."""
    try:
        body = response.json()
    except Exception:
        return f"RevenueCat API error ({response.status_code}): {response.text}"
    if isinstance(body, dict):
        message = body.get("message")
        code = body.get("code")
        if isinstance(message, str) and message:
            return f"{message} (code {code})" if code is not None else message
    return f"RevenueCat API error ({response.status_code}): {response.text}"


def _extract_subscriber(data: Any) -> dict[str, Any]:
    """Several v1 endpoints wrap responses in ``{value: {subscriber}}``;
    GET customer returns the same payload unwrapped. Handle both."""
    if not isinstance(data, dict):
        return {}
    wrapped = data.get("value")
    subscriber: Any = None
    if isinstance(wrapped, dict):
        subscriber = wrapped.get("subscriber")
    if subscriber is None:
        subscriber = data.get("subscriber")
    return subscriber if isinstance(subscriber, dict) else {}


def _extract_customer(data: Any) -> dict[str, Any] | None:
    """``POST /receipts`` may return a top-level ``customer`` object."""
    if not isinstance(data, dict):
        return None
    customer = data.get("customer")
    return customer if isinstance(customer, dict) else None


def _shape_subscriber(raw: dict[str, Any]) -> Subscriber:
    return Subscriber(
        first_seen=raw.get("first_seen"),
        last_seen=raw.get("last_seen"),
        original_app_user_id=raw.get("original_app_user_id"),
        original_application_version=raw.get("original_application_version"),
        original_purchase_date=raw.get("original_purchase_date"),
        management_url=raw.get("management_url"),
        subscriptions=raw.get("subscriptions") or {},
        entitlements=raw.get("entitlements") or {},
        non_subscriptions=raw.get("non_subscriptions") or {},
        other_purchases=raw.get("other_purchases") or {},
        subscriber_attributes=raw.get("subscriber_attributes"),
    )


def _parse_iso_ms(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).timestamp() * 1000.0
    except ValueError:
        return None


def _is_active_by_dates(
    now_ms: float,
    expires: Any,
    grace: Any,
    refunded_at: Any = None,
) -> bool:
    if refunded_at:
        return False
    expires_ms = _parse_iso_ms(expires)
    if expires_ms is None:
        return True
    if expires_ms > now_ms:
        return True
    grace_ms = _parse_iso_ms(grace)
    if grace_ms is not None and grace_ms > now_ms:
        return True
    return False


# --- Input schemas (args_schema for each @tool) ----------------------------


class GetCustomerInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber")
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")


class DeleteCustomerInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber to delete")
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")


class CreatePurchaseInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber")
    fetch_token: str = Field(
        description=(
            "For iOS, the base64-encoded receipt (or JWSTransaction for StoreKit2); "
            "for Android the purchase token; for Amazon the receipt; for Stripe the "
            "subscription or Checkout Session ID; for Roku the transaction ID; for "
            "Paddle the subscription or transaction ID"
        )
    )
    platform: str = Field(
        description=(
            "Platform of the purchase. One of: ios, android, amazon, macos, "
            "uikitformac, stripe, roku, paddle. Sent as the X-Platform header."
        )
    )
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")
    product_id: str | None = Field(
        default=None,
        description="Product identifier or SKU. Required for Google.",
    )
    price: float | None = Field(
        default=None, description="Price of the product. Required if you provide a currency."
    )
    currency: str | None = Field(
        default=None, description="ISO 4217 currency code. Required if you provide a price."
    )
    is_restore: bool | None = Field(
        default=None,
        description="Deprecated. Triggers configured restore behavior for shared fetch tokens.",
    )
    presented_offering_identifier: str | None = Field(
        default=None,
        description="Identifier of the offering presented to the customer at purchase time.",
    )
    payment_mode: str | None = Field(
        default=None,
        description="Payment mode: pay_as_you_go, pay_up_front, or free_trial.",
    )
    introductory_price: float | None = Field(
        default=None, description="Introductory price paid (if any)."
    )
    attributes: str | None = Field(
        default=None,
        description=(
            'JSON object of subscriber attributes to set alongside the purchase. '
            'Each key maps to {"value": string, "updated_at_ms": number}.'
        ),
    )
    updated_at_ms: int | None = Field(
        default=None,
        description="UNIX epoch ms used to resolve attribute conflicts at the request level.",
    )


class GrantEntitlementInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber")
    entitlement_identifier: str = Field(description="The entitlement identifier to grant")
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")
    duration: str | None = Field(
        default=None,
        description=(
            "Deprecated. Provide either duration or end_time_ms (end_time_ms preferred). "
            "One of: daily, three_day, weekly, two_week, monthly, two_month, three_month, "
            "six_month, yearly, lifetime."
        ),
    )
    end_time_ms: int | None = Field(
        default=None,
        description="Absolute end time in ms since Unix epoch. Use instead of duration.",
    )
    start_time_ms: int | None = Field(
        default=None,
        description="Deprecated. Optional start time in ms since Unix epoch, used with duration.",
    )


class RevokeEntitlementInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber")
    entitlement_identifier: str = Field(description="The entitlement identifier to revoke")
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")


class ListOfferingsInput(BaseModel):
    app_user_id: str = Field(description="An app user ID to retrieve offerings for")
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")
    platform: str | None = Field(
        default=None,
        description=(
            "X-Platform header value. One of: ios, android, amazon, stripe, roku, paddle. "
            "Required for legacy public API keys; ignored with app-specific keys."
        ),
    )


class UpdateSubscriberAttributesInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber")
    attributes: str = Field(
        description=(
            'JSON object of attributes to set. Each key maps to an object with "value" '
            '(string; null or empty deletes the attribute) and "updated_at_ms" (Unix '
            'epoch ms used for conflict resolution — required). Example: '
            '{"$email": {"value": "user@example.com", "updated_at_ms": 1709195668093}}'
        )
    )
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")


class DeferGoogleSubscriptionInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber")
    product_id: str = Field(
        description="The Google Play product identifier of the subscription to defer"
    )
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")
    extend_by_days: int | None = Field(
        default=None,
        description=(
            "Number of days to extend by (1-365). Provide extend_by_days or expiry_time_ms."
        ),
    )
    expiry_time_ms: int | None = Field(
        default=None,
        description=(
            "Absolute new expiry time in ms since Unix epoch. Use instead of extend_by_days."
        ),
    )


class RefundGoogleSubscriptionInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber")
    store_transaction_id: str = Field(
        description=(
            "The store transaction identifier of the purchase to refund "
            "(e.g., GPA.3309-9122-6177-45730 for Google Play)"
        )
    )
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")


class RevokeGoogleSubscriptionInput(BaseModel):
    app_user_id: str = Field(description="The app user ID of the subscriber")
    product_id: str = Field(
        description="The Google Play product identifier of the subscription to revoke"
    )
    api_key: str = Field(description="RevenueCat API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=GetCustomerInput)
@serialize_pydantic_return
async def get_customer(app_user_id: str, api_key: str) -> GetCustomerOutput:
    """Retrieve subscriber information by app user ID."""
    if not api_key or not api_key.strip():
        return GetCustomerOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    url = f"{_BASE_URL}/subscribers/{_enc(app_user_id)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=_headers(api_key))
        if response.status_code != 200:
            return GetCustomerOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return GetCustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCustomerOutput(success=False, error=f"get_customer failed: {exc}")

    subscriber = _shape_subscriber(_extract_subscriber(data))
    request_date = None
    if isinstance(data, dict):
        wrapped = data.get("value")
        if isinstance(wrapped, dict):
            request_date = wrapped.get("request_date")
        if request_date is None:
            request_date = data.get("request_date")
    now_ms = _parse_iso_ms(request_date)
    if now_ms is None:
        now_ms = datetime.now(UTC).timestamp() * 1000.0

    active_entitlements = sum(
        1
        for ent in subscriber.entitlements.values()
        if isinstance(ent, dict)
        and _is_active_by_dates(
            now_ms, ent.get("expires_date"), ent.get("grace_period_expires_date")
        )
    )
    active_subscriptions = sum(
        1
        for sub in subscriber.subscriptions.values()
        if isinstance(sub, dict)
        and _is_active_by_dates(
            now_ms,
            sub.get("expires_date"),
            sub.get("grace_period_expires_date"),
            sub.get("refunded_at"),
        )
    )

    return GetCustomerOutput(
        success=True,
        subscriber=subscriber,
        metadata=SubscriberMetadata(
            app_user_id=subscriber.original_app_user_id,
            first_seen=subscriber.first_seen,
            active_entitlements=active_entitlements,
            active_subscriptions=active_subscriptions,
        ),
    )


@tool(args_schema=DeleteCustomerInput)
@serialize_pydantic_return
async def delete_customer(app_user_id: str, api_key: str) -> DeleteCustomerOutput:
    """Permanently delete a subscriber and all associated data."""
    if not api_key or not api_key.strip():
        return DeleteCustomerOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    url = f"{_BASE_URL}/subscribers/{_enc(app_user_id)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(url, headers=_headers(api_key))
        if response.status_code != 200:
            return DeleteCustomerOutput(success=False, error=_error_message(response))
        try:
            body = response.json()
        except Exception:
            body = {}
    except httpx.TimeoutException:
        return DeleteCustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteCustomerOutput(success=False, error=f"delete_customer failed: {exc}")

    deleted = body.get("deleted") if isinstance(body, dict) else None
    returned_id = body.get("app_user_id") if isinstance(body, dict) else None
    return DeleteCustomerOutput(
        success=True,
        deleted=deleted if isinstance(deleted, bool) else True,
        app_user_id=returned_id if isinstance(returned_id, str) else app_user_id,
    )


@tool(args_schema=CreatePurchaseInput)
@serialize_pydantic_return
async def create_purchase(
    app_user_id: str,
    fetch_token: str,
    platform: str,
    api_key: str,
    product_id: str | None = None,
    price: float | None = None,
    currency: str | None = None,
    is_restore: bool | None = None,
    presented_offering_identifier: str | None = None,
    payment_mode: str | None = None,
    introductory_price: float | None = None,
    attributes: str | None = None,
    updated_at_ms: int | None = None,
) -> CreatePurchaseOutput:
    """Record a purchase (receipt) for a subscriber via the REST API."""
    if not api_key or not api_key.strip():
        return CreatePurchaseOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    body: dict[str, Any] = {
        "app_user_id": app_user_id,
        "fetch_token": fetch_token,
    }
    if product_id:
        body["product_id"] = product_id
    if price is not None:
        body["price"] = price
    if currency:
        body["currency"] = currency
    if is_restore is not None:
        body["is_restore"] = is_restore
    if presented_offering_identifier:
        body["presented_offering_identifier"] = presented_offering_identifier
    if payment_mode:
        body["payment_mode"] = payment_mode
    if introductory_price is not None:
        body["introductory_price"] = introductory_price
    if attributes is not None and attributes != "":
        try:
            body["attributes"] = json.loads(attributes)
        except (ValueError, TypeError):
            return CreatePurchaseOutput(
                success=False, error="attributes must be a valid JSON object"
            )
    if updated_at_ms is not None:
        body["updated_at_ms"] = updated_at_ms

    headers = _headers(api_key)
    if platform:
        headers["X-Platform"] = platform

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{_BASE_URL}/receipts", headers=headers, json=body)
        if response.status_code != 200:
            return CreatePurchaseOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return CreatePurchaseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreatePurchaseOutput(success=False, error=f"create_purchase failed: {exc}")

    return CreatePurchaseOutput(
        success=True,
        customer=_extract_customer(data),
        subscriber=_shape_subscriber(_extract_subscriber(data)),
    )


@tool(args_schema=GrantEntitlementInput)
@serialize_pydantic_return
async def grant_entitlement(
    app_user_id: str,
    entitlement_identifier: str,
    api_key: str,
    duration: str | None = None,
    end_time_ms: int | None = None,
    start_time_ms: int | None = None,
) -> GrantEntitlementOutput:
    """Grant a promotional entitlement to a subscriber."""
    if not api_key or not api_key.strip():
        return GrantEntitlementOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    has_end = end_time_ms is not None
    has_duration = bool(duration)
    if not has_duration and not has_end:
        return GrantEntitlementOutput(
            success=False,
            error="Provide either duration or end_time_ms to grant a promotional entitlement.",
        )
    if has_duration and has_end:
        return GrantEntitlementOutput(
            success=False,
            error="Provide only one of duration or end_time_ms — they cannot be used together.",
        )

    body: dict[str, Any] = {}
    if has_end:
        body["end_time_ms"] = end_time_ms
    elif has_duration:
        body["duration"] = duration
    if start_time_ms is not None:
        body["start_time_ms"] = start_time_ms

    url = (
        f"{_BASE_URL}/subscribers/{_enc(app_user_id)}"
        f"/entitlements/{_enc(entitlement_identifier)}/promotional"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=_headers(api_key), json=body)
        if response.status_code != 200:
            return GrantEntitlementOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return GrantEntitlementOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GrantEntitlementOutput(success=False, error=f"grant_entitlement failed: {exc}")

    return GrantEntitlementOutput(
        success=True, subscriber=_shape_subscriber(_extract_subscriber(data))
    )


@tool(args_schema=RevokeEntitlementInput)
@serialize_pydantic_return
async def revoke_entitlement(
    app_user_id: str,
    entitlement_identifier: str,
    api_key: str,
) -> RevokeEntitlementOutput:
    """Revoke all promotional entitlements for a specific entitlement identifier."""
    if not api_key or not api_key.strip():
        return RevokeEntitlementOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    url = (
        f"{_BASE_URL}/subscribers/{_enc(app_user_id)}"
        f"/entitlements/{_enc(entitlement_identifier)}/revoke_promotionals"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=_headers(api_key))
        if response.status_code != 200:
            return RevokeEntitlementOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return RevokeEntitlementOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RevokeEntitlementOutput(success=False, error=f"revoke_entitlement failed: {exc}")

    return RevokeEntitlementOutput(
        success=True, subscriber=_shape_subscriber(_extract_subscriber(data))
    )


@tool(args_schema=ListOfferingsInput)
@serialize_pydantic_return
async def list_offerings(
    app_user_id: str,
    api_key: str,
    platform: str | None = None,
) -> ListOfferingsOutput:
    """List all offerings configured for the project."""
    if not api_key or not api_key.strip():
        return ListOfferingsOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    headers = _headers(api_key)
    if platform:
        headers["X-Platform"] = platform

    url = f"{_BASE_URL}/subscribers/{_enc(app_user_id)}/offerings"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return ListOfferingsOutput(success=False, error=_error_message(response))
        raw = response.json()
    except httpx.TimeoutException:
        return ListOfferingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListOfferingsOutput(success=False, error=f"list_offerings failed: {exc}")

    data = raw
    if isinstance(raw, dict) and isinstance(raw.get("value"), dict):
        data = raw["value"]
    offerings_raw = data.get("offerings") if isinstance(data, dict) else None
    offerings_raw = offerings_raw if isinstance(offerings_raw, list) else []
    current_offering_id = data.get("current_offering_id") if isinstance(data, dict) else None

    offerings = [
        Offering(
            identifier=off.get("identifier") if isinstance(off, dict) else None,
            description=off.get("description") if isinstance(off, dict) else None,
            packages=[
                OfferingPackage(
                    identifier=pkg.get("identifier"),
                    platform_product_identifier=pkg.get("platform_product_identifier"),
                )
                for pkg in (off.get("packages") or [])
                if isinstance(pkg, dict)
            ]
            if isinstance(off, dict)
            else [],
        )
        for off in offerings_raw
    ]

    return ListOfferingsOutput(
        success=True,
        current_offering_id=current_offering_id,
        offerings=offerings,
        metadata=OfferingsMetadata(
            count=len(offerings), current_offering_id=current_offering_id
        ),
    )


@tool(args_schema=UpdateSubscriberAttributesInput)
@serialize_pydantic_return
async def update_subscriber_attributes(
    app_user_id: str,
    attributes: str,
    api_key: str,
) -> UpdateSubscriberAttributesOutput:
    """Update custom subscriber attributes (e.g., $email, $displayName, or custom pairs)."""
    if not api_key or not api_key.strip():
        return UpdateSubscriberAttributesOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    try:
        parsed_attributes = json.loads(attributes)
    except (ValueError, TypeError):
        return UpdateSubscriberAttributesOutput(
            success=False, error="attributes must be a valid JSON object"
        )

    url = f"{_BASE_URL}/subscribers/{_enc(app_user_id)}/attributes"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                url, headers=_headers(api_key), json={"attributes": parsed_attributes}
            )
        if response.status_code != 200:
            return UpdateSubscriberAttributesOutput(
                success=False, error=_error_message(response)
            )
    except httpx.TimeoutException:
        return UpdateSubscriberAttributesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateSubscriberAttributesOutput(
            success=False, error=f"update_subscriber_attributes failed: {exc}"
        )

    return UpdateSubscriberAttributesOutput(
        success=True, updated=True, app_user_id=app_user_id
    )


@tool(args_schema=DeferGoogleSubscriptionInput)
@serialize_pydantic_return
async def defer_google_subscription(
    app_user_id: str,
    product_id: str,
    api_key: str,
    extend_by_days: int | None = None,
    expiry_time_ms: int | None = None,
) -> DeferGoogleSubscriptionOutput:
    """Defer a Google Play subscription by extending its billing date (Google Play only)."""
    if not api_key or not api_key.strip():
        return DeferGoogleSubscriptionOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    has_extend = extend_by_days is not None
    has_expiry = expiry_time_ms is not None
    if not has_extend and not has_expiry:
        return DeferGoogleSubscriptionOutput(
            success=False,
            error="Provide either extend_by_days or expiry_time_ms to defer a subscription.",
        )
    if has_extend and has_expiry:
        return DeferGoogleSubscriptionOutput(
            success=False,
            error="Provide only one of extend_by_days or expiry_time_ms — not both.",
        )

    body: dict[str, Any] = {}
    if has_expiry:
        body["expiry_time_ms"] = expiry_time_ms
    elif has_extend:
        if extend_by_days is None or extend_by_days < 1 or extend_by_days > 365:
            return DeferGoogleSubscriptionOutput(
                success=False, error="extend_by_days must be an integer between 1 and 365."
            )
        body["extend_by_days"] = extend_by_days

    url = (
        f"{_BASE_URL}/subscribers/{_enc(app_user_id)}"
        f"/subscriptions/{_enc(product_id)}/defer"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=_headers(api_key), json=body)
        if response.status_code != 200:
            return DeferGoogleSubscriptionOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return DeferGoogleSubscriptionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeferGoogleSubscriptionOutput(
            success=False, error=f"defer_google_subscription failed: {exc}"
        )

    return DeferGoogleSubscriptionOutput(
        success=True, subscriber=_shape_subscriber(_extract_subscriber(data))
    )


@tool(args_schema=RefundGoogleSubscriptionInput)
@serialize_pydantic_return
async def refund_google_subscription(
    app_user_id: str,
    store_transaction_id: str,
    api_key: str,
) -> RefundGoogleSubscriptionOutput:
    """Refund a store transaction by its store transaction identifier and revoke access."""
    if not api_key or not api_key.strip():
        return RefundGoogleSubscriptionOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    url = (
        f"{_BASE_URL}/subscribers/{_enc(app_user_id)}"
        f"/transactions/{_enc(store_transaction_id)}/refund"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=_headers(api_key))
        if response.status_code != 200:
            return RefundGoogleSubscriptionOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return RefundGoogleSubscriptionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RefundGoogleSubscriptionOutput(
            success=False, error=f"refund_google_subscription failed: {exc}"
        )

    return RefundGoogleSubscriptionOutput(
        success=True, subscriber=_shape_subscriber(_extract_subscriber(data))
    )


@tool(args_schema=RevokeGoogleSubscriptionInput)
@serialize_pydantic_return
async def revoke_google_subscription(
    app_user_id: str,
    product_id: str,
    api_key: str,
) -> RevokeGoogleSubscriptionOutput:
    """Immediately revoke access to a Google Play subscription and issue a refund."""
    if not api_key or not api_key.strip():
        return RevokeGoogleSubscriptionOutput(
            success=False,
            error="RevenueCat API key is empty. Please configure a valid credential.",
        )

    url = (
        f"{_BASE_URL}/subscribers/{_enc(app_user_id)}"
        f"/subscriptions/{_enc(product_id)}/revoke"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=_headers(api_key))
        if response.status_code != 200:
            return RevokeGoogleSubscriptionOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return RevokeGoogleSubscriptionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RevokeGoogleSubscriptionOutput(
            success=False, error=f"revoke_google_subscription failed: {exc}"
        )

    return RevokeGoogleSubscriptionOutput(
        success=True, subscriber=_shape_subscriber(_extract_subscriber(data))
    )
