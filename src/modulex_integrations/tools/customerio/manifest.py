"""Customer.io integration manifest.

Notes for migration:

- Legacy JSON's auth_schema carried two implementation-specific fields
  not in our schema: ``credential_mapping`` (key remap dict) and
  ``test_endpoint.auth = {type: basic, username, password}`` (Basic
  Auth using site_id:api_key). Both are dropped here. The test_endpoint
  is omitted entirely — modulex's credential test path for Customer.io
  needs a Basic-Auth-aware test endpoint that our ``TestEndpoint``
  schema doesn't yet model; until that schema enhancement lands,
  modulex skips credential validation for customerio.
- The runtime tool functions construct ``Authorization: Basic ...``
  themselves from the resolved site_id+api_key pair, so action
  invocation works unchanged.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="customerio",
    display_name="Customer.io",
    description=(
        "Marketing automation platform for personalized customer experiences "
        "through email, SMS, and push notifications"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="https://cdn.jsdelivr.net/gh/ModuleXAI/logox@main/tools/customerio.svg",
    app_url="https://customer.io",
    categories=["Marketing & Email", "social_media", "customer_support"],
    actions=[
        ActionDefinition(
            name="create_or_update_customer",
            description=(
                "Creates a new customer profile or updates an existing one "
                "in Customer.io"
            ),
            parameters={
                "customer_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the customer",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="The customer's email address",
                    required=True,
                ),
                "created_at": ParameterDef(
                    type="integer",
                    description=(
                        "UNIX timestamp from when the user was created in your system"
                    ),
                ),
                "attributes": ParameterDef(
                    type="object",
                    description="Custom attributes (name, plan, company, etc.)",
                ),
            },
        ),
        ActionDefinition(
            name="send_event",
            description=(
                "Sends a tracking event to a customer for triggering campaigns "
                "and segmentation"
            ),
            parameters={
                "customer_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the customer",
                    required=True,
                ),
                "event_name": ParameterDef(
                    type="string",
                    description="The name of the event to track",
                    required=True,
                ),
                "event_type": ParameterDef(
                    type="string",
                    description="Event type modifier (set to 'page' for page views)",
                ),
                "data": ParameterDef(
                    type="object", description="Custom data to include with the event"
                ),
            },
        ),
        ActionDefinition(
            name="add_customers_to_segment",
            description=(
                "Adds customers to a manual segment by their IDs (max 1000 per request)"
            ),
            parameters={
                "segment_id": ParameterDef(
                    type="string",
                    description="The segment ID",
                    required=True,
                ),
                "customer_ids": ParameterDef(
                    type="array",
                    description="List of customer IDs (max 1000)",
                    required=True,
                ),
                "id_type": ParameterDef(
                    type="string",
                    description="The type of IDs: 'id', 'email', or 'cio_id'",
                    default="id",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Customer.io Site ID and API Key",
            setup_environment_variables=[
                EnvVar(
                    name="CUSTOMERIO_SITE_ID",
                    display_name="Site ID",
                    description=(
                        "Your Customer.io Site ID (Settings > Workspace Settings > "
                        "API Credentials)"
                    ),
                    required=False,
                    sensitive=True,
                    sample_format="x" * 8 + "-" + "x" * 4 + "-" + "x" * 4,
                    about_url=(
                        "https://customer.io/docs/api/#section/Overview/Authentication"
                    ),
                ),
                EnvVar(
                    name="CUSTOMERIO_API_KEY",
                    display_name="API Key",
                    description=(
                        "Your Customer.io Tracking API Key (Settings > Workspace "
                        "Settings > API Credentials)"
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="x" * 32,
                    about_url=(
                        "https://customer.io/docs/api/#section/Overview/Authentication"
                    ),
                ),
            ],
            # test_endpoint dropped — Customer.io uses HTTP Basic Auth on its test
            # endpoint, which our TestEndpoint schema doesn't yet model. Schema
            # enhancement needed before modulex can validate these credentials
            # via the package manifest.
        ),
    ],
)
