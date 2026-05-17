"""Tests for the Cloudflare integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.cloudflare import (
    TOOLS,
    create_dns_record,
    create_waf_list,
    delete_dns_record,
    delete_waf_list,
    list_account_members,
    list_accounts,
    list_firewall_rules,
    list_monitors,
    list_pools,
    list_waf_lists,
    list_zones,
    manifest,
    update_dns_record,
    update_waf_list,
)
from modulex_integrations.tools.cloudflare.outputs import (
    CreateDNSRecordOutput,
    CreateWAFListOutput,
    DeleteDNSRecordOutput,
    DeleteWAFListOutput,
    ListAccountMembersOutput,
    ListAccountsOutput,
    ListFirewallRulesOutput,
    ListMonitorsOutput,
    ListPoolsOutput,
    ListWAFListsOutput,
    ListZonesOutput,
    UpdateDNSRecordOutput,
    UpdateWAFListOutput,
)

API = "https://api.cloudflare.com/client/v4"
_API_KEY = "cf-fake-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _ok(result: Any, **info: Any) -> dict[str, Any]:
    body = {"success": True, "errors": [], "messages": [], "result": result}
    if info:
        body["result_info"] = info
    return body


class TestManifest:
    def test_manifest_exposes_thirteen_actions(self) -> None:
        assert len(manifest.actions) == 13

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_list_zones(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/zones?page=1&per_page=20&direction=asc",
        json=_ok(
            [{"id": "Z1", "name": "example.com", "status": "active"}],
            total_count=1,
            page=1,
            per_page=20,
        ),
    )
    result_dict = await list_zones.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListZonesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.result[0]["name"] == "example.com"


@pytest.mark.asyncio
async def test_list_zones_envelope_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/zones?page=1&per_page=20&direction=asc",
        json={
            "success": False,
            "errors": [{"code": 10000, "message": "Authentication error"}],
        },
    )
    result = ListZonesOutput.model_validate(await list_zones.ainvoke(_args()))
    assert result.success is False
    assert result.error == "Authentication error"


@pytest.mark.asyncio
async def test_create_dns_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/zones/Z1/dns_records",
        json=_ok({"id": "R1", "type": "A", "name": "foo.example.com"}),
    )
    result = CreateDNSRecordOutput.model_validate(
        await create_dns_record.ainvoke(
            _args(zone_id="Z1", type="A", name="foo.example.com", content="1.2.3.4")
        )
    )
    assert result.success is True
    assert result.result["id"] == "R1"


@pytest.mark.asyncio
async def test_update_dns_record_patch(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/zones/Z1/dns_records/R1",
        json=_ok({"id": "R1", "content": "5.6.7.8"}),
    )
    result = UpdateDNSRecordOutput.model_validate(
        await update_dns_record.ainvoke(
            _args(zone_id="Z1", record_id="R1", content="5.6.7.8")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_dns_record(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/zones/Z1/dns_records/R1",
        json=_ok({"id": "R1"}),
    )
    result = DeleteDNSRecordOutput.model_validate(
        await delete_dns_record.ainvoke(_args(zone_id="Z1", record_id="R1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_waf_lists(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/A1/rules/lists",
        json=_ok([{"id": "L1", "name": "blocklist", "kind": "ip"}]),
    )
    result = ListWAFListsOutput.model_validate(
        await list_waf_lists.ainvoke(_args(account_id="A1"))
    )
    assert result.success is True
    assert result.result[0]["name"] == "blocklist"


@pytest.mark.asyncio
async def test_create_waf_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/accounts/A1/rules/lists",
        json=_ok({"id": "L1", "name": "blocklist", "kind": "ip"}),
    )
    result = CreateWAFListOutput.model_validate(
        await create_waf_list.ainvoke(
            _args(account_id="A1", name="blocklist", kind="ip", description="block IPs")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_waf_list_put(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/accounts/A1/rules/lists/L1",
        json=_ok({"id": "L1", "description": "new desc"}),
    )
    result = UpdateWAFListOutput.model_validate(
        await update_waf_list.ainvoke(
            _args(account_id="A1", list_id="L1", description="new desc")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_waf_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/accounts/A1/rules/lists/L1",
        json=_ok({"id": "L1"}),
    )
    result = DeleteWAFListOutput.model_validate(
        await delete_waf_list.ainvoke(_args(account_id="A1", list_id="L1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_accounts(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts?page=1&per_page=20&direction=asc",
        json=_ok(
            [{"id": "A1", "name": "Acme"}],
            total_count=1,
            page=1,
            per_page=20,
        ),
    )
    result = ListAccountsOutput.model_validate(await list_accounts.ainvoke(_args()))
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_list_account_members(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/accounts/A1/members"
            "?page=1&per_page=20&order=status&direction=asc&status=accepted"
        ),
        json=_ok(
            [{"id": "M1", "user": {"email": "a@x.io"}, "status": "accepted"}],
            total_count=1,
            page=1,
            per_page=20,
        ),
    )
    result = ListAccountMembersOutput.model_validate(
        await list_account_members.ainvoke(
            _args(account_id="A1", status="accepted")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_firewall_rules(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/zones/Z1/firewall/rules?page=1&per_page=25",
        json=_ok([{"id": "FR1", "action": "block"}]),
    )
    result = ListFirewallRulesOutput.model_validate(
        await list_firewall_rules.ainvoke(_args(zone_id="Z1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_monitors(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/A1/load_balancers/monitors?page=1&per_page=25",
        json=_ok([{"id": "MN1", "type": "http"}]),
    )
    result = ListMonitorsOutput.model_validate(
        await list_monitors.ainvoke(_args(account_id="A1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_pools(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/A1/load_balancers/pools?page=1&per_page=25",
        json=_ok([{"id": "P1", "enabled": True}]),
    )
    result = ListPoolsOutput.model_validate(
        await list_pools.ainvoke(_args(account_id="A1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = ListZonesOutput.model_validate(
        await list_zones.ainvoke({"api_key": ""})
    )
    assert result.success is False
    assert result.error is not None and "API token" in result.error
