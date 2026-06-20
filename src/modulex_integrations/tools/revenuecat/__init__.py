"""RevenueCat integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.revenuecat.manifest import manifest
from modulex_integrations.tools.revenuecat.tools import (
    create_purchase,
    defer_google_subscription,
    delete_customer,
    get_customer,
    grant_entitlement,
    list_offerings,
    refund_google_subscription,
    revoke_entitlement,
    revoke_google_subscription,
    update_subscriber_attributes,
)

TOOLS = (
    get_customer,
    delete_customer,
    create_purchase,
    grant_entitlement,
    revoke_entitlement,
    list_offerings,
    update_subscriber_attributes,
    defer_google_subscription,
    refund_google_subscription,
    revoke_google_subscription,
)

__all__ = [
    "TOOLS",
    "create_purchase",
    "defer_google_subscription",
    "delete_customer",
    "get_customer",
    "grant_entitlement",
    "list_offerings",
    "manifest",
    "refund_google_subscription",
    "revoke_entitlement",
    "revoke_google_subscription",
    "update_subscriber_attributes",
]
