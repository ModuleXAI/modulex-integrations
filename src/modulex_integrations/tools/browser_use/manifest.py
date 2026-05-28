"""Browser Use integration manifest."""
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


manifest = IntegrationManifest(
    name="browser_use",
    display_name="Browser Use",
    logo="modulex:browser_use-themed",
    description="AI-powered cloud browser automation via the Browser Use API",
    version="1.0.0",
    author="ModuleX",
    app_url="https://browser-use.com",
    categories=["Automation", "AI", "Developer Tools & Infrastructure"],
    actions=[
        ActionDefinition(
            name="create_session",
            description="Create an agent session, dispatch a task, or dispatch a follow-up task to an existing idle session",
            parameters={
                "task": ParameterDef(
                    type="string",
                    description="Natural-language instruction for the agent",
                ),
                "model": ParameterDef(
                    type="string",
                    description="Browser Use agent model. Allowed values: claude-sonnet-4.6, claude-opus-4.6, gemini-3-flash, bu-mini, bu-max, bu-ultra",
                    default="claude-sonnet-4.6",
                ),
                "session_id": ParameterDef(
                    type="string",
                    description="ID of an existing session to dispatch a follow-up task to",
                ),
                "keep_alive": ParameterDef(
                    type="boolean",
                    description="If true, the session stays idle after the task completes so it can accept follow-up tasks",
                    default=False,
                ),
                "max_cost_usd": ParameterDef(
                    type="string",
                    description="Maximum total session cost in USD. Example: 1.50",
                ),
                "profile_id": ParameterDef(
                    type="string",
                    description="ID of a Browser Use profile to use",
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of a Browser Use workspace to attach",
                ),
                "proxy_country_code": ParameterDef(
                    type="string",
                    description="Lowercase proxy country code for browser traffic. Examples: us, de, jp. Enter none to disable proxy",
                    default="us",
                ),
                "output_schema": ParameterDef(
                    type="object",
                    description="Optional JSON Schema for structured output",
                ),
                "enable_scheduled_tasks": ParameterDef(
                    type="boolean",
                    description="If true, the agent can create scheduled tasks tied to your project",
                    default=False,
                ),
                "sensitive_data": ParameterDef(
                    type="object",
                    description="Key-value pairs available to the agent through secure placeholders. Keys are visible to the model; values are hidden",
                ),
                "enable_recording": ParameterDef(
                    type="boolean",
                    description="If true, Browser Use records the browser session and returns recording URLs after completion",
                    default=False,
                ),
                "skills": ParameterDef(
                    type="boolean",
                    description="If true, enables built-in Browser Use agent skills such as file management",
                    default=True,
                ),
                "agentmail": ParameterDef(
                    type="boolean",
                    description="If true, provisions a temporary email inbox for the session",
                    default=True,
                ),
                "cache_script": ParameterDef(
                    type="string",
                    description="Controls deterministic script caching. Allowed values: auto, enabled, disabled",
                    default="auto",
                ),
                "use_own_key": ParameterDef(
                    type="boolean",
                    description="If true, uses your configured LLM provider key instead of Browser Use managed keys",
                    default=False,
                ),
                "auto_heal": ParameterDef(
                    type="boolean",
                    description="When script caching is active, validates cached script output and reruns the full agent if the result looks incorrect",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_session",
            description="Get the current state, output, live URL, screenshot URL, and cost details for an agent session",
            parameters={
                "session_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use agent session",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_sessions",
            description="List Browser Use agent sessions for the authenticated project",
            parameters={
                "page_number": ParameterDef(
                    type="integer",
                    description="Page number to fetch. The first page is 1",
                    default=1,
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of records to return per page. Maximum: 100",
                    default=20,
                ),
            },
        ),
        ActionDefinition(
            name="delete_session",
            description="Delete an agent session",
            parameters={
                "session_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use agent session to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="stop_session",
            description="Stop the current task or stop the entire Browser Use agent session",
            parameters={
                "session_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use agent session",
                    required=True,
                ),
                "strategy": ParameterDef(
                    type="string",
                    description="Use task to stop only the current task and keep the session alive, or session to destroy the sandbox entirely. Allowed values: task, session",
                    default="session",
                ),
            },
        ),
        ActionDefinition(
            name="list_session_messages",
            description="List messages from a Browser Use agent session, including reasoning, tool calls, browser actions, screenshots, and results",
            parameters={
                "session_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use agent session",
                    required=True,
                ),
                "after": ParameterDef(
                    type="string",
                    description="Return messages after this message ID cursor",
                ),
                "before": ParameterDef(
                    type="string",
                    description="Return messages before this message ID cursor",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of messages to return. Maximum: 100",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="create_browser_session",
            description="Create a standalone browser session for direct browser control through CDP",
            parameters={
                "profile_id": ParameterDef(
                    type="string",
                    description="ID of a Browser Use profile",
                ),
                "proxy_country_code": ParameterDef(
                    type="string",
                    description="Lowercase proxy country code for browser traffic. Examples: us, de, jp. Enter none to disable proxy",
                    default="us",
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Session timeout in minutes. Supported range: 1 to 240",
                    default=60,
                ),
                "browser_screen_width": ParameterDef(
                    type="integer",
                    description="Custom browser screen width in pixels. Supported range: 320 to 6144",
                ),
                "browser_screen_height": ParameterDef(
                    type="integer",
                    description="Custom browser screen height in pixels. Supported range: 320 to 3456",
                ),
                "allow_resizing": ParameterDef(
                    type="boolean",
                    description="Whether to allow browser resizing during the session",
                    default=False,
                ),
                "custom_proxy": ParameterDef(
                    type="object",
                    description="Custom proxy object with host, port, username, and password fields. Requires an active subscription",
                ),
                "enable_recording": ParameterDef(
                    type="boolean",
                    description="If true, records the browser session",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_browser_session",
            description="Get details for a standalone browser session, including live URL, CDP URL, status, timeout, and cost fields",
            parameters={
                "browser_session_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use browser session",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_browser_sessions",
            description="List standalone browser sessions for direct browser control via CDP",
            parameters={
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of records to return per page. Maximum: 100",
                    default=20,
                ),
                "page_number": ParameterDef(
                    type="integer",
                    description="Page number to fetch. The first page is 1",
                    default=1,
                ),
                "filter_by": ParameterDef(
                    type="string",
                    description="Filter browser sessions by status. Allowed values: active, stopped",
                ),
            },
        ),
        ActionDefinition(
            name="update_browser_session",
            description="Update a standalone browser session. Currently supports the stop action",
            parameters={
                "browser_session_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use browser session",
                    required=True,
                ),
                "action": ParameterDef(
                    type="string",
                    description="Action to perform on the browser session. Currently supported value: stop",
                    required=True,
                    default="stop",
                ),
            },
        ),
        ActionDefinition(
            name="create_profile",
            description="Create a profile to preserve cookies, local storage, and login state across sessions",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Optional profile name. Maximum length: 100 characters",
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="Optional internal user identifier from your system. Maximum length: 255 characters",
                ),
            },
        ),
        ActionDefinition(
            name="get_profile",
            description="Get a Browser Use profile by ID",
            parameters={
                "profile_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use profile",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_profiles",
            description="List Browser Use profiles, optionally searching by profile name or user ID",
            parameters={
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of records to return per page. Maximum: 100",
                    default=20,
                ),
                "page_number": ParameterDef(
                    type="integer",
                    description="Page number to fetch. The first page is 1",
                    default=1,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Search query for profile name or user ID. Maximum length: 200 characters",
                ),
            },
        ),
        ActionDefinition(
            name="delete_profile",
            description="Delete a Browser Use profile and its persisted browser state",
            parameters={
                "profile_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use profile to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_profile",
            description="Update a Browser Use profile name or user ID",
            parameters={
                "profile_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use profile",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Updated profile name. Maximum length: 100 characters",
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="Updated internal user identifier. Maximum length: 255 characters",
                ),
            },
        ),
        ActionDefinition(
            name="create_workspace",
            description="Create a workspace for persistent shared file storage across sessions",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Optional workspace name. Maximum length: 100 characters",
                ),
            },
        ),
        ActionDefinition(
            name="get_workspace",
            description="Get a Browser Use workspace by ID",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use workspace",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_workspaces",
            description="List Browser Use workspaces for persistent shared file storage across sessions",
            parameters={
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of records to return per page. Maximum: 100",
                    default=20,
                ),
                "page_number": ParameterDef(
                    type="integer",
                    description="Page number to fetch. The first page is 1",
                    default=1,
                ),
            },
        ),
        ActionDefinition(
            name="delete_workspace",
            description="Delete a Browser Use workspace and its stored files. This cannot be undone",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use workspace to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_workspace",
            description="Update a Browser Use workspace name",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use workspace",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Updated workspace name. Maximum length: 100 characters",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_workspace_size",
            description="Get storage usage for a Browser Use workspace",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use workspace",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_workspace_files",
            description="List files and folders in a Browser Use workspace, optionally returning presigned download URLs",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use workspace",
                    required=True,
                ),
                "prefix": ParameterDef(
                    type="string",
                    description="Optional directory prefix to list. Example: reports/",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of files to return. Maximum: 100",
                    default=50,
                ),
                "cursor": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous response",
                ),
                "include_urls": ParameterDef(
                    type="boolean",
                    description="If true, include presigned download URLs for files",
                    default=False,
                ),
                "shallow": ParameterDef(
                    type="boolean",
                    description="If true, list only immediate files and folders at the prefix",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_workspace_file",
            description="Delete a file from a Browser Use workspace",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use workspace",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Relative workspace file path to delete. Example: reports/data.csv",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="upload_workspace_files",
            description="Create presigned upload URLs for workspace files",
            parameters={
                "workspace_id": ParameterDef(
                    type="string",
                    description="ID of the Browser Use workspace",
                    required=True,
                ),
                "prefix": ParameterDef(
                    type="string",
                    description="Optional directory prefix to upload into. Example: uploads/",
                ),
                "files_json": ParameterDef(
                    type="string",
                    description="JSON array of file metadata objects. Each object has name (required), contentType (optional), and size (optional integer). 1 to 10 files per request",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_account_billing",
            description="Get account billing details for the authenticated project",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Browser Use API key",
            setup_instructions=[
                "Go to https://cloud.browser-use.com and sign in",
                "Navigate to your project settings or API Keys section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="BROWSER_USE_API_KEY",
                    display_name="Browser Use API Key",
                    description="Your Browser Use API key from cloud.browser-use.com",
                    required=True,
                    sensitive=True,
                    sample_format="bu_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://cloud.browser-use.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.browser-use.com/api/v3/billing/account",
                method="GET",
                headers={"X-Browser-Use-API-Key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates the API key by fetching account billing details",
            ),
        ),
    ],
)
