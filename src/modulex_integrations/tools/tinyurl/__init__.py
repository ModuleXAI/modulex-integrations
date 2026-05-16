"""TinyURL integration."""
from modulex_integrations.tools.tinyurl.manifest import manifest
from modulex_integrations.tools.tinyurl.tools import (
    create_shortened_link,
    retrieve_link_analytics,
    update_link_metadata,
)

TOOLS = (create_shortened_link, retrieve_link_analytics, update_link_metadata)

__all__ = [
    "TOOLS",
    "create_shortened_link",
    "manifest",
    "retrieve_link_analytics",
    "update_link_metadata",
]
