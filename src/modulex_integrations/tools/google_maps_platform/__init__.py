"""Google Maps Platform integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_maps_platform.manifest import manifest
from modulex_integrations.tools.google_maps_platform.tools import (
    get_place_details,
    search_places,
)

TOOLS = (
    search_places,
    get_place_details,
)

__all__ = [
    "TOOLS",
    "get_place_details",
    "manifest",
    "search_places",
]
