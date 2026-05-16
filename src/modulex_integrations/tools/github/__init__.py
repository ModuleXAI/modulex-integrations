"""GitHub integration — discovered by the modulex runtime via the
``modulex.tools`` entry point declared in the root ``pyproject.toml``.

The runtime imports this module, then reads:

- ``manifest`` — an :class:`~modulex_integrations.schema.IntegrationManifest`
  describing the integration's metadata, actions, and auth schemas.
- ``TOOLS`` — a tuple of LangChain ``StructuredTool`` objects, one per
  action.
"""
from modulex_integrations.tools.github.manifest import manifest
from modulex_integrations.tools.github.tools import (
    create_branch,
    create_commit,
    create_issue,
    create_pull_request,
    create_repository,
    delete_repository,
    get_file_content,
    get_issue,
    get_pull_request,
    get_repository,
    list_issues,
    list_pull_requests,
    list_repositories,
    merge_pull_request,
    search_code,
    update_issue,
)

TOOLS = (
    list_repositories,
    create_repository,
    delete_repository,
    get_repository,
    list_issues,
    create_issue,
    get_issue,
    update_issue,
    list_pull_requests,
    create_pull_request,
    get_pull_request,
    merge_pull_request,
    create_branch,
    get_file_content,
    create_commit,
    search_code,
)

__all__ = [
    "TOOLS",
    "create_branch",
    "create_commit",
    "create_issue",
    "create_pull_request",
    "create_repository",
    "delete_repository",
    "get_file_content",
    "get_issue",
    "get_pull_request",
    "get_repository",
    "list_issues",
    "list_pull_requests",
    "list_repositories",
    "manifest",
    "merge_pull_request",
    "search_code",
    "update_issue",
]
