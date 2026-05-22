"""Happy-path tests for every google_search_console @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_search_console import (
    TOOLS,
    manifest,
    retrieve_site_performance_data,
    submit_url_for_indexing,
)
from modulex_integrations.tools.google_search_console.outputs import (
    RetrieveSitePerformanceDataOutput,
    SubmitUrlForIndexingOutput,
)

_SEARCH_ANALYTICS_URL = "https://searchconsole.googleapis.com/webmasters/v3/sites"
_INDEXING_URL = "https://indexing.googleapis.com/v3/urlNotifications:publish"

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
async def test_retrieve_site_performance_data(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{_SEARCH_ANALYTICS_URL}/sc-domain%3Aexample.com/searchAnalytics/query",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "rows": [
                {
                    "keys": ["example query"],
                    "clicks": 100.0,
                    "impressions": 1000.0,
                    "ctr": 0.1,
                    "position": 3.5,
                }
            ],
            "responseAggregationType": "auto",
        },
    )

    result_dict = await retrieve_site_performance_data.ainvoke(
        _args(
            site_url="sc-domain:example.com",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
    )

    assert isinstance(result_dict, dict)
    result = RetrieveSitePerformanceDataOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.rows) == 1
    assert result.rows[0].clicks == 100.0


@pytest.mark.asyncio
async def test_submit_url_for_indexing(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=_INDEXING_URL,
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "urlNotificationMetadata": {
                "url": "https://example.com/page",
                "latestUpdate": {
                    "type": "URL_UPDATED",
                    "notifyTime": "2024-01-15T10:00:00Z",
                },
            },
        },
    )

    result_dict = await submit_url_for_indexing.ainvoke(
        _args(
            site_url="https://example.com/page",
            notification_type="URL_UPDATED",
        )
    )

    assert isinstance(result_dict, dict)
    result = SubmitUrlForIndexingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.url_notification_metadata is not None
    assert result.url_notification_metadata.url == "https://example.com/page"


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_retrieve_site_performance_data_empty_credentials():  # type: ignore[no-untyped-def]
    """Empty access_token should return success=False without hitting the wire."""
    result_dict = await retrieve_site_performance_data.ainvoke(
        _args(
            auth_data={},
            site_url="sc-domain:example.com",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
    )
    assert isinstance(result_dict, dict)
    result = RetrieveSitePerformanceDataOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
