"""PagerDuty integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.pagerduty.manifest import manifest
from modulex_integrations.tools.pagerduty.tools import (
    acknowledge_incident,
    find_oncall_user,
    resolve_incident,
    trigger_incident,
)

TOOLS = (
    trigger_incident,
    acknowledge_incident,
    resolve_incident,
    find_oncall_user,
)

__all__ = [
    "TOOLS",
    "acknowledge_incident",
    "find_oncall_user",
    "manifest",
    "resolve_incident",
    "trigger_incident",
]
