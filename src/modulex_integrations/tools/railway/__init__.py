"""Railway integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.railway.manifest import manifest
from modulex_integrations.tools.railway.tools import (
    create_environment,
    create_project,
    create_service,
    delete_environment,
    delete_project,
    delete_service,
    delete_variable,
    deploy_service,
    get_deployment,
    get_deployment_logs,
    get_project,
    list_deployments,
    list_project_members,
    list_projects,
    list_variables,
    restart_deployment,
    rollback_deployment,
    transfer_project,
    update_project,
    upsert_variable,
)

TOOLS = (
    list_projects,
    get_project,
    create_project,
    update_project,
    delete_project,
    transfer_project,
    list_project_members,
    create_environment,
    delete_environment,
    create_service,
    delete_service,
    list_deployments,
    get_deployment,
    deploy_service,
    restart_deployment,
    rollback_deployment,
    get_deployment_logs,
    list_variables,
    upsert_variable,
    delete_variable,
)

__all__ = [
    "TOOLS",
    "create_environment",
    "create_project",
    "create_service",
    "delete_environment",
    "delete_project",
    "delete_service",
    "delete_variable",
    "deploy_service",
    "get_deployment",
    "get_deployment_logs",
    "get_project",
    "list_deployments",
    "list_project_members",
    "list_projects",
    "list_variables",
    "manifest",
    "restart_deployment",
    "rollback_deployment",
    "transfer_project",
    "update_project",
    "upsert_variable",
]
