"""Mixpanel integration manifest."""
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
    name="mixpanel",
    display_name="Mixpanel",
    description="Product analytics platform for tracking user events and behaviors",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:mixpanel",
    app_url="https://mixpanel.com",
    categories=["Analytics", "Product Analytics"],
    actions=[
        ActionDefinition(
            name="emit_event_to",
            description="Send an event to Mixpanel",
            parameters={
                "event_name": ParameterDef(
                    type="string",
                    description="The name of the event (e.g. 'Button Click', 'Sign Up', 'Item Purchased')",
                    required=True,
                ),
                "distinct_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the user performing the event",
                    required=True,
                ),
                "properties": ParameterDef(
                    type="object",
                    description="A set of properties to include with the event describing the user or event details",
                    required=False,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Project Token",
            description="Authenticate using your Mixpanel Project Token for event ingestion",
            setup_instructions=[
                "Sign in at https://mixpanel.com",
                "Go to Settings > Project Settings",
                "Copy your Project Token",
                "Paste the token below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MIXPANEL_API_KEY",
                    display_name="Project Token",
                    description="Your Mixpanel Project Token from Settings > Project Settings",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developer.mixpanel.com/reference/project-token",
                ),
                EnvVar(
                    name="MIXPANEL_BASE_URL",
                    display_name="Ingestion Base URL",
                    description=(
                        "Mixpanel ingestion base URL (optional — leave "
                        "empty for https://api.mixpanel.com US default). "
                        "Set to https://api-eu.mixpanel.com for EU data "
                        "residency projects."
                    ),
                    required=False,
                    sensitive=False,
                    sample_format="https://api.mixpanel.com",
                    about_url="https://developer.mixpanel.com/reference/ingestion-api",
                ),
            ],
            test_endpoint=TestEndpoint(
                # Hardcoded US endpoint here because MIXPANEL_BASE_URL is
                # optional — when empty, ``{MIXPANEL_BASE_URL}`` would
                # substitute to "" and break the URL. tools.py reads the
                # user-supplied base URL at action call time and routes
                # ingest to the right region; this test only validates
                # the API token format.
                url="https://api.mixpanel.com/engage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body={
                    "$token": "{MIXPANEL_API_KEY}",
                    "$distinct_id": "$credential_test",
                    "$set": {"$credential_test": True},
                },
                # Mixpanel's /engage endpoint accepts JSON and returns 200
                # for any well-formed event regardless of token validity
                # (project tokens are not server-validated against an
                # account). This is a reachability + payload-format check
                # that confirms the configured base URL is reachable and
                # the token placeholder is substituted correctly.
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="minimal",
                description=(
                    "Reachability + payload check against Mixpanel's "
                    "/engage profile endpoint with a $credential_test "
                    "sentinel event. Returns 200 when the configured "
                    "base URL responds."
                ),
            ),
        ),
    ],
)
