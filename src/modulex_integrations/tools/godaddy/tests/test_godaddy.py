"""Happy-path tests for every godaddy @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.godaddy import (
    TOOLS,
    check_domain_availability,
    list_domains,
    list_tlds_options,
    manifest,
    renew_domain,
    suggest_domains,
)
from modulex_integrations.tools.godaddy.outputs import (
    CheckDomainAvailabilityOutput,
    ListDomainsOutput,
    ListTldsOptionsOutput,
    RenewDomainOutput,
    SuggestDomainsOutput,
)

API = "https://api.godaddy.com"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "api_key": "fake_key",
        "api_secret": "fake_secret",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_5_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_check_domain_availability(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/domains/available?domain=example.com",
        json={
            # TODO: fill in a representative response from the GoDaddy API docs
            "available": True,
            "domain": "example.com",
            "definitive": False,
            "price": 1199,
            "currency": "USD",
            "period": 1,
        },
    )

    result_dict = await check_domain_availability.ainvoke(_args(domain="example.com"))

    assert isinstance(result_dict, dict)
    result = CheckDomainAvailabilityOutput.model_validate(result_dict)
    assert result.success is True
    assert result.available is True
    assert result.domain == "example.com"


@pytest.mark.asyncio
async def test_list_domains(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/domains",
        json=[
            # TODO: fill in representative domain objects from the GoDaddy API docs
            {
                "domain": "mydomain.com",
                "status": "ACTIVE",
                "expires": "2027-01-01T00:00:00Z",
                "createdAt": "2020-01-01T00:00:00Z",
                "renewable": True,
            },
        ],
    )

    result_dict = await list_domains.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListDomainsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.domains) == 1
    assert result.domains[0].domain == "mydomain.com"


@pytest.mark.asyncio
async def test_list_tlds_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/domains/tlds",
        json=[
            # TODO: fill in representative TLD objects from the GoDaddy API docs
            {"name": "com", "type": "GENERIC"},
            {"name": "net", "type": "GENERIC"},
        ],
    )

    result_dict = await list_tlds_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTldsOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.tlds) == 2
    assert result.tlds[0].name == "com"


@pytest.mark.asyncio
async def test_renew_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/domains/example.com/renew",
        json={
            # TODO: fill in a representative renewal response from the GoDaddy API docs
            "orderId": 12345,
            "itemCount": 1,
            "total": 1199,
            "currency": "USD",
        },
    )

    result_dict = await renew_domain.ainvoke(_args(domain="example.com"))

    assert isinstance(result_dict, dict)
    result = RenewDomainOutput.model_validate(result_dict)
    assert result.success is True
    assert result.order_id == 12345


@pytest.mark.asyncio
async def test_suggest_domains(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/domains/suggest?query=mysite",
        json=[
            # TODO: fill in representative suggestion objects from the GoDaddy API docs
            {"domain": "mysite.com"},
            {"domain": "mysite.net"},
        ],
    )

    result_dict = await suggest_domains.ainvoke(_args(query="mysite"))

    assert isinstance(result_dict, dict)
    result = SuggestDomainsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.suggestions) == 2


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_check_domain_availability_empty_credentials():  # type: ignore[no-untyped-def]
    """Empty credentials should short-circuit without hitting the wire."""
    result_dict = await check_domain_availability.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {"api_key": "", "api_secret": ""},
            "domain": "example.com",
        }
    )

    assert isinstance(result_dict, dict)
    result = CheckDomainAvailabilityOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
