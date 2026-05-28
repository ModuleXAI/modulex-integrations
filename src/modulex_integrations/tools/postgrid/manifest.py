"""PostGrid integration manifest."""
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
    name="postgrid",
    display_name="PostGrid",
    description="Programmatic direct mail delivery via the PostGrid Print & Mail API",
    logo="modulex:postgrid-themed",
    version="1.0.0",
    author="ModuleX",
    app_url="https://www.postgrid.com",
    categories=["Marketing", "Business Services"],
    actions=[
        ActionDefinition(
            name="create_contact",
            description="Create a new contact in PostGrid",
            parameters={
                "first_name": ParameterDef(
                    type="string",
                    description="The first name of the contact",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="The last name of the contact",
                ),
                "company_name": ParameterDef(
                    type="string",
                    description="The contact's company name",
                ),
                "address_line1": ParameterDef(
                    type="string",
                    description="The contact's first address line",
                    required=True,
                ),
                "address_line2": ParameterDef(
                    type="string",
                    description="The contact's second address line",
                ),
                "city": ParameterDef(
                    type="string",
                    description="The contact's city",
                ),
                "province_or_state": ParameterDef(
                    type="string",
                    description="The province or state of the contact",
                ),
                "email": ParameterDef(
                    type="string",
                    description="The contact's email address",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="The contact's phone number",
                ),
                "job_title": ParameterDef(
                    type="string",
                    description="The contact's job title",
                ),
                "postal_or_zip": ParameterDef(
                    type="string",
                    description="The postal code or ZIP code of the contact",
                ),
                "country_code": ParameterDef(
                    type="string",
                    description="ISO 3166-1 country code of the contact's address. Defaults to CA",
                    default="CA",
                ),
                "description": ParameterDef(
                    type="string",
                    description="A description for the contact",
                ),
                "skip_verification": ParameterDef(
                    type="boolean",
                    description="If true, skip address verification and mark the address as failed",
                ),
            },
        ),
        ActionDefinition(
            name="create_letter",
            description="Create a new letter in PostGrid",
            parameters={
                "to": ParameterDef(
                    type="string",
                    description="The ID or contact object of the receiver",
                    required=True,
                ),
                "from_contact": ParameterDef(
                    type="string",
                    description="The ID or contact object of the sender",
                    required=True,
                ),
                "html": ParameterDef(
                    type="string",
                    description="The HTML content of the letter",
                    required=True,
                ),
                "address_placement": ParameterDef(
                    type="string",
                    description="Location where the address will be placed. One of: top_first_page, insert_blank_page",
                ),
                "double_sided": ParameterDef(
                    type="boolean",
                    description="Whether the letter is double sided",
                ),
                "color": ParameterDef(
                    type="boolean",
                    description="Whether the letter will be printed in color",
                ),
                "perforated_page": ParameterDef(
                    type="integer",
                    description="Page number to be perforated",
                ),
                "extra_service": ParameterDef(
                    type="string",
                    description="Extra services for the letter. One of: certified, certified_return_receipt, registered",
                ),
                "envelope_type": ParameterDef(
                    type="string",
                    description="Envelope type. One of: standard_double_window, flat",
                ),
                "return_envelope": ParameterDef(
                    type="string",
                    description="The ID of the return envelope to be used",
                ),
                "send_date": ParameterDef(
                    type="string",
                    description="Desired date for the letter to be sent out (ISO 8601 format)",
                ),
                "description": ParameterDef(
                    type="string",
                    description="A description for the letter",
                ),
                "express": ParameterDef(
                    type="boolean",
                    description="Whether to use express shipping",
                ),
                "mailing_class": ParameterDef(
                    type="string",
                    description="Mailing class. One of: standard_class, first_class. Defaults to first_class",
                ),
                "size": ParameterDef(
                    type="string",
                    description="Letter size. One of: us_letter, us_legal, a4",
                ),
            },
        ),
        ActionDefinition(
            name="create_postcard",
            description="Create a new postcard in PostGrid",
            parameters={
                "to": ParameterDef(
                    type="string",
                    description="The ID or contact object of the receiver",
                    required=True,
                ),
                "from_contact": ParameterDef(
                    type="string",
                    description="The ID or contact object of the sender",
                    required=True,
                ),
                "front_html": ParameterDef(
                    type="string",
                    description="The HTML content for the front of the postcard",
                    required=True,
                ),
                "back_html": ParameterDef(
                    type="string",
                    description="The HTML content for the back of the postcard",
                    required=True,
                ),
                "size": ParameterDef(
                    type="string",
                    description="Postcard size. One of: 6x4, 9x6, 11x6",
                    required=True,
                ),
                "send_date": ParameterDef(
                    type="string",
                    description="Desired date for the postcard to be sent out (ISO 8601 format)",
                ),
                "express": ParameterDef(
                    type="boolean",
                    description="Whether to use express shipping",
                ),
                "description": ParameterDef(
                    type="string",
                    description="A description for the postcard",
                ),
                "mailing_class": ParameterDef(
                    type="string",
                    description="Mailing class. One of: standard_class, first_class. Defaults to first_class",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your PostGrid API key",
            setup_instructions=[
                "Sign in at https://app.postgrid.com",
                "Navigate to 'Settings' > 'API Keys'",
                "Copy your live or test API key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="POSTGRID_API_KEY",
                    display_name="PostGrid API Key",
                    description="Your PostGrid API key from app.postgrid.com",
                    required=True,
                    sensitive=True,
                    sample_format="live_sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.postgrid.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.postgrid.com/print-mail/v1/contacts",
                method="GET",
                headers={"x-api-key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API key by listing contacts",
            ),
        ),
    ],
)
