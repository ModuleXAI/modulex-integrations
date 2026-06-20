"""Daytona integration manifest.

Daytona runs AI-generated code and shell commands in secure, isolated
cloud sandboxes. Authentication is a single API key (BYOK) sent as
``Authorization: Bearer <api_key>``.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_SANDBOX_ID_PARAM = ParameterDef(
    type="string",
    description="ID or name of the sandbox",
    required=True,
)


manifest = IntegrationManifest(
    name="daytona",
    display_name="Daytona",
    description=(
        "Run AI-generated code in secure, isolated cloud sandboxes. Create and "
        "manage sandboxes, execute shell commands, run Python, JavaScript, or "
        "TypeScript code, transfer files, and clone Git repositories."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:daytona-themed",
    app_url="https://www.daytona.io",
    categories=["Developer Tools & Infrastructure", "cloud", "automation"],
    actions=[
        ActionDefinition(
            name="create_sandbox",
            description=(
                "Create a new Daytona sandbox for running AI-generated code in isolation."
            ),
            parameters={
                "snapshot": ParameterDef(
                    type="string",
                    description=(
                        "ID or name of the snapshot to create the sandbox from "
                        "(uses default if empty)"
                    ),
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name for the sandbox (defaults to the sandbox ID)",
                ),
                "target": ParameterDef(
                    type="string",
                    description="Region where the sandbox will be created (e.g., us, eu)",
                ),
                "user": ParameterDef(
                    type="string", description="User associated with the sandbox"
                ),
                "env": ParameterDef(
                    type="object",
                    description="Environment variables to set in the sandbox as key-value pairs",
                ),
                "labels": ParameterDef(
                    type="object",
                    description="Labels to attach to the sandbox as key-value pairs",
                ),
                "cpu": ParameterDef(
                    type="integer", description="CPU cores to allocate to the sandbox"
                ),
                "memory": ParameterDef(
                    type="integer", description="Memory to allocate to the sandbox in GB"
                ),
                "disk": ParameterDef(
                    type="integer", description="Disk space to allocate to the sandbox in GB"
                ),
                "auto_stop_interval": ParameterDef(
                    type="integer",
                    description="Auto-stop interval in minutes (0 disables auto-stop)",
                ),
                "auto_archive_interval": ParameterDef(
                    type="integer",
                    description="Auto-archive interval in minutes (0 uses the maximum interval)",
                ),
                "auto_delete_interval": ParameterDef(
                    type="integer",
                    description=(
                        "Auto-delete interval in minutes (negative disables, 0 deletes "
                        "immediately on stop)"
                    ),
                ),
                "public": ParameterDef(
                    type="boolean",
                    description="Whether the sandbox HTTP preview is publicly accessible",
                ),
            },
        ),
        ActionDefinition(
            name="run_code",
            description=(
                "Run Python, JavaScript, or TypeScript code inside a Daytona sandbox."
            ),
            parameters={
                "sandbox_id": ParameterDef(
                    type="string",
                    description="ID of the sandbox to run the code in",
                    required=True,
                ),
                "code": ParameterDef(
                    type="string", description="Code to run", required=True
                ),
                "language": ParameterDef(
                    type="string",
                    description="Language of the code: python, javascript, or typescript",
                    required=True,
                ),
                "env": ParameterDef(
                    type="object",
                    description="Environment variables to set for the run as key-value pairs",
                ),
                "timeout": ParameterDef(
                    type="integer", description="Timeout in seconds (defaults to 10 seconds)"
                ),
            },
        ),
        ActionDefinition(
            name="execute_command",
            description="Execute a shell command inside a Daytona sandbox.",
            parameters={
                "sandbox_id": ParameterDef(
                    type="string",
                    description="ID of the sandbox to execute the command in",
                    required=True,
                ),
                "command": ParameterDef(
                    type="string", description="Shell command to execute", required=True
                ),
                "cwd": ParameterDef(
                    type="string",
                    description=(
                        "Working directory for the command (defaults to the sandbox "
                        "working directory)"
                    ),
                ),
                "env": ParameterDef(
                    type="object",
                    description="Environment variables to set for the command as key-value pairs",
                ),
                "timeout": ParameterDef(
                    type="integer", description="Timeout in seconds (defaults to 10 seconds)"
                ),
            },
        ),
        ActionDefinition(
            name="upload_file",
            description="Upload a file to a Daytona sandbox.",
            parameters={
                "sandbox_id": ParameterDef(
                    type="string",
                    description="ID of the sandbox to upload the file to",
                    required=True,
                ),
                "destination_path": ParameterDef(
                    type="string",
                    description=(
                        "Destination path in the sandbox (a trailing slash uploads into "
                        "that directory using the file name)"
                    ),
                    required=True,
                ),
                "file_content_base64": ParameterDef(
                    type="string",
                    description="Base64-encoded content of the file to upload",
                    required=True,
                ),
                "file_name": ParameterDef(
                    type="string", description="Optional file name override"
                ),
            },
        ),
        ActionDefinition(
            name="download_file",
            description=(
                "Download a file from a Daytona sandbox (returned base64-encoded inline)."
            ),
            parameters={
                "sandbox_id": ParameterDef(
                    type="string",
                    description="ID of the sandbox to download the file from",
                    required=True,
                ),
                "file_path": ParameterDef(
                    type="string",
                    description="Path of the file in the sandbox",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_files",
            description="List files in a directory of a Daytona sandbox.",
            parameters={
                "sandbox_id": ParameterDef(
                    type="string",
                    description="ID of the sandbox to list files in",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description=(
                        "Directory path to list (defaults to the sandbox working directory)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="git_clone",
            description="Clone a Git repository into a Daytona sandbox.",
            parameters={
                "sandbox_id": ParameterDef(
                    type="string",
                    description="ID of the sandbox to clone the repository into",
                    required=True,
                ),
                "url": ParameterDef(
                    type="string",
                    description="URL of the Git repository to clone",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Path in the sandbox to clone the repository into",
                    required=True,
                ),
                "branch": ParameterDef(
                    type="string",
                    description="Branch to clone (defaults to the default branch)",
                ),
                "commit_id": ParameterDef(
                    type="string",
                    description="Specific commit to check out after cloning",
                ),
                "username": ParameterDef(
                    type="string",
                    description="Username for authenticating to private repositories",
                ),
                "password": ParameterDef(
                    type="string",
                    description="Password or personal access token for private repositories",
                ),
            },
        ),
        ActionDefinition(
            name="list_sandboxes",
            description="List Daytona sandboxes in the organization.",
            parameters={
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of sandboxes to return (1-200)",
                ),
                "name": ParameterDef(
                    type="string",
                    description="Filter sandboxes by name prefix (case-insensitive)",
                ),
                "labels": ParameterDef(
                    type="object",
                    description="Filter sandboxes by labels as key-value pairs",
                ),
                "cursor": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous response",
                ),
            },
        ),
        ActionDefinition(
            name="get_sandbox",
            description="Get details of a Daytona sandbox.",
            parameters={"sandbox_id": _SANDBOX_ID_PARAM},
        ),
        ActionDefinition(
            name="start_sandbox",
            description="Start a stopped Daytona sandbox.",
            parameters={"sandbox_id": _SANDBOX_ID_PARAM},
        ),
        ActionDefinition(
            name="stop_sandbox",
            description="Stop a running Daytona sandbox.",
            parameters={"sandbox_id": _SANDBOX_ID_PARAM},
        ),
        ActionDefinition(
            name="delete_sandbox",
            description="Delete a Daytona sandbox.",
            parameters={"sandbox_id": _SANDBOX_ID_PARAM},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Daytona API key",
            setup_instructions=[
                "Go to https://app.daytona.io and sign up or log in",
                "Open the dashboard and navigate to the 'Keys' (API Keys) section",
                "Create a new API key and copy it",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="DAYTONA_API_KEY",
                    display_name="Daytona API Key",
                    description="Your Daytona API key from app.daytona.io",
                    required=True,
                    sensitive=True,
                    about_url="https://app.daytona.io",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://app.daytona.io/api/sandbox",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                params={"limit": "1"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates the API key by listing at most one sandbox",
            ),
        ),
    ],
)
