"""Zendesk integration manifest.

Zendesk uses an unusual triple-credential pattern: `subdomain` +
`email` + `api_key` together form a Basic Auth header
(`{email}/token:{api_key}` base64-encoded). Modeled as
``api_key`` auth_type with three env vars.
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


def _subdomain_param() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="Zendesk subdomain (e.g. 'mycompany' for mycompany.zendesk.com)",
        required=True,
    )


def _email_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Zendesk user email", required=True
    )


def _ticket_id_param() -> ParameterDef:
    return ParameterDef(
        type="integer", description="Zendesk ticket ID", required=True
    )


def _per_page() -> ParameterDef:
    return ParameterDef(
        type="integer", description="Results per page (max 100)", default=25
    )


def _sort_order() -> ParameterDef:
    return ParameterDef(
        type="string", description="Sort order: asc or desc", default="desc"
    )


manifest = IntegrationManifest(
    name="zendesk",
    display_name="Zendesk",
    description=(
        "Zendesk customer support integration: ticket CRUD + tags, "
        "macros, users, locales, and help center articles."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:zendesk-icon",
    app_url="https://www.zendesk.com",
    categories=["Customer Support", "Helpdesk", "Communication & Collaboration"],
    actions=[
        ActionDefinition(
            name="create_ticket",
            description="Create a new support ticket",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "subject": ParameterDef(
                    type="string", description="Ticket subject", required=True
                ),
                "comment_body": ParameterDef(
                    type="string",
                    description="Initial comment body",
                    required=True,
                ),
                "priority": ParameterDef(
                    type="string",
                    description="urgent / high / normal / low",
                ),
                "status": ParameterDef(
                    type="string",
                    description="new / open / pending / hold / solved / closed",
                ),
                "requester_email": ParameterDef(
                    type="string", description="Requester email"
                ),
                "assignee_id": ParameterDef(
                    type="integer", description="Assignee user ID"
                ),
                "tags": ParameterDef(type="array", description="Tags to add"),
                "custom_fields": ParameterDef(
                    type="array",
                    description="List of {id, value} custom field objects",
                ),
            },
        ),
        ActionDefinition(
            name="update_ticket",
            description="Update an existing ticket",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "ticket_id": _ticket_id_param(),
                "subject": ParameterDef(type="string", description="New subject"),
                "comment_body": ParameterDef(
                    type="string", description="Comment to add"
                ),
                "comment_public": ParameterDef(
                    type="boolean",
                    description="Public (true) or internal (false)",
                    default=True,
                ),
                "priority": ParameterDef(type="string", description="Priority"),
                "status": ParameterDef(type="string", description="Status"),
                "assignee_id": ParameterDef(
                    type="integer", description="Assignee user ID"
                ),
                "tags": ParameterDef(
                    type="array", description="Tags (replaces existing)"
                ),
            },
        ),
        ActionDefinition(
            name="delete_ticket",
            description="Delete a ticket",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "ticket_id": _ticket_id_param(),
            },
        ),
        ActionDefinition(
            name="get_ticket",
            description="Get a ticket by ID",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "ticket_id": _ticket_id_param(),
            },
        ),
        ActionDefinition(
            name="list_tickets",
            description="List tickets with optional sorting",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "sort_by": ParameterDef(type="string", description="Sort field"),
                "sort_order": _sort_order(),
                "per_page": _per_page(),
            },
        ),
        ActionDefinition(
            name="search_tickets",
            description="Search tickets using Zendesk search syntax",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "query": ParameterDef(
                    type="string",
                    description="Zendesk search query",
                    required=True,
                ),
                "sort_by": ParameterDef(type="string", description="Sort field"),
                "sort_order": _sort_order(),
                "per_page": _per_page(),
            },
        ),
        ActionDefinition(
            name="add_ticket_tags",
            description="Append tags to a ticket (PUT — additive)",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "ticket_id": _ticket_id_param(),
                "tags": ParameterDef(
                    type="array", description="Tags to add", required=True
                ),
            },
        ),
        ActionDefinition(
            name="set_ticket_tags",
            description="Replace all tags on a ticket (POST — destructive)",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "ticket_id": _ticket_id_param(),
                "tags": ParameterDef(
                    type="array",
                    description="Tags (replaces existing)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="remove_ticket_tags",
            description="Remove specific tags from a ticket",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "ticket_id": _ticket_id_param(),
                "tags": ParameterDef(
                    type="array",
                    description="Tags to remove",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_ticket_comments",
            description="List comments on a ticket",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "ticket_id": _ticket_id_param(),
                "sort_order": ParameterDef(
                    type="string", description="asc or desc", default="asc"
                ),
                "per_page": _per_page(),
            },
        ),
        ActionDefinition(
            name="set_custom_fields",
            description="Set custom field values on a ticket",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "ticket_id": _ticket_id_param(),
                "custom_fields": ParameterDef(
                    type="array",
                    description="List of {id, value} custom field objects",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_user",
            description="Get a Zendesk user by ID",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "user_id": ParameterDef(
                    type="integer", description="User ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_locales",
            description="List supported locales",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
            },
        ),
        ActionDefinition(
            name="list_macros",
            description="List Zendesk macros with filtering / sorting",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "access": ParameterDef(
                    type="string",
                    description="personal / agents / shared / account",
                ),
                "active": ParameterDef(type="boolean", description="Active filter"),
                "category": ParameterDef(
                    type="integer", description="Category ID filter"
                ),
                "group_id": ParameterDef(
                    type="integer", description="Group ID filter"
                ),
                "sort_by": ParameterDef(
                    type="string",
                    description="alphabetical / created_at / updated_at / usage_*",
                ),
                "sort_order": ParameterDef(
                    type="string", description="asc or desc", default="asc"
                ),
                "per_page": _per_page(),
            },
        ),
        ActionDefinition(
            name="get_macro",
            description="Get a macro by ID",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "macro_id": ParameterDef(
                    type="integer", description="Macro ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_articles",
            description="List help-center articles",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "locale": ParameterDef(type="string", description="Locale code"),
                "category_id": ParameterDef(
                    type="integer", description="Category ID filter"
                ),
                "section_id": ParameterDef(
                    type="integer", description="Section ID filter"
                ),
                "per_page": _per_page(),
            },
        ),
        ActionDefinition(
            name="get_article",
            description="Get a help-center article by ID",
            parameters={
                "subdomain": _subdomain_param(),
                "email": _email_param(),
                "article_id": ParameterDef(
                    type="integer", description="Article ID", required=True
                ),
                "locale": ParameterDef(type="string", description="Locale code"),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Token Authentication",
            description=(
                "Authenticate using your Zendesk email + API token. "
                "Generate the token in Admin Center > Apps and "
                "integrations > APIs > Zendesk API."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="ZENDESK_SUBDOMAIN",
                    display_name="Subdomain",
                    description="Subdomain (e.g. 'mycompany')",
                    required=True,
                    sensitive=False,
                    sample_format="mycompany",
                ),
                EnvVar(
                    name="ZENDESK_EMAIL",
                    display_name="Email",
                    description="Zendesk user email",
                    required=True,
                    sensitive=False,
                ),
                EnvVar(
                    name="ZENDESK_API_KEY",
                    display_name="API Token",
                    description="Zendesk API token",
                    required=True,
                    sensitive=True,
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://{subdomain}.zendesk.com/api/v2/users/me.json",
                method="GET",
                headers={"Accept": "application/json"},
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["user"]
                ),
                cost_level="free",
                description="Validates Basic Auth by fetching current user",
            ),
        ),
    ],
)
