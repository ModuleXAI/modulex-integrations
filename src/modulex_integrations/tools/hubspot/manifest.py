"""HubSpot integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _id_param(label: str) -> ParameterDef:
    return ParameterDef(
        type="string", description=f"HubSpot {label} ID", required=True
    )


def _properties_filter() -> ParameterDef:
    return ParameterDef(
        type="array",
        description="Properties to retrieve (None = default property set)",
    )


def _properties_update() -> ParameterDef:
    return ParameterDef(
        type="object",
        description="Properties to update",
        required=True,
    )


def _query_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Search query string", required=True
    )


def _limit_param(default: int = 10) -> ParameterDef:
    return ParameterDef(
        type="integer",
        description="Maximum results to return",
        default=default,
    )


def _profile_test_endpoint(placeholder: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
        method="GET",
        headers={
            "Authorization": f"Bearer {{{placeholder}}}",
            "Accept": "application/json",
        },
        success_indicators=SuccessIndicators(status_codes=[200]),
        cost_level="minimal",
        description="Validates token by listing one contact",
    )


def _engagement_assoc_params() -> dict[str, ParameterDef]:
    return {
        "contact_ids": ParameterDef(
            type="array", description="Contact IDs to associate"
        ),
        "company_ids": ParameterDef(
            type="array", description="Company IDs to associate"
        ),
        "deal_ids": ParameterDef(
            type="array", description="Deal IDs to associate"
        ),
    }


manifest = IntegrationManifest(
    name="hubspot",
    display_name="HubSpot",
    description=(
        "HubSpot CRM integration: contacts, companies, deals, tickets, "
        "and engagement (note/task/meeting) management. Uses the "
        "hubspot-api-client SDK."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:hubspot",
    app_url="https://www.hubspot.com",
    categories=["CRM", "Sales", "Marketing"],
    actions=[
        # --- Contacts ----------------------------------------------------
        ActionDefinition(
            name="get_recent_contacts",
            description="List recently modified contacts (sort: lastmodifieddate DESC)",
            parameters={"limit": _limit_param()},
        ),
        ActionDefinition(
            name="get_contact_by_id",
            description="Retrieve a contact by its HubSpot ID",
            parameters={
                "contact_id": _id_param("contact"),
                "properties": _properties_filter(),
            },
        ),
        ActionDefinition(
            name="create_contact",
            description="Create a new contact (email required)",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Contact email address",
                    required=True,
                ),
                "firstname": ParameterDef(type="string", description="First name"),
                "lastname": ParameterDef(type="string", description="Last name"),
                "phone": ParameterDef(type="string", description="Phone number"),
                "company": ParameterDef(type="string", description="Company"),
                "website": ParameterDef(type="string", description="Website URL"),
                "properties": ParameterDef(
                    type="object", description="Additional properties to set"
                ),
            },
        ),
        ActionDefinition(
            name="update_contact",
            description="Update a contact's properties",
            parameters={
                "contact_id": _id_param("contact"),
                "properties": _properties_update(),
            },
        ),
        ActionDefinition(
            name="search_contacts",
            description="Search contacts by query string",
            parameters={
                "query": _query_param(),
                "limit": _limit_param(),
                "properties": _properties_filter(),
            },
        ),
        # --- Companies ---------------------------------------------------
        ActionDefinition(
            name="get_recent_companies",
            description="List recently modified companies",
            parameters={"limit": _limit_param()},
        ),
        ActionDefinition(
            name="get_company_by_id",
            description="Retrieve a company by its HubSpot ID",
            parameters={
                "company_id": _id_param("company"),
                "properties": _properties_filter(),
            },
        ),
        ActionDefinition(
            name="create_company",
            description="Create a new company (name required)",
            parameters={
                "name": ParameterDef(
                    type="string", description="Company name", required=True
                ),
                "domain": ParameterDef(type="string", description="Primary domain"),
                "industry": ParameterDef(type="string", description="Industry"),
                "phone": ParameterDef(type="string", description="Phone number"),
                "website": ParameterDef(type="string", description="Website URL"),
                "properties": ParameterDef(
                    type="object", description="Additional properties"
                ),
            },
        ),
        ActionDefinition(
            name="update_company",
            description="Update a company's properties",
            parameters={
                "company_id": _id_param("company"),
                "properties": _properties_update(),
            },
        ),
        ActionDefinition(
            name="get_company_activity",
            description=(
                "Get the engagement history for a company "
                "(N+1: list associations, then GET each engagement)"
            ),
            parameters={"company_id": _id_param("company")},
        ),
        ActionDefinition(
            name="search_companies",
            description="Search companies by query string",
            parameters={
                "query": _query_param(),
                "limit": _limit_param(),
                "properties": _properties_filter(),
            },
        ),
        # --- Deals -------------------------------------------------------
        ActionDefinition(
            name="get_recent_deals",
            description="List recently modified deals",
            parameters={"limit": _limit_param()},
        ),
        ActionDefinition(
            name="get_deal_by_id",
            description="Retrieve a deal by its HubSpot ID",
            parameters={
                "deal_id": _id_param("deal"),
                "properties": _properties_filter(),
            },
        ),
        ActionDefinition(
            name="create_deal",
            description="Create a new deal (dealname required)",
            parameters={
                "dealname": ParameterDef(
                    type="string", description="Deal name", required=True
                ),
                "pipeline": ParameterDef(type="string", description="Pipeline ID"),
                "dealstage": ParameterDef(type="string", description="Stage ID"),
                "amount": ParameterDef(type="number", description="Deal amount"),
                "closedate": ParameterDef(
                    type="string", description="Expected close date (ISO 8601)"
                ),
                "properties": ParameterDef(
                    type="object", description="Additional properties"
                ),
            },
        ),
        ActionDefinition(
            name="update_deal",
            description="Update a deal's properties",
            parameters={
                "deal_id": _id_param("deal"),
                "properties": _properties_update(),
            },
        ),
        ActionDefinition(
            name="search_deals",
            description="Search deals by query string",
            parameters={
                "query": _query_param(),
                "limit": _limit_param(),
                "properties": _properties_filter(),
            },
        ),
        # --- Tickets -----------------------------------------------------
        ActionDefinition(
            name="get_recent_tickets",
            description="List recently modified tickets",
            parameters={"limit": _limit_param()},
        ),
        ActionDefinition(
            name="get_ticket_by_id",
            description="Retrieve a ticket by its HubSpot ID",
            parameters={
                "ticket_id": _id_param("ticket"),
                "properties": _properties_filter(),
            },
        ),
        ActionDefinition(
            name="create_ticket",
            description="Create a new support ticket (subject required)",
            parameters={
                "subject": ParameterDef(
                    type="string", description="Ticket subject", required=True
                ),
                "content": ParameterDef(type="string", description="Ticket content"),
                "hs_pipeline": ParameterDef(type="string", description="Pipeline ID"),
                "hs_pipeline_stage": ParameterDef(
                    type="string", description="Pipeline stage ID"
                ),
                "hs_ticket_priority": ParameterDef(
                    type="string", description="LOW / MEDIUM / HIGH"
                ),
                "properties": ParameterDef(
                    type="object", description="Additional properties"
                ),
            },
        ),
        ActionDefinition(
            name="update_ticket",
            description="Update a ticket's properties",
            parameters={
                "ticket_id": _id_param("ticket"),
                "properties": _properties_update(),
            },
        ),
        ActionDefinition(
            name="search_tickets",
            description="Search tickets by query string",
            parameters={
                "query": _query_param(),
                "limit": _limit_param(),
                "properties": _properties_filter(),
            },
        ),
        # --- Engagements -------------------------------------------------
        ActionDefinition(
            name="create_note",
            description="Create a note engagement (optionally associated with objects)",
            parameters={
                "body": ParameterDef(
                    type="string", description="Note body content", required=True
                ),
                **_engagement_assoc_params(),
            },
        ),
        ActionDefinition(
            name="create_task",
            description="Create a task engagement (subject required)",
            parameters={
                "subject": ParameterDef(
                    type="string", description="Task subject", required=True
                ),
                "body": ParameterDef(type="string", description="Task body"),
                "due_date": ParameterDef(
                    type="string", description="Due date (ISO 8601)"
                ),
                "priority": ParameterDef(
                    type="string",
                    description="Priority (NONE/LOW/MEDIUM/HIGH)",
                    default="NONE",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Status (NOT_STARTED/IN_PROGRESS/COMPLETED/etc.)",
                    default="NOT_STARTED",
                ),
                **_engagement_assoc_params(),
            },
        ),
        ActionDefinition(
            name="create_meeting",
            description="Create a meeting engagement",
            parameters={
                "title": ParameterDef(
                    type="string", description="Meeting title", required=True
                ),
                "start_time": ParameterDef(
                    type="string",
                    description="Start time (ISO 8601 or epoch ms)",
                    required=True,
                ),
                "end_time": ParameterDef(
                    type="string", description="End time", required=True
                ),
                "body": ParameterDef(type="string", description="Meeting body"),
                **_engagement_assoc_params(),
            },
        ),
        # --- Properties --------------------------------------------------
        ActionDefinition(
            name="get_property",
            description="Get a single property definition by name",
            parameters={
                "object_type": ParameterDef(
                    type="string",
                    description="One of contacts/companies/deals/tickets",
                    required=True,
                ),
                "property_name": ParameterDef(
                    type="string",
                    description="Property name to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_properties",
            description="List all property definitions for an object type",
            parameters={
                "object_type": ParameterDef(
                    type="string",
                    description="One of contacts/companies/deals/tickets",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using HubSpot OAuth (recommended for most use cases)",
            setup_environment_variables=[
                EnvVar(
                    name="HUBSPOT_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="HubSpot OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://app.hubspot.com/developer/applications",
                ),
                EnvVar(
                    name="HUBSPOT_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="HubSpot OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://app.hubspot.com/developer/applications",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://app.hubspot.com/oauth/authorize",
                token_url="https://api.hubapi.com/oauth/v1/token",
                scopes=[
                    "crm.objects.contacts.read",
                    "crm.objects.contacts.write",
                    "crm.objects.companies.read",
                    "crm.objects.companies.write",
                    "crm.objects.deals.read",
                    "crm.objects.deals.write",
                    "tickets",
                    "crm.schemas.contacts.read",
                    "crm.schemas.companies.read",
                    "crm.schemas.deals.read",
                ],
                token_auth_method="body",
            ),
            test_endpoint=_profile_test_endpoint("access_token"),
        ),
        BearerTokenAuthSchema(
            display_name="Private App Access Token",
            description="Use a HubSpot Private App access token for authentication",
            setup_environment_variables=[
                EnvVar(
                    name="HUBSPOT_ACCESS_TOKEN",
                    display_name="Access Token",
                    description="HubSpot Private App access token",
                    required=True,
                    sensitive=True,
                    sample_format="pat-eu1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url=(
                        "https://developers.hubspot.com/docs/api/private-apps"
                    ),
                ),
            ],
            test_endpoint=_profile_test_endpoint("bearer_token"),
        ),
    ],
)
