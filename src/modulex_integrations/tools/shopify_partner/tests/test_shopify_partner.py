"""Happy-path tests for every shopify_partner @tool, plus a manifest sanity check."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

import pytest

from modulex_integrations.tools.shopify_partner import (
    TOOLS,
    manifest,
    verify_webhook,
)
from modulex_integrations.tools.shopify_partner.outputs import (
    VerifyWebhookOutput,
)

_ORGANIZATION_ID = "12345678"
_API_KEY = "fake-api-key"
_APP_SECRET = "test-secret-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(organization_id=_ORGANIZATION_ID, api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


@pytest.mark.asyncio
async def test_verify_webhook_valid() -> None:
    payload = json.dumps({"shop_domain": "example.myshopify.com", "topic": "app/uninstalled"})
    expected_hmac = base64.b64encode(
        hmac.new(_APP_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")

    result_dict = await verify_webhook.ainvoke(
        _args(app_secret_key=_APP_SECRET, shopify_hmac=expected_hmac, body=payload)
    )

    assert isinstance(result_dict, dict)
    result = VerifyWebhookOutput.model_validate(result_dict)
    assert result.success is True
    assert result.valid is True


@pytest.mark.asyncio
async def test_verify_webhook_invalid_signature() -> None:
    payload = json.dumps({"shop_domain": "example.myshopify.com"})

    result_dict = await verify_webhook.ainvoke(
        _args(app_secret_key=_APP_SECRET, shopify_hmac="invalid-hmac-value", body=payload)
    )

    assert isinstance(result_dict, dict)
    result = VerifyWebhookOutput.model_validate(result_dict)
    assert result.success is True
    assert result.valid is False


@pytest.mark.asyncio
async def test_verify_webhook_empty_secret() -> None:
    result_dict = await verify_webhook.ainvoke(
        _args(app_secret_key="", shopify_hmac="anything", body="{}")
    )

    assert isinstance(result_dict, dict)
    result = VerifyWebhookOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "secret key" in result.error.lower()
