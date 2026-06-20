"""Enrow integration manifest.

Enrow is a B2B email-finding and verification service. Both actions are
asynchronous on Enrow's side (submit returns a job id, a result endpoint
is polled until completion); each ``@tool`` folds the submit + poll loop
into one call.

Authentication is a single bring-your-own API key passed as the
``x-api-key`` header.
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
    name="enrow",
    display_name="Enrow",
    description=(
        "Find verified B2B email addresses from a full name and company, or "
        "verify the deliverability of an existing email. Enrow performs "
        "deterministic verifications including catch-all emails — no "
        "additional verifier needed."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:enrow-themed",
    app_url="https://enrow.io",
    categories=["Sales", "enrichment", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="find_email",
            description=(
                "Find a verified B2B email address from a full name and company "
                "domain or name. Submits an asynchronous search and polls until "
                "the result is ready. Provide company_domain (preferred) or "
                "company_name."
            ),
            parameters={
                "fullname": ParameterDef(
                    type="string",
                    description='Full name of the person (e.g. "John Doe")',
                    required=True,
                ),
                "company_domain": ParameterDef(
                    type="string",
                    description=(
                        'Company domain (e.g. "apple.com"). Preferred over '
                        "company_name. Provide company_domain or company_name."
                    ),
                ),
                "company_name": ParameterDef(
                    type="string",
                    description=(
                        'Company name (e.g. "Apple"). Used when the company '
                        "domain is unavailable. Provide company_domain or "
                        "company_name."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="verify_email",
            description=(
                "Verify the deliverability of an email address. Submits an "
                "asynchronous verification and polls until the result is ready."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description='Email address to verify (e.g. "john@example.com")',
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Enrow API key",
            setup_instructions=[
                "Sign in to your Enrow account at https://enrow.io",
                "Open the Integrations section of your account settings",
                "Copy your API key (or create a new one)",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="ENROW_API_KEY",
                    display_name="Enrow API Key",
                    description="Your Enrow API key from the Integrations section",
                    required=True,
                    sensitive=True,
                    about_url="https://enrow.readme.io",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.enrow.io/account/info",
                method="GET",
                headers={"x-api-key": "{api_key}"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates the API key against the account info endpoint",
            ),
        ),
    ],
)
