"""Sentry integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.sentry.manifest import manifest
from modulex_integrations.tools.sentry.tools import (
    list_issue_events,
    list_project_events,
    list_project_issues,
    update_issue,
)

TOOLS = (
    list_issue_events,
    list_project_events,
    list_project_issues,
    update_issue,
)

__all__ = [
    "TOOLS",
    "list_issue_events",
    "list_project_events",
    "list_project_issues",
    "manifest",
    "update_issue",
]
