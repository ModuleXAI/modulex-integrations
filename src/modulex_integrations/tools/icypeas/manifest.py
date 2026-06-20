"""Icypeas integration manifest."""
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
    name="icypeas",
    display_name="Icypeas",
    description=(
        "Find a professional email address from a name and company domain, or "
        "verify whether an existing email is valid and deliverable. Results are "
        "returned asynchronously via polling."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:icypeas-themed",
    app_url="https://www.icypeas.com",
    categories=["Sales", "enrichment", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="find_email",
            description=(
                "Find a professional email address from a first name, last name, "
                "and company domain or name. Submits the search and polls until a "
                "result is available."
            ),
            parameters={
                "domain_or_company": ParameterDef(
                    type="string",
                    description=(
                        "Target company domain (e.g. stripe.com) or company name "
                        "(e.g. Stripe)"
                    ),
                    required=True,
                ),
                "firstname": ParameterDef(
                    type="string",
                    description="Target person's first name",
                ),
                "lastname": ParameterDef(
                    type="string",
                    description="Target person's last name",
                ),
            },
        ),
        ActionDefinition(
            name="verify_email",
            description=(
                "Verify whether an email address is valid and deliverable. Submits "
                "the verification and polls until a result is available."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address to verify (e.g. john@stripe.com)",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Icypeas API key",
            setup_instructions=[
                "Go to https://app.icypeas.com and sign up or log in",
                "Open the API settings / API access section in your account",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="ICYPEAS_API_KEY",
                    display_name="Icypeas API Key",
                    description="Your Icypeas API key from app.icypeas.com",
                    required=True,
                    sensitive=True,
                    about_url="https://www.icypeas.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://app.icypeas.com/api/email-verification",
                method="POST",
                headers={
                    "Authorization": "{api_key}",
                    "Content-Type": "application/json",
                },
                body={"email": "test@example.com"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["success"],
                ),
                cost_level="minimal",
                description="Validates the API key by submitting a minimal verification job",
            ),
        ),
    ],
)
