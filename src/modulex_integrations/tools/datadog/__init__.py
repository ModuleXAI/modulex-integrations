"""Datadog integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.datadog.manifest import manifest
from modulex_integrations.tools.datadog.tools import (
    get_account_info,
    get_metric_data,
    post_metric_data,
    search_dashboards,
    search_events,
    search_hosts,
    search_incidents,
    search_logs,
    search_metrics,
    search_monitors,
    search_services,
)

TOOLS = (
    get_account_info,
    get_metric_data,
    post_metric_data,
    search_dashboards,
    search_events,
    search_hosts,
    search_incidents,
    search_logs,
    search_metrics,
    search_monitors,
    search_services,
)

__all__ = [
    "TOOLS",
    "get_account_info",
    "get_metric_data",
    "manifest",
    "post_metric_data",
    "search_dashboards",
    "search_events",
    "search_hosts",
    "search_incidents",
    "search_logs",
    "search_metrics",
    "search_monitors",
    "search_services",
]
