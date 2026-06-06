"""Hunter integration manifest."""
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
    name="hunter",
    display_name="Hunter",
    description="Find and verify professional email addresses using the Hunter.io API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:hunter",
    app_url="https://hunter.io",
    categories=["Sales", "Marketing & Sales", "Lead Generation", "Email"],
    actions=[
        ActionDefinition(
            name="account_information",
            description="Get information about your Hunter account",
            parameters={},
        ),
        ActionDefinition(
            name="combined_enrichment",
            description="Returns all the information associated with an email address and its domain name",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="The email address you want to find information about",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_lead",
            description="Create a new lead in your Hunter account",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="The email address of the lead",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="The first name of the lead",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="The last name of the lead",
                ),
                "position": ParameterDef(
                    type="string",
                    description="The job title of the lead",
                ),
                "company": ParameterDef(
                    type="string",
                    description="The name of the company the lead is working in",
                ),
                "company_industry": ParameterDef(
                    type="string",
                    description="The sector of the company. Allowed values: Animal, Art & Entertainment, Automotive, Beauty & Fitness, Books & Literature, Education & Career, Finance, Food & Drink, Game, Health, Hobby & Leisure, Home & Garden, Industry, Internet & Telecom, Law & Government, Manufacturing, News, Real Estate, Science, Retail, Sport, Technology, Travel",
                ),
                "company_size": ParameterDef(
                    type="string",
                    description="The size of the company the lead is working in",
                ),
                "confidence_score": ParameterDef(
                    type="integer",
                    description="Estimation of the probability the email address returned is correct, between 0 and 100",
                ),
                "website": ParameterDef(
                    type="string",
                    description="The domain name of the company",
                ),
                "country_code": ParameterDef(
                    type="string",
                    description="The country of the lead (ISO 3166-1 alpha-2 standard)",
                ),
                "linkedin_url": ParameterDef(
                    type="string",
                    description="The address of the public profile on LinkedIn",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="The phone number of the lead",
                ),
                "twitter": ParameterDef(
                    type="string",
                    description="The Twitter handle of the lead",
                ),
                "notes": ParameterDef(
                    type="string",
                    description="Some personal notes about the lead",
                ),
                "source": ParameterDef(
                    type="string",
                    description="The source where the lead has been found",
                ),
                "leads_list_id": ParameterDef(
                    type="string",
                    description="The identifier of the list the lead belongs to. If not specified, the lead is saved in the last list created",
                ),
            },
        ),
        ActionDefinition(
            name="delete_lead",
            description="Delete an existing lead from your Hunter account",
            parameters={
                "lead_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the lead",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="domain_search",
            description="Search all the email addresses corresponding to one website or company",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Domain name from which you want to find the email addresses. For example, 'stripe.com'. Either domain or company must be provided",
                ),
                "company": ParameterDef(
                    type="string",
                    description="The company name from which you want to find the email addresses. For example, 'stripe'. Either domain or company must be provided",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Specifies the max number of email addresses to return",
                    default=100,
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="Get only personal or generic email addresses. Allowed values: personal, generic",
                ),
                "seniority": ParameterDef(
                    type="string",
                    description="Get only email addresses for people with the selected seniority level(s). Comma-separated values: junior, senior, executive",
                ),
                "department": ParameterDef(
                    type="string",
                    description="Get only email addresses for people working in the selected department(s). Comma-separated values: executive, it, finance, management, sales, legal, support, hr, marketing, communication, education, design, health, operations",
                ),
            },
        ),
        ActionDefinition(
            name="email_count",
            description="Get the number of email addresses Hunter has for one domain or company",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Domain name from which you want to find the email addresses. For example, 'stripe.com'. Either domain or company must be provided",
                ),
                "company": ParameterDef(
                    type="string",
                    description="The company name from which you want to find the email addresses. For example, 'stripe'. Either domain or company must be provided",
                ),
                "type": ParameterDef(
                    type="string",
                    description="Get only personal or generic email addresses. Allowed values: personal, generic",
                ),
            },
        ),
        ActionDefinition(
            name="email_finder",
            description="Find the most likely email address from a domain name, a first name and a last name",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Domain name from which you want to find the email addresses. For example, 'stripe.com'. Either domain or company must be provided",
                ),
                "company": ParameterDef(
                    type="string",
                    description="The company name from which you want to find the email addresses. For example, 'stripe'. Either domain or company must be provided",
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="The person's first name",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="The person's last name",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="email_verifier",
            description="Check the deliverability of a given email address, verify if it has been found in Hunter's database, and return their sources",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="The email address you want to verify",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_lead",
            description="Retrieve one of your leads by ID",
            parameters={
                "lead_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the lead",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_leads_list",
            description="Retrieves all the fields of a leads list, including its leads",
            parameters={
                "leads_list_id": ParameterDef(
                    type="string",
                    description="Identifier of the leads list to retrieve",
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="A limit on the number of leads to be returned. Limit can range between 1 and 100",
                    default=100,
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_leads",
            description="List all your leads with comprehensive filtering options",
            parameters={
                "leads_list_id": ParameterDef(
                    type="string",
                    description="Only returns the leads belonging to this list",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Filter leads by email",
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="Filter leads by first name",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Filter leads by last name",
                ),
                "position": ParameterDef(
                    type="string",
                    description="Filter leads by position",
                ),
                "company": ParameterDef(
                    type="string",
                    description="Filter leads by company",
                ),
                "industry": ParameterDef(
                    type="string",
                    description="Filter leads by industry",
                ),
                "website": ParameterDef(
                    type="string",
                    description="Filter leads by website",
                ),
                "country_code": ParameterDef(
                    type="string",
                    description="Filter leads by country code (ISO 3166-1 alpha-2)",
                ),
                "company_size": ParameterDef(
                    type="string",
                    description="Filter leads by company size",
                ),
                "source": ParameterDef(
                    type="string",
                    description="Filter leads by source",
                ),
                "twitter": ParameterDef(
                    type="string",
                    description="Filter leads by Twitter handle",
                ),
                "linkedin_url": ParameterDef(
                    type="string",
                    description="Filter leads by LinkedIn URL",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="Filter leads by phone number",
                ),
                "sync_status": ParameterDef(
                    type="string",
                    description="Filter by synchronization status. Allowed values: pending, error, success",
                ),
                "sending_status": ParameterDef(
                    type="string",
                    description="Filter by sending status. Comma-separated values: clicked, opened, sent, pending, error, bounced, unsubscribed, replied",
                ),
                "verification_status": ParameterDef(
                    type="string",
                    description="Filter by verification status. Comma-separated values: accept_all, disposable, invalid, unknown, valid, webmail, pending",
                ),
                "last_activity_at": ParameterDef(
                    type="string",
                    description="Filter by last activity. Allowed values: * (any), ~ (unset)",
                ),
                "last_contacted_at": ParameterDef(
                    type="string",
                    description="Filter by last contact date. Allowed values: * (any), ~ (unset)",
                ),
                "query": ParameterDef(
                    type="string",
                    description="Only returns leads with First Name, Last Name, or Email matching the query",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="A limit on the number of leads to be returned. Limit can range between 1 and 1000",
                    default=100,
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_leads_lists",
            description="List all your leads lists, sorted with the most recent first",
            parameters={
                "limit": ParameterDef(
                    type="integer",
                    description="A limit on the number of lists to be returned. Limit can range between 1 and 100",
                    default=100,
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_lead",
            description="Update an existing lead in your Hunter account",
            parameters={
                "lead_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the lead",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="The email address of the lead",
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="The person's first name",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="The person's last name",
                ),
                "position": ParameterDef(
                    type="string",
                    description="The person's position in the company",
                ),
                "company": ParameterDef(
                    type="string",
                    description="The company name",
                ),
                "website": ParameterDef(
                    type="string",
                    description="The website URL of the company",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="The person's phone number",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Hunter API key",
            setup_instructions=[
                "Go to https://hunter.io and sign in",
                "Navigate to your account API settings at https://hunter.io/api-keys",
                "Copy your API key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="HUNTER_API_KEY",
                    display_name="Hunter API Key",
                    description="Your Hunter API key from hunter.io/api-keys",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://hunter.io/api-keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.hunter.io/v2/account",
                method="GET",
                headers={},
                params={"api_key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API key by fetching account information",
            ),
        ),
    ],
)
