"""DigitalOcean integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.digital_ocean.manifest import manifest
from modulex_integrations.tools.digital_ocean.tools import (
    add_ssh_key,
    create_domain,
    create_droplet,
    create_snapshot,
    list_all_droplets,
    turnonoff_droplet,
)

TOOLS = (
    add_ssh_key,
    create_domain,
    create_droplet,
    create_snapshot,
    list_all_droplets,
    turnonoff_droplet,
)

__all__ = [
    "TOOLS",
    "add_ssh_key",
    "create_domain",
    "create_droplet",
    "create_snapshot",
    "list_all_droplets",
    "manifest",
    "turnonoff_droplet",
]
