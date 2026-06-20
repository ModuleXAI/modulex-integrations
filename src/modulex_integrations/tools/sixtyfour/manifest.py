"""Sixtyfour AI integration manifest."""
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
    name="sixtyfour",
    display_name="Sixtyfour AI",
    description=(
        "Find emails, phone numbers, and enrich lead or company data with contact "
        "information, social profiles, and detailed research using Sixtyfour AI."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:sixtyfour-themed",
    app_url="https://sixtyfour.ai",
    categories=["Sales", "enrichment", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="find_phone",
            description="Find phone numbers for a lead using Sixtyfour AI.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Full name of the person",
                    required=True,
                ),
                "company": ParameterDef(
                    type="string",
                    description="Company name",
                ),
                "linkedin_url": ParameterDef(
                    type="string",
                    description="LinkedIn profile URL",
                ),
                "domain": ParameterDef(
                    type="string",
                    description="Company website domain",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Email address",
                ),
            },
        ),
        ActionDefinition(
            name="find_email",
            description="Find email addresses for a lead using Sixtyfour AI.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Full name of the person",
                    required=True,
                ),
                "company": ParameterDef(
                    type="string",
                    description="Company name",
                ),
                "linkedin_url": ParameterDef(
                    type="string",
                    description="LinkedIn profile URL",
                ),
                "domain": ParameterDef(
                    type="string",
                    description="Company website domain",
                ),
                "phone": ParameterDef(
                    type="string",
                    description="Phone number",
                ),
                "title": ParameterDef(
                    type="string",
                    description="Job title",
                ),
                "mode": ParameterDef(
                    type="string",
                    description="Email discovery mode: 'PROFESSIONAL' (default) or 'PERSONAL'",
                    default="PROFESSIONAL",
                ),
            },
        ),
        ActionDefinition(
            name="enrich_lead",
            description=(
                "Enrich lead information with contact details, social profiles, and "
                "company data using Sixtyfour AI."
            ),
            parameters={
                "lead_info": ParameterDef(
                    type="object",
                    description=(
                        "Lead information as a JSON object with key-value pairs "
                        "(e.g. name, company, title, linkedin)"
                    ),
                    required=True,
                ),
                "struct": ParameterDef(
                    type="object",
                    description=(
                        "Fields to collect as a JSON object. Keys are field names, "
                        "values are descriptions (e.g. {\"email\": \"Email address\", "
                        "\"phone\": \"Phone number\"})"
                    ),
                    required=True,
                ),
                "research_plan": ParameterDef(
                    type="string",
                    description="Optional research plan to guide enrichment strategy",
                ),
            },
        ),
        ActionDefinition(
            name="enrich_company",
            description=(
                "Enrich company data with additional information and find associated "
                "people using Sixtyfour AI."
            ),
            parameters={
                "target_company": ParameterDef(
                    type="object",
                    description=(
                        "Company data as a JSON object "
                        "(e.g. {\"name\": \"Acme Inc\", \"domain\": \"acme.com\"})"
                    ),
                    required=True,
                ),
                "struct": ParameterDef(
                    type="object",
                    description=(
                        "Fields to collect as a JSON object. Keys are field names, "
                        "values are descriptions (e.g. {\"website\": \"Company website "
                        "URL\", \"num_employees\": \"Employee count\"})"
                    ),
                    required=True,
                ),
                "find_people": ParameterDef(
                    type="boolean",
                    description="Whether to find people associated with the company",
                ),
                "full_org_chart": ParameterDef(
                    type="boolean",
                    description="Whether to retrieve the full organizational chart",
                ),
                "research_plan": ParameterDef(
                    type="string",
                    description=(
                        "Optional strategy describing how the agent should search for "
                        "information"
                    ),
                ),
                "people_focus_prompt": ParameterDef(
                    type="string",
                    description="Description of people to find (roles, responsibilities)",
                ),
                "lead_struct": ParameterDef(
                    type="object",
                    description="Custom schema for returned lead data as a JSON object",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Sixtyfour AI API key",
            setup_instructions=[
                "Sign up or log in at https://app.sixtyfour.ai",
                "Open your account settings and locate the API keys section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SIXTYFOUR_API_KEY",
                    display_name="Sixtyfour AI API Key",
                    description="Your Sixtyfour AI API key",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.sixtyfour.ai/introduction",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.sixtyfour.ai/find-email",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": "{api_key}",
                },
                body={"lead": {"name": "Test User"}},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="minimal",
                description="Validates the API key with a minimal find-email request",
            ),
        ),
    ],
)
