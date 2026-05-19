"""GitLab integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.gitlab.manifest import manifest
from modulex_integrations.tools.gitlab.tools import (
    create_branch,
    create_epic,
    create_issue,
    get_issue,
    get_repo_branch,
    list_commits,
    list_groups,
    list_project_members,
    list_repo_branches,
    search_issues,
    update_epic,
    update_issue,
)

TOOLS = (
    create_branch,
    create_epic,
    create_issue,
    get_issue,
    get_repo_branch,
    list_commits,
    list_groups,
    list_project_members,
    list_repo_branches,
    search_issues,
    update_epic,
    update_issue,
)

__all__ = [
    "TOOLS",
    "create_branch",
    "create_epic",
    "create_issue",
    "get_issue",
    "get_repo_branch",
    "list_commits",
    "list_groups",
    "list_project_members",
    "list_repo_branches",
    "manifest",
    "search_issues",
    "update_epic",
    "update_issue",
]
