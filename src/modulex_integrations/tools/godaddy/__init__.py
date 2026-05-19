"""GoDaddy integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.godaddy.manifest import manifest
from modulex_integrations.tools.godaddy.tools import (
    check_domain_availability,
    list_domains,
    list_tlds_options,
    renew_domain,
    suggest_domains,
)

TOOLS = (
    check_domain_availability,
    list_domains,
    list_tlds_options,
    renew_domain,
    suggest_domains,
)

__all__ = [
    "TOOLS",
    "check_domain_availability",
    "list_domains",
    "list_tlds_options",
    "manifest",
    "renew_domain",
    "suggest_domains",
]
