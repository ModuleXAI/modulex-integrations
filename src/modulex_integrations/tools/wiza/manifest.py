"""Wiza integration manifest.

Wiza is a B2B contact-data platform: prospect search, company
enrichment, individual contact reveal (verified emails + phones), and
credit-balance lookup. Authentication is a single API key sent as
``Authorization: Bearer <api_key>``; the credential test hits
``GET /api/meta/credits``.
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


manifest = IntegrationManifest(
    name="wiza",
    display_name="Wiza",
    description=(
        "Find, enrich, and verify B2B contact data with Wiza. Search prospects, "
        "enrich companies, reveal verified emails and phone numbers for "
        "individuals, and check your account credit balance."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:wiza-themed",
    app_url="https://wiza.co",
    categories=["Sales", "enrichment", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="prospect_search",
            description=(
                "Search Wiza's database of prospects using person, company, and "
                "financial filters."
            ),
            parameters={
                "size": ParameterDef(
                    type="integer",
                    description=(
                        "Number of sample profiles to return (0-30, default 0 "
                        "returns total only)"
                    ),
                ),
                "filters": ParameterDef(
                    type="object",
                    description=(
                        "Full filters object (overrides individual filter params "
                        "if provided)"
                    ),
                ),
                "first_name": ParameterDef(
                    type="array",
                    description='Exact first names to match (e.g., ["John", "Jane"])',
                ),
                "last_name": ParameterDef(
                    type="array",
                    description="Exact last names to match",
                ),
                "job_title": ParameterDef(
                    type="array",
                    description=(
                        'Job titles to include/exclude (e.g., [{"v":"CEO","s":"i"}])'
                    ),
                ),
                "job_title_level": ParameterDef(
                    type="array",
                    description='Seniority levels (e.g., ["cxo", "director", "manager"])',
                ),
                "job_role": ParameterDef(
                    type="array",
                    description='Job role categories (e.g., ["sales", "engineering"])',
                ),
                "job_sub_role": ParameterDef(
                    type="array",
                    description='Detailed role categories (e.g., ["software", "product"])',
                ),
                "location": ParameterDef(
                    type="array",
                    description=(
                        "Person location filters (city/state/country with "
                        "include/exclude)"
                    ),
                ),
                "skill": ParameterDef(
                    type="array",
                    description='Professional skills (e.g., ["python", "marketing"])',
                ),
                "school": ParameterDef(
                    type="array",
                    description="Educational institutions",
                ),
                "major": ParameterDef(
                    type="array",
                    description="Field of study",
                ),
                "linkedin_slug": ParameterDef(
                    type="array",
                    description="LinkedIn profile slugs",
                ),
                "job_company": ParameterDef(
                    type="array",
                    description="Current company filters (include/exclude)",
                ),
                "past_company": ParameterDef(
                    type="array",
                    description="Past company filters (include/exclude)",
                ),
                "company_location": ParameterDef(
                    type="array",
                    description="Company HQ location filters",
                ),
                "company_industry": ParameterDef(
                    type="array",
                    description="Company industry filters (include/exclude)",
                ),
                "company_size": ParameterDef(
                    type="array",
                    description='Company headcount brackets (e.g., ["11-50", "51-200"])',
                ),
                "company_type": ParameterDef(
                    type="array",
                    description='Company type (e.g., ["private", "public"])',
                ),
            },
        ),
        ActionDefinition(
            name="company_enrichment",
            description=(
                "Enrich a company by name, domain, LinkedIn ID, or LinkedIn slug "
                "with detailed firmographic data."
            ),
            parameters={
                "company_name": ParameterDef(
                    type="string",
                    description='Company name (e.g., "Wiza")',
                ),
                "company_domain": ParameterDef(
                    type="string",
                    description='Company domain (e.g., "wiza.co")',
                ),
                "company_linkedin_id": ParameterDef(
                    type="string",
                    description="Company LinkedIn ID",
                ),
                "company_linkedin_slug": ParameterDef(
                    type="string",
                    description="Company LinkedIn slug from the URL",
                ),
            },
        ),
        ActionDefinition(
            name="individual_reveal",
            description=(
                "Reveal a contact via LinkedIn URL, name + company/domain, or "
                "email. Starts the reveal and polls until it resolves. Uses 2 "
                "credits per valid email and 5 credits per phone, charged only on "
                "success."
            ),
            parameters={
                "enrichment_level": ParameterDef(
                    type="string",
                    description="Enrichment depth: 'none', 'partial', 'phone', or 'full'",
                    required=True,
                ),
                "profile_url": ParameterDef(
                    type="string",
                    description=(
                        "LinkedIn profile URL (e.g., https://linkedin.com/in/johndoe)"
                    ),
                ),
                "full_name": ParameterDef(
                    type="string",
                    description="Full name (used with company or domain)",
                ),
                "company": ParameterDef(
                    type="string",
                    description="Company name (used with full_name)",
                ),
                "domain": ParameterDef(
                    type="string",
                    description="Company domain (used with full_name)",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Email address (use alone or with other identifiers)",
                ),
                "accept_work": ParameterDef(
                    type="boolean",
                    description="Whether to accept work emails (email_options)",
                ),
                "accept_personal": ParameterDef(
                    type="boolean",
                    description="Whether to accept personal emails (email_options)",
                ),
            },
        ),
        ActionDefinition(
            name="get_credits",
            description="Retrieve the remaining credits on your Wiza account.",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Wiza API key",
            setup_instructions=[
                "Log in to your Wiza account at https://app.wiza.co",
                "Open Settings -> API and generate a new API key (or copy an existing one)",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="WIZA_API_KEY",
                    display_name="Wiza API Key",
                    description="Your Wiza API key from Settings -> API",
                    required=True,
                    sensitive=True,
                    about_url="https://app.wiza.co",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://wiza.co/api/meta/credits",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["credits"],
                ),
                cost_level="free",
                description="Validates the API key by reading the account credit balance",
            ),
        ),
    ],
)
