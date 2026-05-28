"""Shopify Partner LangChain @tool functions."""
from __future__ import annotations

import base64
import hashlib
import hmac

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.shopify_partner.outputs import (
    VerifyWebhookOutput,
)

__all__ = [
    "verify_webhook",
]


class VerifyWebhookInput(BaseModel):
    app_secret_key: str = Field(description="The secret key associated with the Shopify App receiving the webhook")
    shopify_hmac: str = Field(description="The value of the x-shopify-hmac-sha256 webhook request header")
    body: str = Field(description="The incoming webhook payload as a JSON string")
    organization_id: str = Field(description="Shopify Partner organization ID (provided by credential system)")
    api_key: str = Field(description="Shopify Partner API key (provided by credential system)")


@tool(args_schema=VerifyWebhookInput)
@serialize_pydantic_return
async def verify_webhook(
    app_secret_key: str,
    shopify_hmac: str,
    body: str,
    organization_id: str,
    api_key: str,
) -> VerifyWebhookOutput:
    """Verify an incoming webhook from Shopify by validating its HMAC-SHA256 signature."""
    if not app_secret_key or not app_secret_key.strip():
        return VerifyWebhookOutput(
            success=False,
            error="App secret key is empty. Please provide the Shopify App secret key.",
        )

    try:
        body_bytes = body.encode("utf-8")
    except Exception as exc:
        return VerifyWebhookOutput(
            success=False,
            error=f"Failed to encode body: {exc}",
        )

    computed = hmac.new(
        app_secret_key.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).digest()

    computed_b64 = base64.b64encode(computed).decode("utf-8")
    is_valid = hmac.compare_digest(computed_b64, shopify_hmac)

    return VerifyWebhookOutput(
        success=True,
        valid=is_valid,
    )
