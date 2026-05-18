"""Google Analytics integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_analytics.manifest import manifest
from modulex_integrations.tools.google_analytics.tools import (
    create_ga4_property,
    create_key_event,
    list_account_options,
    list_property_options,
    run_report,
    run_report_in_ga4,
)

TOOLS = (
    list_account_options,
    list_property_options,
    create_ga4_property,
    create_key_event,
    run_report,
    run_report_in_ga4,
)

__all__ = [
    "TOOLS",
    "create_ga4_property",
    "create_key_event",
    "list_account_options",
    "list_property_options",
    "manifest",
    "run_report",
    "run_report_in_ga4",
]
