"""Findymail integration manifest."""
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


_TEST_HEADERS = {
    "Authorization": "Bearer {api_key}",
    "Accept": "application/json",
}
_TEST_SUCCESS = SuccessIndicators(
    status_codes=[200],
    response_fields=["credits"],
)


manifest = IntegrationManifest(
    name="findymail",
    display_name="Findymail",
    description=(
        "Find verified work emails by name, domain, or LinkedIn URL, verify "
        "deliverability, reverse-lookup profiles from emails, enrich company "
        "data, find employees by job title, look up phone numbers, search "
        "technology stacks, and check credit usage."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:findymail",
    app_url="https://www.findymail.com",
    categories=["Sales", "enrichment", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="find_email_from_name",
            description=(
                "Find someone's email from their name and a company domain or "
                "company name. Uses one finder credit when a verified email is found."
            ),
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Person's full name (e.g., 'John Doe')",
                    required=True,
                ),
                "domain": ParameterDef(
                    type="string",
                    description=(
                        "Company domain (preferred) or company name (e.g., stripe.com)"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="find_email_from_linkedin",
            description=(
                "Find someone's email from a LinkedIn profile URL or username. "
                "Uses one finder credit when a verified email is found."
            ),
            parameters={
                "linkedin_url": ParameterDef(
                    type="string",
                    description=(
                        "Person's LinkedIn URL or username "
                        "(e.g., 'https://linkedin.com/in/johndoe' or 'johndoe')"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="find_emails_by_domain",
            description=(
                "Find verified contacts at a given domain matching one or more "
                "target roles (max 3 roles)."
            ),
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Company domain (e.g., stripe.com)",
                    required=True,
                ),
                "roles": ParameterDef(
                    type="array",
                    description='Target roles at the company (max 3, e.g., ["CEO", "Founder"])',
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="verify_email",
            description=(
                "Verify the deliverability of an email address. Uses one verifier credit."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address to verify (e.g., john@example.com)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="reverse_email_lookup",
            description=(
                "Find a business profile from an email address. Uses 1 finder "
                "credit if a profile is found, 2 credits if returning full profile data."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Work or personal email address to look up",
                    required=True,
                ),
                "with_profile": ParameterDef(
                    type="boolean",
                    description="Whether to return enriched profile metadata (default: false)",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_company",
            description=(
                "Retrieve company information from a LinkedIn URL, domain, or "
                "company name (provide at least one). Uses 1 finder credit per "
                "successful response."
            ),
            parameters={
                "linkedin_url": ParameterDef(
                    type="string",
                    description=(
                        "Company LinkedIn URL "
                        "(e.g., https://www.linkedin.com/company/stripe/)"
                    ),
                ),
                "domain": ParameterDef(
                    type="string",
                    description="Company domain (e.g., stripe.com)",
                ),
                "name": ParameterDef(
                    type="string",
                    description="Company name (e.g., Stripe)",
                ),
            },
        ),
        ActionDefinition(
            name="find_employees",
            description=(
                "Find employees at a company by website and target job titles. "
                "Uses 1 credit per found contact. Does not return email addresses."
            ),
            parameters={
                "website": ParameterDef(
                    type="string",
                    description="Company website or domain (e.g., google.com)",
                    required=True,
                ),
                "job_titles": ParameterDef(
                    type="array",
                    description=(
                        'Target job titles to search for '
                        '(max 10, e.g., ["Software Engineer", "CEO"])'
                    ),
                    required=True,
                ),
                "count": ParameterDef(
                    type="integer",
                    description="Number of contacts to return (max 5, default 1)",
                ),
            },
        ),
        ActionDefinition(
            name="find_phone",
            description=(
                "Find someone's phone number from a LinkedIn profile URL. Uses 10 "
                "finder credits if a phone is found. EU citizens are excluded for "
                "legal reasons."
            ),
            parameters={
                "linkedin_url": ParameterDef(
                    type="string",
                    description=(
                        "Person's LinkedIn URL or username "
                        "(e.g., 'https://linkedin.com/in/johndoe' or 'johndoe')"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_technologies",
            description=(
                "Search the technology catalog by name. Returns up to 25 "
                "technologies. Free endpoint, rate limited to 10 requests per minute."
            ),
            parameters={
                "q": ParameterDef(
                    type="string",
                    description='Search term (min 2 characters, e.g., "React")',
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="lookup_technologies",
            description=(
                "Get the technology stack for a company by domain. Optionally "
                "filter by technology names. 1 finder credit if technologies are "
                "found, free otherwise."
            ),
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Company domain to look up (e.g., stripe.com)",
                    required=True,
                ),
                "technologies": ParameterDef(
                    type="array",
                    description=(
                        'Filter by technology names, case-insensitive '
                        '(e.g., ["React", "TypeScript"])'
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_credits",
            description=(
                "Retrieve the remaining finder and verifier credits for the "
                "authenticated account."
            ),
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Findymail API key",
            setup_instructions=[
                "Sign in at https://app.findymail.com",
                "Open the API page in your dashboard",
                "Copy your API key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="FINDYMAIL_API_KEY",
                    display_name="Findymail API Key",
                    description="Your Findymail API key from the dashboard API page",
                    required=True,
                    sensitive=True,
                    about_url="https://app.findymail.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://app.findymail.com/api/credits",
                method="GET",
                headers=_TEST_HEADERS,
                success_indicators=_TEST_SUCCESS,
                cost_level="minimal",
                description="Validates the API key by reading the account's remaining credits",
            ),
        ),
    ],
)
