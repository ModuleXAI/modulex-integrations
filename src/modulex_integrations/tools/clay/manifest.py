"""Clay integration manifest.

Clay is a data-enrichment and outbound automation platform. Records are
pushed into a Clay table through that table's inbound webhook URL; Clay
then runs its enrichment waterfall asynchronously.

Auth is key-based: the credential is the *optional* webhook auth token
that Clay sends in the ``x-clay-webhook-auth`` header when a table has
webhook authentication enabled. Most webhooks accept unauthenticated
requests, so the token is not strictly required.
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
    name="clay",
    display_name="Clay",
    description=(
        "Push records into a Clay table via its inbound webhook so Clay can "
        "run its data-enrichment waterfall on prospects and accounts."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:clay",
    app_url="https://www.clay.com",
    categories=["Sales", "CRM", "enrichment"],
    actions=[
        ActionDefinition(
            name="populate",
            description=(
                "Populate a Clay table with a record by sending it to the "
                "table's webhook URL. Clay enriches the record asynchronously; "
                "the response is an acknowledgment plus transport metadata."
            ),
            parameters={
                "webhook_url": ParameterDef(
                    type="string",
                    description="The Clay table webhook URL to send the record to",
                    required=True,
                ),
                "data": ParameterDef(
                    type="object",
                    description=(
                        "The record to populate, as a JSON object whose keys map "
                        "to the Clay table column names (e.g. name, email, "
                        "company, domain)"
                    ),
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Webhook Auth Token",
            description=(
                "Authenticate with the optional auth token from a Clay table's "
                "webhook source. Sent in the x-clay-webhook-auth header. Leave "
                "empty if the table's webhook does not require authentication."
            ),
            setup_instructions=[
                "In a Clay workbook, click + Add and search for 'Webhooks', "
                "then 'Monitor webhook'.",
                "Copy the webhook URL Clay shows for the table — this is the "
                "webhook_url action parameter.",
                "If the table has webhook authentication enabled, copy the "
                "auth token Clay displays (it is shown only once).",
                "Paste the auth token below; otherwise leave it blank.",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="CLAY_WEBHOOK_AUTH_TOKEN",
                    display_name="Clay Webhook Auth Token",
                    description=(
                        "Optional auth token for a Clay table webhook, sent in "
                        "the x-clay-webhook-auth header"
                    ),
                    required=False,
                    sensitive=True,
                    about_url="https://university.clay.com/docs/webhook-integration-guide",
                ),
            ],
        ),
    ],
)
