"""Cloudflare integration."""
from modulex_integrations.tools.cloudflare.manifest import manifest
from modulex_integrations.tools.cloudflare.tools import (
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
    update_dns_record,
    update_waf_list,
)

TOOLS = (
    list_zones,
    create_dns_record,
    update_dns_record,
    delete_dns_record,
    list_waf_lists,
    create_waf_list,
    update_waf_list,
    delete_waf_list,
    list_accounts,
    list_account_members,
    list_firewall_rules,
    list_monitors,
    list_pools,
)

__all__ = [
    "TOOLS",
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
    "manifest",
    "update_dns_record",
    "update_waf_list",
]
