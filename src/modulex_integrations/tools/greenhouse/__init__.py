"""Greenhouse integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.greenhouse.manifest import manifest
from modulex_integrations.tools.greenhouse.tools import (
    get_application,
    get_candidate,
    get_job,
    get_user,
    list_applications,
    list_candidates,
    list_departments,
    list_job_stages,
    list_jobs,
    list_offices,
    list_users,
)

TOOLS = (
    list_candidates,
    get_candidate,
    list_jobs,
    get_job,
    list_applications,
    get_application,
    list_users,
    get_user,
    list_departments,
    list_offices,
    list_job_stages,
)

__all__ = [
    "TOOLS",
    "get_application",
    "get_candidate",
    "get_job",
    "get_user",
    "list_applications",
    "list_candidates",
    "list_departments",
    "list_job_stages",
    "list_jobs",
    "list_offices",
    "list_users",
    "manifest",
]
