"""New Relic integration for the modulex runtime."""
from __future__ import annotations

from modulex_integrations.tools.new_relic.manifest import manifest
from modulex_integrations.tools.new_relic.tools import (
    create_deployment_event,
    get_entity,
    nrql_query,
    search_entities,
)

TOOLS = (nrql_query, search_entities, get_entity, create_deployment_event)

__all__ = [
    "TOOLS",
    "create_deployment_event",
    "get_entity",
    "manifest",
    "nrql_query",
    "search_entities",
]
