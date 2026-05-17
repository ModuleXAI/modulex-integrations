"""Cloudflare LangChain ``@tool`` functions.

Every Cloudflare v4 endpoint returns the same envelope:
``{"success": bool, "errors": [...], "messages": [...], "result": ...,
   "result_info": {...}}``. The shared ``_call`` helper unwraps that
envelope into our standard ``(ok, error, result, pagination)`` tuple
so per-action code stays tiny.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "create_dns_record",
    "create_waf_list",
    "delete_dns_record",
    "delete_waf_list",
    "list_account_members",
    "list_accounts",
    "list_firewall_rules",
    "list_monitors",
    "list_pools",
    "list_waf_lists",
    "list_zones",
    "update_dns_record",
    "update_waf_list",
]

_API_BASE = "https://api.cloudflare.com/client/v4"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _empty_key_error(name: str) -> str:
    return (
        f"Cloudflare API token is empty for {name}. "
        "Please configure a valid credential."
    )


def _envelope_error(body: dict[str, Any]) -> str:
    errors = body.get("errors") or []
    if errors and isinstance(errors[0], dict):
        return str(errors[0].get("message") or "Unknown Cloudflare error")
    return "Unknown Cloudflare error"


async def _call(
    path: str,
    api_key: str,
    *,
    method: str = "GET",
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[bool, str | None, Any, dict[str, Any]]:
    """Single HTTP path for every Cloudflare action.

    Returns (ok, error, result_payload, result_info_dict).
    """
    url = f"{_API_BASE}{path}"
    method_upper = method.upper()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            if method_upper == "GET":
                response = await client.get(
                    url, headers=_headers(api_key), params=params
                )
            elif method_upper == "POST":
                response = await client.post(
                    url, headers=_headers(api_key), json=json_data or {}
                )
            elif method_upper == "PATCH":
                response = await client.patch(
                    url, headers=_headers(api_key), json=json_data or {}
                )
            elif method_upper == "PUT":
                response = await client.put(
                    url, headers=_headers(api_key), json=json_data or {}
                )
            elif method_upper == "DELETE":
                response = await client.delete(url, headers=_headers(api_key))
            else:
                return False, f"Unsupported HTTP method: {method}", None, {}
    except Exception as exc:
        return False, f"Cloudflare request failed: {exc}", None, {}

    try:
        body = response.json()
    except Exception as exc:
        return (
            False,
            f"Failed to parse Cloudflare response ({response.status_code}): {exc}",
            None,
            {},
        )

    if not isinstance(body, dict):
        return False, "Cloudflare returned a non-object response", None, {}

    if not body.get("success"):
        return False, _envelope_error(body), None, {}

    result_info = body.get("result_info") if isinstance(body.get("result_info"), dict) else {}
    return True, None, body.get("result"), result_info or {}


def _pagination_from(result_info: dict[str, Any]) -> dict[str, int | None]:
    return {
        "total": result_info.get("total_count"),
        "page": result_info.get("page"),
        "per_page": result_info.get("per_page"),
    }


# --- Input schemas ---------------------------------------------------------


class _AuthOnly(BaseModel):
    api_key: str = Field(description="Cloudflare API token (provided by credential system)")


class ListZonesInput(_AuthOnly):
    name: str | None = Field(default=None, description="Zone name filter")
    status: str | None = Field(default=None, description="Zone status filter")
    account_id: str | None = Field(default=None, description="Account ID filter")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=20, description="Per page (max 50)")
    order: str | None = Field(default=None, description="Sort field")
    direction: str = Field(default="asc", description="Sort direction")


class CreateDNSRecordInput(_AuthOnly):
    zone_id: str = Field(description="Zone identifier")
    type: str = Field(description="DNS record type")
    name: str = Field(description="DNS record name")
    content: str = Field(description="DNS record content")
    ttl: int = Field(default=1, description="TTL (1 = automatic)")
    priority: int | None = Field(default=None, description="MX/SRV priority")
    proxied: bool = Field(default=False, description="Proxy through Cloudflare")
    comment: str | None = Field(default=None, description="Comment")
    tags: list[str] | None = Field(default=None, description="Tags")


class UpdateDNSRecordInput(_AuthOnly):
    zone_id: str = Field(description="Zone identifier")
    record_id: str = Field(description="DNS record identifier")
    type: str | None = Field(default=None, description="DNS record type")
    name: str | None = Field(default=None, description="DNS record name")
    content: str | None = Field(default=None, description="DNS record content")
    ttl: int | None = Field(default=None, description="TTL")
    priority: int | None = Field(default=None, description="MX/SRV priority")
    proxied: bool | None = Field(default=None, description="Proxy through Cloudflare")
    comment: str | None = Field(default=None, description="Comment")
    tags: list[str] | None = Field(default=None, description="Tags")


class DeleteDNSRecordInput(_AuthOnly):
    zone_id: str = Field(description="Zone identifier")
    record_id: str = Field(description="DNS record identifier to delete")


class ListWAFListsInput(_AuthOnly):
    account_id: str = Field(description="Account identifier")


class CreateWAFListInput(_AuthOnly):
    account_id: str = Field(description="Account identifier")
    name: str = Field(description="List name")
    kind: str = Field(description="List type (ip/redirect/hostname/asn)")
    description: str | None = Field(default=None, description="List description")


class UpdateWAFListInput(_AuthOnly):
    account_id: str = Field(description="Account identifier")
    list_id: str = Field(description="List identifier")
    description: str = Field(description="New description for the list")


class DeleteWAFListInput(_AuthOnly):
    account_id: str = Field(description="Account identifier")
    list_id: str = Field(description="List identifier to delete")


class ListAccountsInput(_AuthOnly):
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=20, description="Per page (max 50)")
    direction: str = Field(default="asc", description="Sort direction")


class ListAccountMembersInput(_AuthOnly):
    account_id: str = Field(description="Account identifier")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=20, description="Per page (max 50)")
    order: str = Field(default="status", description="Sort field")
    direction: str = Field(default="asc", description="Sort direction")
    status: str | None = Field(default=None, description="Status filter")


class ListFirewallRulesInput(_AuthOnly):
    zone_id: str = Field(description="Zone identifier")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page (max 100)")


class ListMonitorsInput(_AuthOnly):
    account_id: str = Field(description="Account identifier")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page")


class ListPoolsInput(_AuthOnly):
    account_id: str = Field(description="Account identifier")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=25, description="Per page")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=ListZonesInput)
@serialize_pydantic_return
async def list_zones(
    api_key: str,
    name: str | None = None,
    status: str | None = None,
    account_id: str | None = None,
    page: int = 1,
    per_page: int = 20,
    order: str | None = None,
    direction: str = "asc",
) -> ListZonesOutput:
    """List, search, sort, and filter Cloudflare zones."""
    if not api_key or not api_key.strip():
        return ListZonesOutput(success=False, error=_empty_key_error("list_zones"))

    params: dict[str, Any] = {"page": page, "per_page": per_page, "direction": direction}
    if name:
        params["name"] = name
    if status:
        params["status"] = status
    if account_id:
        params["account.id"] = account_id
    if order:
        params["order"] = order

    ok, err, result, info = await _call("/zones", api_key, params=params)
    return ListZonesOutput(success=ok, error=err, result=result, **_pagination_from(info))


@tool(args_schema=CreateDNSRecordInput)
@serialize_pydantic_return
async def create_dns_record(
    api_key: str,
    zone_id: str,
    type: str,
    name: str,
    content: str,
    ttl: int = 1,
    priority: int | None = None,
    proxied: bool = False,
    comment: str | None = None,
    tags: list[str] | None = None,
) -> CreateDNSRecordOutput:
    """Create a new DNS record within a specific zone."""
    if not api_key or not api_key.strip():
        return CreateDNSRecordOutput(
            success=False, error=_empty_key_error("create_dns_record")
        )

    payload: dict[str, Any] = {
        "type": type,
        "name": name,
        "content": content,
        "ttl": ttl,
        "proxied": proxied,
    }
    if priority is not None:
        payload["priority"] = priority
    if comment is not None:
        payload["comment"] = comment
    if tags is not None:
        payload["tags"] = tags

    ok, err, result, _ = await _call(
        f"/zones/{zone_id}/dns_records", api_key, method="POST", json_data=payload
    )
    return CreateDNSRecordOutput(success=ok, error=err, result=result)


@tool(args_schema=UpdateDNSRecordInput)
@serialize_pydantic_return
async def update_dns_record(
    api_key: str,
    zone_id: str,
    record_id: str,
    type: str | None = None,
    name: str | None = None,
    content: str | None = None,
    ttl: int | None = None,
    priority: int | None = None,
    proxied: bool | None = None,
    comment: str | None = None,
    tags: list[str] | None = None,
) -> UpdateDNSRecordOutput:
    """Update an existing DNS record (only provided fields are modified)."""
    if not api_key or not api_key.strip():
        return UpdateDNSRecordOutput(
            success=False, error=_empty_key_error("update_dns_record")
        )

    payload: dict[str, Any] = {}
    if type is not None:
        payload["type"] = type
    if name is not None:
        payload["name"] = name
    if content is not None:
        payload["content"] = content
    if ttl is not None:
        payload["ttl"] = ttl
    if priority is not None:
        payload["priority"] = priority
    if proxied is not None:
        payload["proxied"] = proxied
    if comment is not None:
        payload["comment"] = comment
    if tags is not None:
        payload["tags"] = tags

    ok, err, result, _ = await _call(
        f"/zones/{zone_id}/dns_records/{record_id}",
        api_key,
        method="PATCH",
        json_data=payload,
    )
    return UpdateDNSRecordOutput(success=ok, error=err, result=result)


@tool(args_schema=DeleteDNSRecordInput)
@serialize_pydantic_return
async def delete_dns_record(
    api_key: str, zone_id: str, record_id: str
) -> DeleteDNSRecordOutput:
    """Delete a DNS record within a specific zone."""
    if not api_key or not api_key.strip():
        return DeleteDNSRecordOutput(
            success=False, error=_empty_key_error("delete_dns_record")
        )
    ok, err, result, _ = await _call(
        f"/zones/{zone_id}/dns_records/{record_id}", api_key, method="DELETE"
    )
    return DeleteDNSRecordOutput(success=ok, error=err, result=result)


@tool(args_schema=ListWAFListsInput)
@serialize_pydantic_return
async def list_waf_lists(api_key: str, account_id: str) -> ListWAFListsOutput:
    """List all WAF lists (no items) for an account."""
    if not api_key or not api_key.strip():
        return ListWAFListsOutput(success=False, error=_empty_key_error("list_waf_lists"))
    ok, err, result, _ = await _call(
        f"/accounts/{account_id}/rules/lists", api_key
    )
    return ListWAFListsOutput(success=ok, error=err, result=result)


@tool(args_schema=CreateWAFListInput)
@serialize_pydantic_return
async def create_waf_list(
    api_key: str,
    account_id: str,
    name: str,
    kind: str,
    description: str | None = None,
) -> CreateWAFListOutput:
    """Create a new empty WAF list for the account."""
    if not api_key or not api_key.strip():
        return CreateWAFListOutput(
            success=False, error=_empty_key_error("create_waf_list")
        )

    payload: dict[str, Any] = {"name": name, "kind": kind}
    if description is not None:
        payload["description"] = description

    ok, err, result, _ = await _call(
        f"/accounts/{account_id}/rules/lists",
        api_key,
        method="POST",
        json_data=payload,
    )
    return CreateWAFListOutput(success=ok, error=err, result=result)


@tool(args_schema=UpdateWAFListInput)
@serialize_pydantic_return
async def update_waf_list(
    api_key: str, account_id: str, list_id: str, description: str
) -> UpdateWAFListOutput:
    """Update the description of a WAF list."""
    if not api_key or not api_key.strip():
        return UpdateWAFListOutput(
            success=False, error=_empty_key_error("update_waf_list")
        )
    ok, err, result, _ = await _call(
        f"/accounts/{account_id}/rules/lists/{list_id}",
        api_key,
        method="PUT",
        json_data={"description": description},
    )
    return UpdateWAFListOutput(success=ok, error=err, result=result)


@tool(args_schema=DeleteWAFListInput)
@serialize_pydantic_return
async def delete_waf_list(
    api_key: str, account_id: str, list_id: str
) -> DeleteWAFListOutput:
    """Delete a WAF list."""
    if not api_key or not api_key.strip():
        return DeleteWAFListOutput(
            success=False, error=_empty_key_error("delete_waf_list")
        )
    ok, err, result, _ = await _call(
        f"/accounts/{account_id}/rules/lists/{list_id}", api_key, method="DELETE"
    )
    return DeleteWAFListOutput(success=ok, error=err, result=result)


@tool(args_schema=ListAccountsInput)
@serialize_pydantic_return
async def list_accounts(
    api_key: str, page: int = 1, per_page: int = 20, direction: str = "asc"
) -> ListAccountsOutput:
    """List all accounts accessible to the user."""
    if not api_key or not api_key.strip():
        return ListAccountsOutput(success=False, error=_empty_key_error("list_accounts"))
    ok, err, result, info = await _call(
        "/accounts",
        api_key,
        params={"page": page, "per_page": per_page, "direction": direction},
    )
    return ListAccountsOutput(
        success=ok, error=err, result=result, **_pagination_from(info)
    )


@tool(args_schema=ListAccountMembersInput)
@serialize_pydantic_return
async def list_account_members(
    api_key: str,
    account_id: str,
    page: int = 1,
    per_page: int = 20,
    order: str = "status",
    direction: str = "asc",
    status: str | None = None,
) -> ListAccountMembersOutput:
    """List members of a given Cloudflare account."""
    if not api_key or not api_key.strip():
        return ListAccountMembersOutput(
            success=False, error=_empty_key_error("list_account_members")
        )
    params: dict[str, Any] = {
        "page": page,
        "per_page": per_page,
        "order": order,
        "direction": direction,
    }
    if status:
        params["status"] = status
    ok, err, result, info = await _call(
        f"/accounts/{account_id}/members", api_key, params=params
    )
    return ListAccountMembersOutput(
        success=ok, error=err, result=result, **_pagination_from(info)
    )


@tool(args_schema=ListFirewallRulesInput)
@serialize_pydantic_return
async def list_firewall_rules(
    api_key: str, zone_id: str, page: int = 1, per_page: int = 25
) -> ListFirewallRulesOutput:
    """List firewall rules for a specific zone."""
    if not api_key or not api_key.strip():
        return ListFirewallRulesOutput(
            success=False, error=_empty_key_error("list_firewall_rules")
        )
    ok, err, result, info = await _call(
        f"/zones/{zone_id}/firewall/rules",
        api_key,
        params={"page": page, "per_page": per_page},
    )
    return ListFirewallRulesOutput(
        success=ok, error=err, result=result, **_pagination_from(info)
    )


@tool(args_schema=ListMonitorsInput)
@serialize_pydantic_return
async def list_monitors(
    api_key: str, account_id: str, page: int = 1, per_page: int = 25
) -> ListMonitorsOutput:
    """List all load-balancer monitors in a Cloudflare account."""
    if not api_key or not api_key.strip():
        return ListMonitorsOutput(success=False, error=_empty_key_error("list_monitors"))
    ok, err, result, info = await _call(
        f"/accounts/{account_id}/load_balancers/monitors",
        api_key,
        params={"page": page, "per_page": per_page},
    )
    return ListMonitorsOutput(
        success=ok, error=err, result=result, **_pagination_from(info)
    )


@tool(args_schema=ListPoolsInput)
@serialize_pydantic_return
async def list_pools(
    api_key: str, account_id: str, page: int = 1, per_page: int = 25
) -> ListPoolsOutput:
    """List all load balancer pools in a Cloudflare account."""
    if not api_key or not api_key.strip():
        return ListPoolsOutput(success=False, error=_empty_key_error("list_pools"))
    ok, err, result, info = await _call(
        f"/accounts/{account_id}/load_balancers/pools",
        api_key,
        params={"page": page, "per_page": per_page},
    )
    return ListPoolsOutput(
        success=ok, error=err, result=result, **_pagination_from(info)
    )
