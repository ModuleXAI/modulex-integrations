"""CoinMarketCap integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.coinmarketcap.manifest import manifest
from modulex_integrations.tools.coinmarketcap.tools import (
    get_cryptocurrency_metadata,
    id_map,
    latest_listings,
    latest_quotes,
)

TOOLS = (
    get_cryptocurrency_metadata,
    id_map,
    latest_listings,
    latest_quotes,
)

__all__ = [
    "TOOLS",
    "get_cryptocurrency_metadata",
    "id_map",
    "latest_listings",
    "latest_quotes",
    "manifest",
]
