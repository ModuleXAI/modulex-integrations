"""Salesforce integration manifest."""
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


def _object_type_param() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="Salesforce object type (e.g. Account, Contact, Lead)",
        required=True,
    )


def _record_id_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Salesforce record ID", required=True
    )


def _additional_fields() -> ParameterDef:
    return ParameterDef(type="object", description="Additional custom fields")


# Identity endpoint is the conventional Salesforce health check.
def _test_endpoint(placeholder: str) -> TestEndpoint:
    # Salesforce's OAuth userinfo endpoint validates any valid access
    # token. The placeholder name matches the auth_data key the modulex
    # credential service ships:
    #   - "access_token" for OAuth2 (set by the OAuth2 flow)
    #   - "bearer_token" for the BearerTokenAuthSchema (sent by the UI)
    return TestEndpoint(
        url="https://login.salesforce.com/services/oauth2/userinfo",
        method="GET",
        headers={"Authorization": f"Bearer {{{placeholder}}}"},
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["user_id"]
        ),
        cost_level="free",
        description="Validates token via OAuth userinfo endpoint",
    )


manifest = IntegrationManifest(
    name="salesforce",
    display_name="Salesforce",
    description=(
        "Salesforce CRM integration: SOQL/SOSL queries, record CRUD, "
        "and convenience helpers for Accounts, Contacts, Leads, "
        "Opportunities, Tasks, Cases, and Campaign membership."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:salesforce",
    app_url="https://www.salesforce.com",
    categories=["CRM", "Sales", "Customer Support"],
    actions=[
        ActionDefinition(
            name="soql_query",
            description="Execute a SOQL query (Salesforce Object Query Language)",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="SOQL query (e.g. 'SELECT Id, Name FROM Account LIMIT 10')",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="sosl_search",
            description="Execute a SOSL cross-object search",
            parameters={
                "search": ParameterDef(
                    type="string",
                    description=(
                        "SOSL search (e.g. "
                        "'FIND {test} IN ALL FIELDS RETURNING Account(Id, Name)')"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_record",
            description="Get a record by object type + ID",
            parameters={
                "object_type": _object_type_param(),
                "record_id": _record_id_param(),
                "fields": ParameterDef(
                    type="array",
                    description="Specific fields to return (all if omitted)",
                ),
            },
        ),
        ActionDefinition(
            name="create_record",
            description="Generic create — works for any object type",
            parameters={
                "object_type": _object_type_param(),
                "data": ParameterDef(
                    type="object",
                    description="Record data as key-value pairs",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_record",
            description="PATCH an existing record",
            parameters={
                "object_type": _object_type_param(),
                "record_id": _record_id_param(),
                "data": ParameterDef(
                    type="object", description="Updated fields", required=True
                ),
            },
        ),
        ActionDefinition(
            name="delete_record",
            description="DELETE a record by object type + ID",
            parameters={
                "object_type": _object_type_param(),
                "record_id": _record_id_param(),
            },
        ),
        ActionDefinition(
            name="create_account",
            description="Create an Account record",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Account name",
                    required=True,
                ),
                "description": ParameterDef(type="string", description="Description"),
                "website": ParameterDef(type="string", description="Website URL"),
                "phone": ParameterDef(type="string", description="Phone number"),
                "industry": ParameterDef(type="string", description="Industry"),
                "annual_revenue": ParameterDef(
                    type="number", description="Annual revenue"
                ),
                "number_of_employees": ParameterDef(
                    type="integer", description="Number of employees"
                ),
                "billing_street": ParameterDef(type="string", description="Billing street"),
                "billing_city": ParameterDef(type="string", description="Billing city"),
                "billing_state": ParameterDef(
                    type="string", description="Billing state/province"
                ),
                "billing_postal_code": ParameterDef(
                    type="string", description="Billing postal code"
                ),
                "billing_country": ParameterDef(
                    type="string", description="Billing country"
                ),
                "additional_fields": _additional_fields(),
            },
        ),
        ActionDefinition(
            name="create_contact",
            description="Create a Contact record",
            parameters={
                "last_name": ParameterDef(
                    type="string",
                    description="Last name (required)",
                    required=True,
                ),
                "first_name": ParameterDef(type="string", description="First name"),
                "account_id": ParameterDef(
                    type="string", description="Linked Account ID"
                ),
                "email": ParameterDef(type="string", description="Email address"),
                "phone": ParameterDef(type="string", description="Phone number"),
                "mobile_phone": ParameterDef(type="string", description="Mobile phone"),
                "title": ParameterDef(type="string", description="Job title"),
                "department": ParameterDef(type="string", description="Department"),
                "mailing_street": ParameterDef(type="string", description="Mailing street"),
                "mailing_city": ParameterDef(type="string", description="Mailing city"),
                "mailing_state": ParameterDef(type="string", description="Mailing state"),
                "mailing_postal_code": ParameterDef(
                    type="string", description="Mailing postal code"
                ),
                "mailing_country": ParameterDef(
                    type="string", description="Mailing country"
                ),
                "additional_fields": _additional_fields(),
            },
        ),
        ActionDefinition(
            name="create_lead",
            description="Create a Lead record",
            parameters={
                "last_name": ParameterDef(
                    type="string", description="Last name", required=True
                ),
                "company": ParameterDef(
                    type="string", description="Company", required=True
                ),
                "first_name": ParameterDef(type="string", description="First name"),
                "email": ParameterDef(type="string", description="Email"),
                "phone": ParameterDef(type="string", description="Phone"),
                "title": ParameterDef(type="string", description="Title"),
                "status": ParameterDef(type="string", description="Status"),
                "rating": ParameterDef(type="string", description="Rating"),
                "industry": ParameterDef(type="string", description="Industry"),
                "annual_revenue": ParameterDef(
                    type="number", description="Annual revenue"
                ),
                "lead_source": ParameterDef(type="string", description="Lead source"),
                "additional_fields": _additional_fields(),
            },
        ),
        ActionDefinition(
            name="create_opportunity",
            description="Create an Opportunity record",
            parameters={
                "name": ParameterDef(
                    type="string", description="Opportunity name", required=True
                ),
                "stage_name": ParameterDef(
                    type="string", description="Stage", required=True
                ),
                "close_date": ParameterDef(
                    type="string",
                    description="Expected close date (YYYY-MM-DD)",
                    required=True,
                ),
                "account_id": ParameterDef(type="string", description="Account ID"),
                "amount": ParameterDef(type="number", description="Amount"),
                "probability": ParameterDef(
                    type="integer", description="Probability % (0-100)"
                ),
                "type": ParameterDef(type="string", description="Type"),
                "lead_source": ParameterDef(type="string", description="Lead source"),
                "description": ParameterDef(type="string", description="Description"),
                "additional_fields": _additional_fields(),
            },
        ),
        ActionDefinition(
            name="create_task",
            description="Create a Task record",
            parameters={
                "subject": ParameterDef(
                    type="string", description="Task subject", required=True
                ),
                "status": ParameterDef(
                    type="string",
                    description="Status (Not Started / In Progress / Completed / etc.)",
                    default="Not Started",
                ),
                "priority": ParameterDef(
                    type="string", description="Priority", default="Normal"
                ),
                "activity_date": ParameterDef(
                    type="string", description="Due date (YYYY-MM-DD)"
                ),
                "what_id": ParameterDef(
                    type="string",
                    description="Related object ID (Account/Opportunity/etc.)",
                ),
                "who_id": ParameterDef(
                    type="string", description="Related Lead/Contact ID"
                ),
                "description": ParameterDef(type="string", description="Description"),
                "additional_fields": _additional_fields(),
            },
        ),
        ActionDefinition(
            name="create_case",
            description="Create a Case record (support ticket)",
            parameters={
                "subject": ParameterDef(
                    type="string", description="Case subject", required=True
                ),
                "status": ParameterDef(
                    type="string", description="Status", default="New"
                ),
                "priority": ParameterDef(
                    type="string", description="Priority", default="Medium"
                ),
                "origin": ParameterDef(
                    type="string", description="Origin (Email/Phone/Web/...)"
                ),
                "account_id": ParameterDef(
                    type="string", description="Linked Account ID"
                ),
                "contact_id": ParameterDef(
                    type="string", description="Linked Contact ID"
                ),
                "description": ParameterDef(type="string", description="Description"),
                "type": ParameterDef(type="string", description="Case type"),
                "reason": ParameterDef(type="string", description="Case reason"),
                "additional_fields": _additional_fields(),
            },
        ),
        ActionDefinition(
            name="add_contact_to_campaign",
            description="Create a CampaignMember linking a Contact to a Campaign",
            parameters={
                "campaign_id": ParameterDef(
                    type="string", description="Campaign ID", required=True
                ),
                "contact_id": ParameterDef(
                    type="string", description="Contact ID", required=True
                ),
                "status": ParameterDef(
                    type="string", description="Member status"
                ),
            },
        ),
        ActionDefinition(
            name="add_lead_to_campaign",
            description="Create a CampaignMember linking a Lead to a Campaign",
            parameters={
                "campaign_id": ParameterDef(
                    type="string", description="Campaign ID", required=True
                ),
                "lead_id": ParameterDef(
                    type="string", description="Lead ID", required=True
                ),
                "status": ParameterDef(
                    type="string", description="Member status"
                ),
            },
        ),
        ActionDefinition(
            name="describe_object",
            description="Describe an object type's fields + capabilities",
            parameters={"object_type": _object_type_param()},
        ),
        ActionDefinition(
            name="list_objects",
            description="List all queryable Salesforce objects in the org",
            parameters={},
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth 2.0 (Connected App)",
            description=(
                "Authenticate via a Salesforce Connected App. Provides "
                "refresh tokens for long-lived access."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="SALESFORCE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Connected App consumer key",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                ),
                EnvVar(
                    name="SALESFORCE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Connected App consumer secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.salesforce.com/services/oauth2/authorize",
                token_url="https://login.salesforce.com/services/oauth2/token",
                scopes=["api", "refresh_token", "offline_access"],
                token_auth_method="body",
            ),
            test_endpoint=_test_endpoint("access_token"),
        ),
        BearerTokenAuthSchema(
            display_name="Session ID / Access Token",
            description=(
                "Authenticate using a Salesforce Session ID or manually "
                "obtained Access Token. Useful for development."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="SALESFORCE_ACCESS_TOKEN",
                    display_name="Access Token / Session ID",
                    description="Salesforce access token or session ID",
                    required=True,
                    sensitive=True,
                ),
                EnvVar(
                    name="SALESFORCE_INSTANCE_URL",
                    display_name="Instance URL",
                    description=(
                        "Your Salesforce instance URL "
                        "(e.g. https://your-org.my.salesforce.com)"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="https://your-org.my.salesforce.com",
                ),
            ],
            test_endpoint=_test_endpoint("bearer_token"),
        ),
    ],
)
