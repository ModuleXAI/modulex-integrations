"""Apollo.io integration manifest."""
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


def _pagination_params(default_per_page: int = 25) -> dict[str, ParameterDef]:
    return {
        "page": ParameterDef(type="integer", description="Page number", default=1),
        "per_page": ParameterDef(
            type="integer",
            description="Results per page",
            default=default_per_page,
        ),
    }


manifest = IntegrationManifest(
    name="apollo_io",
    display_name="Apollo.io",
    description=(
        "B2B sales intelligence platform with 210M+ contacts and 35M+ "
        "companies. Full CRM capabilities including enrichment, "
        "prospecting, contacts, accounts, deals, sequences, and tasks."
    ),
    version="2.0.0",
    author="ModuleX",
    logo="https://cdn.jsdelivr.net/gh/ModuleXAI/logox@main/tools/apollo.svg",
    app_url="https://www.apollo.io",
    categories=["CRM & Customer", "sales", "customer_support"],
    actions=[
        # --- Enrichment ---
        ActionDefinition(
            name="people_enrichment",
            description=(
                "Enrich a person's profile with employment history, contact "
                "info, and organization details. Consumes credits."
            ),
            parameters={
                "first_name": ParameterDef(type="string", description="First name"),
                "last_name": ParameterDef(type="string", description="Last name"),
                "name": ParameterDef(type="string", description="Full name"),
                "email": ParameterDef(type="string", description="Email address"),
                "organization_name": ParameterDef(
                    type="string", description="Employer name"
                ),
                "domain": ParameterDef(type="string", description="Employer domain"),
                "linkedin_url": ParameterDef(
                    type="string", description="LinkedIn profile URL"
                ),
                "reveal_personal_emails": ParameterDef(
                    type="boolean",
                    description="Include personal emails",
                    default=False,
                ),
                "reveal_phone_number": ParameterDef(
                    type="boolean", description="Include phone numbers", default=False
                ),
            },
        ),
        ActionDefinition(
            name="bulk_people_enrichment",
            description=(
                "Enrich up to 10 people in a single request. More efficient "
                "than individual calls. Consumes credits."
            ),
            parameters={
                "details": ParameterDef(
                    type="array",
                    description="List of person detail dicts (max 10)",
                    required=True,
                ),
                "reveal_personal_emails": ParameterDef(
                    type="boolean", description="Include personal emails", default=False
                ),
            },
        ),
        ActionDefinition(
            name="organization_enrichment",
            description=(
                "Enrich a company's profile with industry, revenue, employee "
                "count, funding, technologies. Consumes credits."
            ),
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Company domain (e.g. 'apollo.io')",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="bulk_organization_enrichment",
            description=(
                "Enrich up to 10 organizations in a single request. "
                "Consumes credits."
            ),
            parameters={
                "domains": ParameterDef(
                    type="array",
                    description="List of company domains (max 10)",
                    required=True,
                ),
            },
        ),
        # --- Search ---
        ActionDefinition(
            name="people_search",
            description=(
                "Search 210M+ contacts by job title, seniority, location, "
                "company. Requires paid plan."
            ),
            parameters={
                "person_titles": ParameterDef(
                    type="array", description="Job titles to search"
                ),
                "person_seniorities": ParameterDef(
                    type="array", description="Seniority levels"
                ),
                "person_locations": ParameterDef(
                    type="array", description="Person locations"
                ),
                "organization_locations": ParameterDef(
                    type="array", description="Company HQ locations"
                ),
                "q_organization_domains": ParameterDef(
                    type="array", description="Company domains"
                ),
                "organization_ids": ParameterDef(
                    type="array", description="Apollo organization IDs"
                ),
                "organization_num_employees_ranges": ParameterDef(
                    type="array", description="Employee ranges"
                ),
                "contact_email_status": ParameterDef(
                    type="array", description="Email verification status"
                ),
                "q_keywords": ParameterDef(type="string", description="Keyword search"),
                **_pagination_params(),
            },
        ),
        ActionDefinition(
            name="organization_search",
            description=(
                "Search 35M+ companies by size, location, revenue, "
                "technologies. Requires paid plan."
            ),
            parameters={
                "q_organization_name": ParameterDef(
                    type="string", description="Company name"
                ),
                "organization_locations": ParameterDef(
                    type="array", description="HQ locations"
                ),
                "organization_not_locations": ParameterDef(
                    type="array", description="Exclude locations"
                ),
                "organization_num_employees_ranges": ParameterDef(
                    type="array", description="Employee ranges"
                ),
                "revenue_range_min": ParameterDef(
                    type="integer", description="Min revenue"
                ),
                "revenue_range_max": ParameterDef(
                    type="integer", description="Max revenue"
                ),
                "currently_using_any_of_technology_uids": ParameterDef(
                    type="array", description="Technologies"
                ),
                "q_organization_keyword_tags": ParameterDef(
                    type="array", description="Industry keywords"
                ),
                **_pagination_params(),
            },
        ),
        ActionDefinition(
            name="organization_job_postings",
            description=(
                "Get active job postings for a company to understand "
                "hiring trends."
            ),
            parameters={
                "organization_id": ParameterDef(
                    type="string",
                    description="Apollo organization ID",
                    required=True,
                ),
            },
        ),
        # --- Contacts ---
        ActionDefinition(
            name="create_contact",
            description="Create a new contact in your Apollo database. Does not consume credits.",
            parameters={
                "email": ParameterDef(type="string", description="Contact email"),
                "first_name": ParameterDef(type="string", description="First name"),
                "last_name": ParameterDef(type="string", description="Last name"),
                "title": ParameterDef(type="string", description="Job title"),
                "organization_name": ParameterDef(
                    type="string", description="Company name"
                ),
                "account_id": ParameterDef(
                    type="string", description="Link to existing account"
                ),
                "phone_number": ParameterDef(type="string", description="Phone number"),
                "linkedin_url": ParameterDef(type="string", description="LinkedIn URL"),
                "present_raw_address": ParameterDef(
                    type="string", description="Address"
                ),
                "label_names": ParameterDef(type="array", description="Labels/tags"),
            },
        ),
        ActionDefinition(
            name="update_contact",
            description="Update an existing contact's information.",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="Contact ID to update",
                    required=True,
                ),
                "email": ParameterDef(type="string", description="New email"),
                "first_name": ParameterDef(type="string", description="New first name"),
                "last_name": ParameterDef(type="string", description="New last name"),
                "title": ParameterDef(type="string", description="New job title"),
                "phone_number": ParameterDef(type="string", description="New phone"),
                "account_id": ParameterDef(type="string", description="Link to account"),
            },
        ),
        ActionDefinition(
            name="search_contacts",
            description="Search contacts in your Apollo database.",
            parameters={
                "q_keywords": ParameterDef(type="string", description="Search keywords"),
                "contact_stage_ids": ParameterDef(
                    type="array", description="Filter by stage"
                ),
                "contact_owner_ids": ParameterDef(
                    type="array", description="Filter by owner"
                ),
                **_pagination_params(),
            },
        ),
        ActionDefinition(
            name="view_contact",
            description="View detailed information for a specific contact.",
            parameters={
                "contact_id": ParameterDef(
                    type="string", description="Contact ID to view", required=True
                ),
            },
        ),
        # --- Accounts ---
        ActionDefinition(
            name="create_account",
            description=(
                "Create a new account (company) in your database. Requires "
                "master API key."
            ),
            parameters={
                "name": ParameterDef(
                    type="string", description="Account/company name", required=True
                ),
                "domain": ParameterDef(
                    type="string", description="Company domain", required=True
                ),
                "phone_number": ParameterDef(type="string", description="Phone number"),
                "raw_address": ParameterDef(type="string", description="Address"),
                "owner_id": ParameterDef(type="string", description="Owner user ID"),
            },
        ),
        ActionDefinition(
            name="update_account",
            description="Update an existing account's information.",
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account ID to update", required=True
                ),
                "name": ParameterDef(type="string", description="New name"),
                "phone_number": ParameterDef(type="string", description="New phone"),
                "raw_address": ParameterDef(type="string", description="New address"),
                "owner_id": ParameterDef(type="string", description="New owner ID"),
            },
        ),
        ActionDefinition(
            name="search_accounts",
            description="Search accounts in your Apollo database.",
            parameters={
                "q_organization_name": ParameterDef(
                    type="string", description="Search by name"
                ),
                "account_stage_ids": ParameterDef(
                    type="array", description="Filter by stage"
                ),
                "account_owner_ids": ParameterDef(
                    type="array", description="Filter by owner"
                ),
                **_pagination_params(),
            },
        ),
        ActionDefinition(
            name="view_account",
            description="View detailed information for a specific account.",
            parameters={
                "account_id": ParameterDef(
                    type="string", description="Account ID to view", required=True
                ),
            },
        ),
        # --- Deals ---
        ActionDefinition(
            name="create_deal",
            description="Create a new deal/opportunity. Requires master API key.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Deal name", required=True
                ),
                "deal_stage_id": ParameterDef(
                    type="string", description="Deal stage ID", required=True
                ),
                "amount": ParameterDef(type="number", description="Deal amount"),
                "account_id": ParameterDef(
                    type="string", description="Associated account ID"
                ),
                "contact_ids": ParameterDef(
                    type="array", description="Associated contact IDs"
                ),
                "owner_id": ParameterDef(
                    type="string", description="Deal owner user ID"
                ),
                "closed_date": ParameterDef(
                    type="string",
                    description="Expected close date (YYYY-MM-DD)",
                ),
            },
        ),
        ActionDefinition(
            name="update_deal",
            description="Update an existing deal.",
            parameters={
                "deal_id": ParameterDef(
                    type="string", description="Deal ID to update", required=True
                ),
                "name": ParameterDef(type="string", description="New name"),
                "deal_stage_id": ParameterDef(
                    type="string", description="New stage ID"
                ),
                "amount": ParameterDef(type="number", description="New amount"),
                "owner_id": ParameterDef(type="string", description="New owner ID"),
            },
        ),
        ActionDefinition(
            name="list_deals",
            description="List all deals in your Apollo account.",
            parameters=_pagination_params(),
        ),
        ActionDefinition(
            name="view_deal",
            description="View detailed information for a specific deal.",
            parameters={
                "deal_id": ParameterDef(
                    type="string", description="Deal ID to view", required=True
                ),
            },
        ),
        # --- Sequences ---
        ActionDefinition(
            name="search_sequences",
            description="Search for email sequences in your Apollo account.",
            parameters={
                "q_name": ParameterDef(
                    type="string", description="Sequence name to search"
                ),
                **_pagination_params(),
            },
        ),
        ActionDefinition(
            name="add_contacts_to_sequence",
            description="Add contacts to an email sequence for automated outreach.",
            parameters={
                "sequence_id": ParameterDef(
                    type="string", description="Sequence ID", required=True
                ),
                "contact_ids": ParameterDef(
                    type="array",
                    description="Contact IDs to enroll",
                    required=True,
                ),
                "emailer_campaign_id": ParameterDef(
                    type="string", description="Email campaign ID"
                ),
                "send_email_from_email_account_id": ParameterDef(
                    type="string", description="Sender email account ID"
                ),
            },
        ),
        # --- Tasks ---
        ActionDefinition(
            name="create_task",
            description="Create a new task/reminder in Apollo.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Task name/subject", required=True
                ),
                "due_date": ParameterDef(
                    type="string", description="Due date (YYYY-MM-DD)", required=True
                ),
                "priority": ParameterDef(
                    type="string",
                    description="Priority ('low', 'normal', 'high')",
                    default="normal",
                ),
                "contact_id": ParameterDef(
                    type="string", description="Associated contact ID"
                ),
                "account_id": ParameterDef(
                    type="string", description="Associated account ID"
                ),
                "user_id": ParameterDef(
                    type="string", description="Assigned user ID"
                ),
                "note": ParameterDef(type="string", description="Task notes"),
            },
        ),
        ActionDefinition(
            name="search_tasks",
            description="Search tasks in your Apollo account.",
            parameters={
                "status": ParameterDef(type="string", description="Status filter"),
                "user_ids": ParameterDef(
                    type="array", description="Filter by assigned users"
                ),
                **_pagination_params(),
            },
        ),
        # --- Utility ---
        ActionDefinition(
            name="get_api_usage",
            description="Get API usage statistics and rate limit information.",
            parameters={},
        ),
        ActionDefinition(
            name="list_users",
            description="List all team members in your Apollo account.",
            parameters=_pagination_params(),
        ),
        ActionDefinition(
            name="list_contact_stages",
            description="List all contact stages configured in your Apollo account.",
            parameters={},
        ),
        ActionDefinition(
            name="list_account_stages",
            description="List all account stages configured in your Apollo account.",
            parameters={},
        ),
        ActionDefinition(
            name="list_deal_stages",
            description="List all deal stages configured in your Apollo account.",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using your Apollo.io API key. Some endpoints "
                "require master API key."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="APOLLO_IO_API_KEY",
                    display_name="Apollo.io API Key",
                    description="Your Apollo.io API key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="x" * 32,
                    about_url="https://docs.apollo.io/reference/authentication",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.apollo.io/api/v1/organizations/enrich",
                method="GET",
                headers={
                    "Content-Type": "application/json",
                    "X-Api-Key": "{api_key}",
                },
                params={"domain": "apollo.io"},
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["organization"]
                ),
                cost_level="minimal",
                description="Validates API key with organization enrichment",
            ),
        ),
    ],
)
