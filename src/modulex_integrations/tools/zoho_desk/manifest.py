"""Zoho Desk integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_ORG_ID_PARAM = ParameterDef(
    type="string",
    description=(
        "Zoho Desk organization (portal) ID. Optional — defaults to the"
        " organization configured on the credential; override it to work in"
        " another portal the same credential can reach (list_organizations"
        " enumerates them)."
    ),
)


manifest = IntegrationManifest(
    name="zoho_desk",
    display_name="Zoho Desk",
    description=(
        "Customer support help desk: read and update tickets, work with"
        " conversation threads and internal comments, and look up the"
        " contacts behind them"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:zoho_desk",
    app_url="https://www.zoho.com/desk/",
    categories=["Customer Support", "Helpdesk", "Ticketing"],
    actions=[
        ActionDefinition(
            name="list_tickets",
            description=(
                "List tickets from a Zoho Desk organization with optional"
                " filters. Returns a list projection: description, resolution,"
                " statusType and classification are only available from"
                " get_ticket."
            ),
            parameters={
                "org_id": _ORG_ID_PARAM,
                "from_index": ParameterDef(
                    type="integer",
                    description=(
                        "Pagination start index, sent as the `from` query"
                        " parameter (0-based, max 4999)"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of tickets to return (1-100, default 10)",
                ),
                "department_ids": ParameterDef(
                    type="string",
                    description="Filter by department ID (comma-separated for multiple)",
                ),
                "status": ParameterDef(
                    type="string",
                    description=(
                        "Filter by status, including custom statuses."
                        ' Comma-separate to match multiple (e.g. "Open,On Hold")'
                    ),
                ),
                "priority": ParameterDef(
                    type="string",
                    description=(
                        "Filter by priority. Comma-separate to match multiple"
                        ' (e.g. "High,Urgent")'
                    ),
                ),
                "sort_by": ParameterDef(
                    type="string",
                    description=(
                        "Sort field: createdTime, customerResponseTime, or"
                        " responseDueDate. Prefix with - for descending."
                    ),
                ),
                "include": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated related data to embed. Allowed:"
                        " contacts, products, departments, team, isRead, assignee"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_ticket",
            description="Retrieve a single Zoho Desk ticket by ID",
            parameters={
                "ticket_id": ParameterDef(
                    type="string",
                    description="Ticket ID to retrieve",
                    required=True,
                ),
                "org_id": _ORG_ID_PARAM,
                "include": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated related data to embed. Allowed:"
                        " contacts, products, assignee, departments, contract,"
                        " isRead, team, skills"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="update_ticket",
            description="Update fields on an existing Zoho Desk ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="string",
                    description="Ticket ID to update",
                    required=True,
                ),
                "org_id": _ORG_ID_PARAM,
                "subject": ParameterDef(type="string", description="Ticket subject"),
                "status": ParameterDef(
                    type="string",
                    description="Ticket status (e.g. Open, Closed)",
                ),
                "priority": ParameterDef(
                    type="string",
                    description="Ticket priority (e.g. High)",
                ),
                "assignee_id": ParameterDef(type="string", description="Assignee (agent) ID"),
                "department_id": ParameterDef(type="string", description="Department ID"),
                "category": ParameterDef(type="string", description="Ticket category"),
                "sub_category": ParameterDef(type="string", description="Ticket sub-category"),
                "due_date": ParameterDef(type="string", description="Due date (ISO 8601)"),
                "description": ParameterDef(type="string", description="Ticket description"),
                "resolution": ParameterDef(
                    type="string",
                    description="Resolution notes recorded on the ticket",
                ),
                "classification": ParameterDef(
                    type="string",
                    description=(
                        "Ticket classification: Problem, Request, Question, or Others"
                    ),
                ),
                "custom_fields": ParameterDef(
                    type="object",
                    description=(
                        "Custom field values as a JSON object, keyed by custom"
                        " field API name"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_comments",
            description="List comments on a Zoho Desk ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="string",
                    description="Ticket ID",
                    required=True,
                ),
                "org_id": _ORG_ID_PARAM,
                "from_index": ParameterDef(
                    type="integer",
                    description=(
                        "Pagination start index, sent as the `from` query parameter (0-based)"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of comments to return (1-100, default 50)",
                ),
            },
        ),
        ActionDefinition(
            name="add_comment",
            description="Add a comment to a Zoho Desk ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="string",
                    description="Ticket ID",
                    required=True,
                ),
                "content": ParameterDef(
                    type="string",
                    description="Comment content",
                    required=True,
                ),
                "org_id": _ORG_ID_PARAM,
                "content_type": ParameterDef(
                    type="string",
                    description=(
                        "Content type: plainText or html. Defaults to plainText"
                        " so agent-written text posts literally; pass 'html' to"
                        " send markup (the Zoho Desk API's own default is html)."
                    ),
                    default="plainText",
                ),
                "is_public": ParameterDef(
                    type="boolean",
                    description="Whether the comment is public",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_threads",
            description=(
                "List conversation threads on a Zoho Desk ticket, newest first."
                " Returns a list projection: message bodies (content, summary,"
                " to/cc/bcc) come back only from get_thread."
            ),
            parameters={
                "ticket_id": ParameterDef(
                    type="string",
                    description="Ticket ID",
                    required=True,
                ),
                "org_id": _ORG_ID_PARAM,
                "from_index": ParameterDef(
                    type="integer",
                    description=(
                        "Pagination start index, sent as the `from` query parameter (0-based)"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of threads to return (1-200, default 100)",
                ),
            },
        ),
        ActionDefinition(
            name="get_thread",
            description="Retrieve the full content of a single Zoho Desk ticket thread",
            parameters={
                "ticket_id": ParameterDef(
                    type="string",
                    description="Ticket ID",
                    required=True,
                ),
                "thread_id": ParameterDef(
                    type="string",
                    description="Thread ID",
                    required=True,
                ),
                "org_id": _ORG_ID_PARAM,
            },
        ),
        ActionDefinition(
            name="get_contact",
            description="Retrieve a Zoho Desk contact by ID",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="Contact ID to retrieve",
                    required=True,
                ),
                "org_id": _ORG_ID_PARAM,
            },
        ),
        ActionDefinition(
            name="list_organizations",
            description=(
                "List the Zoho Desk organizations (portals) the connected"
                " account can access"
            ),
            parameters={},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Zoho Self Client",
            description=(
                "Authenticate with a Zoho Self Client credential pair. No"
                " browser redirect or user consent step is involved."
            ),
            setup_instructions=[
                "Sign in at https://api-console.zoho.com and click Add Client.",
                "Choose Self Client and create it, then open the Client Secret tab.",
                "Copy the Client ID and Client Secret.",
                (
                    "Grant the client the Desk.tickets.READ, Desk.tickets.UPDATE, "
                    "Desk.contacts.READ and Desk.basic.READ scopes."
                ),
                (
                    "Find your Zoho Desk organization (portal) ID in Setup > "
                    "Developer Space > API, and enter it below."
                ),
                (
                    "If your Zoho account lives outside the US data center, set "
                    "the Data Center value (eu, in, com.au, ...) so tokens are "
                    "minted at, and API calls reach, that data center."
                ),
            ],
            setup_environment_variables=[
                EnvVar(
                    name="ZOHO_DESK_CLIENT_ID",
                    display_name="Client ID",
                    description="Client ID shown under Self Client > Client Secret",
                    required=True,
                    sensitive=False,
                    sample_format="1000.ABCDEFGHIJKLMNOPQRSTUVWXYZ1234",
                    about_url="https://api-console.zoho.com",
                ),
                EnvVar(
                    name="ZOHO_DESK_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Client secret shown under Self Client > Client Secret",
                    required=True,
                    sensitive=True,
                    sample_format="1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
                    about_url="https://api-console.zoho.com",
                ),
                EnvVar(
                    name="ZOHO_DESK_ORG_ID",
                    display_name="Organization ID",
                    description=(
                        "Zoho Desk organization (portal) ID. Sent as the orgId"
                        " header and used to scope the minted token; an action"
                        " may override it with org_id."
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="123456789",
                    about_url="https://desk.zoho.com/DeskAPIDocument",
                ),
                EnvVar(
                    name="ZOHO_DESK_DATA_CENTER",
                    display_name="Data Center",
                    description=(
                        "Zoho data center the account lives in, as the domain"
                        " suffix of desk.zoho.<tld>: com (default), eu, in,"
                        " com.au, jp, ca, sa, uk, com.cn"
                    ),
                    required=False,
                    sensitive=False,
                    sample_format="com",
                    about_url="https://www.zoho.com/accounts/protocol/oauth/multi-dc.html",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://accounts.zoho.com/oauth/serverinfo",
                method="GET",
                # Reachability check only. Minting a token requires POSTing the
                # client secret with a data-center-specific host, which the
                # runtime cannot assemble from a static endpoint definition, so
                # the credential is truly validated on the first action call.
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description=(
                    "Reachability check against the Zoho accounts server."
                    " Credentials are validated when an action first mints a"
                    " token."
                ),
            ),
        ),
    ],
)
