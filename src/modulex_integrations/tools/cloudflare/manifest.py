"""Cloudflare integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _pagination(default_per_page: int = 20) -> dict[str, ParameterDef]:
    return {
        "page": ParameterDef(type="integer", description="Page number", default=1),
        "per_page": ParameterDef(
            type="integer",
            description="Results per page (max 50 for most endpoints)",
            default=default_per_page,
        ),
    }


manifest = IntegrationManifest(
    name="cloudflare",
    display_name="Cloudflare",
    description=(
        "Cloudflare DNS, WAF, zones, firewall rules, and load balancer "
        "management."
    ),
    version="1.0.0",
    author="ModuleX",
    app_url="https://cloudflare.com",
    logo="logos:cloudflare-icon",
    categories=[
        "Developer Tools & Infrastructure",
        "security",
        "infrastructure",
        "networking",
    ],
    actions=[
        ActionDefinition(
            name="list_zones",
            description="List, search, sort, and filter your Cloudflare zones",
            parameters={
                "name": ParameterDef(type="string", description="Zone name filter"),
                "status": ParameterDef(
                    type="string",
                    description=(
                        "Zone status: active, pending, initializing, moved, "
                        "deleted, deactivated"
                    ),
                ),
                "account_id": ParameterDef(
                    type="string", description="Account identifier filter"
                ),
                **_pagination(),
                "order": ParameterDef(
                    type="string",
                    description="Sort order: name, status, account.id, account.name",
                ),
                "direction": ParameterDef(
                    type="string", description="Sort direction (asc/desc)", default="asc"
                ),
            },
        ),
        ActionDefinition(
            name="create_dns_record",
            description="Create a new DNS record within a specific zone",
            parameters={
                "zone_id": ParameterDef(
                    type="string", description="Zone identifier", required=True
                ),
                "type": ParameterDef(
                    type="string",
                    description="DNS record type (A, AAAA, CNAME, TXT, MX, NS, SRV, etc.)",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string", description="DNS record name", required=True
                ),
                "content": ParameterDef(
                    type="string", description="DNS record content", required=True
                ),
                "ttl": ParameterDef(
                    type="integer", description="TTL (1 = automatic)", default=1
                ),
                "priority": ParameterDef(
                    type="integer", description="Priority for MX/SRV records"
                ),
                "proxied": ParameterDef(
                    type="boolean",
                    description="Proxy through Cloudflare",
                    default=False,
                ),
                "comment": ParameterDef(type="string", description="DNS record comment"),
                "tags": ParameterDef(type="array", description="DNS record tags"),
            },
        ),
        ActionDefinition(
            name="update_dns_record",
            description=(
                "Update an existing DNS record. Only provided fields are modified."
            ),
            parameters={
                "zone_id": ParameterDef(
                    type="string", description="Zone identifier", required=True
                ),
                "record_id": ParameterDef(
                    type="string", description="DNS record identifier", required=True
                ),
                "type": ParameterDef(type="string", description="DNS record type"),
                "name": ParameterDef(type="string", description="DNS record name"),
                "content": ParameterDef(type="string", description="DNS record content"),
                "ttl": ParameterDef(type="integer", description="TTL"),
                "priority": ParameterDef(
                    type="integer", description="Priority for MX/SRV records"
                ),
                "proxied": ParameterDef(
                    type="boolean", description="Proxy through Cloudflare"
                ),
                "comment": ParameterDef(type="string", description="DNS record comment"),
                "tags": ParameterDef(type="array", description="DNS record tags"),
            },
        ),
        ActionDefinition(
            name="delete_dns_record",
            description="Delete a DNS record within a specific zone",
            parameters={
                "zone_id": ParameterDef(
                    type="string", description="Zone identifier", required=True
                ),
                "record_id": ParameterDef(
                    type="string",
                    description="DNS record identifier to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_waf_lists",
            description="Fetch all WAF lists (no items) for an account",
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account identifier", required=True
                ),
            },
        ),
        ActionDefinition(
            name="create_waf_list",
            description="Create a new empty WAF list for the account",
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account identifier", required=True
                ),
                "name": ParameterDef(
                    type="string", description="Name of the list", required=True
                ),
                "kind": ParameterDef(
                    type="string",
                    description="List type: ip, redirect, hostname, asn",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string", description="Description of the list"
                ),
            },
        ),
        ActionDefinition(
            name="update_waf_list",
            description=(
                "Update the description of a WAF list (cannot update items)"
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account identifier", required=True
                ),
                "list_id": ParameterDef(
                    type="string", description="List identifier", required=True
                ),
                "description": ParameterDef(
                    type="string",
                    description="New description for the list",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_waf_list",
            description="Delete a WAF list",
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account identifier", required=True
                ),
                "list_id": ParameterDef(
                    type="string",
                    description="List identifier to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_accounts",
            description="List all accounts accessible to the user",
            parameters={
                **_pagination(),
                "direction": ParameterDef(
                    type="string",
                    description="Sort direction (asc/desc)",
                    default="asc",
                ),
            },
        ),
        ActionDefinition(
            name="list_account_members",
            description="List members of a given Cloudflare account",
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account identifier", required=True
                ),
                **_pagination(),
                "order": ParameterDef(
                    type="string",
                    description="Sort: user.first_name, user.last_name, user.email, status",
                    default="status",
                ),
                "direction": ParameterDef(
                    type="string",
                    description="Sort direction (asc/desc)",
                    default="asc",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Filter by status: accepted, pending, rejected",
                ),
            },
        ),
        ActionDefinition(
            name="list_firewall_rules",
            description="List firewall rules for a specific zone",
            parameters={
                "zone_id": ParameterDef(
                    type="string", description="Zone identifier", required=True
                ),
                **_pagination(25),
            },
        ),
        ActionDefinition(
            name="list_monitors",
            description="List all load-balancer monitors in a Cloudflare account",
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account identifier", required=True
                ),
                **_pagination(25),
            },
        ),
        ActionDefinition(
            name="list_pools",
            description="List all load balancer pools in a Cloudflare account",
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account identifier", required=True
                ),
                **_pagination(25),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Token Authentication",
            description="Authenticate using your Cloudflare API Token (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="CLOUDFLARE_API_TOKEN",
                    display_name="Cloudflare API Token",
                    description="Your Cloudflare API Token for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="x" * 40,
                    about_url=(
                        "https://developers.cloudflare.com/fundamentals/api/"
                        "get-started/create-token/"
                    ),
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.cloudflare.com/client/v4/user/tokens/verify",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["result.status"]
                ),
                cost_level="free",
                description="Validates API token via verify endpoint (no API cost)",
            ),
        ),
    ],
)
