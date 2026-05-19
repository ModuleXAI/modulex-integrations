"""Postman integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.postman.manifest import manifest
from modulex_integrations.tools.postman.tools import (
    create_environment,
    list_workspace_id_options,
    run_monitor,
    update_variable,
)

TOOLS = (
    create_environment,
    list_workspace_id_options,
    run_monitor,
    update_variable,
)

__all__ = [
    "TOOLS",
    "create_environment",
    "list_workspace_id_options",
    "manifest",
    "run_monitor",
    "update_variable",
]
