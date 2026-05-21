"""Happy-path tests for every google_merchant_center @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_merchant_center import (
    TOOLS,
    create_product,
    manifest,
    update_product,
)
from modulex_integrations.tools.google_merchant_center.outputs import (
    CreateProductOutput,
    UpdateProductOutput,
)

API = "https://shoppingcontent.googleapis.com/content/v2.1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token", "merchant_id": "123456789"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_product(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/123456789/products",
        json={
            # TODO: fill in a representative response shape from the Google Shopping Content API docs
            "id": "online:en:US:offer123",
            "offerId": "offer123",
            "title": "Test Product",
            "contentLanguage": "en",
            "targetCountry": "US",
            "channel": "online",
        },
    )

    result_dict = await create_product.ainvoke(
        _args(
            offer_id="offer123",
            content_language="en",
            target_country="US",
            channel="online",
            title="Test Product",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["offerId"] == "offer123"


@pytest.mark.asyncio
async def test_update_product(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/123456789/products/online%3Aen%3AUS%3Aoffer123?updateMask=title",
        json={
            # TODO: fill in a representative response shape from the Google Shopping Content API docs
            "id": "online:en:US:offer123",
            "offerId": "offer123",
            "title": "Updated Product",
            "contentLanguage": "en",
            "targetCountry": "US",
            "channel": "online",
        },
    )

    result_dict = await update_product.ainvoke(
        _args(
            product_id="online:en:US:offer123",
            updated_values={"title": "Updated Product"},
            update_mask=["title"],
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["title"] == "Updated Product"


@pytest.mark.asyncio
async def test_create_product_missing_credentials():  # type: ignore[no-untyped-def]
    """Failure path: missing access_token returns error without hitting the wire."""
    result_dict = await create_product.ainvoke(
        _args(
            auth_data={"merchant_id": "123456789"},
            offer_id="offer123",
            content_language="en",
            target_country="US",
            channel="online",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateProductOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error
