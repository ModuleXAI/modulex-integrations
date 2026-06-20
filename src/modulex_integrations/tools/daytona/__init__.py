"""Daytona integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.daytona.manifest import manifest
from modulex_integrations.tools.daytona.tools import (
    create_sandbox,
    delete_sandbox,
    download_file,
    execute_command,
    get_sandbox,
    git_clone,
    list_files,
    list_sandboxes,
    run_code,
    start_sandbox,
    stop_sandbox,
    upload_file,
)

TOOLS = (
    create_sandbox,
    run_code,
    execute_command,
    upload_file,
    download_file,
    list_files,
    git_clone,
    list_sandboxes,
    get_sandbox,
    start_sandbox,
    stop_sandbox,
    delete_sandbox,
)

__all__ = [
    "TOOLS",
    "create_sandbox",
    "delete_sandbox",
    "download_file",
    "execute_command",
    "get_sandbox",
    "git_clone",
    "list_files",
    "list_sandboxes",
    "manifest",
    "run_code",
    "start_sandbox",
    "stop_sandbox",
    "upload_file",
]
