"""Dropcontact integration manifest.

Dropcontact is a GDPR-compliant B2B contact enrichment service. The
single action submits a contact and polls until verified email,
phone, company firmographics, and LinkedIn data are returned.

Auth is key-based (``api_key``): the runtime injects the user's
Dropcontact API key, which the tools send as the ``X-Access-Token``
header.
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
    name="dropcontact",
    display_name="Dropcontact",
    description=(
        "Verify and enrich B2B contacts. Submit a contact with their name, "
        "company, website, or LinkedIn URL and receive a verified "
        "professional email, phone number, company firmographics, and "
        "LinkedIn profile. Enrichment is asynchronous: the request is "
        "submitted and polled until the result is ready. Credits are only "
        "charged when a verified email is returned."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:dropcontact",
    app_url="https://www.dropcontact.com",
    categories=["Sales", "CRM", "enrichment"],
    actions=[
        ActionDefinition(
            name="enrich_contact",
            description=(
                "Enrich a contact with verified B2B email, phone, company data, "
                "and LinkedIn info via Dropcontact. Submits an async enrichment "
                "request, then polls until the result is ready (up to 2 minutes). "
                "Charges 1 credit only when a verified email is returned. Provide "
                "at least one of: email, first_name + last_name + company, "
                "full_name + company, or a LinkedIn URL."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address of the contact to enrich",
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="First name of the contact",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Last name of the contact",
                ),
                "full_name": ParameterDef(
                    type="string",
                    description="Full name (alternative to first_name + last_name)",
                ),
                "company": ParameterDef(
                    type="string",
                    description="Company name",
                ),
                "website": ParameterDef(
                    type="string",
                    description="Company website (e.g. acme.com)",
                ),
                "num_siren": ParameterDef(
                    type="string",
                    description="French company SIREN number",
                ),
                "phone": ParameterDef(
                    type="string",
                    description="Phone number",
                ),
                "linkedin": ParameterDef(
                    type="string",
                    description="LinkedIn profile URL",
                ),
                "country": ParameterDef(
                    type="string",
                    description='Country code (ISO 3166-1 alpha-2, e.g. "US", "FR")',
                ),
                "siren": ParameterDef(
                    type="boolean",
                    description="Include SIREN/SIRET enrichment (France only)",
                    default=False,
                ),
                "language": ParameterDef(
                    type="string",
                    description='Language for returned data (e.g. "en", "fr")',
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Dropcontact API key",
            setup_instructions=[
                "Sign in to your Dropcontact account at https://app.dropcontact.com",
                "Open the 'API & Integrations' settings",
                "Copy your personal API key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="DROPCONTACT_API_KEY",
                    display_name="Dropcontact API Key",
                    description="Your Dropcontact API key (sent as the X-Access-Token header)",
                    required=True,
                    sensitive=True,
                    about_url="https://support.dropcontact.com/article/237-how-to-use-the-dropcontact-api-key",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.dropcontact.com/v1/enrich/all",
                method="POST",
                headers={
                    "X-Access-Token": "{api_key}",
                    "Content-Type": "application/json",
                },
                body={"data": [{"email": "test@dropcontact.com"}], "siren": False},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["request_id"],
                ),
                cost_level="minimal",
                description=(
                    "Validates the API key by submitting a minimal enrichment "
                    "request and confirming a request_id is returned"
                ),
            ),
        ),
    ],
)
