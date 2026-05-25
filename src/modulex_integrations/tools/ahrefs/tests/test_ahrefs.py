"""Happy-path tests for every ahrefs @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.ahrefs import (
    TOOLS,
    get_backlinks,
    get_backlinks_one_per_domain,
    get_referring_domains,
    manifest,
)
from modulex_integrations.tools.ahrefs.outputs import (
    GetBacklinksOnePerDomainOutput,
    GetBacklinksOutput,
    GetReferringDomainsOutput,
)

API = "https://api.ahrefs.com/v3"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_get_backlinks(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/site-explorer/all-backlinks?target=example.com&select=url_from%2Curl_to&mode=domain&limit=10&output=json",
        json={
            # TODO: fill in a representative response shape from the Ahrefs API docs
            "backlinks": [
                {
                    "url_from": "https://blog.example.org/post",
                    "url_to": "https://example.com",
                    "ahrefs_rank": 42,
                    "anchor": "Example",
                    "page_title": "A Blog Post",
                }
            ]
        },
    )

    result_dict = await get_backlinks.ainvoke(
        _args(target="example.com", select=["url_from", "url_to"], mode="domain", limit=10)
    )

    assert isinstance(result_dict, dict)
    result = GetBacklinksOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.backlinks) == 1
    assert result.backlinks[0].url_from == "https://blog.example.org/post"


@pytest.mark.asyncio
async def test_get_backlinks_one_per_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/site-explorer/all-backlinks?target=example.com&select=url_from%2Curl_to&mode=domain&limit=10&aggregation=1_per_domain&output=json",
        json={
            # TODO: fill in a representative response shape from the Ahrefs API docs
            "backlinks": [
                {
                    "url_from": "https://other.org/page",
                    "url_to": "https://example.com",
                    "ahrefs_rank": 99,
                    "anchor": "Link",
                    "page_title": "Other Page",
                }
            ]
        },
    )

    result_dict = await get_backlinks_one_per_domain.ainvoke(
        _args(target="example.com", select=["url_from", "url_to"], mode="domain", limit=10)
    )

    assert isinstance(result_dict, dict)
    result = GetBacklinksOnePerDomainOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.backlinks) == 1
    assert result.backlinks[0].ahrefs_rank == 99


@pytest.mark.asyncio
async def test_get_referring_domains(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/site-explorer/refdomains?target=example.com&select=domain%2Cdomain_rating&mode=domain&limit=10&output=json",
        json={
            # TODO: fill in a representative response shape from the Ahrefs API docs
            "refdomains": [
                {
                    "domain": "blog.example.org",
                    "domain_rating": 55.0,
                    "backlinks": 3,
                }
            ]
        },
    )

    result_dict = await get_referring_domains.ainvoke(
        _args(target="example.com", select=["domain", "domain_rating"], mode="domain", limit=10)
    )

    assert isinstance(result_dict, dict)
    result = GetReferringDomainsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.refdomains) == 1
    assert result.refdomains[0].domain == "blog.example.org"


# --- Failure-path tests -------------------------------------------------------


@pytest.mark.asyncio
async def test_get_backlinks_empty_credential() -> None:
    """Tool returns error envelope when access_token is missing."""
    result_dict = await get_backlinks.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}, "target": "example.com", "select": ["url_from"], "mode": "domain", "limit": 10}
    )
    assert isinstance(result_dict, dict)
    result = GetBacklinksOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error
