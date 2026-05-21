"""Happy-path tests for every google_ad_manager @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_ad_manager import (
    TOOLS,
    create_report,
    list_network_options,
    manifest,
)
from modulex_integrations.tools.google_ad_manager.outputs import (
    CreateReportOutput,
    ListNetworkOptionsOutput,
)

API = "https://admanager.googleapis.com/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
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
async def test_create_report(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/networks/12345/reports",
        json={
            # TODO: fill in a representative response shape from the Google Ad Manager API docs
            "name": "networks/12345/reports/67890",
            "visibility": "SAVED",
            "reportDefinition": {},
        },
    )

    result_dict = await create_report.ainvoke(
        _args(
            parent="networks/12345",
            name="networks/12345/reports/67890",
            visibility="SAVED",
            dimensions=["DATE"],
            metrics=["IMPRESSIONS"],
            report_type="HISTORICAL",
            date_range="relative",
            relative="LAST_7_DAYS",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateReportOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None


@pytest.mark.asyncio
async def test_list_network_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/networks",
        json={
            # TODO: fill in a representative response shape from the Google Ad Manager API docs
            "networks": [
                {"networkCode": "12345", "displayName": "My Network"},
                {"networkCode": "67890", "displayName": "Other Network"},
            ],
        },
    )

    result_dict = await list_network_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListNetworkOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.networks) == 2
    assert "My Network" in result.networks


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_create_report_empty_credentials():  # type: ignore[no-untyped-def]
    """Empty access_token returns inline error without hitting the API."""
    result_dict = await create_report.ainvoke(
        _args(
            auth_data={},
            parent="networks/12345",
            name="networks/12345/reports/67890",
            visibility="SAVED",
            dimensions=["DATE"],
            metrics=["IMPRESSIONS"],
            report_type="HISTORICAL",
            date_range="relative",
            relative="LAST_7_DAYS",
        )
    )
    assert isinstance(result_dict, dict)
    result = CreateReportOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error.lower()
