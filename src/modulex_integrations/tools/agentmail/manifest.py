"""AgentMail integration manifest.

AgentMail is an API-first email platform for agents and automation:
create inboxes, send and receive messages, reply to and forward threads,
manage drafts, and organize conversations with labels — all over a
REST API (``https://api.agentmail.to/v0``).

Authentication is a single API key sent as
``Authorization: Bearer <api_key>``. This integration follows the
modulex *api_key* runtime convention (the ``ToolExecutor`` injects the
key directly into each tool's ``api_key`` parameter).
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


_API_BASE = "https://api.agentmail.to/v0"

_TEST_HEADERS = {"Authorization": "Bearer {api_key}"}
_TEST_SUCCESS = SuccessIndicators(status_codes=[200])


# --- Reusable parameter pieces ---------------------------------------------


def _inbox_id(description: str) -> ParameterDef:
    return ParameterDef(type="string", description=description, required=True)


_LIMIT = ParameterDef(type="integer", description="Maximum number of results to return")
_PAGE_TOKEN = ParameterDef(
    type="string", description="Pagination token for the next page of results"
)


manifest = IntegrationManifest(
    name="agentmail",
    display_name="AgentMail",
    description=(
        "Integrate AgentMail into your workflow. Create and manage email inboxes, "
        "send and receive messages, reply to threads, manage drafts, and organize "
        "threads with labels."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:agentmail-themed",
    app_url="https://agentmail.to",
    categories=["Communication", "email", "automation"],
    actions=[
        # --- Messages ------------------------------------------------------
        ActionDefinition(
            name="send_message",
            description="Send an email message from an AgentMail inbox.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to send from"),
                "to": ParameterDef(
                    type="string",
                    description="Recipient email address (comma-separated for multiple)",
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string", description="Email subject line", required=True
                ),
                "text": ParameterDef(type="string", description="Plain text email body"),
                "html": ParameterDef(type="string", description="HTML email body"),
                "cc": ParameterDef(
                    type="string",
                    description="CC recipient email addresses (comma-separated)",
                ),
                "bcc": ParameterDef(
                    type="string",
                    description="BCC recipient email addresses (comma-separated)",
                ),
            },
        ),
        ActionDefinition(
            name="reply_message",
            description="Reply to an existing email message in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to reply from"),
                "message_id": ParameterDef(
                    type="string", description="ID of the message to reply to", required=True
                ),
                "text": ParameterDef(type="string", description="Plain text reply body"),
                "html": ParameterDef(type="string", description="HTML reply body"),
                "to": ParameterDef(
                    type="string",
                    description="Override recipient email addresses (comma-separated)",
                ),
                "cc": ParameterDef(
                    type="string", description="CC email addresses (comma-separated)"
                ),
                "bcc": ParameterDef(
                    type="string", description="BCC email addresses (comma-separated)"
                ),
                "reply_all": ParameterDef(
                    type="boolean",
                    description="Reply to all recipients of the original message",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="forward_message",
            description="Forward an email message to new recipients in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the message"),
                "message_id": ParameterDef(
                    type="string", description="ID of the message to forward", required=True
                ),
                "to": ParameterDef(
                    type="string",
                    description="Recipient email addresses (comma-separated)",
                    required=True,
                ),
                "subject": ParameterDef(type="string", description="Override subject line"),
                "text": ParameterDef(
                    type="string", description="Additional plain text to prepend"
                ),
                "html": ParameterDef(type="string", description="Additional HTML to prepend"),
                "cc": ParameterDef(
                    type="string",
                    description="CC recipient email addresses (comma-separated)",
                ),
                "bcc": ParameterDef(
                    type="string",
                    description="BCC recipient email addresses (comma-separated)",
                ),
            },
        ),
        ActionDefinition(
            name="list_messages",
            description="List messages in an inbox in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to list messages from"),
                "limit": _LIMIT,
                "page_token": _PAGE_TOKEN,
            },
        ),
        ActionDefinition(
            name="get_message",
            description="Get details of a specific email message in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the message"),
                "message_id": ParameterDef(
                    type="string", description="ID of the message to retrieve", required=True
                ),
            },
        ),
        ActionDefinition(
            name="update_message",
            description="Add or remove labels on an email message in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the message"),
                "message_id": ParameterDef(
                    type="string", description="ID of the message to update", required=True
                ),
                "add_labels": ParameterDef(
                    type="string",
                    description="Comma-separated labels to add to the message",
                ),
                "remove_labels": ParameterDef(
                    type="string",
                    description="Comma-separated labels to remove from the message",
                ),
            },
        ),
        # --- Threads -------------------------------------------------------
        ActionDefinition(
            name="list_threads",
            description="List email threads in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to list threads from"),
                "limit": _LIMIT,
                "page_token": _PAGE_TOKEN,
                "labels": ParameterDef(
                    type="string",
                    description="Comma-separated labels to filter threads by",
                ),
                "before": ParameterDef(
                    type="string",
                    description="Filter threads before this ISO 8601 timestamp",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Filter threads after this ISO 8601 timestamp",
                ),
            },
        ),
        ActionDefinition(
            name="get_thread",
            description=(
                "Get details of a specific email thread including messages in AgentMail."
            ),
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the thread"),
                "thread_id": ParameterDef(
                    type="string", description="ID of the thread to retrieve", required=True
                ),
            },
        ),
        ActionDefinition(
            name="update_thread",
            description="Add or remove labels on an email thread in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the thread"),
                "thread_id": ParameterDef(
                    type="string", description="ID of the thread to update", required=True
                ),
                "add_labels": ParameterDef(
                    type="string",
                    description="Comma-separated labels to add to the thread",
                ),
                "remove_labels": ParameterDef(
                    type="string",
                    description="Comma-separated labels to remove from the thread",
                ),
            },
        ),
        ActionDefinition(
            name="delete_thread",
            description=(
                "Delete an email thread in AgentMail (moves to trash, or permanently "
                "deletes if already in trash)."
            ),
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the thread"),
                "thread_id": ParameterDef(
                    type="string", description="ID of the thread to delete", required=True
                ),
                "permanent": ParameterDef(
                    type="boolean",
                    description="Force permanent deletion instead of moving to trash",
                    default=False,
                ),
            },
        ),
        # --- Drafts --------------------------------------------------------
        ActionDefinition(
            name="create_draft",
            description="Create a new email draft in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to create the draft in"),
                "to": ParameterDef(
                    type="string",
                    description="Recipient email addresses (comma-separated)",
                ),
                "subject": ParameterDef(type="string", description="Draft subject line"),
                "text": ParameterDef(type="string", description="Plain text draft body"),
                "html": ParameterDef(type="string", description="HTML draft body"),
                "cc": ParameterDef(
                    type="string",
                    description="CC recipient email addresses (comma-separated)",
                ),
                "bcc": ParameterDef(
                    type="string",
                    description="BCC recipient email addresses (comma-separated)",
                ),
                "in_reply_to": ParameterDef(
                    type="string", description="ID of message being replied to"
                ),
                "send_at": ParameterDef(
                    type="string",
                    description="ISO 8601 timestamp to schedule sending",
                ),
            },
        ),
        ActionDefinition(
            name="list_drafts",
            description="List email drafts in an inbox in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to list drafts from"),
                "limit": _LIMIT,
                "page_token": _PAGE_TOKEN,
            },
        ),
        ActionDefinition(
            name="get_draft",
            description="Get details of a specific email draft in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox the draft belongs to"),
                "draft_id": ParameterDef(
                    type="string", description="ID of the draft to retrieve", required=True
                ),
            },
        ),
        ActionDefinition(
            name="update_draft",
            description="Update an existing email draft in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the draft"),
                "draft_id": ParameterDef(
                    type="string", description="ID of the draft to update", required=True
                ),
                "to": ParameterDef(
                    type="string",
                    description="Recipient email addresses (comma-separated)",
                ),
                "subject": ParameterDef(type="string", description="Draft subject line"),
                "text": ParameterDef(type="string", description="Plain text draft body"),
                "html": ParameterDef(type="string", description="HTML draft body"),
                "cc": ParameterDef(
                    type="string",
                    description="CC recipient email addresses (comma-separated)",
                ),
                "bcc": ParameterDef(
                    type="string",
                    description="BCC recipient email addresses (comma-separated)",
                ),
                "send_at": ParameterDef(
                    type="string",
                    description="ISO 8601 timestamp to schedule sending",
                ),
            },
        ),
        ActionDefinition(
            name="delete_draft",
            description="Delete an email draft in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the draft"),
                "draft_id": ParameterDef(
                    type="string", description="ID of the draft to delete", required=True
                ),
            },
        ),
        ActionDefinition(
            name="send_draft",
            description="Send an existing email draft in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox containing the draft"),
                "draft_id": ParameterDef(
                    type="string", description="ID of the draft to send", required=True
                ),
            },
        ),
        # --- Inboxes -------------------------------------------------------
        ActionDefinition(
            name="create_inbox",
            description="Create a new email inbox with AgentMail.",
            parameters={
                "username": ParameterDef(
                    type="string", description="Username for the inbox email address"
                ),
                "domain": ParameterDef(
                    type="string", description="Domain for the inbox email address"
                ),
                "display_name": ParameterDef(
                    type="string", description="Display name for the inbox"
                ),
            },
        ),
        ActionDefinition(
            name="list_inboxes",
            description="List all email inboxes in AgentMail.",
            parameters={
                "limit": _LIMIT,
                "page_token": _PAGE_TOKEN,
            },
        ),
        ActionDefinition(
            name="get_inbox",
            description="Get details of a specific email inbox in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to retrieve"),
            },
        ),
        ActionDefinition(
            name="update_inbox",
            description="Update the display name of an email inbox in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to update"),
                "display_name": ParameterDef(
                    type="string",
                    description="New display name for the inbox",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_inbox",
            description="Delete an email inbox in AgentMail.",
            parameters={
                "inbox_id": _inbox_id("ID of the inbox to delete"),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your AgentMail API key",
            setup_instructions=[
                "Sign up or log in at https://agentmail.to",
                "Open the dashboard and navigate to the API Keys section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="AGENTMAIL_API_KEY",
                    display_name="AgentMail API Key",
                    description="Your AgentMail API key",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.agentmail.to",
                ),
            ],
            test_endpoint=TestEndpoint(
                url=f"{_API_BASE}/inboxes",
                method="GET",
                headers=_TEST_HEADERS,
                params={"limit": "1"},
                success_indicators=_TEST_SUCCESS,
                cost_level="free",
                description="Validates the API key by listing inboxes (1 result).",
            ),
        ),
    ],
)
