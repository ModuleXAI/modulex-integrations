"""Tests for the Short.io integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.short_io import (
    TOOLS,
    create_link,
    delete_link,
    expire_link,
    get_domain_statistics,
    get_link_info,
    list_domains,
    list_links,
    manifest,
    update_link,
)
from modulex_integrations.tools.short_io.outputs import (
    CreateLinkOutput,
    DeleteLinkOutput,
    ExpireLinkOutput,
    GetDomainStatisticsOutput,
    GetLinkInfoOutput,
    ListDomainsOutput,
    ListLinksOutput,
    UpdateLinkOutput,
)

API = "https://api.short.io"
STATS = "https://api-v2.short.cm"
_API_KEY = "sk_shortio_fake_key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _link_payload(path: str = "abc", link_id: str = "L1") -> dict[str, Any]:
    return {
        "originalURL": "https://example.com",
        "path": path,
        "idString": "abc",
        "id": link_id,
        "shortURL": f"https://my.short.io/{path}",
        "secureShortURL": f"https://my.short.io/{path}",
        "cloaking": False,
        "title": "Example",
        "tags": [],
        "createdAt": "2026-05-16T00:00:00Z",
        "DomainId": 42,
        "OwnerId": 99,
    }


class TestManifest:
    def test_manifest_exposes_eight_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_create_link(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{API}/links", status_code=200, json=_link_payload()
    )

    result_dict = await create_link.ainvoke(
        _args(domain="my.short.io", original_url="https://example.com")
    )
    assert isinstance(result_dict, dict)
    result = CreateLinkOutput.model_validate(result_dict)
    assert result.success is True
    assert result.link is not None
    assert result.link.shortURL == "https://my.short.io/abc"


@pytest.mark.asyncio
async def test_create_link_handles_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/links",
        status_code=400,
        json={"message": "path already taken"},
    )
    result = CreateLinkOutput.model_validate(
        await create_link.ainvoke(
            _args(domain="my.short.io", original_url="https://example.com", path="taken")
        )
    )
    assert result.success is False
    assert result.error is not None and "path already taken" in result.error


@pytest.mark.asyncio
async def test_update_link(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/links/L1",
        json=_link_payload(path="renamed", link_id="L1"),
    )
    result = UpdateLinkOutput.model_validate(
        await update_link.ainvoke(_args(link_id="L1", path="renamed"))
    )
    assert result.success is True
    assert result.link is not None and result.link.path == "renamed"


@pytest.mark.asyncio
async def test_delete_link(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/links/L1", status_code=204, text=""
    )
    result = DeleteLinkOutput.model_validate(
        await delete_link.ainvoke(_args(link_id="L1"))
    )
    assert result.success is True
    assert result.link_id == "L1"


@pytest.mark.asyncio
async def test_delete_link_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/links/L1",
        status_code=404,
        json={"error": "link not found"},
    )
    result = DeleteLinkOutput.model_validate(
        await delete_link.ainvoke(_args(link_id="L1"))
    )
    assert result.success is False
    assert result.error is not None and "link not found" in result.error


@pytest.mark.asyncio
async def test_expire_link(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/links/L1",
        json={
            "originalURL": "https://example.com",
            "path": "abc",
            "id": "L1",
            "shortURL": "https://my.short.io/abc",
            "expiresAt": 1769904000000,
            "expiredURL": "https://example.com/expired",
        },
    )
    result = ExpireLinkOutput.model_validate(
        await expire_link.ainvoke(
            _args(
                link_id="L1",
                expires_at="2026-12-31",
                expired_url="https://example.com/expired",
            )
        )
    )
    assert result.success is True
    assert result.link is not None
    assert result.link.expiredURL == "https://example.com/expired"


@pytest.mark.asyncio
async def test_get_link_info(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/links/expand?domain=my.short.io&path=abc",
        json=_link_payload(),
    )
    result = GetLinkInfoOutput.model_validate(
        await get_link_info.ainvoke(_args(domain="my.short.io", path="/abc"))
    )
    assert result.success is True
    assert result.link is not None and result.link.id == "L1"


@pytest.mark.asyncio
async def test_list_links(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/links?domain_id=42&limit=150",
        json={"links": [_link_payload(), _link_payload(path="def", link_id="L2")]},
    )
    result = ListLinksOutput.model_validate(
        await list_links.ainvoke(_args(domain_id=42))
    )
    assert result.success is True
    assert result.count == 2
    assert {link.id for link in result.links} == {"L1", "L2"}


@pytest.mark.asyncio
async def test_list_domains(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/domains",
        json=[
            {"id": 1, "hostname": "my.short.io", "protocol": "https", "created": "2026-01-01"},
            {"id": 2, "hostname": "links.example.com", "protocol": "https", "created": "2026-02-01"},
        ],
    )
    result = ListDomainsOutput.model_validate(
        await list_domains.ainvoke(_args())
    )
    assert result.success is True
    assert result.count == 2
    assert result.domains[0].hostname == "my.short.io"


@pytest.mark.asyncio
async def test_get_domain_statistics(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{STATS}/statistics/domain/42?period=last30",
        json={"clicks": 1234, "humanClicks": 1000, "links": 50},
    )
    result = GetDomainStatisticsOutput.model_validate(
        await get_domain_statistics.ainvoke(_args(domain_id=42))
    )
    assert result.success is True
    assert result.statistics is not None
    assert result.statistics["clicks"] == 1234


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = CreateLinkOutput.model_validate(
        await create_link.ainvoke(
            {"api_key": "", "domain": "my.short.io", "original_url": "https://example.com"}
        )
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
