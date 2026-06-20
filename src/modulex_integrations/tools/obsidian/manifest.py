"""Obsidian integration manifest.

Exposes the Obsidian Local REST API plugin as a set of vault operations
(read, create, update, search, delete notes; periodic notes; commands;
active file). Authentication is a single API key (BYOK) issued by the
Local REST API plugin and sent as a bearer token; the plugin's base URL
is supplied per call as the ``base_url`` action parameter.
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


_BASE_URL_PARAM = ParameterDef(
    type="string",
    description="Base URL for the Obsidian Local REST API (e.g. https://127.0.0.1:27124)",
    required=True,
)


manifest = IntegrationManifest(
    name="obsidian",
    display_name="Obsidian",
    description=(
        "Read, create, update, search, and delete notes in your Obsidian vault. "
        "Manage periodic notes, execute commands, and patch content at specific "
        "locations. Requires the Obsidian Local REST API plugin."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:obsidian-themed",
    app_url="https://obsidian.md",
    categories=["Productivity & Collaboration", "note-taking", "knowledge-base"],
    actions=[
        ActionDefinition(
            name="list_files",
            description="List files and directories in your Obsidian vault.",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "path": ParameterDef(
                    type="string",
                    description=(
                        "Directory path relative to vault root. Leave empty to list the root."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_note",
            description="Retrieve the content of a note from your Obsidian vault.",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "filename": ParameterDef(
                    type="string",
                    description='Path to the note relative to vault root (e.g. "folder/note.md")',
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_note",
            description="Create or replace a note in your Obsidian vault.",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "filename": ParameterDef(
                    type="string",
                    description='Path for the note relative to vault root (e.g. "folder/note.md")',
                    required=True,
                ),
                "content": ParameterDef(
                    type="string",
                    description="Markdown content for the note",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="append_note",
            description="Append content to an existing note in your Obsidian vault.",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "filename": ParameterDef(
                    type="string",
                    description='Path to the note relative to vault root (e.g. "folder/note.md")',
                    required=True,
                ),
                "content": ParameterDef(
                    type="string",
                    description="Markdown content to append to the note",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="patch_note",
            description=(
                "Insert or replace content at a specific heading, block reference, or "
                "frontmatter field in a note."
            ),
            parameters={
                "base_url": _BASE_URL_PARAM,
                "filename": ParameterDef(
                    type="string",
                    description='Path to the note relative to vault root (e.g. "folder/note.md")',
                    required=True,
                ),
                "content": ParameterDef(
                    type="string",
                    description="Content to insert at the target location",
                    required=True,
                ),
                "operation": ParameterDef(
                    type="string",
                    description="How to insert content: append, prepend, or replace",
                    required=True,
                ),
                "target_type": ParameterDef(
                    type="string",
                    description="Type of target: heading, block, or frontmatter",
                    required=True,
                ),
                "target": ParameterDef(
                    type="string",
                    description=(
                        "Target identifier (heading text, block reference ID, or "
                        "frontmatter field name)"
                    ),
                    required=True,
                ),
                "target_delimiter": ParameterDef(
                    type="string",
                    description='Delimiter for nested headings (default: "::")',
                ),
                "trim_target_whitespace": ParameterDef(
                    type="boolean",
                    description="Whether to trim whitespace from target before matching",
                ),
            },
        ),
        ActionDefinition(
            name="delete_note",
            description="Delete a note from your Obsidian vault.",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "filename": ParameterDef(
                    type="string",
                    description="Path to the note to delete relative to vault root",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search",
            description="Search for text across notes in your Obsidian vault.",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "query": ParameterDef(
                    type="string",
                    description="Text to search for across vault notes",
                    required=True,
                ),
                "context_length": ParameterDef(
                    type="integer",
                    description="Number of characters of context around each match (default: 100)",
                ),
            },
        ),
        ActionDefinition(
            name="get_active",
            description="Retrieve the content of the currently active file in Obsidian.",
            parameters={"base_url": _BASE_URL_PARAM},
        ),
        ActionDefinition(
            name="append_active",
            description="Append content to the currently active file in Obsidian.",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "content": ParameterDef(
                    type="string",
                    description="Markdown content to append to the active file",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="patch_active",
            description=(
                "Insert or replace content at a specific heading, block reference, or "
                "frontmatter field in the active file."
            ),
            parameters={
                "base_url": _BASE_URL_PARAM,
                "content": ParameterDef(
                    type="string",
                    description="Content to insert at the target location",
                    required=True,
                ),
                "operation": ParameterDef(
                    type="string",
                    description="How to insert content: append, prepend, or replace",
                    required=True,
                ),
                "target_type": ParameterDef(
                    type="string",
                    description="Type of target: heading, block, or frontmatter",
                    required=True,
                ),
                "target": ParameterDef(
                    type="string",
                    description=(
                        "Target identifier (heading text, block reference ID, or "
                        "frontmatter field name)"
                    ),
                    required=True,
                ),
                "target_delimiter": ParameterDef(
                    type="string",
                    description='Delimiter for nested headings (default: "::")',
                ),
                "trim_target_whitespace": ParameterDef(
                    type="boolean",
                    description="Whether to trim whitespace from target before matching",
                ),
            },
        ),
        ActionDefinition(
            name="open_file",
            description="Open a file in the Obsidian UI (creates the file if it does not exist).",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "filename": ParameterDef(
                    type="string",
                    description="Path to the file relative to vault root",
                    required=True,
                ),
                "new_leaf": ParameterDef(
                    type="boolean",
                    description="Whether to open the file in a new leaf/tab",
                ),
            },
        ),
        ActionDefinition(
            name="list_commands",
            description="List all available commands in Obsidian.",
            parameters={"base_url": _BASE_URL_PARAM},
        ),
        ActionDefinition(
            name="execute_command",
            description="Execute a command in Obsidian (e.g. open daily note, toggle sidebar).",
            parameters={
                "base_url": _BASE_URL_PARAM,
                "command_id": ParameterDef(
                    type="string",
                    description=(
                        "ID of the command to execute (use list_commands to discover "
                        "available commands)"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_periodic_note",
            description=(
                "Retrieve the current periodic note (daily, weekly, monthly, quarterly, "
                "or yearly)."
            ),
            parameters={
                "base_url": _BASE_URL_PARAM,
                "period": ParameterDef(
                    type="string",
                    description="Period type: daily, weekly, monthly, quarterly, or yearly",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="append_periodic_note",
            description=(
                "Append content to the current periodic note (daily, weekly, monthly, "
                "quarterly, or yearly). Creates the note if it does not exist."
            ),
            parameters={
                "base_url": _BASE_URL_PARAM,
                "period": ParameterDef(
                    type="string",
                    description="Period type: daily, weekly, monthly, quarterly, or yearly",
                    required=True,
                ),
                "content": ParameterDef(
                    type="string",
                    description="Markdown content to append to the periodic note",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using the API key from the Obsidian Local REST API plugin",
            setup_instructions=[
                "Install the 'Local REST API' community plugin in Obsidian",
                "Open the plugin settings and enable it",
                "Copy the API key shown in the plugin settings",
                "Note the server URL (default https://127.0.0.1:27124) for the base_url parameter",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="OBSIDIAN_API_KEY",
                    display_name="Obsidian Local REST API Key",
                    description="API key from the Obsidian Local REST API plugin settings",
                    required=True,
                    sensitive=True,
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://127.0.0.1:27124/",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["authenticated"],
                ),
                cost_level="free",
                description=(
                    "Validates the API key against the Local REST API root endpoint, "
                    "which reports authentication status."
                ),
            ),
        ),
    ],
)
