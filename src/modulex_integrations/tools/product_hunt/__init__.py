"""Product Hunt integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.product_hunt.manifest import manifest
from modulex_integrations.tools.product_hunt.tools import (
    list_topic_options,
)

TOOLS = (list_topic_options,)

__all__ = [
    "TOOLS",
    "list_topic_options",
    "manifest",
]
