"""Netlify integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.netlify.manifest import manifest
from modulex_integrations.tools.netlify.tools import (
    get_site,
    list_files,
    list_site_deploys,
    rollback_deploy,
)

TOOLS = (
    get_site,
    list_files,
    list_site_deploys,
    rollback_deploy,
)

__all__ = [
    "TOOLS",
    "get_site",
    "list_files",
    "list_site_deploys",
    "manifest",
    "rollback_deploy",
]
