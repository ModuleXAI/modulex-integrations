"""Amazon Alexa integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.amazon_alexa.manifest import manifest
from modulex_integrations.tools.amazon_alexa.tools import (
    get_simulation_results,
    simulate_skill,
)

TOOLS = (
    simulate_skill,
    get_simulation_results,
)

__all__ = [
    "TOOLS",
    "get_simulation_results",
    "manifest",
    "simulate_skill",
]
