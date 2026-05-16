"""Short.io integration."""
from modulex_integrations.tools.short_io.manifest import manifest
from modulex_integrations.tools.short_io.tools import (
    create_link,
    delete_link,
    expire_link,
    get_domain_statistics,
    get_link_info,
    list_domains,
    list_links,
    update_link,
)

TOOLS = (
    create_link,
    update_link,
    delete_link,
    expire_link,
    get_link_info,
    list_links,
    list_domains,
    get_domain_statistics,
)

__all__ = [
    "TOOLS",
    "create_link",
    "delete_link",
    "expire_link",
    "get_domain_statistics",
    "get_link_info",
    "list_domains",
    "list_links",
    "manifest",
    "update_link",
]
