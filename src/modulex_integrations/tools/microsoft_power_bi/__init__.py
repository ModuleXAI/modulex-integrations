"""Microsoft Power BI integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_power_bi.manifest import manifest
from modulex_integrations.tools.microsoft_power_bi.tools import (
    add_rows_to_push_dataset,
    execute_dax_query,
    export_report,
    get_refresh_history,
    get_reports_by_id,
    list_dashboards,
    list_datasets,
    list_reports,
    list_workspaces,
    refresh_dataset,
)

TOOLS = (
    add_rows_to_push_dataset,
    execute_dax_query,
    export_report,
    get_refresh_history,
    get_reports_by_id,
    list_dashboards,
    list_datasets,
    list_reports,
    list_workspaces,
    refresh_dataset,
)

__all__ = [
    "TOOLS",
    "add_rows_to_push_dataset",
    "execute_dax_query",
    "export_report",
    "get_refresh_history",
    "get_reports_by_id",
    "list_dashboards",
    "list_datasets",
    "list_reports",
    "list_workspaces",
    "manifest",
    "refresh_dataset",
]
