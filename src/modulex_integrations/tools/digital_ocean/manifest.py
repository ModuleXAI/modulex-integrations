"""DigitalOcean integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="digital_ocean",
    display_name="DigitalOcean",
    description="Cloud infrastructure platform for deploying and managing Droplets, domains, and SSH keys via the DigitalOcean API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:digital_ocean-themed",
    app_url="https://www.digitalocean.com",
    categories=["Developer Tools & Infrastructure", "cloud-infrastructure", "devops"],
    actions=[
        ActionDefinition(
            name="add_ssh_key",
            description="Add a new SSH key to your DigitalOcean account",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="A human-readable display name for this key, used to easily identify the SSH keys when they are displayed",
                    required=True,
                ),
                "public_key": ParameterDef(
                    type="string",
                    description="The entire public key string that will be embedded into the root user's authorized_keys file",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_domain",
            description="Create a new domain in DigitalOcean DNS",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The domain name in standard domain.TLD format (e.g. example.com)",
                    required=True,
                ),
                "ip_address": ParameterDef(
                    type="string",
                    description="An IP address to automatically create an A record pointing to the apex domain",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_droplet",
            description="Create a new DigitalOcean Droplet (virtual machine)",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Human-readable string used as the Droplet display name",
                    required=True,
                ),
                "region": ParameterDef(
                    type="string",
                    description="Region slug where the Droplet will be deployed (e.g. nyc1, sfo1, ams3)",
                    required=True,
                ),
                "image": ParameterDef(
                    type="string",
                    description="Image ID or slug for the base image (e.g. ubuntu-22-04-x64)",
                    required=True,
                ),
                "size": ParameterDef(
                    type="string",
                    description="Size slug for the Droplet (e.g. s-1vcpu-1gb)",
                    required=True,
                ),
                "volumes": ParameterDef(
                    type="array",
                    description="List of Block Storage volume IDs to attach to the Droplet",
                ),
                "ssh_keys": ParameterDef(
                    type="array",
                    description="List of SSH key IDs or fingerprints to embed in the Droplet's root account",
                ),
                "backups": ParameterDef(
                    type="boolean",
                    description="Whether automated backups should be enabled",
                ),
                "ipv6": ParameterDef(
                    type="boolean",
                    description="Whether IPv6 is enabled on the Droplet",
                ),
                "user_data": ParameterDef(
                    type="string",
                    description="Cloud-init user data or Bash script for first-boot configuration (max 64 KiB)",
                ),
                "private_networking": ParameterDef(
                    type="boolean",
                    description="Whether private networking is enabled for the Droplet",
                ),
                "monitoring": ParameterDef(
                    type="boolean",
                    description="Whether to install the DigitalOcean monitoring agent",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="List of tag names to apply to the Droplet after creation",
                ),
            },
        ),
        ActionDefinition(
            name="create_snapshot",
            description="Create a snapshot from an existing DigitalOcean Droplet",
            parameters={
                "droplet_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the Droplet to snapshot",
                    required=True,
                ),
                "snapshot_name": ParameterDef(
                    type="string",
                    description="The name to give the new snapshot",
                ),
            },
        ),
        ActionDefinition(
            name="list_all_droplets",
            description="List all Droplets in your DigitalOcean account",
            parameters={
                "tag_name": ParameterDef(
                    type="string",
                    description="Filter Droplets by a specific tag name",
                ),
                "page": ParameterDef(
                    type="integer",
                    description="Which page of paginated results to return",
                    default=1,
                ),
                "per_page": ParameterDef(
                    type="integer",
                    description="Number of items returned per page",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="turnonoff_droplet",
            description="Turn a Droplet's power on or off",
            parameters={
                "turn_on_off": ParameterDef(
                    type="string",
                    description="Power action to perform: power_on or power_off",
                    required=True,
                ),
                "droplet_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the Droplet to power on/off",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using DigitalOcean OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="DIGITAL_OCEAN_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="DigitalOcean OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://cloud.digitalocean.com/account/api/applications/new",
                ),
                EnvVar(
                    name="DIGITAL_OCEAN_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="DigitalOcean OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://cloud.digitalocean.com/account/api/applications/new",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://cloud.digitalocean.com/v1/oauth/authorize",
                token_url="https://cloud.digitalocean.com/v1/oauth/token",
                scopes=["read", "write"],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.digitalocean.com/v2/account",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["account"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated account info",
            ),
        ),
    ],
)
